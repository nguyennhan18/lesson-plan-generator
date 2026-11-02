"""Protect public API and resource locations across internal refactors."""
import json
import os
from pathlib import Path
import subprocess
import sys

from lessonai.core.config import DATA_DIR, TEMPLATES_DIR, TEST_CASES_PATH
from lessonai.main import app
from lessonai.rag.curriculum_registry import CurriculumRegistry


def test_public_api_matches_pre_refactor_contract():
    expected = json.loads((Path(__file__).parent / "fixtures/api_contract.json").read_text())
    actual = app.openapi()
    assert actual["paths"] == expected["paths"]
    assert actual["components"] == expected["components"]


def test_runtime_resources_use_canonical_locations():
    registry = CurriculumRegistry()
    assert registry.base_dir == DATA_DIR
    assert registry.get_all_lessons()
    assert TEST_CASES_PATH.is_file()
    assert (TEMPLATES_DIR / "manifest.json").is_file()
    assert list(TEMPLATES_DIR.glob("*.pptx"))


def test_installed_package_imports_outside_checkout(tmp_path):
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", "import lessonai; print(lessonai.__file__)"],
        cwd=tmp_path, env=environment, text=True, capture_output=True, check=True,
    )
    assert Path(result.stdout.strip()).resolve().parent.name == "lessonai"
