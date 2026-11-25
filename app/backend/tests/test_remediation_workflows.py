"""Behavioral acceptance for the production workflows introduced after M0."""
import copy
import hashlib
import io
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from docx import Document
from pptx import Presentation
from lessonai.main import create_app
from lessonai.schemas.slide_schema import SlideDeckSchema
from lessonai.services.assistant.copilot import CopilotOutput
from lessonai.services.quality.visual_requirements import confirm_requirement,visual_source
from lessonai.rag.content_units import source_hash,approved_units
from lessonai.rag.curriculum_registry import infer_lesson_id
from lessonai.services.uploads import inspect_office
from lessonai.services.jobs import JobError

pytestmark=pytest.mark.critical_regressions

@pytest.fixture
def api(tmp_path,monkeypatch):
    monkeypatch.setenv('LESSONAI_CONFIG_DIR',str(tmp_path/'signing-config'))  # A throwaway key, never the teacher's (ADR 0005).
    with TestClient(create_app()) as client:
        assert client.post('/api/v1/session').status_code==200
        yield client

@pytest.fixture
def deck():
    return SlideDeckSchema.model_validate({'subject':'Toán học','grade':12,'presentation_title':'Kiểm tra bài','slides':[{'slide_index':1,'title':'Bài của giáo viên','bullet_points':['Tính tổng $1+1$.'],'worked_solution_steps':['$1+1=2$']}]}).model_dump(mode='json')


def test_contract_preserves_legacy_source_and_unknown_blocks():
    raw={'subject':'Toán học','grade':12,'presentation_title':'Nhập','slides':[{'slide_number':3,'title':'Đề','blocks':[{'type':'table','rows':[['x','y'],[1,2]]}],'source_refs':[{'source':'book','slide_id':'p5','page':5}]}]}
    model=SlideDeckSchema.model_validate(raw)
    assert model.slides[0].slide_index==1
    assert model.slides[0].source_refs[0].id=='p5'
    assert model.slides[0].source_refs[0].model_dump()['page']==5
    assert model.model_dump()['slides'][0]['blocks']==raw['slides'][0]['blocks']
    with pytest.raises(ValueError):
        SlideDeckSchema.model_validate({**raw,'slides':[{'slide_number':1,'slide_index':2,'title':'Mâu thuẫn'}]})


def test_quality_gate_rejects_false_numeric_step_and_stale_approval(api,deck):
    deck['slides'][0]['worked_solution_steps']=['$1+1=3$']
    report=api.post('/api/v1/quality/check',json=deck).json()
    assert report['status']=='blocked'
    assert api.post('/api/v1/quality/approve',json={'deck':deck,'acknowledged':True}).status_code==409
    deck['slides'][0]['worked_solution_steps']=['$1+1=2$']
    report=api.post('/api/v1/quality/check',json=deck).json()
    approval=api.post('/api/v1/quality/approve',json={'deck':deck,'acknowledged':True,'content_fingerprint':report['content_fingerprint'],'reviewed_issue_ids':[i['issue_id'] for i in report['issues']]})
    assert approval.status_code==200,approval.text
    deck['review_token']=approval.json()['review_token']
    assert api.post('/api/v1/quality/check',json=deck).json()['status']=='ready'
    exported=Presentation(io.BytesIO(api.post('/api/v1/lesson-plan/export-slide',json=deck).content))
    assert 'BẢN NHÁP' not in ' '.join(shape.text for page in exported.slides for shape in page.shapes if shape.has_text_frame)
    deck['slides'][0]['title']='Đổi đề'
    assert api.post('/api/v1/quality/check',json=deck).json()['status']=='needs_review'


def test_visual_confirmation_bound_to_slide_source(api,deck):
    slide=deck['slides'][0]
    spec={'kind':'geometry','polyhedron_type':'square_pyramid_at_a','base_edge':4,'height':3,'deck_id':deck['deck_id'],'slide_id':slide['slide_id']}
    response=api.post('/api/v1/visuals/confirm',json={**spec,'source':slide}).json()
    slide.update(has_3d=True,scene_spec={**spec,**response['requirement']['spec'],'requirement_token':response['requirement_token']})
    assert api.post('/api/v1/visuals/scene',json=slide['scene_spec']).json()['vertices']['S']==[0,0,3]
    assert api.post('/api/v1/quality/check',json=deck).json()['status']=='needs_review'
    slide['bullet_points']=['Dữ kiện mới']
    assert api.post('/api/v1/quality/check',json=deck).json()['status']=='blocked'


