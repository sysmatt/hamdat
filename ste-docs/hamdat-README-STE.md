# hamdat

**Author:** Matt Hoskins, K2TTA — k2tta@arrl.net
**GitHub:** https://github.com/sysmatt/hamdat

hamdat is a command-line tool. It downloads, caches, and searches FCC Amateur Radio license data from the ULS (Universal Licensing System) bulk data files.

hamdat stores the data locally in a SQLite database (about 500 MB). hamdat applies the FCC daily incremental updates on top of the weekly full snapshot to keep the data current.

> **CAUTION:** External utilities use the SQLite database. Do not change the schema, except for a major structural update. An unplanned schema change can break these external utilities.

---

## Requirements

- Python 3.9 or later
- [`requests`](https://pypi.org/project/requests/) — for HTTP downloads
- [`pgeocode`](https://pypi.org/project/pgeocode/) — for offline ZIP code geocoding. Needed only for the `--zip` radius search.

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
hamdat [--pull] [--status] [--call CALLSIGN] [--callsearch QUERY] [--zip ZIPCODE] [--name QUERY] [--address QUERY] [--type TYPE [...]] [--class CLASS [...]] [--grant-date DATESPEC] [--change-date DATESPEC] [--limit N] [--keep-db [N]] [--keep-sources [N]] [--version] [options]
```

### Options

**Data management**

| Flag | Description |
|---|---|
| `--pull` | Download FCC data and load it into the local SQLite database |
| `--force` | Force a new download of the full dataset even if the cached copy is current |
| `--zips-folder DIR` | Load FCC zip files from a local folder. Do not download the files from the FCC. |
| `--status` | Show the state of the local database, cached FCC files, and pgeocode ZIP data |
| `--keep-db [N]` | Before you run `--pull`, hamdat makes a timestamped backup of the database and keeps the N most recent copies (default 1). `--keep-db 0` deletes all existing backups and makes no new backup. |
| `--keep-sources [N]` | Before hamdat downloads new files, hamdat makes a timestamped backup of each FCC zip file and keeps the N most recent copies (default 1). `--keep-sources 0` deletes all existing source backups and makes no new backup. |

**Queries**

| Flag | Description |
|---|---|
| `--call CALLSIGN` | Look up a **single** callsign — full formatted profile (exact match) |
| `--history` | With `--call`: append a compact table of all past licensees for the callsign |
| `--full-history` | With `--call`: show full formatted records for every past licensee |
| `--callsearch QUERY` | Search active operators by callsign (substring or `--regex`). Returns a list. |
| `--name QUERY` | Search active operators by name (substring or `--regex`) |
| `--address QUERY` | Search active operators by any part of mailing address (substring or `--regex`) |
| `--type TYPE [...]` | Filter by entity type: `individual`, `club`, `races`, `military`, `government` (or raw FCC code). Multiple values allowed: `--type individual club` |
| `--class CLASS [...]` | Filter by operator class: `T` `G` `E` `A` `N` `P` or full name. Multiple values allowed. |
| `--grant-date DATESPEC` | Filter by license grant date (see [Date query language](#date-query-language)) |
| `--change-date DATESPEC` | Filter by last action/change date (same format as `--grant-date`) |
| `--zip ZIPCODE` | Find active operators near a ZIP code (see `--radius-miles`) |
| `--radius-miles MILES` | Search radius for `--zip`. `0` means exact ZIP only (default: `0`) |
| `--limit N` | Maximum number of search results to return. `0` means no limit (default: `0`) |
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

**Misc**

| Flag | Description |
|---|---|
| `--version` | Print the version and exit |

---

## Workflow

### First run — build the database

```
hamdat --pull
```

`--pull` downloads the FCC weekly snapshot (`l_amat.zip`, about 200 MB compressed) and loads it into the local SQLite database. `--pull` then applies any daily update files published since the snapshot. `--pull` also seeds the pgeocode ZIP code cache. As a result, radius searches work offline immediately.

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

- If the weekly snapshot ETag has not changed, hamdat skips the full download.
- hamdat compares each daily file's `Last-Modified` date against the stored snapshot baseline. hamdat skips already-applied files by ETag.
- hamdat downloads and applies new files in chronological order.
- hamdat verifies the pgeocode cache and re-seeds it if the cache is missing.

```
hamdat --pull
```

If you run `--pull` daily, for example with cron, the database stays within 24 hours of the FCC live data.

### Load from a local folder

```
hamdat --pull --zips-folder /path/to/downloaded/zips/
```

`--pull --zips-folder` skips all HTTP activity and reads directly from local files. The folder must contain `l_amat.zip` (the weekly snapshot). If any daily files are present (`l_am_sun.zip` through `l_am_sat.zip`), hamdat applies them automatically in day-of-week order after the full load. Use this option for offline environments, pre-staged files, or testing.

### Force a full reload

```
hamdat --pull --force
```

`--pull --force` downloads the full weekly snapshot again regardless of the ETag. `--pull --force` drops and reloads all tables, then applies daily updates. Use this option after a schema change or if you suspect data corruption.

### Keeping backups — `--keep-db` and `--keep-sources`

Both flags follow the same rotation model. Before hamdat overwrites a file, hamdat makes a timestamped copy of it in the same directory. hamdat keeps the N most recent copies and deletes all older copies automatically. hamdat derives the backup filename from the original filename; hamdat does not use a hardcoded name.

| Flag | Backs up | Example backup filename |
|---|---|---|
| `--keep-db [N]` | `hamdat.db` (~500 MB each) | `hamdat-20260606143022.db` |
| `--keep-sources [N]` | `l_amat.zip` + each daily `l_am_*.zip` | `l_amat-20260606143022.zip` |

> **Note:** Backup filename timestamps use local time, not UTC.

**`--keep-db` — database rotation**

```
hamdat --pull --keep-db        # keep 1 backup (default)
hamdat --pull --keep-db 3      # rolling rotation of 3 database backups
hamdat --pull --keep-db 0      # purge all existing database backups, make no new one
```

**`--keep-sources` — source zip rotation**

```
hamdat --pull --keep-sources       # keep 1 backup of each zip (default)
hamdat --pull --keep-sources 2     # keep 2 copies of each zip file
hamdat --pull --keep-sources 0     # purge all existing zip backups
```

`--keep-sources` only applies in remote mode — it has no effect with `--zips-folder`.

**Using both together**

```
hamdat --pull --keep-db 3 --keep-sources 2
```

With a custom `--db` path, the backup filenames follow the same stem: `--db /data/myradio.db` produces `myradio-20260606143022.db`. As a result, `--keep-sources 2` can retain up to 16 zip files in the cache directory: 2 copies each of the weekly file and the 7 daily files. Plan for this in your available disk space.

---

## Offline Operations

hamdat works fully offline after the initial setup. This section explains which operations need network access, so you can plan for an air-gapped or low-connectivity environment.

### What requires network access

| Operation | Network required |
|---|---|
| `--pull` (remote mode) | Yes — downloads FCC snapshot and daily files (`--keep-db`, `--keep-sources` follow this mode) |
| `--pull --zips-folder` | No — reads from local files only (`--keep-db` works here; `--keep-sources` has no effect) |
| `--call`, `--callsearch`, `--name`, `--address`, `--type`, `--class`, `--grant-date`, `--change-date` | No |
| `--zip` radius search (after first use) | No |
| `--zip` radius search (first ever use) | Yes — one-time pgeocode data download (~1 MB) |
| `--status` | No |

### Ensuring full offline readiness

Run `--pull` at least once while the machine has network access. The `--pull` command builds the database and seeds the pgeocode ZIP code cache in one step. After that, all queries, including radius searches, work with no network access.

To verify readiness before you disconnect the machine:

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
  Entity records              4,201,883
  Amateur records                783,441
  History entries              1,293,004
  Comments                        42,817

Weekly snapshot cache: /home/user/.hamdat/l_amat.zip
  Size                   198.4 MB
  Downloaded             2026-05-25 03:41 UTC
  ETag                   "d41d8cd98f00b204e980..."

pgeocode ZIP cache:
  Cached                 2026-05-30 11:42 UTC
  Cache path             /home/user/.hamdat/pgeocode/
  Files                  3  (1,024 KB)
```

### Offline setup on an air-gapped machine

1. On a connected machine, download the FCC zip files manually:
   - Weekly snapshot: `https://data.fcc.gov/download/pub/uls/complete/l_amat.zip`
   - Daily files: `https://data.fcc.gov/download/pub/uls/daily/l_am_sun.zip` through `l_am_sat.zip`
2. Copy the zip files to a folder on the target machine.
3. Run: `hamdat --pull --zips-folder /path/to/zips/`
4. For pgeocode, copy `~/.hamdat/pgeocode/` from the connected machine to the same path on the target machine.

---

## Commands

### `--call` vs `--callsearch` — single record vs. list

These two flags serve distinct purposes:

| Flag | Match type | Output |
|---|---|---|
| `--call CALLSIGN` | Exact, case-insensitive | Full formatted operator profile (one record) |
| `--callsearch QUERY` | Substring or regex (active licenses only) | Tabular list supporting all output formats |

Use `--call` when you know the exact callsign. Use `--callsearch` when you search for a prefix, suffix, or pattern across multiple callsigns.

---

### `--call` — Look up a callsign

```
hamdat --call W1AW
hamdat --call K2TTA
```

`--call` shows a full formatted operator profile for a single, exact callsign. `--call` always shows the most recent active licensee, so it correctly handles a callsign that changed hands more than once. If the callsign is not in the database, `--call` shows an error message.

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

`--history` appends a compact table that shows all past licensees for the callsign, sorted most-recent first, after the normal profile. Use `--history` when a callsign moved between individual and club licensees over time.

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

`--full-history` shows the complete formatted operator profile for every licensee that has held the callsign, most-recent first. `--full-history` separates each record with a `Record X of Y` banner. `--full-history` shows the FCC action history only for the most recent record. If you give both `--full-history` and `--history`, hamdat uses `--full-history` and ignores `--history`.

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

`--callsearch` returns a tabular list of active operators whose callsign matches the query. `--callsearch` supports all output formats.

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

`--name` searches the `first_name`, `last_name`, and `entity_name` fields for active licensees.

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

`--address` searches the `street_address`, `po_box`, `city`, `state`, and `zip_code` fields for active licensees.

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

`--type` filters results by the FCC applicant type. `--type` accepts a friendly name or a raw FCC code. You can combine `--type` with any other search flag.

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
hamdat --type individual club                # individuals or clubs (OR logic)
hamdat --type races military                 # RACES or military organizations
hamdat --type individual club --grant-date -30   # new individuals or clubs in last 30 days
```

---

### `--class` — Filter by operator class

`--class` filters results by FCC operator class. `--class` accepts single-letter FCC codes or full names; the match is not case-sensitive. You can give more than one value. `--class` returns a result if the result matches any of the given classes: this is OR logic within `--class`, and AND logic with every other flag.

| Code | Full name |
|---|---|
| `T` | Technician |
| `G` | General |
| `E` | Amateur Extra |
| `A` | Advanced |
| `N` | Novice |
| `P` | Technician Plus |

```
hamdat --class T                             # all active Technicians
hamdat --class E                             # all active Amateur Extras
hamdat --class T G                           # Technicians and Generals
hamdat --class technician                    # full name also works
hamdat --class extra --address "CT"          # Extras in Connecticut
hamdat --class T --name "Smith"              # Technicians named Smith
```

---

### `--grant-date` and `--change-date` — Date filters

`--grant-date` filters active licenses by the date the FCC granted the license. `--change-date` filters active licenses by the date of the last FCC action. Both flags accept the same date query language, and both AND with all other search flags.

---

#### Date query language

| Format | Meaning | Boundary date |
|---|---|---|
| `YYYY-MM-DD` | Exact date | — |
| `YYYY-MM-DD:YYYY-MM-DD` | Inclusive range (both ends included) | included |
| `since:YYYY-MM-DD` | On or after DATE | **included** |
| `after:YYYY-MM-DD` | Strictly after DATE | **excluded** |
| `thru:YYYY-MM-DD` | On or before DATE | **included** |
| `before:YYYY-MM-DD` | Strictly before DATE | **excluded** |
| `-N` | Last N days (BETWEEN today−N AND today) | — |
| `+N` | Next N days (BETWEEN today AND today+N) | — |
| `-M:-N` | Relative range (M days ago to N days ago) | — |

**`since` vs `after` — on or after vs strictly after**

Both filter for dates in the future direction, but differ on whether the boundary date itself counts:

- `since:2025-01-01` — matches January 1 and everything after. Use this when you mean the range begins on this date.
- `after:2025-01-01` — matches only January 2 onwards. January 1 itself is excluded. Use this when you mean a later date than this one.

**`thru` vs `before` — on or before vs strictly before**

Both filter for dates in the past direction, with the same inclusive/exclusive distinction:

- `thru:2024-12-31` — matches December 31 and everything before. Use this when you mean the range ends on this date, including this date.
- `before:2024-12-31` — matches only up to December 30. December 31 itself is excluded. Use this when you mean an earlier date than this one.

> **Quick reference:** `since` and `thru` include the boundary date. `after` and `before` do not include the boundary date.

Relative dates (`-N`, `+N`) can also appear on either side of `:` in a range: `-90:2025-12-31` is valid.

---

#### `--grant-date` examples

```
# Licenses granted in the last 30 days
hamdat --grant-date -30

# Licenses granted on a specific date
hamdat --grant-date 2025-03-15

# Licenses granted during a calendar year (both endpoints included)
hamdat --grant-date 2025-01-01:2025-12-31

# Licenses granted from Jan 1 onward — Jan 1 IS included
hamdat --grant-date since:2025-01-01

# Licenses granted strictly after Jan 1 — Jan 1 is NOT included
hamdat --grant-date after:2025-01-01

# Licenses granted up through Dec 31 — Dec 31 IS included
hamdat --grant-date thru:2024-12-31

# Licenses granted strictly before Dec 31 — Dec 31 is NOT included
hamdat --grant-date before:2024-12-31

# Licenses granted between 90 and 30 days ago
hamdat --grant-date -90:-30
```

#### `--change-date` examples

```
# Any license with FCC action in the last 7 days
hamdat --change-date -7

# Licenses with changes from the start of the year onward (Jan 1 included)
hamdat --change-date since:2025-01-01
```

---

#### Combining date filters with other search flags — "new ham" queries

hamdat combines all flags with AND, so date and class filters compose freely with name, address, callsign, ZIP, and type filters:

```
# Newly granted Technicians (last 60 days) — the "new ham" query
hamdat --class T --grant-date -60

# New Technicians or Generals in the last 30 days
hamdat --class T G --grant-date -30

# New Technicians in New Jersey
hamdat --class T --grant-date -90 --address "NJ"

# New Technicians within 50 miles of a ZIP code
hamdat --class T --grant-date -90 --zip 07030 --radius-miles 50

# Recent grants to individuals named Smith
hamdat --grant-date -30 --name "Smith" --type individual

# W2 callsigns granted from the start of this year (Jan 1 included)
hamdat --callsearch "^W2" --regex --grant-date since:2025-01-01

# Export new Technicians from the last 30 days to CSV
hamdat --class T --grant-date -30 --csv --file new_techs.csv

# Export new Technicians from the last 30 days to HTML
hamdat --class T --grant-date -30 --html --file new_techs.html
```

---

### `--zip` — Find operators by ZIP code

`--zip` finds all active license holders within the specified radius of a ZIP code.

```
hamdat --zip 07030
hamdat --zip 07030 --radius-miles 25
hamdat --zip 07030 --radius-miles 25 --csv --file nearby.csv
hamdat --zip 07030 --radius-miles 25 --html --file nearby.html
```

With `--radius-miles 0` (the default), `--zip` returns only the operators whose mailing address ZIP matches exactly.

> **Note:** Distances are approximate. The radius search uses ZIP code centroid coordinates, not precise addresses, so a result's distance is an estimate.

**Combined with other filters:**
```
hamdat --zip 07848 --radius-miles 20 --type club
hamdat --zip 06111 --radius-miles 10 --name "Smith"
hamdat --zip 10001 --radius-miles 50 --callsearch "^W2" --regex --type club
```

---

### Understanding `--regex`

By default, `--callsearch`, `--name`, and `--address` do a simple substring search: if the query appears anywhere in the field, the record matches. If you add `--regex`, hamdat switches to regular expression matching. Regular expression matching lets you describe a pattern instead of a fixed string.

A regular expression (regex) is a small pattern language for text. If you have not used a regular expression before, here are the most useful symbols:

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

When you give more than one search flag together, a result must satisfy all conditions (AND, not OR). Every flag, including `--class`, `--grant-date`, and `--change-date`, participates in this AND logic:

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

# Newly granted Technicians in the last 30 days — the "new ham" query
hamdat --class T --grant-date -30

# New Technicians or Generals in Connecticut in the last 60 days
hamdat --class T G --grant-date -60 --address "CT"

# Extra class licenses granted within the last year
hamdat --class E --grant-date since:2025-01-01
```

---

## Output formats

All tabular search commands (`--callsearch`, `--name`, `--address`, `--type`, `--class`, `--grant-date`, `--change-date`, `--zip`) support four output formats:

| Flag | Destination | Default filename |
|---|---|---|
| `--table` | stdout | — |
| `--csv` | file | `~/.hamdat/results.csv` |
| `--json` | file | `~/.hamdat/results.json` |
| `--html` | file | `~/.hamdat/results.html` |

Use `--file PATH` to override the output file location. The `--table` output sets each column width automatically and shortens a value that exceeds the column's maximum width. `--csv`, `--json`, and `--html` always include the full value, with no shortening.

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

The FCC replaces the weekly file every Sunday. The FCC replaces each daily file once a week, on its matching day. hamdat uses HTTP ETags and `Last-Modified` headers to avoid redundant downloads and to correctly order incremental updates.

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

hamdat indexes all tables on `call_sign` and `unique_system_identifier`. The `unique_system_identifier` (USID) is the key that links all tables for a single license grant.

---

## Cache files

hamdat stores all files under `~/.hamdat/` by default:

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

~/.hamdat/pgeocode/  pgeocode US postal code data (~1 MB, seeded by --pull)
```

---

## Troubleshooting

**`Database not found: ~/.hamdat/hamdat.db — Run --pull first.`**

The database does not exist yet, or `--db` points to the wrong path. Run `hamdat --pull` to download and build the database.

**`Install requests: pip install requests`**

hamdat needs the `requests` package. Install it with `pip install requests`. To install both dependencies at the same time, use `pip install requests pgeocode`.

**`Install pgeocode: pip install pgeocode`**

You need the `pgeocode` package only for `--zip` radius searches. Install it with `pip install pgeocode`. Then run `hamdat --pull` once to seed the ZIP code cache.

**`Could not find coordinates for zip code: 12345`**

hamdat did not find the ZIP code in the pgeocode database. Confirm that the ZIP code is a valid US postal code. If the pgeocode cache is missing or corrupt, run `hamdat --pull` to re-seed the cache.

**`Cannot reach FCC servers and no cached data available. Check network.`**

`--pull` could not contact the FCC, and no local cache exists. Check your network connection. If you are in an offline environment, use `--pull --zips-folder` with pre-downloaded files (see [Offline Operations](#offline-operations)).

**`No record found for callsign: W1XYZ`**

The callsign does not exist in the local database. Confirm the spelling. Then check whether the database is current with `hamdat --status`. If the FCC granted the license recently, run `hamdat --pull` to apply the latest daily updates.
