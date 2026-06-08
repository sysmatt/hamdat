"""Integration tests against the real FCC database.

All tests in this file require ~/.hamdat/hamdat.db (or HAMDAT_TEST_DB) to
exist. They are skipped automatically if the database is absent.
"""
import json

import pytest


EXPECTED_FIELDS = {
    "call_sign", "name", "operator_class", "address",
    "city", "state", "zip_code", "grant_date",
    "expired_date", "effective_date", "last_action",
}


def _json_results(hm, tmp_path, **kwargs):
    """Helper: run search_multi with fmt=json and return parsed results list."""
    out = tmp_path / "r.json"
    hm.search_multi(fmt="json", outfile=out, **kwargs)
    return json.loads(out.read_text())


# ---------------------------------------------------------------------------
# show_status
# ---------------------------------------------------------------------------

def test_show_status_runs(real_db, hm, capsys):
    hm.show_status(db_path=str(real_db))
    out = capsys.readouterr().out
    assert "Database" in out
    assert "MB" in out
    assert "License headers" in out


def test_show_status_reports_snapshot_date(real_db, hm, capsys):
    hm.show_status(db_path=str(real_db))
    out = capsys.readouterr().out
    assert "Snapshot date" in out


# ---------------------------------------------------------------------------
# lookup — single callsign
# ---------------------------------------------------------------------------

def test_lookup_w1aw_is_active(real_db, hm, capsys):
    hm.lookup("W1AW", db_path=real_db)
    out = capsys.readouterr().out
    assert "W1AW" in out
    assert "ACTIVE" in out


def test_lookup_w1aw_lowercase(real_db, hm, capsys):
    """Callsign lookup is case-insensitive."""
    hm.lookup("w1aw", db_path=real_db)
    out = capsys.readouterr().out
    assert "W1AW" in out


def test_lookup_k2tta(real_db, hm, capsys):
    hm.lookup("K2TTA", db_path=real_db)
    out = capsys.readouterr().out
    assert "K2TTA" in out


def test_lookup_unknown_callsign(real_db, hm, capsys):
    hm.lookup("ZZZZZZZ", db_path=real_db)
    out = capsys.readouterr().out
    assert "No record found" in out


def test_lookup_with_history(real_db, hm, capsys):
    hm.lookup("W1AW", db_path=real_db, show_history=True)
    out = capsys.readouterr().out
    assert "LICENSEE HISTORY" in out


def test_lookup_with_full_history(real_db, hm, capsys):
    hm.lookup("W1AW", db_path=real_db, show_full_history=True)
    out = capsys.readouterr().out
    assert "Record 1 of" in out


# ---------------------------------------------------------------------------
# search_multi — result structure
# ---------------------------------------------------------------------------

def test_search_result_has_expected_fields(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, op_class=["E"], limit=5, db_path=real_db)
    assert len(results) > 0
    for r in results:
        assert EXPECTED_FIELDS.issubset(r.keys())


def test_search_all_results_nonempty_callsign(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, op_class=["T"], limit=20, db_path=real_db)
    assert all(r["call_sign"] for r in results)


# ---------------------------------------------------------------------------
# search_multi — operator class filter
# ---------------------------------------------------------------------------

def test_search_class_technician(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, op_class=["T"], limit=50, db_path=real_db)
    assert len(results) > 0
    assert all(r["operator_class"] == "Technician" for r in results)


def test_search_class_extra(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, op_class=["E"], limit=50, db_path=real_db)
    assert all(r["operator_class"] == "Amateur Extra" for r in results)


def test_search_multiple_classes(real_db, hm, tmp_path):
    """Multi-class query returns only results from the requested classes."""
    results = _json_results(hm, tmp_path, op_class=["T", "G"], limit=100, db_path=real_db)
    assert len(results) > 0
    assert all(r["operator_class"] in {"Technician", "General"} for r in results)


# ---------------------------------------------------------------------------
# search_multi — type filter
# ---------------------------------------------------------------------------