def test_copilot_proposal_ownership_revision_idempotence_reset(api,deck):
    sid=api.post('/api/v1/chat/sessions',json={'slide_deck':deck}).json()['session_id']
    output=CopilotOutput(ai_response='Đổi tiêu đề theo yêu cầu',slide_id=deck['slides'][0]['slide_id'],changes={'title':'Tiêu đề đã sửa'})
    payload={'session_id':sid,'slide_deck':deck,'slide_id':output.slide_id,'user_message':'Sửa tiêu đề'}
    with patch('lessonai.services.assistant.copilot.llm_gateway.generate_structured',return_value=output):
        response=api.post('/api/v1/chat/interact',json=payload)
    assert response.status_code==200,response.text
    proposal=response.json()['suggested_patch'];assert proposal and proposal['before']['title']=='Bài của giáo viên'
    apply={'proposal_id':proposal['proposal_id'],'slide_deck':deck,'acknowledged':True}
    changed=copy.deepcopy(deck);changed['slides'][0]['title']='Đã sửa tay'
    assert api.post('/api/v1/chat/apply-patch',json={**apply,'slide_deck':changed}).status_code==409
    with TestClient(create_app()) as outsider:
        outsider.post('/api/v1/session')
        assert outsider.get('/api/v1/chat/history/'+sid).status_code==404
        assert outsider.post('/api/v1/chat/apply-patch',json=apply).status_code==404
    first=api.post('/api/v1/chat/apply-patch',json=apply)
    assert first.status_code==200,first.text
    result=first.json()['slide_deck'];assert result['revision']==deck['revision']+1
    assert result['slides'][0]['title']=='Tiêu đề đã sửa'
    assert api.post('/api/v1/chat/apply-patch',json=apply).json()['slide_deck']==result
    assert api.delete('/api/v1/chat/session/'+sid).status_code==200
    assert api.post('/api/v1/chat/apply-patch',json=apply).status_code==404


def test_copilot_provider_failure_does_not_create_patch(api,deck):
    sid=api.post('/api/v1/chat/sessions',json={'slide_deck':deck}).json()['session_id']
    with patch('lessonai.services.assistant.copilot.llm_gateway.generate_structured',side_effect=TimeoutError('offline')):
        response=api.post('/api/v1/chat/interact',json={'session_id':sid,'slide_deck':deck,'slide_id':deck['slides'][0]['slide_id'],'user_message':'Sửa bài'})
    assert response.status_code==503
    assert api.get('/api/v1/chat/history/'+sid).json()['history']==[]


_WB_OUTLINE_PAYLOAD = {
    'title': 'Khảo sát hàm số',
    'level': 'standard',
    'outline': {
        'items': [
            {'item_id': 'm1', 'activity': 'Khởi động', 'kind': 'Mở đầu', 'title': 'Mở đầu', 'points': ['Ý 1'], 'slide_count': 1, 'minutes': 5},
            {'item_id': 'm2', 'activity': 'Hình thành kiến thức', 'kind': 'Kiến thức trọng tâm', 'title': 'Kiến thức', 'points': ['Ý 2'], 'slide_count': 1, 'minutes': 15},
            {'item_id': 'm3', 'activity': 'Luyện tập', 'kind': 'Bài luyện tập', 'title': 'Luyện tập', 'points': ['Ý 3'], 'slide_count': 1, 'minutes': 15},
            {'item_id': 'm4', 'activity': 'Vận dụng', 'kind': 'Tổng kết', 'title': 'Tổng kết', 'points': ['Ý 4'], 'slide_count': 1, 'minutes': 10},
        ]
    },
}


