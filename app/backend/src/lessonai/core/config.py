"""Application paths and environment configuration."""
import logging
import os
from pathlib import Path
from tempfile import gettempdir
from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parents[3]
REPO_ROOT = BACKEND_DIR.parents[1]
load_dotenv(BACKEND_DIR / ".env")
DATA_DIR = Path(os.getenv("LESSONAI_DATA_DIR", str(BACKEND_DIR / "data"))).resolve()
OUTPUT_DIR = Path(os.getenv("LESSONAI_OUTPUT_DIR", str(BACKEND_DIR / "output"))).resolve()
TEMPLATES_DIR = PACKAGE_DIR / "templates"
TEST_CASES_PATH = DATA_DIR / "test_cases.json"
FRONTEND_DIST_DIR = BACKEND_DIR.parent / "frontend" / "dist"
os.environ.setdefault("MPLCONFIGDIR", str(Path(gettempdir()) / "lessonai_matplotlib"))


def configure_logging():
    logging.basicConfig(level=os.getenv("LESSONAI_LOG_LEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
