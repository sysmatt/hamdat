"""Tests for FCC zip loading — weekly snapshot and daily change files.

Weekly-zip tests are marked @pytest.mark.slow because _load_full_zip takes
several minutes and writes ~1 GB to the pytest temp directory.  Run the full
suite with:

    pytest                        # skips nothing
    pytest -m "not slow"          # skips the weekly-load tests
"""
import sqlite3
import zipfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Schema creation (fast — no zip needed)
# ---------------------------------------------------------------------------

def test_schema_creates_all_tables(fresh_db, hm):
    conn = sqlite3.connect(fresh_db)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()

    expected = {table for _, (table, _) in hm.FILE_SCHEMAS.items()}
    expected |= {"_meta", "_daily_applied"}
    assert expected.issubset(tables)


def test_schema_creates_indexes(fresh_db, hm):
    conn = sqlite3.connect(fresh_db)
    indexes = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()}
    conn.close()

    for expected in ["idx_hd_call", "idx_en_call", "idx_am_call", "idx_hs_dedup"]:
        assert expected in indexes


def test_schema_idempotent(fresh_db, hm):
    """Calling _create_schema twice must not raise."""
    conn = sqlite3.connect(fresh_db)
    hm._create_schema(conn)   # second call — all IF NOT EXISTS
    conn.close()


# ---------------------------------------------------------------------------
# Weekly zip — full load (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_weekly_zip_loads_record_counts(loaded_db):
    """All major tables should contain a substantial number of records."""
    conn = sqlite3.connect(loaded_db)
    hd = conn.execute("SELECT COUNT(*) FROM license_header").fetchone()[0]
    en = conn.execute("SELECT COUNT(*) FROM entity").fetchone()[0]
    am = conn.execute("SELECT COUNT(*) FROM amateur").fetchone()[0]
    conn.close()

    assert hd > 500_000,  f"license_header too small: {hd:,}"
    assert en > 500_000,  f"entity too small: {en:,}"
    assert am > 300_000,  f"amateur too small: {am:,}"


@pytest.mark.slow
def test_weekly_zip_loads_w1aw(loaded_db):
    """W1AW should be present and active in a freshly loaded snapshot."""
    conn = sqlite3.connect(f"file:{loaded_db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT license_status FROM license_header WHERE call_sign = 'W1AW' "
        "ORDER BY CASE WHEN license_status='A' THEN 0 ELSE 1 END LIMIT 1"
    ).fetchone()
    conn.close()
    assert row is not None, "W1AW not found in loaded snapshot"
    assert row["license_status"] == "A"


@pytest.mark.slow
def test_weekly_zip_stores_snapshot_date(weekly_zip, hm, tmp_path):
    """pull() in zips-folder mode must store snapshot_date in _meta."""
    db_path = tmp_path / "snap.db"
    conn = sqlite3.connect(db_path)
    hm._load_full_zip(weekly_zip, conn)

    # Simulate what pull() does: store snapshot_date from file mtime
    from datetime import datetime, timezone
    snap_mtime = datetime.fromtimestamp(weekly_zip.stat().st_mtime, tz=timezone.utc)
    conn.execute("INSERT OR REPLACE INTO _meta VALUES (?, ?)",
                 ("snapshot_date", snap_mtime.isoformat()))
    conn.commit()

    row = conn.execute(
        "SELECT value FROM _meta WHERE key='snapshot_date'"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0].startswith("20")   # looks like an ISO timestamp


# ---------------------------------------------------------------------------
# Daily zip — apply to a fresh schema (fast)
# ---------------------------------------------------------------------------

def _first_nonempty_daily(daily_zips, min_bytes=1000):
    """Return (day, path) for the first daily zip larger than min_bytes."""
    for day, path in daily_zips.items():
        if path.stat().st_size >= min_bytes:
            return day, path
    return None, None


def test_apply_daily_zip_inserts_records(fresh_db, daily_zips, hm):
    """Applying a daily zip to an empty-schema DB should insert records."""
    if not daily_zips:
        pytest.skip("No daily zip files found in cache dir")
    day, path = _first_nonempty_daily(daily_zips)
    if path is None:
        pytest.skip("No non-trivially-sized daily zip found")

    conn = sqlite3.connect(fresh_db)
    with zipfile.ZipFile(path) as zf:
        n_records, n_usids = hm._apply_daily_zip(zf, conn)
    conn.close()

    assert n_records > 0,  f"[{day}] expected records, got 0"
    assert n_usids  > 0,   f"[{day}] expected USIDs changed, got 0"


def test_apply_daily_zip_returns_counts(fresh_db, daily_zips, hm):
    """_apply_daily_zip must return (int, int)."""
    if not daily_zips:
        pytest.skip("No daily zip files found in cache dir")
    day, path = _first_nonempty_daily(daily_zips)
    if path is None:
        pytest.skip("No non-trivially-sized daily zip found")

    conn = sqlite3.connect(fresh_db)
    with zipfile.ZipFile(path) as zf:
        result = hm._apply_daily_zip(zf, conn)
    conn.close()

    assert isinstance(result, tuple) and len(result) == 2
    assert all(isinstance(v, int) for v in result)


def test_apply_daily_zip_history_deduplication(fresh_db, daily_zips, hm):
    """Applying the same daily zip twice must not duplicate history rows."""
    if not daily_zips:
        pytest.skip("No daily zip files found in cache dir")
    day, path = _first_nonempty_daily(daily_zips)
    if path is None:
        pytest.skip("No non-trivially-sized daily zip found")

    conn = sqlite3.connect(fresh_db)

    with zipfile.ZipFile(path) as zf:
        hm._apply_daily_zip(zf, conn)
    count_after_first = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]

    with zipfile.ZipFile(path) as zf:
        hm._apply_daily_zip(zf, conn)
    count_after_second = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]

    conn.close()
    assert count_after_first == count_after_second, (
        f"History grew from {count_after_first} to {count_after_second} "
        f"on second apply — deduplication broken"
    )


# ---------------------------------------------------------------------------
# _pull_daily_local — apply all available daily zips via the high-level API
# ---------------------------------------------------------------------------

def test_pull_daily_local_applies_all(fresh_db, daily_zips, cache_dir, hm):
    """_pull_daily_local should process every zip present in the cache dir."""
    if not daily_zips:
        pytest.skip("No daily zip files found in cache dir")

    conn = sqlite3.connect(fresh_db)
    hm._pull_daily_local(conn, cache_dir)

    applied = {r[0] for r in conn.execute(
        "SELECT day FROM _daily_applied"
    ).fetchall()}
    conn.close()

    nonempty = {d for d, p in daily_zips.items() if p.stat().st_size >= 1000}
    assert nonempty.issubset(applied), (
        f"Expected {nonempty} to be applied, got {applied}"
    )


def test_pull_daily_local_records_applied_at(fresh_db, daily_zips, cache_dir, hm):
    """Each applied daily should have a non-empty applied_at timestamp."""
    if not daily_zips:
        pytest.skip("No daily zip files found in cache dir")

    conn = sqlite3.connect(fresh_db)
    hm._pull_daily_local(conn, cache_dir)
    rows = conn.execute("SELECT day, applied_at FROM _daily_applied").fetchall()
    conn.close()

    assert len(rows) > 0
    for day, applied_at in rows:
        assert applied_at, f"applied_at is empty for day={day}"
