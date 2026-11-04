"""Regressions for the outstanding content and export handover defects."""
import copy
from unittest.mock import patch
import pytest
from pptx import Presentation
from lessonai.services.content_quality import evaluate_deck
from lessonai.services.content_blocks import block_errors
from lessonai.exporters.slide_exporter import export_slide_deck_to_pptx
from lessonai.services.generation.outline_contract import validate_slide_role
from test_remediation_workflows import api, deck

pytestmark = pytest.mark.critical_regressions


@pytest.mark.parametrize('field', ['question', 'target_outcome'])
def test_false_arithmetic_in_authored_fields_is_blocked(deck, field):
    deck['slides'][0][field] = '$2+2=5$'
    report = evaluate_deck(deck)
    assert report['status'] == 'blocked'
    assert any(issue['field'] == field and issue['severity'] == 'error' for issue in report['issues'])


@pytest.mark.parametrize('block', [
    {'type': 'text', 'text': ' '}, {'type': 'formula'},
    {'type': 'unknown', 'text': 'Do not silently drop this'},
    {'type': 'table', 'rows': [[1, 2], [3]]},
    {'type': 'image', 'data_url': 'data:image/png;base64,bad', 'alt': 'Missing image'},
])
def test_invalid_blocks_block_review_and_export(deck, block):
    deck['slides'][0]['blocks'] = [block]
    assert list(block_errors(deck['slides'][0]))
    assert evaluate_deck(deck)['status'] == 'blocked'
    with pytest.raises(ValueError):
        export_slide_deck_to_pptx(deck)


def test_approval_requires_each_current_issue_and_cannot_override_errors(api, deck):
    report = api.post('/api/v1/quality/check', json=deck).json()
    payload = {'deck': deck, 'acknowledged': True, 'content_fingerprint': report['content_fingerprint']}
    assert api.post('/api/v1/quality/approve', json=payload).status_code == 409
    payload['reviewed_issue_ids'] = [i['issue_id'] for i in report['issues']]
    approved = api.post('/api/v1/quality/approve', json=payload)
    assert approved.status_code == 200
    record = approved.json()['report']['review_record']
    assert record['reviewed_issue_ids'] == sorted(payload['reviewed_issue_ids'])
    assert record['reviewer'] and record['confirmed_at']
    changed = copy.deepcopy(deck)
    changed['slides'][0]['question'] = '$2+2$'
    assert api.post('/api/v1/quality/approve', json={**payload, 'deck': changed}).status_code == 409
    changed['slides'][0]['question'] = '$2+2=5$'
    assert api.post('/api/v1/quality/approve', json={**payload, 'deck': changed}).json()['detail']['code'] == 'content_blocked'


def test_continuations_and_native_tables_precede_next_source_slide(deck):
    first = deck['slides'][0]
    first['blocks'] = [{'type': 'text', 'text': 'First continuation'}, {'type': 'table', 'rows': [['x', 'y'], [11, 22], [33, 44]]}]
    deck['slides'].append({'slide_id': 'second', 'title': 'NEXT SOURCE', 'bullet_points': ['Second source body']})
    before = copy.deepcopy(deck)
    prs = Presentation(export_slide_deck_to_pptx(deck))
    texts = [' '.join(s.text for s in page.shapes if s.has_text_frame) for page in prs.slides]
    next_index = next(i for i, text in enumerate(texts) if 'NEXT SOURCE' in text)
    assert next(i for i, text in enumerate(texts) if 'First continuation' in text) < next_index
    tables = [(i, s.table) for i, page in enumerate(prs.slides) for s in page.shapes if s.has_table]
    assert tables and all(i < next_index for i, _ in tables)
    assert [c.text for _, table in tables for row in table.rows for c in row.cells] == ['x', 'y', '11', '22', '33', '44']
    assert deck == before


def test_long_table_rows_are_split_without_loss(deck):
    words = [f'cell{i}' for i in range(120)]
    deck['slides'][0]['blocks'] = [{'type': 'table', 'rows': [[' '.join(words), 'other']]}]
    prs = Presentation(export_slide_deck_to_pptx(deck))
    table_shapes = [s for page in prs.slides for s in page.shapes if s.has_table]
    assert len(table_shapes) > 1
    text = ' '.join(c.text for s in table_shapes for row in s.table.rows for c in row.cells)
    assert all(word in text for word in words)
    assert all(s.top + s.height < prs.slide_height for s in table_shapes)


