"""Distinguish portable tests from checks against the author's untracked corpus."""
import pytest

CORPUS_MODULES={'test_phase3_pedagogical_rag.py','test_phase5_e2e_rag_system.py'}
CORPUS_TESTS={'test_m0_artifacts_exist_and_valid','test_auto_infer_lesson_id_across_curriculum'}

def pytest_collection_modifyitems(items):
    for item in items:
        if item.path.name in CORPUS_MODULES or item.originalname in CORPUS_TESTS:
            item.add_marker(pytest.mark.corpus_integration)
