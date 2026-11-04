"""Public block/provenance contract and independent lesson-plan review workflow."""
import copy
import io
import json
import zipfile
from unittest.mock import patch
import pytest
from docx import Document
from pydantic import ValidationError
from lessonai.schemas.schemas import LessonPlanSchema
from lessonai.schemas.slide_schema import SlideDeckSchema
from lessonai.schemas.provenance import GenerationMetadata
from lessonai.services.lesson_quality import reviewed_plan, plan_snapshot
from test_remediation_workflows import api, deck

pytestmark = pytest.mark.critical_regressions


@pytest.fixture
def plan():
    return LessonPlanSchema.model_validate({
        'lesson_title': 'Tổng hai số', 'knowledge_goals': ['Tính tổng hai số'],
        'competency_goals': ['Trình bày phép tính'],
        'activities': [
            {'activity_number': i, 'time_minutes': minutes, 'goal': name + ': tính tổng hai số',
             'expected_product': '$1+1=2$', 'execution': {
                 'step_1_assign': 'Giáo viên giao nhiệm vụ tính tổng.',
                 'step_2_excute': 'Học sinh thực hiện và ghi phép tính.',
                 'step_3_report': 'Học sinh báo cáo và đối chiếu kết quả.',
                 'step_4_conclusion': 'Giáo viên kết luận về phép tính.'}}
            for i, (name, minutes) in enumerate(zip(['Khởi động', 'Hình thành kiến thức', 'Luyện tập', 'Vận dụng'], [5,20,10,10]), 1)
        ],
        'generation_metadata': {'provider': 'google', 'model': 'test-model', 'task': 'lesson_plan', 'generated_at': 123, 'prompt_sha256': 'a'*64},
        'approved_outline': {'outline_slides': [{'id': 'start', 'title': 'Khởi động', 'activity_type': 'Khởi động', 'bullet_points': ['tính tổng hai số']}]},
    }).model_dump(mode='json')


def approve(api, plan):
    report = api.post('/api/v1/quality/lesson-plan/check', json=plan).json()
    assert report['status'] == 'needs_review', report
    payload = {'plan': plan, 'acknowledged': True, 'content_fingerprint': report['content_fingerprint'],
               'reviewed_issue_ids': [i['issue_id'] for i in report['issues'] if i['severity'] == 'warning']}
    result = api.post('/api/v1/quality/lesson-plan/approve', json=payload)
    assert result.status_code == 200, result.text
    return {**plan, 'review_token': result.json()['review_token'], 'quality_report': result.json()['report']}, payload


def test_public_blocks_discriminate_and_preserve_extensions(api, deck):
    for block in [{'type':'alien','text':'keep in backup'}, {'type':'formula'}, {'type':'text','text':' '}, {'type':'table','rows':[[1,2],[3]]}]:
        value = copy.deepcopy(deck);value['slides'][0]['blocks'] = [block]
        response = api.post('/api/v1/quality/check', json=value)
        assert response.status_code == 422 and response.headers['x-request-id']
    blocks = [{'type':'text','text':'Nội dung','custom':'original'}, {'type':'formula','latex':'x^2'}, {'type':'table','data':[[1,2]]}]
    deck['slides'][0]['blocks'] = blocks
    normalized = SlideDeckSchema.model_validate(deck).model_dump(mode='json')
    assert normalized['slides'][0]['blocks'] == blocks
    schema = api.get('/openapi.json').json()['components']['schemas']
    slide = schema.get('SlideSchema') or schema['SlideSchema-Input']
    assert slide['properties']['blocks']['items']['discriminator']['propertyName'] == 'type'
    assert 'question' in slide['properties'] and 'generation_metadata' in slide['properties']


def test_plan_review_requires_owner_all_claims_and_current_content(api, plan):
    from fastapi.testclient import TestClient
    from lessonai.main import create_app
    with TestClient(create_app()) as visitor:
        assert visitor.post('/api/v1/quality/lesson-plan/check', json=plan).status_code == 401
    ready, payload = approve(api, plan)
    assert api.post('/api/v1/quality/lesson-plan/check', json=ready).json()['status'] == 'ready'
    assert api.post('/api/v1/quality/lesson-plan/approve', json={**payload, 'reviewed_issue_ids': []}).status_code == 409
    assert api.post('/api/v1/quality/lesson-plan/approve', json={**payload, 'acknowledged': False}).status_code == 422
    changed = {**ready, 'lesson_title': 'Tên mới'}
    assert api.post('/api/v1/quality/lesson-plan/check', json=changed).json()['status'] == 'needs_review'
    assert api.post('/api/v1/quality/lesson-plan/approve', json={**payload, 'plan': changed}).status_code == 409