def test_outline_activity_visual_and_math_roles_are_enforced():
    slide = {'activity_type': 'luyen_tap', 'layout': 'QUIZ_OPTION', 'quiz_options': [{}], 'main_definition_latex': 'x+1'}
    item = {'activity_type': 'Luyện tập', 'visual_type': 'Interactive Quiz', 'math_focus': 'x+1'}
    validate_slide_role(slide, item)
    for changed in [{'activity_type': 'van_dung'}, {'quiz_options': []}, {'main_definition_latex': 'x+2'}]:
        with pytest.raises(ValueError):
            validate_slide_role({**slide, **changed}, item)


def test_runtime_package_has_no_curated_fallback():
    from importlib.util import find_spec
    assert find_spec('lessonai.services.generation.fallback') is None


def test_office_fraction_and_power_conversion_preserves_unsupported_nodes():
    from lxml import etree
    from lessonai.services.office_math import omml_to_latex
    ns = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
    xml = f'<m:oMath xmlns:m="{ns}"><m:f><m:num><m:sSup><m:e><m:r><m:t>x</m:t></m:r></m:e><m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup></m:num><m:den><m:r><m:t>3</m:t></m:r></m:den></m:f></m:oMath>'
    assert omml_to_latex(etree.fromstring(xml)) == r'\frac{{x}^{2}}{3}'
    with pytest.raises(ValueError, match='chưa hỗ trợ'):
        omml_to_latex(etree.fromstring(f'<m:oMath xmlns:m="{ns}"><m:acc/></m:oMath>'))


def test_owner_expiry_does_not_allow_old_cookie_to_approve(api, deck, monkeypatch):
    from lessonai.core import ownership
    token = api.cookies.get('lessonai_owner')
    monkeypatch.setitem(ownership._owners, token, 0)
    assert api.post('/api/v1/quality/check', json=deck).status_code == 401
    assert api.post('/api/v1/session').status_code == 200
    assert api.cookies.get('lessonai_owner') != token
    assert api.post('/api/v1/quality/check', json=deck).status_code == 200


def test_plan_cannot_drop_approved_outline():
    from curated_examples import get_curated_lesson_plan
    from lessonai.services.generation.lesson_plan import generate_lesson_plan
    plan = get_curated_lesson_plan('Bài')
    outline = {'outline_slides': [{'id': 'a', 'title': 'Nội dung bắt buộc chưa có trong bài', 'activity_type': 'Khởi động'}]}
    with patch('lessonai.llm.gateway.llm_gateway.generate_structured', return_value=plan):
        with pytest.raises(RuntimeError):
            generate_lesson_plan('Bài', use_rag=False, approved_outline=outline, max_retries=0)


def _crash_worker(connection, operation, payload):
    import os
    os._exit(17)


def test_worker_capacity_crash_and_shutdown_recover(monkeypatch):
    from lessonai.core import jobs
    runner = jobs.JobRunner(concurrency=1, capacity=1)
    assert runner._capacity.acquire(blocking=False)
    with pytest.raises(jobs.JobError) as busy:
        runner.run('math.evaluate', {})
    assert busy.value.code == 'job_busy'
    runner._capacity.release()
    original = jobs._entry
    monkeypatch.setattr(jobs, '_entry', _crash_worker)
    with pytest.raises(jobs.JobError) as crash:
        runner.run('math.evaluate', {}, timeout=5)
    assert crash.value.code == 'job_crashed'
    assert not runner._processes
    monkeypatch.setattr(jobs, '_entry', original)
    # The slot is reusable after a crash; unsupported operation reaches a fresh worker.
    with pytest.raises(jobs.JobError) as recovered:
        runner.run('unsupported', {}, timeout=5)
    assert recovered.value.code == 'job_unsupported'
    runner.close()
    with pytest.raises(jobs.JobError) as closed:
        runner.run('unsupported', {})
    assert closed.value.code == 'job_unavailable'


def test_generated_artifact_records_actual_fallback_model(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from pydantic import BaseModel, ConfigDict
    from lessonai.llm import gateway as module
    class Result(BaseModel):
        model_config = ConfigDict(extra='allow')
        value: str
    gateway = module.LLMGateway()
    gateway.gemini_key = 'test-only'
    gateway.google_client = SimpleNamespace(models=SimpleNamespace(generate_content=Mock(side_effect=[RuntimeError('404 NOT_FOUND'), SimpleNamespace(text='{"value":"ok"}') ])))
    monkeypatch.setattr(gateway, 'get_active_routes', lambda task: [module.ProviderRoute('google', 'available')])
    result = gateway.generate_structured('user', 'system', Result, model_provider='gemini', model_id='missing')
    metadata = result.model_dump()['generation_metadata']
    assert metadata['provider'] == 'google' and metadata['model'] == 'available'
    assert metadata['status'] == 'unverified_draft'
    assert len(metadata['prompt_sha256']) == 64