@pytest.mark.parametrize('path,payload,empty_payload',[
    ('/api/v1/workbench/outline', {'request': 'Bài chưa có nguồn', 'level': 'standard'}, {'request': '  ', 'level': 'standard'}),
    ('/api/v1/workbench/slides', _WB_OUTLINE_PAYLOAD, {**_WB_OUTLINE_PAYLOAD, 'title': '  '}),
    ('/api/v1/workbench/lesson-plan', _WB_OUTLINE_PAYLOAD, {**_WB_OUTLINE_PAYLOAD, 'title': '  '}),
])
def test_generation_failure_returns_no_sample(path,payload,empty_payload,api):
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured',side_effect=TimeoutError('offline')):
        response=api.post(path,json=payload)
    assert response.status_code==503,response.text
    assert response.json()['detail']['code']=='generation_unavailable'
    assert not any(key in response.json() for key in ['slides','plan','outline'])
    assert api.post(path,json=empty_payload).status_code==422
    # Các endpoint sinh cũ trả 410 Gone (#59)
    assert api.post('/api/v1/presentation/outline',json={'topic':'Bài'}).status_code==410
    assert api.post('/api/presentation/outline',json={'topic':'Bài'}).status_code==410
    assert api.post('/api/v1/slide/generate',json={'topic':'Bài'}).status_code==410


@pytest.mark.parametrize('path,payload',[
    ('/api/v1/workbench/outline', {'request': 'Khảo sát hàm số', 'level': 'standard'}),
    ('/api/v1/workbench/slides', _WB_OUTLINE_PAYLOAD),
    ('/api/v1/workbench/lesson-plan', _WB_OUTLINE_PAYLOAD),
])
def test_generation_error_classification_across_exception_chain(path,payload,api):
    import json
    from lessonai.schemas.schemas import LessonPlanSchema

    # 1. ValidationError & JSONDecodeError bọc trong nhiều tầng RuntimeError (__cause__ / __context__),
    #    kể cả khi thông báo chứa từ khóa "schema", "401", "additionalProperties"
    try:
        LessonPlanSchema.model_validate({'lesson_title':'401 invalid api key schema additionalProperties is only supported'})
    except Exception as raw_val_err:
        validation_err = raw_val_err
    wrapped_val = RuntimeError('Toàn bộ 3 tuyến LLM đều không phản hồi')
    wrapped_val.__cause__ = validation_err
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured',side_effect=wrapped_val):
        res_val = api.post(path,json=payload)
    assert res_val.status_code==503
    detail_val = res_val.json()['detail']
    assert detail_val['code']=='invalid_ai_output'
    assert 'Bản soạn được giữ nguyên' in detail_val['message']
    assert detail_val.get('request_id') and res_val.headers.get('X-Request-ID') == detail_val['request_id']
    assert not any(key in res_val.json() for key in ['slides','plan','outline'])

    wrapped_json = RuntimeError('Toàn bộ 3 tuyến LLM đều không phản hồi')
    wrapped_json.__context__ = json.JSONDecodeError('Expecting value', '{bad json', 1)
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured',side_effect=wrapped_json):
        res_json = api.post(path,json=payload)
    assert res_json.status_code==503
    assert res_json.json()['detail']['code']=='invalid_ai_output'

    # 2. Lỗi cấu hình / API key / SDK schema bị bọc trong RuntimeError
    for cfg_exc in [
        ValueError('Không tìm thấy tuyến LLM khả dụng. Kiểm tra API key.'),
        ValueError('additionalProperties is only supported in Gemini Enterprise Agent Platform mode'),
        RuntimeError('401 API_KEY_INVALID'),
    ]:
        wrapped_cfg = RuntimeError('Toàn bộ 3 tuyến LLM đều không phản hồi')
        wrapped_cfg.__cause__ = cfg_exc
        with patch('lessonai.llm.gateway.llm_gateway.generate_structured',side_effect=wrapped_cfg):
            res_cfg = api.post(path,json=payload)
        assert res_cfg.status_code==503
        detail_cfg = res_cfg.json()['detail']
        assert detail_cfg['code']=='llm_configuration_error'
        assert 'Bản soạn được giữ nguyên' in detail_cfg['message']
        assert detail_cfg.get('request_id') and res_cfg.headers.get('X-Request-ID') == detail_cfg['request_id']

    # 3. ValueError do lệch hợp đồng dàn ý / định dạng đầu ra
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured',side_effect=ValueError('Slide không giữ định danh/thứ tự/tiêu đề dàn ý đã duyệt')):
        res_contract = api.post(path,json=payload)
    assert res_contract.status_code==503
    detail_contract = res_contract.json()['detail']
    assert detail_contract['code']=='invalid_ai_output'
    assert 'Bản soạn được giữ nguyên' in detail_contract['message']
    assert detail_contract.get('request_id') and res_contract.headers.get('X-Request-ID') == detail_contract['request_id']