def test_search_type_club(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, type_code=["B"], limit=20, db_path=real_db)
    assert len(results) > 0
    assert all(r["operator_class"] == "Amateur Club" for r in results)


def test_search_type_individual(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, type_code=["I"], limit=20, db_path=real_db)
    assert len(results) > 0


def test_search_type_multi(real_db, hm, tmp_path):
    """Multi-type query returns results (both types exist in the FCC data)."""
    results = _json_results(hm, tmp_path, type_code=["I", "B"], limit=50, db_path=real_db)
    assert len(results) > 0


# ---------------------------------------------------------------------------
# search_multi — name and address
# ---------------------------------------------------------------------------

def test_search_name_returns_results(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, name="Smith", limit=10, db_path=real_db)
    assert len(results) > 0


def test_search_address_state(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, address="NJ", limit=10, db_path=real_db)
    assert len(results) > 0


# ---------------------------------------------------------------------------
# search_multi — callsearch
# ---------------------------------------------------------------------------

def test_search_callsearch_substring(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, callsearch="W1AW", db_path=real_db)
    assert any(r["call_sign"] == "W1AW" for r in results)


def test_search_callsearch_regex_exact(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, callsearch="^W1AW$", regex=True, db_path=real_db)
    assert len(results) == 1
    assert results[0]["call_sign"] == "W1AW"


def test_search_callsearch_regex_prefix(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, callsearch="^W1AW", regex=True, limit=20, db_path=real_db)
    assert all(r["call_sign"].startswith("W1AW") for r in results)


# ---------------------------------------------------------------------------
# search_multi — date filters
# ---------------------------------------------------------------------------

def test_search_grant_date_recent(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, grant_date="-365", limit=10, db_path=real_db)
    assert len(results) > 0


def test_search_change_date_recent(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, change_date="-365", limit=10, db_path=real_db)
    assert len(results) > 0


def test_search_new_technicians(real_db, hm, tmp_path):
    """The canonical 'new ham' query should always return results."""
    results = _json_results(hm, tmp_path, op_class=["T"], grant_date="-365", limit=10, db_path=real_db)
    assert len(results) > 0


# ---------------------------------------------------------------------------
# search_multi — limit
# ---------------------------------------------------------------------------

def test_search_limit_respected(real_db, hm, tmp_path):
    results = _json_results(hm, tmp_path, op_class=["T"], limit=7, db_path=real_db)
    assert len(results) == 7


def test_search_limit_zero_returns_results(real_db, hm, tmp_path):
    """limit=0 means no limit — should return more than a small fixed number."""
    results = _json_results(hm, tmp_path, callsearch="^W1AW", regex=True, limit=0, db_path=real_db)
    assert len(results) > 0


# ---------------------------------------------------------------------------
# search_multi — ZIP radius
# ---------------------------------------------------------------------------

def test_search_zip_exact_match(real_db, hm, tmp_path):
    pgeocode = pytest.importorskip("pgeocode")  # noqa: F841 — skip if not installed
    results = _json_results(hm, tmp_path, zipcode="07030", distance_miles=0, limit=10, db_path=real_db)
    assert len(results) > 0
    assert all(r["zip_code"] == "07030" for r in results)


def test_search_zip_radius_includes_distance(real_db, hm, tmp_path):
    pytest.importorskip("pgeocode")
    results = _json_results(hm, tmp_path, zipcode="07030", distance_miles=10, limit=20, db_path=real_db)
    assert len(results) > 0
    assert all("distance_miles" in r for r in results)


def test_search_zip_radius_sorted_by_distance(real_db, hm, tmp_path):
    pytest.importorskip("pgeocode")
    results = _json_results(hm, tmp_path, zipcode="07030", distance_miles=25, limit=50, db_path=real_db)
    distances = [r["distance_miles"] for r in results if r["distance_miles"] != ""]
    assert distances == sorted(distances)
