"""Pure logic tests — no database or filesystem required."""
from datetime import date, timedelta

import pytest


# ---------------------------------------------------------------------------
# _trunc
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("s,width,expected", [
    ("hello",       10, "hello"),
    ("hello",        5, "hello"),
    ("hello world",  8, "hello w…"),
    ("hello world", 11, "hello world"),
    (None,           5, ""),
    ("",             5, ""),
])
def test_trunc(hm, s, width, expected):
    assert hm._trunc(s, width) == expected


# ---------------------------------------------------------------------------
# _fmt_po_box
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("val,expected", [
    ("",              ""),
    (None,            ""),
    ("none",          ""),
    ("NONE",          ""),
    ("  ",            ""),
    ("525",           "PO BOX 525"),
    ("PO Box 525",    "PO Box 525"),
    ("PO BOX 525",    "PO BOX 525"),
    ("Box 12",        "Box 12"),
])
def test_fmt_po_box(hm, val, expected):
    assert hm._fmt_po_box(val) == expected


# ---------------------------------------------------------------------------
# _class_or_type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("op_class,app_type,expected", [
    ("E",   "I",  "Amateur Extra"),
    ("T",   None, "Technician"),
    ("G",   "I",  "General"),
    ("",    "B",  "Amateur Club"),
    ("",    "R",  "RACES"),
    ("",    "M",  "Military Recreation"),
    ("",    "G",  "Government Entity"),
    ("",    "I",  ""),       # individual with no class → empty
    (None,  None, ""),
    ("E",   "B",  "Amateur Extra"),  # op_class takes priority over type
])
def test_class_or_type(hm, op_class, app_type, expected):
    assert hm._class_or_type(op_class, app_type) == expected


# ---------------------------------------------------------------------------
# _haversine_miles
# ---------------------------------------------------------------------------

def test_haversine_same_point(hm):
    assert hm._haversine_miles(40.7128, -74.006, 40.7128, -74.006) == pytest.approx(0.0, abs=0.01)


def test_haversine_one_degree_latitude(hm):
    # One degree of latitude ≈ 69.09 miles anywhere on Earth
    d = hm._haversine_miles(0.0, 0.0, 1.0, 0.0)
    assert d == pytest.approx(69.09, abs=0.1)


def test_haversine_known_city_pair(hm):
    # NYC (JFK) to Boston (BOS) ≈ 187 miles
    d = hm._haversine_miles(40.6413, -73.7781, 42.3656, -71.0096)
    assert d == pytest.approx(187, abs=5)


def test_haversine_is_symmetric(hm):
    d1 = hm._haversine_miles(40.0, -74.0, 41.0, -75.0)
    d2 = hm._haversine_miles(41.0, -75.0, 40.0, -74.0)
    assert d1 == pytest.approx(d2, rel=1e-6)


# ---------------------------------------------------------------------------
# _resolve_class_codes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("vals,expected", [
    (["E"],                  ["E"]),
    (["extra"],              ["E"]),
    (["amateur extra"],      ["E"]),
    (["T"],                  ["T"]),
    (["technician"],         ["T"]),
    (["tech"],               ["T"]),
    (["G"],                  ["G"]),
    (["general"],            ["G"]),
    (["A"],                  ["A"]),
    (["advanced"],           ["A"]),
    (["N"],                  ["N"]),
    (["novice"],             ["N"]),
    (["P"],                  ["P"]),
    (["technician plus"],    ["P"]),
    (["tech plus"],          ["P"]),
    (["T", "G"],             ["T", "G"]),
    (["technician", "extra"], ["T", "E"]),
])
def test_resolve_class_codes(hm, vals, expected):
    assert hm._resolve_class_codes(vals) == expected


def test_resolve_class_codes_bad_input_exits(hm):
    with pytest.raises(SystemExit):
        hm._resolve_class_codes(["X"])


def test_resolve_class_codes_bad_input_message(hm):
    with pytest.raises(SystemExit) as exc_info:
        hm._resolve_class_codes(["badclass"])
    assert "badclass" in str(exc_info.value)