def test_outline_contract_rejects_wrong_order_and_preserves_approved_content(deck):
    from lessonai.services.generation.slides import generate_slide_deck
    outline={'outline_slides':[{'id':'out1','title':'Bài của giáo viên','bullet_points':['Tính tổng $1+1$.']}]}
    deck['slides'][0]['source_outline_id']='out1'
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured',return_value=SlideDeckSchema.model_validate(deck)) as gateway:
        result=generate_slide_deck('Bài',approved_outline=outline,use_rag=False,model_provider='groq',model_id='chosen')
        assert result.slides[0].source_outline_id=='out1'
        assert gateway.call_args.kwargs['model_id']=='chosen'
        assert 'out1' in gateway.call_args.kwargs['prompt']
    deck['slides'][0]['source_outline_id']='wrong'
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured',return_value=SlideDeckSchema.model_validate(deck)):
        with pytest.raises(ValueError,match='dàn ý'):generate_slide_deck('Bài',approved_outline=outline,use_rag=False)


def test_outline_contract_3d_draft_and_polyhedron_kinds(api):
    from lessonai.services.generation.slides import generate_slide_deck
    from lessonai.services.quality.content_quality import evaluate_deck

    outline_3d = {
        'outline_slides': [{
            'id': 'out-3d-1',
            'title': 'Hình lập phương',
            'activity_type': 'Hình thành kiến thức',
            'visual_type': '3D Geometry',
            'has_3d': True,
            'polyhedron_type': 'cube',
            'bullet_points': ['Xét hình lập phương cạnh $a$.'],
        }]
    }
    draft_3d = SlideDeckSchema.model_validate({
        'presentation_title': 'Hình học không gian',
        'subject': 'Toán học',
        'grade': 12,
        'slides': [{
            'slide_id': 's-3d',
            'source_outline_id': 'out-3d-1',
            'title': 'Hình lập phương',
            'activity_type': 'Hình thành kiến thức',
            'has_3d': True,
            'polyhedron_type': '  CUBE  ',
            'scene_spec': None,
            'bullet_points': ['Xét hình lập phương cạnh $a$.'],
        }],
    })
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured', return_value=draft_3d):
        generated = generate_slide_deck('Hình lập phương', approved_outline=outline_3d, use_rag=False)
    assert generated.slides[0].polyhedron_type == 'cube'
    assert generated.slides[0].scene_spec is None

    # Bước duyệt chất lượng vẫn bắt buộc phải có scene_spec đã xác nhận HMAC
    report = evaluate_deck(generated.model_dump(mode='json'))
    assert report['status'] == 'blocked'
    assert any(i['field'] == 'scene_spec' and i['severity'] == 'error' for i in report['issues'])

    # Slide không bật 3D giữ polyhedron_type = None
    non_3d = SlideDeckSchema.model_validate({
        'presentation_title': 'Giải tích',
        'subject': 'Toán học',
        'grade': 12,
        'slides': [{'slide_id': 's1', 'title': 'Đạo hàm', 'has_3d': False, 'polyhedron_type': '  '}],
    })
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured', return_value=non_3d):
        res_non_3d = generate_slide_deck('Đạo hàm', use_rag=False)
    assert res_non_3d.slides[0].polyhedron_type is None

    # Tên khối cũ ("pyramid_square") không được tự ép sang "square_pyramid_regular" và trả về invalid_ai_output
    invalid_poly_draft = SlideDeckSchema.model_validate({
        'presentation_title': 'Hình chóp',
        'subject': 'Toán học',
        'grade': 12,
        'slides': [{
            'slide_id': 's-bad',
            'source_outline_id': 'out-3d-1',
            'title': 'Hình lập phương',
            'activity_type': 'Hình thành kiến thức',
            'has_3d': True,
            'polyhedron_type': 'pyramid_square',
            'bullet_points': ['Xét hình lập phương cạnh $a$.'],
        }],
    })
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured', return_value=invalid_poly_draft):
        with pytest.raises(ValueError, match='tập chuẩn được hỗ trợ'):
            generate_slide_deck('Hình chóp', approved_outline=outline_3d, use_rag=False)
    wb_bad_visual = {
        **_WB_OUTLINE_PAYLOAD,
        'outline': {
            'items': [
                *_WB_OUTLINE_PAYLOAD['outline']['items'][:1],
                {
                    **_WB_OUTLINE_PAYLOAD['outline']['items'][1],
                    'visuals': [{'visual_id': 'v-3d', 'kind': 'solid', 'origin': 'ai', 'status': 'confirmed', 'data': {'polyhedron_type': 'cube', 'base_edge': 2, 'height': 2}}],
                },
                *_WB_OUTLINE_PAYLOAD['outline']['items'][2:],
            ]
        },
    }
    with patch('lessonai.services.generation.workbench_slides.llm_gateway.generate_structured', return_value={'slides': [
        {'item_id': 'm1', 'layout': 'Mở đầu', 'title': 'Mở đầu'},
        {'item_id': 'm2', 'layout': 'Chữ trái, hình phải', 'title': 'Kiến thức'},  # thiếu visual_id v-3d
        {'item_id': 'm3', 'layout': 'Nội dung', 'title': 'Luyện tập'},
        {'item_id': 'm4', 'layout': 'Tổng kết', 'title': 'Tổng kết'},
    ]}):
        resp = api.post('/api/v1/workbench/slides', json=wb_bad_visual)
    assert resp.status_code == 503
    assert resp.json()['detail']['code'] == 'invalid_ai_output'


