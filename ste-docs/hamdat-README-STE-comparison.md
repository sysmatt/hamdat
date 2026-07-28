# hamdat README → STE (ASD-STE100) Comparison

Experiment only — README.md is **not** modified. This is a line-by-line look at
what would need to change in `/home/sysmatt/workspace/hamdat/README.md` to
meet the rule set in `STE100-writing-rules.md`.

Scope note: option tables, code blocks, and command examples are mostly
skipped below — they're already terse, fragment-style, and don't carry finite
verbs, so STE's sentence-level rules (passive voice, tense, word count) don't
really bite there. The violations cluster almost entirely in the **prose
paragraphs** between sections. Table cells with a real violation (semicolons,
gerunds) are called out too.

---

## 1. Recurring patterns (fix once, apply everywhere)

| Pattern | Rule(s) | Rough count | Example from README |
|---|---|---|---|
| Passive voice ("is stored," "are applied," "can be combined") | 3.4, 3.6 | ~25 | "New files are downloaded and applied in chronological order." |
| Gerund used as verb/subject ("-ing" as tense) | 3.5 | ~10 | "Before pulling, rotate a timestamped backup..." / "Understanding what requires network access helps you plan..." |
| Present perfect tense (not an allowed tense) | 3.1–3.2 | 5 | "callsigns that **have changed hands**," "has **not been built** yet" |
| Contractions | 4.2 | 2 | "hasn't changed," "you've never used" |
| Semicolons | 8.1 | ~6 | "...are compared...; already-applied files are skipped by ETag." |
| Idioms / phrasal verbs (translation-hostile) | 9.3 | 4 | "changed hands," "Rule of thumb," "locked in," "factor that into" |
| Sentences over the word limit | 5.1 / 6.3 | ~6 | first-run paragraph (line 106), custom-`--db` paragraph (line 198) |
| Dropped subject/verb (sentence fragments) | 4.2 | ~4 | "Useful for offline environments, pre-staged files, or testing." |
| Latin abbreviation | GR-6 | 1 | "(e.g. via cron)" |
| Ambiguous "This" with no noun | GR-3/4 | ~3 | "This means `--keep-sources 2`..." / "This builds the database..." |

None of this is a knock on the README — it's clear, idiomatic engineering
English, which is exactly what STE is designed to move away from in favor of
translatable, mechanically-parseable sentences.

---

## 2. Line-by-line comparison

### Title / intro (README lines 1–10)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 1 | "A command-line utility for downloading, caching, and querying FCC Amateur Radio license data from the ULS (Universal Licensing System) bulk data files." | "hamdat is a command-line tool. It downloads, caches, and searches FCC Amateur Radio license data from the ULS (Universal Licensing System) bulk data files." | 3.5 (gerunds → finite verbs), 4.1 (one idea/sentence) |
| 2 | "Data is stored locally in a SQLite database (~500 MB) and kept current by applying FCC daily incremental updates on top of the weekly full snapshot." | "hamdat stores the data locally in a SQLite database (about 500 MB). hamdat applies the FCC daily incremental updates on top of the weekly full snapshot to keep the data current." | 3.4 (passive), 3.5 (gerund "applying"), 4.1 |
| 3 | "> **Note:** The SQLite database is used by external utilities and the schema is considered locked in. Structural changes are major events only." | "**CAUTION:** External utilities use the SQLite database. Do not change the schema, except for a major structural update. An unplanned schema change can break these external utilities." | 3.4 (passive), 9.3 ("locked in" idiom), 7.1–7.3 (this is really a CAUTION — it warns against an action and should state the consequence, which the original never does) |

### Requirements (lines 14–22)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 4 | "`pgeocode` — offline ZIP code geocoding (only needed for `--zip` radius search)" | "`pgeocode` — needed only for the `--zip` radius search; it geocodes ZIP codes offline." | 3.4 (passive "is needed"); note this is a table cell so lower priority |

### Usage / Options tables (lines 41–95)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 5 | "`--keep-db [N]` — Before pulling, rotate a timestamped backup of the database; keep N copies (default 1). `--keep-db 0` purges all existing backups." | "`--keep-db [N]` — Before you run `--pull`, hamdat makes a timestamped backup of the database. hamdat keeps the N most recent copies (default 1). `--keep-db 0` deletes all existing backups and makes no new backup." | 3.5 (gerund "pulling"), 8.1 (semicolon) |
| 6 | "`--keep-sources [N]` — Before downloading, rotate timestamped backups of each FCC zip file; keep N copies (default 1). `--keep-sources 0` purges all existing source backups." | "`--keep-sources [N]` — Before hamdat downloads new files, hamdat makes a timestamped backup of each FCC zip file. hamdat keeps the N most recent copies (default 1). `--keep-sources 0` deletes all existing source backups and makes no new backup." | 3.5, 8.1 |