# ---------------------------------------------------------------------------
# _resolve_type_codes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("vals,expected", [
    (["individual"],           ["I"]),
    (["club"],                 ["B"]),
    (["races"],                ["R"]),
    (["military"],             ["M"]),
    (["government"],           ["G"]),
    (["I"],                    ["I"]),
    (["B"],                    ["B"]),
    (["individual", "club"],   ["I", "B"]),
])
def test_resolve_type_codes(hm, vals, expected):
    assert hm._resolve_type_codes(vals) == expected


def test_resolve_type_codes_bad_input_exits(hm):
    with pytest.raises(SystemExit):
        hm._resolve_type_codes(["xyz"])


def test_resolve_type_codes_bad_input_message(hm):
    with pytest.raises(SystemExit) as exc_info:
        hm._resolve_type_codes(["badtype"])
    assert "badtype" in str(exc_info.value)


# ---------------------------------------------------------------------------
# _resolve_date_str
# ---------------------------------------------------------------------------

def test_resolve_date_str_iso(hm):
    assert hm._resolve_date_str("2025-06-01") == "2025-06-01"


def test_resolve_date_str_minus_n(hm):
    expected = (date.today() - timedelta(days=30)).isoformat()
    assert hm._resolve_date_str("-30") == expected


def test_resolve_date_str_plus_n(hm):
    expected = (date.today() + timedelta(days=30)).isoformat()
    assert hm._resolve_date_str("+30") == expected


def test_resolve_date_str_zero(hm):
    assert hm._resolve_date_str("-0") == date.today().isoformat()


def test_resolve_date_str_invalid_exits(hm):
    with pytest.raises(SystemExit):
        hm._resolve_date_str("notadate")


def test_resolve_date_str_invalid_exits_bad_format(hm):
    with pytest.raises(SystemExit):
        hm._resolve_date_str(">=2025-01-01")


# ---------------------------------------------------------------------------
# _date_cond
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("spec,expected_op,expected_date", [
    ("2025-03-15",          "= ?",  "2025-03-15"),
    ("since:2025-03-15",    ">= ?", "2025-03-15"),
    ("after:2025-03-15",    "> ?",  "2025-03-15"),
    ("thru:2025-03-15",     "<= ?", "2025-03-15"),
    ("before:2025-03-15",   "< ?",  "2025-03-15"),
])
def test_date_cond_boundary_operators(hm, spec, expected_op, expected_date):
    sql, params = hm._date_cond("col", spec)
    assert expected_op in sql
    assert params == [expected_date]


def test_date_cond_range(hm):
    sql, params = hm._date_cond("col", "2025-01-01:2025-12-31")
    assert "BETWEEN" in sql
    assert params == ["2025-01-01", "2025-12-31"]


def test_date_cond_range_swaps_reversed_endpoints(hm):
    sql, params = hm._date_cond("col", "2025-12-31:2025-01-01")
    assert params == ["2025-01-01", "2025-12-31"]


def test_date_cond_minus_n(hm):
    sql, params = hm._date_cond("col", "-30")
    assert "BETWEEN" in sql
    expected_lo = (date.today() - timedelta(days=30)).isoformat()
    assert params == [expected_lo, date.today().isoformat()]


def test_date_cond_plus_n(hm):
    sql, params = hm._date_cond("col", "+30")
    assert "BETWEEN" in sql
    expected_hi = (date.today() + timedelta(days=30)).isoformat()
    assert params == [date.today().isoformat(), expected_hi]


def test_date_cond_relative_range(hm):
    sql, params = hm._date_cond("col", "-90:-30")
    assert "BETWEEN" in sql
    expected_lo = (date.today() - timedelta(days=90)).isoformat()
    expected_hi = (date.today() - timedelta(days=30)).isoformat()
    assert params == [expected_lo, expected_hi]


def test_date_cond_col_appears_in_sql(hm):
    sql, _ = hm._date_cond("h.grant_date", "2025-01-01")
    assert "h.grant_date" in sql