def test_outline_contract_string_normalization_warns_without_dropping_checks(api):
    from lessonai.schemas.schemas import LessonPlanSchema
    from lessonai.services.generation.slides import generate_slide_deck
    from lessonai.services.generation.outline_contract import validate_plan_outline

    outline = {
        'outline_slides': [{
            'id': 'out-m1',
            'title': 'Định lý tính đơn điệu',
            'activity_type': 'Hình thành kiến thức',
            'visual_type': 'Concept Highlight',
            'bullet_points': ['Nếu đạo hàm dương trên khoảng K thì hàm số đồng biến'],
            'math_focus': "$f'(x) > 0$",
        }]
    }
    draft_slide = SlideDeckSchema.model_validate({
        'presentation_title': 'Tính đơn điệu',
        'subject': 'Toán học',
        'grade': 12,
        'slides': [{
            'slide_id': 's1',
            'source_outline_id': 'out-m1',
            'title': 'Định lý tính đơn điệu.',
            'activity_type': 'Hình thành kiến thức',
            'layout': 'CONCEPT_HIGHLIGHT',
            'bullet_points': ['Nếu đạo hàm dương trên khoảng K thì hàm số đồng biến trên K.'],
            'main_definition_latex': "f'(x) > 0",
        }],
    })
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured', return_value=draft_slide):
        deck_res = generate_slide_deck('Tính đơn điệu', approved_outline=outline, use_rag=False)
    assert getattr(deck_res, 'outline_warnings', None)
    assert len(deck_res.outline_warnings) >= 2

    # Giáo án giữ đủ nội dung dàn ý nhưng khác dấu câu/ký hiệu $ -> trả về cảnh báo, không ném lỗi
    plan = LessonPlanSchema.model_validate({
        'lesson_title': 'Bài 1: Tính đơn điệu',
        'subject': 'Toán học',
        'grade': 12,
        'knowledge_goals': ['Hiểu định lý'],
        'activities': [
            {'activity_number': 1, 'time_minutes': 5, 'goal': 'Khởi động', 'expected_product': 'Trả lời', 'execution': {'step_1_assign': 'A', 'step_2_excute': 'B', 'step_3_report': 'C', 'step_4_conclusion': 'D'}},
            {'activity_number': 2, 'time_minutes': 20, 'goal': "Định lý tính đơn điệu: f'(x) > 0", 'expected_product': 'Nếu đạo hàm dương trên khoảng K thì hàm số đồng biến trên K.', 'execution': {'step_1_assign': 'A', 'step_2_excute': 'B', 'step_3_report': 'C', 'step_4_conclusion': 'D'}},
            {'activity_number': 3, 'time_minutes': 10, 'goal': 'Luyện tập', 'expected_product': 'Giải bài', 'execution': {'step_1_assign': 'A', 'step_2_excute': 'B', 'step_3_report': 'C', 'step_4_conclusion': 'D'}},
            {'activity_number': 4, 'time_minutes': 10, 'goal': 'Vận dụng', 'expected_product': 'Giải bài', 'execution': {'step_1_assign': 'A', 'step_2_excute': 'B', 'step_3_report': 'C', 'step_4_conclusion': 'D'}},
        ],
    })
    plan_warnings = validate_plan_outline(plan, outline)
    assert plan_warnings

    # Nhưng nếu bỏ mất nội dung đã duyệt -> vẫn bắt buộc ném ValueError -> invalid_ai_output
    dropped_slide = SlideDeckSchema.model_validate({
        'presentation_title': 'Tính đơn điệu',
        'subject': 'Toán học',
        'grade': 12,
        'slides': [{
            'slide_id': 's1',
            'source_outline_id': 'out-m1',
            'title': 'Định lý tính đơn điệu',
            'activity_type': 'Hình thành kiến thức',
            'layout': 'CONCEPT_HIGHLIGHT',
            'bullet_points': ['Một nội dung khác hoàn toàn không liên quan'],
            'main_definition_latex': "f'(x) > 0",
        }],
    })
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured', return_value=dropped_slide):
        with pytest.raises(ValueError, match='bỏ nội dung đã duyệt'):
            generate_slide_deck('Tính đơn điệu', approved_outline=outline, use_rag=False)
    with patch('lessonai.services.generation.workbench_slides.llm_gateway.generate_structured', return_value={'slides': [
        {'item_id': 'm1', 'layout': 'Mở đầu', 'title': 'Chỉ trả 1 slide thay vì đủ 4 Mục'},
    ]}):
        resp_drop = api.post('/api/v1/workbench/slides', json=_WB_OUTLINE_PAYLOAD)
    assert resp_drop.status_code == 503
    assert resp_drop.json()['detail']['code'] == 'invalid_ai_output'