### Workflow (lines 98–198)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 7 | "Downloads the FCC weekly snapshot (`l_amat.zip`, ~200 MB compressed), loads it into the local SQLite database, applies any daily update files published since the snapshot, and pre-seeds the pgeocode ZIP code cache so that radius searches work offline immediately." (1 sentence, ~45 words) | "`--pull` downloads the FCC weekly snapshot (`l_amat.zip`, about 200 MB compressed) and loads it into the local SQLite database. `--pull` then applies any daily update files published since the snapshot. `--pull` also seeds the pgeocode ZIP code cache. As a result, radius searches work offline immediately." | 6.3 (25-word max, descriptive text), 4.4 (use "as a result" instead of an implicit connection) |
| 8 | "If the weekly snapshot ETag hasn't changed, the full download is skipped." | "If the weekly snapshot ETag has not changed, hamdat skips the full download." | 4.2 (contraction), 3.4 (passive) — note: "has not changed" is itself present perfect (3.1/3.2 violation); a fully compliant version needs a condition instead: "If the weekly snapshot ETag is the same as the cached ETag, hamdat skips the full download." |
| 9 | "Daily files are compared by `Last-Modified` date against the stored snapshot baseline; already-applied files are skipped by ETag." | "hamdat compares each daily file's `Last-Modified` date against the stored snapshot baseline. hamdat skips already-applied files by ETag." | 3.4 (passive x2), 8.1 (semicolon) |
| 10 | "New files are downloaded and applied in chronological order." | "hamdat downloads and applies new files in chronological order." | 3.4 |
| 11 | "The pgeocode cache is verified and re-seeded if missing." | "hamdat verifies the pgeocode cache and re-seeds it if the cache is missing." | 3.4 |
| 12 | "Running this daily (e.g. via cron) keeps the database within 24 hours of the FCC's live data." | "If you run `--pull` daily, for example with cron, the database stays within 24 hours of the FCC live data." | 3.5 (gerund "Running" as subject), GR-6 ("e.g." → "for example"), GR-8 (drop possessive "FCC's") |
| 13 | "Skips all HTTP activity and reads directly from local files. The folder must contain `l_amat.zip` (the weekly snapshot). Any daily files present (`l_am_sun.zip` … `l_am_sat.zip`) are applied automatically in day-of-week order after the full load. Useful for offline environments, pre-staged files, or testing." | "`--pull --zips-folder` skips all HTTP activity and reads directly from local files. The folder must contain `l_amat.zip` (the weekly snapshot). If any daily files are present (`l_am_sun.zip` through `l_am_sat.zip`), hamdat applies them automatically in day-of-week order after the full load. Use this option for offline environments, pre-staged files, or testing." | 4.2 (dropped subject in first and last sentence), 3.4 (passive "are applied"), GR-6 (avoid "…" — spell out "through") |
| 14 | "Re-downloads the full weekly snapshot regardless of ETag, drops and reloads all tables, then applies daily updates. Useful after a schema change or suspected data corruption." | "`--pull --force` downloads the full weekly snapshot again regardless of the ETag. `--pull --force` drops and reloads all tables, then applies daily updates. Use this option after a schema change or if you suspect data corruption." | 4.2 (dropped subject x2) |
| 15 | "Both flags follow the same rotation model: before anything is overwritten, a timestamped copy is made in the same directory. The N most recent copies are retained and anything older is purged automatically. The filename is derived from the original — no hardcoded names." | "Both flags follow the same rotation model. Before hamdat overwrites a file, hamdat makes a timestamped copy of it in the same directory. hamdat keeps the N most recent copies and deletes all older copies automatically. hamdat derives the backup filename from the original filename; hamdat does not use a hardcoded name." | 3.4 (passive x5) — this paragraph is the single densest cluster of passive voice in the document |
| 16 | "This means `--keep-sources 2` with 7 daily files plus the weekly retains up to 16 zip files total in the cache directory — factor that into available disk space." | "As a result, `--keep-sources 2` can retain up to 16 zip files in the cache directory: 2 copies each of the weekly file and the 7 daily files. Plan for this in your available disk space." | GR-3/4 ("This" with no noun), 9.3 ("factor that into" idiom), 6.3 (split long sentence) |