@pytest.mark.parametrize('change', ['wrong_math','empty_product','empty_goal','missing_activity','wrong_order','wrong_time','outline'])
def test_incomplete_or_false_plan_cannot_be_approved(api, plan, change):
    if change == 'wrong_math': plan['activities'][1]['execution']['step_4_conclusion'] = 'Kết luận $1+1=3$.'
    elif change == 'empty_product': plan['activities'][0]['expected_product'] = ' '
    elif change == 'empty_goal': plan['knowledge_goals'] = [' ']
    elif change == 'missing_activity': plan['activities'].pop()
    elif change == 'wrong_order': plan['activities'].reverse()
    elif change == 'wrong_time': plan['activities'][0]['time_minutes'] = -1
    else: plan['approved_outline']['outline_slides'][0]['title'] = 'Nội dung bị bỏ'
    report = api.post('/api/v1/quality/lesson-plan/check', json=plan).json()
    assert report['status'] == 'blocked', report
    response = api.post('/api/v1/quality/lesson-plan/approve', json={'plan': plan, 'acknowledged': True,
        'content_fingerprint':report['content_fingerprint'], 'reviewed_issue_ids':[i['issue_id'] for i in report['issues']]})
    assert response.status_code == 409 and response.json()['detail']['code'] == 'content_blocked'


def test_plan_token_is_independent_expires_and_does_not_survive_restart(api, plan, deck, monkeypatch):
    from lessonai.services import lesson_quality
    ready, _ = approve(api, plan)
    deck['review_token'] = ready['review_token']
    assert api.post('/api/v1/quality/check', json=deck).json()['status'] != 'ready'
    assert reviewed_plan(ready)
    with monkeypatch.context() as m:
        m.setattr(lesson_quality.time, 'time', lambda: 10**12)
        assert not reviewed_plan(ready)
    monkeypatch.setattr(lesson_quality, '_KEY', b'new-server-key')
    assert not reviewed_plan(ready)


def test_docx_zip_and_reimport_preserve_provenance_without_imported_approval(api, plan, deck):
    ready, _ = approve(api, plan)
    before = copy.deepcopy(ready)
    response = api.post('/api/v1/lesson-plan/export-docx', json=ready)
    assert response.status_code == 200, response.text
    doc = Document(io.BytesIO(response.content))
    assert 'ĐÃ ĐƯỢC GIÁO VIÊN XÁC NHẬN' in doc.paragraphs[0].text
    assert 'BẢN NHÁP' not in doc.paragraphs[0].text
    imported = api.post('/api/v1/ingest/parse-document', files={'file':('lesson.docx', response.content, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')})
    assert imported.status_code == 200, imported.text
    provenance = imported.json()['provenance']
    assert provenance['status'] == 'unverified_import'
    assert provenance['data']['generation_metadata'] == plan['generation_metadata']
    assert provenance['data']['approved_outline'] == plan['approved_outline']
    assert 'review_token' not in provenance['data']
    exported = api.post('/api/v1/lesson-plan/export-dual-package', json={'plan':ready,'slide_deck':deck})
    assert exported.status_code == 200, exported.text
    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        manifest = json.loads(archive.read('Huong_Dan_Goi_Kep_5512.txt'))
        assert manifest['plan_quality'] == 'ready'
        assert manifest['deck_quality'] != 'ready'
        assert manifest['plan_provenance'] == provenance['data']
        with_doc = Document(io.BytesIO(archive.read(next(n for n in archive.namelist() if n.endswith('.docx')))))
        assert any('Phần câu hỏi/lời giải bổ sung từ slide chưa được xác nhận' in p.text for p in with_doc.paragraphs)
    changed = {**ready,'lesson_title':'Bài đã sửa'}
    stale_doc = Document(io.BytesIO(api.post('/api/v1/lesson-plan/export-docx',json=changed).content))
    assert 'BẢN NHÁP' in stale_doc.paragraphs[0].text
    assert ready == before


def test_generation_replaces_model_outline_and_resets_review(api, plan):
    from lessonai.services.generation.lesson_plan import generate_lesson_plan
    model = LessonPlanSchema.model_validate({**plan,'approved_outline':{'invented':True},'review_token':'forged','quality_report':{'status':'ready'}})
    outline = copy.deepcopy(plan['approved_outline'])
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured', return_value=model):
        result, _ = generate_lesson_plan('Tổng hai số',use_rag=False,approved_outline=outline)
    assert result.approved_outline == outline and result.approved_outline is not outline
    assert result.review_token is None and result.quality_report is None
    assert isinstance(result.generation_metadata, GenerationMetadata)
    assert LessonPlanSchema.model_validate_json(result.model_dump_json()).generation_metadata == result.generation_metadata


def test_generation_response_publishes_metadata_and_outline(api, plan):
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured', return_value=LessonPlanSchema.model_validate(plan)):
        response = api.post('/api/v1/lesson-plan/generate', json={'topic':'Tổng hai số','use_rag':False,'approved_outline':plan['approved_outline']})
    assert response.status_code == 200, response.text
    assert response.json()['plan']['generation_metadata'] == plan['generation_metadata']
    assert response.json()['plan']['approved_outline'] == plan['approved_outline']
    contract = api.get('/openapi.json').json()
    assert contract['paths']['/api/v1/lesson-plan/generate']['post']['responses']['200']['content']['application/json']['schema']['$ref'].endswith('/LessonGenerationResponse')
    for path in ('check', 'approve'):
        assert '$ref' in contract['paths']['/api/v1/quality/lesson-plan/'+path]['post']['responses']['200']['content']['application/json']['schema']
