"""CLI smoke tests — invoke the script via subprocess.

Tests that only exercise argument parsing and validation need no database.
Tests that perform a real query receive the real_db fixture and are skipped
if the database is absent.
"""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).parents[1] / "hamdat")


def run(*args, **kwargs):
    """Run the hamdat script with the given arguments."""
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Version and help — no DB needed
# ---------------------------------------------------------------------------

def test_version_flag():
    r = run("--version")
    assert r.returncode == 0
    assert "hamdat" in r.stdout


def test_no_args_prints_help():
    r = run()
    assert r.returncode == 0
    assert "usage" in r.stdout.lower() or "hamdat" in r.stdout


def test_help_flag():
    r = run("--help")
    assert r.returncode == 0
    assert "--pull" in r.stdout
    assert "--call" in r.stdout
    assert "--limit" in r.stdout


# ---------------------------------------------------------------------------
# Input validation — exits with error, no DB needed
# ---------------------------------------------------------------------------

def test_bad_type_exits_nonzero():
    r = run("--type", "xyz", "--name", "test")
    assert r.returncode != 0


def test_bad_type_reports_valid_options():
    r = run("--type", "xyz", "--name", "test")
    assert "xyz" in r.stderr


def test_bad_class_exits_nonzero():
    r = run("--class", "Z", "--name", "test")
    assert r.returncode != 0


def test_bad_class_reports_valid_options():
    r = run("--class", "Z", "--name", "test")
    assert "Z" in r.stderr


def test_bad_grant_date_exits_nonzero():
    r = run("--grant-date", "notadate", "--name", "test")
    assert r.returncode != 0


def test_bad_grant_date_reports_value():
    r = run("--grant-date", "notadate", "--name", "test")
    assert "notadate" in r.stderr


def test_bad_change_date_exits_nonzero():
    r = run("--change-date", ">=2025-01-01", "--name", "test")
    assert r.returncode != 0


# ---------------------------------------------------------------------------
# Real queries via CLI — requires the real DB
# ---------------------------------------------------------------------------

def test_cli_call_w1aw(real_db):
    r = run("--call", "W1AW", "--db", str(real_db))
    assert r.returncode == 0
    assert "W1AW" in r.stdout
    assert "ACTIVE" in r.stdout


def test_cli_callsearch_with_limit(real_db):
    r = run("--callsearch", "W1AW", "--limit", "3", "--db", str(real_db))
    assert r.returncode == 0
    assert "result(s)" in r.stdout


def test_cli_status(real_db):
    r = run("--status", "--db", str(real_db))
    assert r.returncode == 0
    assert "Database" in r.stdout
    assert "MB" in r.stdout


def test_cli_unknown_callsign(real_db):
    r = run("--call", "ZZZZZZZ", "--db", str(real_db))
    assert r.returncode == 0
    assert "No record found" in r.stdout


def test_cli_db_not_found_exits():
    r = run("--call", "W1AW", "--db", "/nonexistent/path/hamdat.db")
    assert r.returncode != 0
    assert "not found" in r.stdout.lower() or "not found" in r.stderr.lower()