### Offline Operations (lines 202–264)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 17 | "hamdat is designed to work fully offline after an initial setup. Understanding what requires network access helps you plan for air-gapped or low-connectivity environments." | "hamdat works fully offline after the initial setup. This section explains which operations need network access, so you can plan for an air-gapped or low-connectivity environment." | 3.4 (passive "is designed"), 3.5 (gerund "Understanding" as subject) |
| 18 | "Run `--pull` at least once while connected. This builds the database **and** pre-seeds the pgeocode ZIP code cache in one step. After that, all queries including radius searches work with no network access." | "Run `--pull` at least once while the machine has network access. The `--pull` command builds the database and seeds the pgeocode ZIP code cache in one step. After that, all queries, including radius searches, work with no network access." | GR-3/4 ("This" with no noun) |
| 19 | "To verify readiness before going offline:" | "To verify readiness before you disconnect the machine:" | 3.5 (gerund "going" after preposition) |

### Commands — `--call` family (lines 267–380)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 20 | "Displays a full formatted operator profile for a single, exact callsign. Always shows the most recent active licensee — correctly handles callsigns that **have changed hands**. Fails with a message if the callsign is not found." | "`--call` shows a full formatted operator profile for a single, exact callsign. `--call` always shows the most recent active licensee, so it correctly handles a callsign that changed hands more than once. If the callsign is not in the database, `--call` shows an error message." | 3.1/3.2 (present perfect), 9.3 ("changed hands" is idiomatic — consider "a callsign that a new licensee now holds" if translation matters), 4.2 (dropped subject) |
| 21 | "Appends a compact table showing all past licensees for the callsign after the normal profile, sorted most-recent first. Useful when a callsign **has changed hands** between individuals and clubs." | "`--history` appends a compact table that shows all past licensees for the callsign, sorted most-recent first, after the normal profile. Use `--history` when a callsign moved between individual and club licensees over time." | 3.5 (gerund "showing"), 9.3 ("changed hands"), 4.2 (dropped subject) |
| 22 | "Shows the complete formatted operator profile for every licensee that **has ever held** the callsign, separated by `Record X of Y` banners, most-recent first. FCC action history is shown only for the most recent record. If both `--full-history` and `--history` are given, `--full-history` takes precedence and `--history` is ignored." | "`--full-history` shows the complete formatted operator profile for every licensee that has held the callsign, most-recent first. `--full-history` separates each record with a `Record X of Y` banner. `--full-history` shows the FCC action history only for the most recent record. If you give both `--full-history` and `--history`, hamdat uses `--full-history` and ignores `--history`." | 3.1/3.2 (present perfect "has ever held"), 3.4 (passive x3), 6.3 (split long sentence) |

### `--type` / `--class` (lines 444–489)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 23 | "Filters results by the FCC applicant type. Accepts a friendly name or raw FCC code. Can be combined with any search flag." | "`--type` filters results by the FCC applicant type. `--type` accepts a friendly name or a raw FCC code. You can combine `--type` with any other search flag." | 3.4 (passive modal "can be combined"), 4.2 (dropped subject) |
| 24 | "Filters results by FCC operator class. Accepts single-letter FCC codes or full names (case-insensitive). Multiple values **may be given**; results **matching** any of the specified classes **are returned** (OR within `--class`, AND with every other flag)." | "`--class` filters results by FCC operator class. `--class` accepts single-letter FCC codes or full names; the match is not case-sensitive. You can give more than one value. `--class` returns a result if the result matches any of the given classes: this is OR logic within `--class`, and AND logic with every other flag." | 3.4 (passive x2), 8.1 (semicolon), 6.3 (split long sentence) |

### Date filters (lines 493–529)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 25 | "Filter active licenses by when they **were granted** (`--grant-date`) or when any FCC action last occurred (`--change-date`). Both accept the same flexible date query language and AND with all other search flags." | "`--grant-date` filters active licenses by the date the FCC granted the license. `--change-date` filters active licenses by the date of the last FCC action. Both flags accept the same date query language, and both AND with all other search flags." | 3.4 (passive "were granted") |
| 26 | "> **Rule of thumb:** `since` and `thru` include the boundary date. `after` and `before` do not." | "> **Quick reference:** `since` and `thru` include the boundary date. `after` and `before` do not include the boundary date." | 9.3 ("Rule of thumb" is an idiom), 4.2 (write "do not include the boundary date" in full rather than the bare "do not") |

### `--zip` (lines 605–625)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 27 | "With `--radius-miles 0` (default), only operators whose mailing address ZIP exactly matches **are returned**." | "With `--radius-miles 0` (the default), `--zip` returns only the operators whose mailing address ZIP matches exactly." | 3.4 (passive) |
| 28 | "> **Note:** Distances are approximate. The radius search **is based on** ZIP code centroid coordinates, not precise addresses." | "> **Note:** Distances are approximate. The radius search uses ZIP code centroid coordinates, not precise addresses, so a result's distance is an estimate." | 3.4 (passive "is based on") |