def test_unknown_curriculum_never_maps_to_first_lesson():
    assert infer_lesson_id('Ứng dụng hình học của tích phân')=='M12-C4-B3'
    assert infer_lesson_id('Ứng dụng tích phân tính diện tích hình phẳng')=='M12-C4-B3'
    assert infer_lesson_id('Chủ đề hoàn toàn chưa xác định') is None
    assert infer_lesson_id('') is None


def test_source_quarantine_requires_reviewed_hash(tmp_path,monkeypatch):
    from lessonai.rag import content_units
    monkeypatch.setattr(content_units,'DATA_DIR',tmp_path)
    item={'id':'q','question':'Tính tổng','worked_solution_steps':['1+1=2'],'images':['p1.png']}
    assert approved_units([item])==[]
    (tmp_path/'p1.png').write_bytes(b'original-image')
    record={'source_id':'q','document_version':'unknown','sha256':source_hash(item),'status':'approved','reviewer':'teacher-id','reviewed_at':'2026-11-03','asset_hashes':content_units.asset_manifest(item)}
    (tmp_path/'reviewed_sources.json').write_text(json.dumps({'sources':[record]}))
    assert approved_units([item])==[]  # approval thiếu hash_version bị từ chối
    (tmp_path/'reviewed_sources.json').write_text(json.dumps({'sources':[{**record,'hash_version':content_units.HASH_VERSION}]}))
    assert approved_units([item])==[item]
    assert approved_units([{**item,'question':'Đã đổi'}])==[]
    (tmp_path/'p1.png').write_bytes(b'changed-image')
    assert approved_units([item])==[]


def test_runtime_registry_is_created_and_revoked_records_are_rejected(tmp_path, monkeypatch):
    from lessonai.rag import content_units
    monkeypatch.setattr(content_units, 'DATA_DIR', tmp_path)
    item = {'id': 'q-revoked', 'question': 'Tính tổng', 'images': []}
    registry = content_units.load_approval_registry()
    assert registry['sources'] == []
    assert (tmp_path / 'reviewed_sources.json').exists()
    assert content_units.approved_units([item]) == []
    revoked = content_units.register_source_approval(item, 'teacher-id', status='revoked')
    assert revoked['status'] == 'revoked'
    assert content_units.approved_units([item]) == []


def test_pptx_export_preserves_solution_and_ignores_unscoped_image(api,deck):
    deck['snapshot_3d_base64']='data:image/png;base64,not-real'
    before=copy.deepcopy(deck)
    response=api.post('/api/v1/lesson-plan/export-slide',json=deck)
    assert response.status_code==200,response.text
    prs=Presentation(io.BytesIO(response.content))
    text=' '.join(shape.text for page in prs.slides for shape in page.shapes if shape.has_text_frame)
    assert '1+1=2' in text.replace(' ','') and 'BẢN NHÁP' in text
    assert deck==before
    assert not any(shape.shape_type==13 for page in prs.slides for shape in page.shapes)


