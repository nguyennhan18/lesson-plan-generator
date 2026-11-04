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
from lessonai.services.copilot import CopilotOutput
from lessonai.services.visual_requirements import confirm_requirement,visual_source
from lessonai.rag.content_units import source_hash,approved_units
from lessonai.rag.curriculum_registry import infer_lesson_id
from lessonai.services.uploads import inspect_office
from lessonai.core.jobs import JobError

pytestmark=pytest.mark.critical_regressions

@pytest.fixture
def api():
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
    with patch('lessonai.services.copilot.llm_gateway.generate_structured',return_value=output):
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
    with patch('lessonai.services.copilot.llm_gateway.generate_structured',side_effect=TimeoutError('offline')):
        response=api.post('/api/v1/chat/interact',json={'session_id':sid,'slide_deck':deck,'slide_id':deck['slides'][0]['slide_id'],'user_message':'Sửa bài'})
    assert response.status_code==503
    assert api.get('/api/v1/chat/history/'+sid).json()['history']==[]


@pytest.mark.parametrize('path',['/api/v1/lesson-plan/generate','/api/v1/slide/generate','/api/v1/presentation/outline'])
def test_generation_failure_returns_no_sample(path,api):
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured',side_effect=TimeoutError('offline')):
        response=api.post(path,json={'topic':'Bài chưa có nguồn','use_rag':False})
    assert response.status_code==503,response.text
    assert not any(key in response.json() for key in ['slides','plan','outline_slides'])
    assert api.post(path,json={'topic':'  '}).status_code==422


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
    (tmp_path/'reviewed_sources.json').write_text(json.dumps({'sources':[{'sha256':source_hash(item),'status':'approved','reviewer':'teacher-id','reviewed_at':'2026-11-03','asset_hashes':content_units.asset_manifest(item)}]}))
    assert approved_units([item])==[item]
    assert approved_units([{**item,'question':'Đã đổi'}])==[]
    (tmp_path/'p1.png').write_bytes(b'changed-image')
    assert approved_units([item])==[]


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
        entry=manifest['files'][0];assert entry['sha256']==hashlib.sha256(archive.read(entry['name'])).hexdigest()
        assert manifest['plan_quality']=='absent'


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


def test_generation_binds_citations_to_supplied_source_version(deck):
    from lessonai.services.generation.slides import generate_slide_deck
    refs=[{'source_type':'slide_kntt12','id':'p1','sha256':'actual-source-version'}]
    deck['slides'][0]['source_refs']=[{'source_type':'slide_kntt12','id':'p1','sha256':'invented-version'}]
    with patch('lessonai.rag.context_builder.PedagogicalContextBuilder.build_slide_deck_context',return_value=('source context',refs)), patch('lessonai.llm.gateway.llm_gateway.generate_structured',return_value=SlideDeckSchema.model_validate(deck)):
        with pytest.raises(ValueError,match='phiên bản nguồn'):
            generate_slide_deck('Bài',lesson_id='M12-C1-B1')
    deck['slides'][0]['source_refs'][0].pop('sha256')
    with patch('lessonai.rag.context_builder.PedagogicalContextBuilder.build_slide_deck_context',return_value=('source context',refs)), patch('lessonai.llm.gateway.llm_gateway.generate_structured',return_value=SlideDeckSchema.model_validate(deck)):
        result=generate_slide_deck('Bài',lesson_id='M12-C1-B1')
        assert result.slides[0].source_refs[0].model_dump()['sha256']=='actual-source-version'


def test_production_sample_preview_is_retired(api):
    response=api.post('/api/v1/rag/preview',json={'lesson_id':'M12-C1-B1'})
    assert response.status_code==410
    assert response.json()['detail']['code']=='sample_preview_removed'
    assert 'slides_preview' not in response.json()