### `--regex` (lines 629–690)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 29 | "By default, `--callsearch`, `--name`, and `--address` do a simple **substring** search — if the query appears anywhere in the field, it matches. **Adding** `--regex` switches to regular expression matching, which lets you describe a pattern instead of just a fixed string." | "By default, `--callsearch`, `--name`, and `--address` do a simple substring search: if the query appears anywhere in the field, the record matches. If you add `--regex`, hamdat switches to regular expression matching. Regular expression matching lets you describe a pattern instead of a fixed string." | 3.5 (gerund "Adding" as subject), GR-3/4 (replace ambiguous "it" with "the record") |
| 30 | "A regular expression (regex) is a mini-language for matching text patterns. If **you've** never used them before, here are the most useful pieces:" | "A regular expression (regex) is a small pattern language for text. If you have not used a regular expression before, here are the most useful symbols:" | 4.2 (contraction "you've"), 3.1/3.2 ("have...used" is present perfect — even written in full this tense is not allowed; better: "If this is your first time using a regular expression, here are the most useful symbols:" but note "using" here is the accepted noun-phrase use of -ing, not a tense) |

### Combining flags / Output formats (lines 694–737)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 31 | "When multiple search flags **are specified** together, results must satisfy all conditions (AND, not OR)." | "When you give more than one search flag together, a result must satisfy all conditions (AND, not OR)." | 3.4 (passive) |
| 32 | "The `--table` output auto-sizes columns and truncates values that exceed per-column maximums; `--csv`, `--json`, and `--html` always include full untruncated values." | "The `--table` output sets each column width automatically and shortens a value that exceeds the column's maximum width. `--csv`, `--json`, and `--html` always include the full value, with no shortening." | 8.1 (semicolon), 1.1 ("auto-sizes" / "untruncated" are non-standard coinages — STE prefers the plain approved verb "shorten" over "truncate," though "truncate" is common enough as a technical verb that some teams would keep it and just define it once) |

### Data source (lines 758–784)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 33 | "The weekly file **is replaced** each Sunday. Daily files **are replaced** each week on their respective day." | "The FCC replaces the weekly file every Sunday. The FCC replaces each daily file once a week, on its matching day." | 3.4 (passive x2) |
| 34 | "All tables **are indexed** on `call_sign` and `unique_system_identifier`." | "hamdat indexes all tables on `call_sign` and `unique_system_identifier`." | 3.4 (passive) |

### Troubleshooting (lines 808–832)

| # | Original | STE rewrite | Rules |
|---|---|---|---|
| 35 | "The database **has not been built** yet, or `--db` points to a wrong path." | "hamdat has not built the database yet, or `--db` points to the wrong path." | 3.4 + 3.1/3.2 (passive present perfect is a double violation); a fully compliant version avoids perfect tense entirely: "The database does not exist yet, or `--db` points to the wrong path." |
| 36 | "The `pgeocode` package **is only required** for `--zip` radius searches." | "You need the `pgeocode` package only for `--zip` radius searches." | 3.4 (passive) |
| 37 | "The ZIP code **was not found** in the pgeocode database." | "hamdat did not find the ZIP code in the pgeocode database." | 3.4 (passive) |

---

## 3. What's already close to compliant

Worth calling out, since it shows the rewrite isn't a full rebuild:

- Most **option-table cells** are already short imperative/noun fragments —
  the format STE recommends for procedural reference material.
- `"Backup filename timestamps use local time, not UTC."` (line 172) — active
  voice, one idea, no jargon. This is a model STE sentence as-is.
- The **date-language table** and its "on or after vs strictly after" bullets
  (lines 513–527) use plain connecting language and short sentences already;
  only the "Rule of thumb" label needs to change.
- Command examples and code blocks are out of STE's scope (they're literal
  syntax, not prose) and need no change.

---

## 4. If you want to actually run this experiment further

A few things worth deciding before any real rewrite:

1. **Technical noun glossary** — STE wants one fixed term per concept. This
   doc already does that well (`--pull`, `--keep-db`, "weekly snapshot",
   "daily update"), so the STE noun-discipline rules mostly just confirm
   existing practice rather than forcing renames.
2. **Passive voice is the dominant fix.** Almost every rewrite above reduces
   to "make hamdat (or the flag) the subject." A search-and-rewrite pass
   for `is/are/was/were + past participle` would catch the majority of
   violations mechanically.
3. **Present perfect** ("has changed," "have held") shows up specifically
   around callsign-history language — worth a standing rule for that section:
   describe the current state ("held by," "previously licensed to") rather
   than the history-of-change ("has changed hands").