def test_partial_zip_manifest_lists_only_existing_parts(api,deck):
    response=api.post('/api/v1/lesson-plan/export-dual-package',json={'slide_deck':deck})
    assert response.status_code==200,response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names=archive.namelist();assert len(names)==2
        manifest=json.loads(archive.read(next(name for name in names if name.endswith('.txt'))))
        assert manifest['deck_id']==deck['deck_id']
        assert len(manifest['files'])==1


def test_corrupted_registry_is_preserved_and_fail_closed(tmp_path, monkeypatch):
    from lessonai.rag import content_units
    monkeypatch.setattr(content_units, 'DATA_DIR', tmp_path)
    registry_path = tmp_path / 'reviewed_sources.json'
    registry_path.write_text('{"schema_version":', encoding='utf-8')
    assert content_units.load_approval_registry()['sources'] == []
    assert list(tmp_path.glob('reviewed_sources.json.corrupt.*'))
    assert registry_path.read_text(encoding='utf-8').startswith('{"schema_version":')


def test_concurrent_registry_updates_do_not_lost_update(tmp_path, monkeypatch):
    from lessonai.rag import content_units
    monkeypatch.setattr(content_units, 'DATA_DIR', tmp_path)
    item = {'id': 'concurrent-1', 'source_id': 'source-1', 'source_type': 'slide_kntt12', 'document_version': 'v1', 'question': 'Tổng', 'images': []}

    def approve():
        return content_units.register_source_approval(item, 'teacher-a', status='approved')

    def revoke():
        return content_units.revoke_source_approval(item, reason='stale', reviewer='teacher-b')

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(approve), executor.submit(revoke)]
        results = [future.result() for future in futures]

    registry = content_units.load_approval_registry()
    assert len(registry['sources']) == 1
    statuses = {entry['status'] for entry in registry['sources']}
    assert statuses.issubset({'approved', 'revoked'})
    assert all('sha256' in entry for entry in registry['sources'])
    assert any(result['status'] in {'approved', 'revoked'} for result in results)


def test_legacy_approval_records_without_identity_are_rejected(tmp_path, monkeypatch):
    from lessonai.rag import content_units
    monkeypatch.setattr(content_units, 'DATA_DIR', tmp_path)
    item = {'id': 'legacy', 'source_id': 'legacy-a', 'source_type': 'question_bank_rag', 'document_version': 'v1', 'question': 'Tổng', 'images': []}
    payload = {'schema_version': 1, 'updated_at': '2026-01-01T00:00:00+00:00', 'sources': [{'status': 'approved', 'sha256': content_units.source_hash(item), 'reviewer': 'teacher', 'reviewed_at': '2026-01-01', 'asset_hashes': {}}]}
    content_units.save_approval_registry(payload)
    assert content_units.approved_units([item]) == []


def test_retriever_public_access_filters_unapproved_sources(tmp_path, monkeypatch):
    from lessonai.rag import content_units
    from lessonai.rag.retriever import Math12HybridRetriever
    monkeypatch.setattr(content_units, 'DATA_DIR', tmp_path)
    raw_item = {'id': 'raw-q', 'source_id': 'raw-q', 'source_type': 'question_bank_rag', 'document_version': 'v1', 'question': 'Tính tổng', 'images': []}
    retriever = Math12HybridRetriever.__new__(Math12HybridRetriever)
    retriever._slides = [raw_item]
    retriever._slides_by_lesson = {'L1': [raw_item]}
    retriever._questions = [raw_item]
    retriever._questions_by_lesson = {'L1': [raw_item]}
    assert retriever.slides == []
    assert retriever.questions == []
    assert retriever.get_approved_slides('L1') == []
    assert retriever.get_approved_questions('L1') == []
    assert retriever.retrieve_exemplar_slides('L1', k=2) == []
    assert retriever.retrieve_questions('L1', k=2) == []


def test_approval_identity_rejects_version_and_asset_changes(tmp_path, monkeypatch):
    from lessonai.rag import content_units
    monkeypatch.setattr(content_units, 'DATA_DIR', tmp_path)
    item = {'id': 'versioned', 'source_id': 'source-2', 'source_type': 'slide_kntt12', 'document_version': 'v1', 'question': 'Tính tổng', 'images': []}
    content_units.register_source_approval(item, 'teacher-id')
    assert content_units.approved_units([item]) == [item]
    version_change = {**item, 'document_version': 'v2'}
    assert content_units.approved_units([version_change]) == []
    asset_item = {**item, 'images': ['asset.png']}
    (tmp_path / 'asset.png').write_bytes(b'asset-v1')
    content_units.register_source_approval(asset_item, 'teacher-id')
    (tmp_path / 'asset.png').write_bytes(b'asset-v2')
    assert content_units.approved_units([asset_item]) == []


