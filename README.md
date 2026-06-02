# hamdat

**Author:** Matt Hoskins, K2TTA — k2tta@arrl.net  
**GitHub:** https://github.com/sysmatt/hamdat

A command-line utility for downloading, caching, and querying FCC Amateur Radio license data from the [ULS (Universal Licensing System)](https://www.fcc.gov/uls/transactions/daily-weekly.html) bulk data files.

Data is stored locally in a SQLite database (~500 MB) and kept current by applying FCC daily incremental updates on top of the weekly full snapshot.

> **Note:** The SQLite database is used by external utilities and the schema is considered locked in. Structural changes are major events only.

---

## Requirements

- Python 3.9+
- [`requests`](https://pypi.org/project/requests/) — HTTP downloads
- [`pgeocode`](https://pypi.org/project/pgeocode/) — offline ZIP code geocoding (only needed for `--zip` radius search)

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
hamdat [--pull] [--status] [--call CALLSIGN] [--callsearch QUERY] [--zip ZIPCODE] [--name QUERY] [--address QUERY] [--type TYPE] [options]
```

### Options

**Data management**

| Flag | Description |
|---|---|
| `--pull` | Download FCC data and load into the local SQLite database |
| `--force` | Force re-download of the full dataset even if the cached copy is current |
| `--zips-folder DIR` | Load FCC zip files from a local folder instead of downloading |
| `--status` | Show the state of the local database, cached FCC files, and pgeocode ZIP data |

**Queries**

| Flag | Description |
|---|---|
| `--call CALLSIGN` | Look up a **single** callsign — full formatted profile (exact match) |
| `--history` | With `--call`: append a compact table of all past licensees for the callsign |
| `--full-history` | With `--call`: show full formatted records for every past licensee |
| `--callsearch QUERY` | Search active operators by callsign (substring or `--regex`); returns a list |
| `--name QUERY` | Search active operators by name (substring or `--regex`) |
| `--address QUERY` | Search active operators by any part of mailing address (substring or `--regex`) |
| `--type TYPE` | Filter by entity type: `individual`, `club`, `races`, `military`, `government` (or raw FCC code) |
| `--zip ZIPCODE` | Find active operators near a ZIP code (see `--radius-miles`) |
| `--radius-miles MILES` | Search radius for `--zip`; `0` = exact ZIP only (default: `0`) |
| `--regex` | Treat `--callsearch` / `--name` / `--address` as a Python regular expression |

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

Downloads the FCC weekly snapshot (`l_amat.zip`, ~200 MB compressed), loads it into the local SQLite database, applies any daily update files published since the snapshot, and pre-seeds the pgeocode ZIP code cache so that radius searches work offline immediately.

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
  ...

Seeding pgeocode ZIP cache ...
  pgeocode cache ready.
```

### Keeping the database current

Run `--pull` at any time — it is safe and incremental:

- If the weekly snapshot ETag hasn't changed, the full download is skipped.
- Daily files are compared by `Last-Modified` date against the stored snapshot baseline; already-applied files are skipped by ETag.
- New files are downloaded and applied in chronological order.
- The pgeocode cache is verified and re-seeded if missing.

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

## Offline Operations

hamdat is designed to work fully offline after an initial setup. Understanding what requires network access helps you plan for air-gapped or low-connectivity environments.

### What requires network access

| Operation | Network required |
|---|---|
| `--pull` (remote mode) | Yes — downloads FCC snapshot and daily files |
| `--pull --zips-folder` | No — reads from local files only |
| `--call`, `--callsearch`, `--name`, `--address`, `--type` | No |
| `--zip` radius search (after first use) | No |
| `--zip` radius search (first ever use) | Yes — one-time pgeocode data download (~1 MB) |
| `--status` | No |

### Ensuring full offline readiness

Run `--pull` at least once while connected. This builds the database **and** pre-seeds the pgeocode ZIP code cache in one step. After that, all queries including radius searches work with no network access.

To verify readiness before going offline:

```
hamdat --status
```

Sample output:

```
Database: /home/user/.hamdat/hamdat.db
  Size                   487.3 MB
  Snapshot date          2026-05-25 02:14 UTC
  Last pull              2026-06-02 14:23 UTC
  Daily updates          mon, tue, wed, thu
    last applied         2026-06-02 14:23 UTC

  Table                    Records
  ──────────────────────── ──────────────
  License headers            3,842,100
  Entity records             4,201,883
  Amateur records              783,441
  History entries            1,293,004
  Comments                      42,817

Weekly snapshot cache: /home/user/.hamdat/l_amat.zip
  Size                   198.4 MB
  Downloaded             2026-05-25 03:41 UTC
  ETag                   "d41d8cd98f00b204e980..."

pgeocode ZIP cache:
  Cached                 2026-05-30 11:42 UTC
  Cache path             /home/user/.cache/pgeocode/
  Files                  3  (1,024 KB)
```

### Offline setup on an air-gapped machine

1. On a connected machine, download the FCC zip files manually:
   - Weekly snapshot: `https://data.fcc.gov/download/pub/uls/complete/l_amat.zip`
   - Daily files: `https://data.fcc.gov/download/pub/uls/daily/l_am_sun.zip` … `l_am_sat.zip`
2. Copy the zip files to a folder on the target machine.
3. Run: `hamdat --pull --zips-folder /path/to/zips/`
4. For pgeocode, copy `~/.cache/pgeocode/` from the connected machine to the same path on the target machine.

---

## Commands

### `--call` vs `--callsearch` — single record vs. list

These two flags serve distinct purposes:

| Flag | Match type | Output |
|---|---|---|
| `--call CALLSIGN` | Exact, case-insensitive | Full formatted operator profile (one record) |
| `--callsearch QUERY` | Substring or regex (active licenses only) | Tabular list supporting all output formats |

Use `--call` when you know the exact callsign. Use `--callsearch` when searching for a prefix, suffix, or pattern across multiple callsigns.

---

### `--call` — Look up a callsign

```
hamdat --call W1AW
hamdat --call K2TTA
```

Displays a full formatted operator profile for a single, exact callsign. Always shows the most recent active licensee — correctly handles callsigns that have changed hands. Fails with a message if the callsign is not found.

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

For club callsigns, a `Type` line appears in the OPERATOR section:

```
  OPERATOR
  ─────────────────────────────────────────────────────────────────────────────
  Type              Amateur Club  (B)
  First Licensed    03/15/2005
  ...
```

### `--history` — compact licensee history

```
hamdat --call W2LV --history
```

Appends a compact table showing all past licensees for the callsign after the normal profile, sorted most-recent first. Useful when a callsign has changed hands between individuals and clubs.

```
  LICENSEE HISTORY  (2 record(s), most recent first)
  ─────────────────────────────────────────────────────────────────────────────
  STATUS     NAME                        CLASS / TYPE    GRANTED     EXPIRED     USID
  ─────────  ──────────────────────────  ──────────────  ──────────  ──────────  ──────────
  Active     Lake Valley ARC             Amateur Club    04/15/2019  04/15/2029  4567890
  Canceled   John Smith                  Amateur Extra   01/15/2010  03/20/2018  1234567
```

### `--full-history` — full records for all past licensees

```
hamdat --call W2LV --full-history
```

Shows the complete formatted operator profile for every licensee that has ever held the callsign, separated by `Record X of Y` banners, most-recent first. FCC action history is shown only for the most recent record.

```
──────────────────────── Record 1 of 2 ─────────────────────────
==============================================================================
  W2LV                                                   [ ACTIVE ]
  Lake Valley ARC                                         Amateur Club
==============================================================================
  ...

──────────────────────── Record 2 of 2 ─────────────────────────
==============================================================================
  W2LV                                                   [ CANCELED ]
  John Smith                                              Amateur Extra
==============================================================================
  ...
```

---

### `--callsearch` — Search by callsign

Returns a tabular list of active operators whose callsign matches the query. Supports all output formats.

**Substring (default):**
```
hamdat --callsearch "W2"              # all calls containing W2
hamdat --callsearch "K2T"             # all calls containing K2T
hamdat --callsearch "AA"              # all calls containing AA
```

**Regex (`--regex`):**
```
hamdat --callsearch "^W2" --regex     # calls starting with W2
hamdat --callsearch "^K2T" --regex    # calls starting with K2T
hamdat --callsearch "^W[0-9]A$" --regex   # 1x1 format calls (special event style)
hamdat --callsearch "^(K|W)2" --regex --csv --file w2.csv
```

---

### `--name` — Search by operator name

Searches `first_name`, `last_name`, and `entity_name` fields for active licensees.

**Substring (default):**
```
hamdat --name "Smith"
hamdat --name "Lake Valley"
hamdat --name "Radio Club"
```

**Regex (`--regex`):**
```
hamdat --name "^John.*Smith$" --regex
hamdat --name "Radio.*(Club|Society)" --regex
hamdat --name "^ARRL" --regex --json --file arrl.json
```

---

### `--address` — Search by mailing address

Searches across `street_address`, `po_box`, `city`, `state`, and `zip_code` for active licensees.

**Substring (default):**
```
hamdat --address "Newington"
hamdat --address "Main St"
hamdat --address "CT"
```

**Regex (`--regex`):**
```
hamdat --address "^06[0-9]{3}$" --regex        # all Connecticut ZIP codes
hamdat --address "^(CT|NY|NJ)$" --regex        # tri-state area
hamdat --address "Elm.*(St|Ave|Rd)" --regex
```

---

### `--type` — Filter by entity type

Filters results by the FCC applicant type. Accepts a friendly name or raw FCC code. Can be combined with any search flag.

| Friendly name | FCC code | Description |
|---|---|---|
| `individual` | `I` | Individual person |
| `club` | `B` | Amateur club |
| `races` | `R` | RACES organization |
| `military` | `M` | Military recreation |
| `government` | `G` | Government entity |

```
hamdat --type club                           # all active clubs
hamdat --type club --name "Radio"            # clubs with "Radio" in the name
hamdat --type club --callsearch "^W2" --regex   # W2 club callsigns
hamdat --type individual --name "Smith" --address "CT"
hamdat --type B                              # raw FCC code also works
```

---

### `--zip` — Find operators by ZIP code

Finds all active license holders within the specified radius of a ZIP code.

```
hamdat --zip 07030
hamdat --zip 07030 --radius-miles 25
hamdat --zip 07030 --radius-miles 25 --csv --file nearby.csv
hamdat --zip 07030 --radius-miles 25 --html --file nearby.html
```

With `--radius-miles 0` (default), only operators whose mailing address ZIP exactly matches are returned.

> **Note:** Distances are approximate. The radius search is based on ZIP code centroid coordinates, not precise addresses.

**Combined with other filters:**
```
hamdat --zip 07848 --radius-miles 20 --type club
hamdat --zip 06111 --radius-miles 10 --name "Smith"
hamdat --zip 10001 --radius-miles 50 --callsearch "^W2" --regex --type club
```

---

### Understanding `--regex`

By default, `--callsearch`, `--name`, and `--address` do a simple **substring** search — if the query appears anywhere in the field, it matches. Adding `--regex` switches to **regular expression** matching, which lets you describe a pattern instead of just a fixed string.

A regular expression (regex) is a mini-language for matching text patterns. If you've never used them before, here are the most useful pieces:

| Pattern | Meaning | Example | Matches |
|---|---|---|---|
| `^` | Start of the value | `^W2` | `W2ABC`, `W2XY` — but not `KW2A` |
| `$` | End of the value | `K$` | `W1K`, `N2K` — but not `K2TTA` |
| `^...$` | Exact full match | `^W2ABC$` | Only `W2ABC` |
| `.` | Any single character | `W.ABC` | `W1ABC`, `W2ABC`, `WXABC` |
| `[ABC]` | Any one of these characters | `^[KWN]2` | Calls starting with K2, W2, or N2 |
| `[0-9]` | Any digit | `[0-9]ABC` | `1ABC`, `5ABC`, etc. |
| `*` | Zero or more of the previous | `KD*A` | `KA`, `KDA`, `KDDA` |
| `+` | One or more of the previous | `KD+A` | `KDA`, `KDDA` — but not `KA` |
| `{n}` | Exactly n of the previous | `[A-Z]{3}$` | Ends in exactly 3 letters |
| `(A\|B)` | A or B | `^(K\|W)2` | Starts with K2 or W2 |

**Callsign pattern examples:**

```
# Calls that start with W2 (^ = beginning of value)
hamdat --callsearch "^W2" --regex

# Calls that end in K ($ = end of value)
hamdat --callsearch "K$" --regex

# Exact 1x1 format calls (one letter, one digit, one letter — e.g. W2A, K1Z)
hamdat --callsearch "^[A-Z][0-9][A-Z]$" --regex

# All 2x3 format calls in district 2 (e.g. KD2ABC, WB2XYZ)
hamdat --callsearch "^[A-Z]{2}2[A-Z]{3}$" --regex

# Calls starting with K2 or W2
hamdat --callsearch "^(K|W)2" --regex
```

**Name pattern examples:**

```
# Last name starting with Smith (^ matches the beginning)
hamdat --name "^Smith" --regex

# Full name exactly "John Smith"
hamdat --name "^John Smith$" --regex

# Names containing "Radio" followed by anything, then "Club" or "Society"
hamdat --name "Radio.*(Club|Society)" --regex
```

**Address pattern examples:**

```
# Connecticut ZIP codes (all start with 06)
hamdat --address "^06[0-9]{3}$" --regex

# Any of CT, NY, or NJ in the state field
hamdat --address "^(CT|NY|NJ)$" --regex
```

For the full regular expression reference, see the [Python regex documentation](https://docs.python.org/3/library/re.html).

---

### Combining search flags — AND logic

When multiple search flags are specified together, results must satisfy **all** conditions (AND, not OR):

```
# Clubs within 20 miles of ZIP 07848
hamdat --zip 07848 --radius-miles 20 --type club

# Operators named Smith in Connecticut
hamdat --name "Smith" --address "CT"

# W2 callsigns belonging to clubs
hamdat --callsearch "^W2" --regex --type club

# Name contains "Radio", callsign starts with W, in New Jersey
hamdat --name "Radio" --callsearch "^W" --address "NJ"

# Operators named "Johnson" with a callsign that begins with N
hamdat --name "Johnson" --callsearch "^N" --regex
```

---

## Output formats

All tabular commands (`--callsearch`, `--name`, `--address`, `--type`, `--zip`) support four output formats:

| Flag | Destination | Default filename |
|---|---|---|
| `--table` | stdout | — |
| `--csv` | file | `~/.hamdat/results.csv` |
| `--json` | file | `~/.hamdat/results.json` |
| `--html` | file | `~/.hamdat/results.html` |

Use `--file PATH` to override the output file location. The `--table` output auto-sizes columns and truncates values that exceed per-column maximums; `--csv`, `--json`, and `--html` always include full untruncated values.

### Result fields

| Field | Description |
|---|---|
| `call_sign` | FCC callsign |
| `distance_miles` | Distance from reference ZIP *(--zip with --radius-miles only)* |
| `name` | Licensee name or entity name |
| `operator_class` | License class for individuals (e.g. `Amateur Extra`); entity type for non-individuals (e.g. `Amateur Club`) |
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
| `entity` | `EN.dat` | Licensee name, address, contact info, entity type |
| `amateur` | `AM.dat` | Operator class, group, region |
| `history` | `HS.dat` | License action history |
| `comments` | `CO.dat` | FCC comments |
| `special_condition` | `SC.dat` | Special conditions |
| `license_free_form_special_condition` | `SF.dat` | Free-form special conditions |
| `license_attachment` | `LA.dat` | Attachments |
| `_meta` | — | Internal metadata (snapshot date, last pull timestamp) |
| `_daily_applied` | — | Tracks which daily file ETags have been applied |

All tables are indexed on `call_sign` and `unique_system_identifier`. The `unique_system_identifier` (USID) is the key linking all tables for a single license grant.

---

## Cache files

All files are stored under `~/.hamdat/` by default:

```
~/.hamdat/
  hamdat.db          SQLite database (~500 MB)
  l_amat.zip         Cached weekly snapshot (~200 MB)
  l_amat.etag        ETag for the weekly snapshot
  l_am_sun.zip       Cached daily files (one per day)
  ...
  results.csv        Default output for --csv
  results.json       Default output for --json
  results.html       Default output for --html

~/.cache/pgeocode/   pgeocode US postal code data (~1 MB, seeded by --pull)
```
