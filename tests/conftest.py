import importlib.util
import os
import sqlite3
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

# Honour HAMDAT_TEST_DB env var so CI can point at a pre-built DB elsewhere.
_default_db = Path.home() / ".hamdat" / "hamdat.db"
DB_PATH    = Path(os.environ.get("HAMDAT_TEST_DB", _default_db))
CACHE_DIR  = DB_PATH.parent
WEEKLY_ZIP = CACHE_DIR / "l_amat.zip"


@pytest.fixture(scope="session")
def hm():
    """Load the hamdat script as a module (handles the no-.py-extension)."""
    script = Path(__file__).parents[1] / "hamdat"
    loader = SourceFileLoader("hamdat", str(script))
    spec = importlib.util.spec_from_loader("hamdat", loader)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="session")
def cache_dir():
    """The hamdat cache directory where zip files live."""
    return CACHE_DIR


@pytest.fixture(scope="session")
def real_db():
    """Path to the real FCC database. Skips all tests in the fixture if absent."""
    if not DB_PATH.exists():
        pytest.skip(f"FCC database not found at {DB_PATH} — run: hamdat --pull")
    return DB_PATH


@pytest.fixture(scope="session")
def weekly_zip():
    """Path to the cached weekly FCC snapshot zip. Skips if absent."""
    if not WEEKLY_ZIP.exists():
        pytest.skip(f"Weekly zip not found at {WEEKLY_ZIP} — run: hamdat --pull")
    return WEEKLY_ZIP


@pytest.fixture(scope="session")
def daily_zips(hm):
    """Dict of {day: Path} for all daily zip files present in the cache dir."""
    return {
        day: CACHE_DIR / f"l_am_{day}.zip"
        for day in hm.DAILY_DAYS
        if (CACHE_DIR / f"l_am_{day}.zip").exists()
    }


@pytest.fixture
def fresh_db(hm, tmp_path):
    """Writable temp DB with schema created but no data loaded."""
    path = tmp_path / "hamdat.db"
    conn = sqlite3.connect(path)
    hm._create_schema(conn)
    conn.close()
    return path


@pytest.fixture(scope="session")
def loaded_db(weekly_zip, hm, tmp_path_factory):
    """Temp DB loaded from the weekly zip — created once per session.

    Requires ~1 GB of free space in the pytest temp directory and takes
    several minutes to build. Only created when a test requests this fixture.
    Mark tests that use it with @pytest.mark.slow.
    """
    path = tmp_path_factory.mktemp("hamdat") / "loaded.db"
    conn = sqlite3.connect(path)
    hm._load_full_zip(weekly_zip, conn)
    conn.close()
    return path