def test_upload_analytics_exact_counts_and_zero_mean(api):
    response=api.post('/api/v1/ingest/classify-grades',files={'file':('scores.csv',b'Name,Score\nA,2\nB,4\nC,8\nD,10\n','text/csv')})
    assert response.status_code==200,response.text
    data=response.json();assert data['counts']=={'below_5':2,'between_5_8':0,'above_8':2}
    response=api.post('/api/v1/ingest/classify-grades',files={'file':('scores.csv',b'Name,Score\nA,0\nB,0\n','text/csv')})
    assert response.status_code==200,response.text
    assert response.json()['cv'] is None


def test_upload_rejects_zip_traversal_and_limits(api):
    content=io.BytesIO()
    with zipfile.ZipFile(content,'w') as archive:
        archive.writestr('word/document.xml','<document/>');archive.writestr('../outside','x')
    with pytest.raises(JobError,match='không được phép'):inspect_office(content.getvalue(),'.docx')
    response=api.post('/api/v1/ingest/parse-document',files={'file':('bad.docx',content.getvalue())})
    assert response.status_code==422
    assert api.post('/api/v1/ingest/parse-document',files={'file':('big.docx',b'x'*(12*1024*1024+1))}).status_code==413
    assert api.post('/api/v1/ingest/parse-document',files={'file':('wrong.txt',b'x')}).status_code==415
    capped=api.post('/api/v1/ingest/parse-document',content=b'',headers={'Content-Length':str(17*1024*1024)})
    assert capped.status_code==413
    assert capped.json()['detail']['request_id']==capped.headers['X-Request-ID']


def test_office_equations_and_media_are_preserved(api):
    from docx.oxml import parse_xml
    doc=Document();p=doc.add_paragraph('Công thức:')
    p._p.append(parse_xml('<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><m:r><m:t>x+1</m:t></m:r></m:oMath>'))
    stream=io.BytesIO();doc.save(stream)
    response=api.post('/api/v1/ingest/parse-document',files={'file':('native.docx',stream.getvalue())})
    assert response.status_code==200,response.text
    assert any(block.get('format')=='omml' and 'x+1' in block.get('xml','') for block in response.json()['blocks'])
    assert response.json()['extraction_status']=='needs_review'


def test_foreign_origin_and_unsigned_sessions_rejected(deck):
    with TestClient(create_app()) as client:
        assert client.post('/api/v1/chat/sessions',json={'slide_deck':deck}).status_code==401
        denied=client.post('/api/v1/session',headers={'Origin':'https://foreign.example'})
        assert denied.status_code==403
        assert denied.json()['detail']['request_id']==denied.headers['X-Request-ID']
        assert client.get('/api/v1/test-cases').status_code==404
        assert client.get('/api/v1/geometry/apex-coordinates').status_code==410


def test_export_fails_explicitly_when_formula_cannot_be_inserted(deck):
    from lessonai.exporters.slide_exporter import export_slide_deck_to_pptx
    deck['slides'][0]['main_definition_latex']='1+1=2'
    with patch('lessonai.exporters.slide_exporter.render_latex_to_bytes',side_effect=RuntimeError('renderer failed')):
        with pytest.raises(ValueError,match='chèn công thức'):
            export_slide_deck_to_pptx(deck)


def test_generation_rejects_citations_while_rag_is_paused(deck):
    from lessonai.services.generation.slides import generate_slide_deck
    deck['slides'][0]['source_refs']=[{'source_type':'slide_kntt12','id':'p1','sha256':'invented-version'}]
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured',return_value=SlideDeckSchema.model_validate(deck)):
        with pytest.raises(ValueError,match='RAG tạm ngừng'):
            generate_slide_deck('Bài',lesson_id='M12-C1-B1',use_rag=True)


def test_production_sample_preview_is_retired(api):
    response=api.post('/api/v1/rag/preview',json={'lesson_id':'M12-C1-B1'})
    assert response.status_code==410
    assert response.json()['detail']['code']=='sample_preview_removed'
    assert 'slides_preview' not in response.json()
