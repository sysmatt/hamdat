# hamdat

**Author:** Matt Hoskins, K2TTA — k2tta@arrl.net  
**GitHub:** https://github.com/sysmatt/hamdat

A command-line utility for downloading, caching, and querying FCC Amateur Radio license data from the [ULS (Universal Licensing System)](https://www.fcc.gov/uls/transactions/daily-weekly.html) bulk data files.

Data is stored locally in a SQLite database (~500 MB) and kept current by applying FCC daily incremental updates on top of the weekly full snapshot.

---

## Requirements

- Python 3.9+
- [`requests`](https://pypi.org/project/requests/) — HTTP downloads
- [`pgeocode`](https://pypi.org/project/pgeocode/) — offline ZIP code geocoding (only needed for `--find-radius`)

```
pip install requests pgeocode
```

---

## Installation

```
chmod +x hamdat
cp hamdat ~/bin/      # or anywhere on your PATH
```

---

## Usage

```
hamdat [--pull] [--force] [--call CALLSIGN] [--zip ZIPCODE] [--name QUERY] [--address QUERY] [options]
```

### Options

**Data management**

| Flag | Description |
|---|---|
| `--pull` | Download FCC data and load into the local SQLite database |
| `--force` | Force re-download of the full dataset even if the cached copy is current |
| `--zips-folder DIR` | Load FCC zip files from a local folder instead of downloading |

**Queries**

| Flag | Description |
|---|---|
| `--call CALLSIGN` | Look up a callsign and display a formatted operator profile |
| `--zip ZIPCODE` | Find active operators near a ZIP code (see `--radius-miles`) |
| `--name QUERY` | Search active operators by name |
| `--address QUERY` | Search active operators by any part of mailing address |
| `--radius-miles MILES` | Search radius for `--zip` (default: `0` — exact ZIP only). Distances are approximate, based on ZIP code centroid data. |
| `--regex` | Treat `--name` / `--address` query as a Python regular expression |

**Output format** *(mutually exclusive; default is `--table`)*

| Flag | Output |
|---|---|
| `--table` | Formatted table printed to stdout (default) |
| `--csv` | CSV file written to `--file` |
| `--json` | JSON file written to `--file` |
| `--html` | HTML table written to `--file` |

**Paths**

| Flag | Description |
|---|---|
| `--file PATH` | Output file for `--csv` / `--json` / `--html` (default: `~/.hamdat/results.{ext}`) |
| `--db PATH` | SQLite database path (default: `~/.hamdat/hamdat.db`) |
| `--cache-dir DIR` | Directory for downloaded zip files and ETags (default: `~/.hamdat/`) |

---

## Workflow

### First run — build the database

```
hamdat --pull
```

Downloads the FCC weekly snapshot (`l_amat.zip`, ~200 MB compressed) from:

```
https://data.fcc.gov/download/pub/uls/complete/l_amat.zip
```

After loading the full snapshot, `--pull` automatically checks all seven FCC daily change files and applies any that were published after the weekly snapshot. Output shows exactly which dates are being compared and why each file is applied or skipped:

```
Checking weekly snapshot ...
  Remote last-modified : 2026-04-20 02:14 UTC
  Remote ETag          : "d41d8cd98f00b204e980..."
  Cached ETag          : (none)
  → no cached copy found; downloading full dataset
Downloading https://data.fcc.gov/download/pub/uls/complete/l_amat.zip
  100%  198.4 MB
  HD.dat -> license_header ... 3,842,100 records
  EN.dat -> entity ...         4,201,883 records
  AM.dat -> amateur ...          783,441 records
  ...
Done. 9,012,345 total records loaded into /home/user/.hamdat/hamdat.db

Checking daily updates (snapshot baseline: 2026-04-20 02:14 UTC)
  sun:  2026-04-19 04:00 UTC  → predates snapshot, skipping
  mon:  2026-04-20 04:00 UTC  → predates snapshot, skipping
  tue:  2026-04-21 04:00 UTC  → will apply
  wed:  2026-04-22 04:00 UTC  → will apply
  thu:  2026-04-23 04:00 UTC  → will apply
  fri:  2026-04-24 04:00 UTC  → will apply
  sat:  2026-04-25 04:00 UTC  → will apply

Applying 5 daily update(s):
  [tue]  4,102 records, 987 licenses updated
  [wed]  3,891 records, 901 licenses updated
  ...
```

### Keeping the database current

Run `--pull` at any time — it is safe and incremental:

- If the weekly snapshot ETag hasn't changed, the full download is skipped.
- Daily files are compared by their `Last-Modified` date against the stored snapshot baseline.
- Files whose ETag matches what was last applied are skipped.
- New files are downloaded and applied in chronological order.

```
hamdat --pull
```

Running this daily (e.g. via cron) keeps the database within 24 hours of the FCC's live data.

### Load from a local folder

```
hamdat --pull --zips-folder /path/to/downloaded/zips/
```

Skips all HTTP activity and reads directly from local files. The folder must contain `l_amat.zip` (the weekly snapshot). Any daily files present (`l_am_sun.zip` … `l_am_sat.zip`) are applied automatically in day-of-week order after the full load. Useful for offline environments, pre-staged files, or testing.

### Force a full reload

```
hamdat --pull --force
```

Re-downloads the full weekly snapshot regardless of ETag, drops and reloads all tables, then applies daily updates. Useful after a schema change or suspected data corruption.

---

## Commands

### `--call` — Look up a callsign

```
hamdat --call W1AW
```

Displays a formatted operator profile. Lookups are anchored to the current license grant's `unique_system_identifier` so the correct licensee is shown even when a callsign has changed hands.

Example output:

```
==============================================================================
  W1AW                                                    [ ACTIVE ]
  Hiram Percy Maxim                                        Amateur Extra
==============================================================================

  OPERATOR
  ─────────────────────────────────────────────────────────────────────────────
  Class             Amateur Extra  (E)
  First Licensed    01/01/1914
  Group             A
  Region            1
  FRN               0001234567

  LICENSE
  ─────────────────────────────────────────────────────────────────────────────
  Granted           01/15/2020
  Expires           01/15/2030
  Effective         01/15/2020
  Last Action       01/15/2020
  Service Code      HA
  USID              1234567

  CONTACT
  ─────────────────────────────────────────────────────────────────────────────
  Address           225 Main St
                    Newington, CT  06111
  Phone             860-594-0200
  Email             w1aw@arrl.org

  HISTORY  (most recent)
  ─────────────────────────────────────────────────────────────────────────────
  01/15/2020   LIRN      Issued — After Renewal
  01/10/2020   LREN      Renewal
==============================================================================
```

### `--zip` — Find operators by ZIP code

```
hamdat --zip 06111
hamdat --zip 06111 --radius-miles 25
hamdat --zip 06111 --radius-miles 25 --csv --file nearby.csv
hamdat --zip 06111 --radius-miles 25 --html --file nearby.html
```

Finds all active license holders within the specified radius of a ZIP code. With the default radius of 0, only operators whose mailing address is in that exact ZIP code are returned. Uses an offline ZIP code database (pgeocode) — no network requests, no rate limits.

> **Note:** Distances are approximate. The radius search is based on ZIP code centroid coordinates, not precise addresses. An operator listed 12.3 miles away may live closer or farther depending on where within their ZIP code they actually reside.

**How it works:**

1. Collects all unique 5-digit ZIP codes from active licenses in the DB (~30k)
2. Batch-geocodes them all via pgeocode (in-memory, instant)
3. Filters to those within the radius using the Haversine formula
4. Queries the DB for operators in those ZIP codes

### `--name` — Search by operator name

```
hamdat --name "Smith"
hamdat --name "John.*Smith" --regex
hamdat --name "ARRL" --json --file clubs.json
```

Searches the `first_name`, `last_name`, and `entity_name` fields for active licensees. By default uses a case-insensitive substring match. With `--regex`, the query is treated as a Python regular expression.

### `--address` — Search by mailing address

```
hamdat --address "Main St"
hamdat --address "Newington" --html --file newington.html
hamdat --address "^06[0-9]{3}$" --regex
```

Searches across `street_address`, `po_box`, `city`, `state`, and `zip_code` for active licensees. Supports the same substring and `--regex` modes as `--name`.

---

## Output formats

All tabular commands (`--find-radius`, `--name`, `--address`) support four output formats selected by a mutually exclusive flag:

| Flag | Destination | Default filename |
|---|---|---|
| `--table` | stdout | — |
| `--csv` | file | `~/.hamdat/results.csv` |
| `--json` | file | `~/.hamdat/results.json` |
| `--html` | file | `~/.hamdat/results.html` |

Use `--file PATH` to override the output file location. The `--table` output auto-sizes columns from the data and truncates values that exceed per-column maximums; `--csv`, `--json`, and `--html` always include the full untruncated values.

### Result fields

All tabular output contains the following fields. `distance_miles` is only present for `--find-radius`.

| Field | Description |
|---|---|
| `call_sign` | FCC callsign |
| `distance_miles` | Distance from reference ZIP *(find-radius only)* |
| `name` | Licensee name |
| `operator_class` | License class (e.g. Amateur Extra) |
| `address` | Full mailing address (street/PO box + city, state + ZIP) |
| `city` | City |
| `state` | State abbreviation |
| `zip_code` | 5-digit ZIP code |
| `grant_date` | License grant date |
| `expired_date` | License expiration date |
| `effective_date` | License effective date |
| `last_action` | Date of most recent FCC action |

---

## Data source

FCC ULS bulk data files:

| File | Description |
|---|---|
| `l_amat.zip` | Weekly full snapshot — all amateur radio licenses |
| `l_am_sun.zip` … `l_am_sat.zip` | Daily change files — updated records for that day of the week |

The weekly file is replaced each Sunday. Daily files are replaced each week on their respective day. `hamdat` uses HTTP ETags and `Last-Modified` headers to avoid redundant downloads and correctly order incremental updates.

### Database tables

| Table | Source file | Contents |
|---|---|---|
| `license_header` | `HD.dat` | License status, dates, call sign |
| `entity` | `EN.dat` | Licensee name, address, contact info |
| `amateur` | `AM.dat` | Operator class, group, region |
| `history` | `HS.dat` | License action history |
| `comments` | `CO.dat` | FCC comments |
| `special_condition` | `SC.dat` | Special conditions |
| `license_free_form_special_condition` | `SF.dat` | Free-form special conditions |
| `license_attachment` | `LA.dat` | Attachments |
| `_meta` | — | Internal metadata (snapshot date, last pull) |
| `_daily_applied` | — | Tracks which daily file ETags have been applied |

All tables are indexed on `call_sign` and `unique_system_identifier`. The `unique_system_identifier` (USID) is the key that links all tables for a single license grant.

---

## Cache files

All files are stored under `~/.hamdat/` by default:

```
~/.hamdat/
  hamdat.db          SQLite database
  l_amat.zip         Cached weekly snapshot
  l_amat.etag        ETag for the weekly snapshot
  l_am_sun.zip       Cached daily files (one per day)
  l_am_sun.etag
  ...
  results.csv        Default output for --csv
  results.json       Default output for --json
  results.html       Default output for --html
```
