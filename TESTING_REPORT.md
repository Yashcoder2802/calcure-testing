# Software Testing & Design — Final Testing Report
## Calcure: Terminal Calendar & Task Manager

**Team:** Yash Salunke · Harshal Gajjar  
**Date:** April 2026  
**Repository:** https://github.com/Yashcoder2802/calcure-testing

---

## 1. Subject Application Overview

**Calcure** is a free, open-source TUI (Terminal User Interface) calendar and task manager written in Python 3. It runs on Linux and macOS entirely through keyboard shortcuts — there is no graphical window. Users create and manage calendar events, to-do tasks, set up recurring events, and import calendar data from standard `.ics` files. Settings for colors and layout are controlled through a configuration file.

| Metric | Value |
|---|---|
| Total Python LOC | ~5,784 |
| Core logic LOC (`calcure/` package only) | ~5,689 |
| Language | Python 3.9+ |
| Platform | Linux, macOS |
| Key modules tested | `data.py`, `calendars.py`, `loaders.py`, `savers.py` |

---

## 2. Testing Strategy Overview

Per the course requirements, we conducted four types of testing across two team members:

| Section | Type | Owner | File | Tests |
|---|---|---|---|---|
| 2.1 | Blackbox (EP + BA + EG + CT) | Yash Salunke | `tests/blackbox/test_blackbox.py` | 117 |
| 2.2 | Whitebox Unit Tests | Yash Salunke | `tests/whitebox/test_whitebox.py` | 86 |
| 2.2 | Whitebox Integration Tests | Yash Salunke | `tests/integration/test_integration.py` | 21 |
| 2.3 | Mutation-Targeted Tests | Harshal Gajjar | `tests/mutation/test_mutation.py` | 73 |
| 2.4 | Alternate — CLI Testing | Harshal Gajjar | `tests/cli/test_cli.py` | 27 |
| **Total** | | | | **324** |

---

## 3. Section 2.1 — Blackbox Testing

Blackbox tests treat each component as an opaque box: only inputs and outputs are observed, with no knowledge of the internal implementation.

### 3.1 Techniques Applied

#### Equivalence Partitioning (EP)
We divided inputs into **valid** and **invalid** partitions and wrote one representative test per partition.

| Component | Valid Partition | Invalid Partition |
|---|---|---|
| Task name | 1–999 characters | 0 chars, ≥1000 chars, whitespace-only |
| Task status | NORMAL, DONE, IMPORTANT, UNIMPORTANT | (all covered) |
| Calendar date input | valid month/day combinations | invalid month, impossible dates |
| Collection index | 0 to len-1 | negative, ≥ len, None |
| Filter results | one or more matches | no matches |
| Persisted event frequency | supported labels | invalid/unknown label |
| Timer output | not started, paused, accumulated | N/A |

**Example — EP test:**
```python
def test_add_task_collection_grows(self):
    """[EP] Valid name partition — task is accepted and stored."""
    self.tasks.add_item(make_task(name="Write report"))
    self.assertEqual(len(self.tasks.items), 1)
```

#### Boundary Value Analysis (BA)
We tested at the **exact edges** of each partition (not just representatives).

| Boundary | Lower | Upper |
|---|---|---|
| Task name length | 0 (invalid) / 1 (valid) | 999 (valid) / 1000 (invalid) |
| Collection index | 0 (valid for non-empty) | len-1 (valid) / len (invalid) |
| Calendar month input | 1 (valid) | 13 (invalid) |
| Elapsed time format | <3600s → MM:SS | ≥3600s → HH:MM:SS |

**Example — BA test:**
```python
def test_add_task_999_char_name_accepted(self):
    """[BA] Upper boundary - 1 — name of length 999 is exactly within valid range."""
    self.tasks.add_item(make_task(name="x" * 999))
    self.assertEqual(len(self.tasks.items), 1)

def test_add_task_name_over_1000_chars_rejected(self):
    """[BA] Upper boundary — name of length 1000 is invalid (>= 1000 rejected)."""
    self.tasks.add_item(make_task(name="x" * 1000))
    self.assertEqual(len(self.tasks.items), 0)
```

#### Error Guessing (EG)
We used intuition and domain knowledge to identify likely error cases.

| Guessed Error | Test |
|---|---|
| Delete non-existent ID | `test_delete_nonexistent_task_leaves_collection_unchanged` |
| Rename with empty string | `test_rename_task_empty_name_ignored` |
| Pass None to is_valid_number | `test_is_valid_number_none` |
| Toggle same status twice | `test_toggle_task_status_back_to_normal` |
| Birthday filter ignoring year | `test_birthdays_filter_ignores_year` |
| Whitespace-only task name | `test_add_task_whitespace_only_name_rejected` (**reveals Fault 1**) |
| Malformed CSV row | `test_event_loader_malformed_csv_does_not_crash` (**reveals Fault 2**) |

**Example — EG test:**
```python
def test_delete_nonexistent_task_leaves_collection_unchanged(self):
    """[EG] Non-existent ID — delete of unknown ID is safe and silent."""
    self.tasks.add_item(make_task(item_id=1))
    self.tasks.delete_item(99)
    self.assertEqual(len(self.tasks.items), 1)
```

#### Combinatorial Testing (CT)
We tested interactions between multiple parameters using a **targeted combination strategy**:

- `frequency × repetition` — 8 combinations (ONCE/DAILY/WEEKLY/MONTHLY/YEARLY/BIWEEKLY × rep=1,2,3,4,5)
- `status × privacy` — 4 combinations (NORMAL/DONE/IMPORTANT/UNIMPORTANT × True/False)
- `deadline × status × privacy` for Tasks — 2 representative combinations
- `firstweekday × month` — Monday-start and Sunday-start for all 12 months
- external resource type × import source — single `.ics` file vs. `.ics` folder with unrelated files present

**Example — CT test:**
```python
def test_ct_weekly_rep2_one_extra_date(self):
    """[CT] WEEKLY × repetition=2 → event recurs on one additional date."""
    self.assertEqual(len(self._make_repeated(2, Frequency.WEEKLY).items), 1)
```

### 3.2 Blackbox Test Results

| Test Class | Tests | Techniques | Result |
|---|---|---|---|
| TestTaskManagement | 24 | EP, BA, EG | ⚠️ 1 FAIL (fault found) |
| TestEventManagement | 11 | EP, BA, EG | ✅ All pass |
| TestTimerBehavior | 8 | EP, BA | ✅ All pass |
| TestCollectionBehavior | 9 | EP, BA, EG | ✅ All pass |
| TestFilteringBehavior | 9 | EP, EG | ✅ All pass |
| TestCalendarBehavior | 15 | EP, BA | ✅ All pass |
| TestRepeatedEventsBehavior | 10 | EP | ✅ All pass |
| TestDataPersistence | 11 | EP, EG | ⚠️ 1 FAIL (fault found) |
| TestICSImportBehavior | 3 | EP, EG | ✅ All pass |
| TestCombinatorialTesting | 17 | CT | ✅ All pass |
| **Total** | **117** | | **✅ 115/117 pass · ❌ 2 reveal faults** |

---

## 4. Section 2.2 — Whitebox Testing

Whitebox tests are written with full knowledge of the source code — they target specific branches, algorithms, and implementation details.

### 4.1 Unit Tests (`tests/whitebox/test_whitebox.py`)

Each test cites the specific source line or algorithm it validates.

| Test Class | Mechanism Tested | Tests |
|---|---|---|
| TestTimerInternals | `len(stamps) % 2 == 1`, pair-summation, format thresholds | 12 |
| TestCollectionInternals | `\[` rejection, 1000-char guard, `max(ids)+1`, same-status revert | 13 |
| TestSubtaskPrefixEncoding | `--` vs `----` prefix, `insert(n+1)`, 100-char cap, strip-2 | 7 |
| TestCalendarInternals | Leap-year formula (`%4/%100/%400`), `itermonthdays` padding | 13 |
| TestPersianCalendarInternals | Persian conversion helpers, Persian week numbers, `use_persian_calendar=True` branches | 4 |
| TestRepeatedEventsInternals | `range(1, repetition)`, month/year overflow, Feb boundary | 8 |
| TestCSVLoadingInternals | old/new CSV format detection, dot-prefix strip, extra stamp columns, `d/w/m/y` codes | 8 |
| TestAuxiliaryLoaderInternals | BirthdayLoader early returns and address-book parsing | 3 |
| TestICSLoaderInternals | TaskLoaderICS/EventLoaderICS branch logic, RRULE/EXDATE, missing-field fallbacks | 8 |
| TestFilterInternals | Stable sort, year check in Events vs. none in Birthdays | 4 |
| TestMoveTaskInternals | `pop+insert` semantics, post-pop index shift | 3 |
| TestPauseAllOtherTimersInternals | `is_counting` guard, selected-ID exemption | 3 |
| **Total** | | **86** |

**Example — Whitebox test (cites exact source code):**
```python
def test_passed_time_paused_sums_one_interval(self):
    """
    stamps = [base, base+30] → one interval of 30s.
    Implementation: for index=1 (odd): time_passed += stamps[1] - stamps[0].
    """
    base = 1_000_000
    t = Timer([base, base + 30])
    self.assertEqual(t.passed_time, "00:30")
```

### 4.2 Integration Tests (`tests/integration/test_integration.py`)

Integration tests cross module boundaries and validate end-to-end pipelines.

| Pipeline | Description | Tests |
|---|---|---|
| Events → RepeatedEvents → filter | Recurring events visible on correct days | 5 |
| Tasks → Save → Load → Modify → Save | Full persistence cycle with state changes | 4 |
| Events → Save → Load → RepeatedEvents | Frequency survives CSV round-trip | 3 |
| Tasks + Timer full lifecycle | start/pause/resume/reset across collection API | 3 |
| Calendar + Filter consistency | Grid dimensions match filter results | 3 |
| ICS import → domain objects → filter | VTODO/VEVENT import through real `.ics` files and recurring-event filtering | 3 |
| **Total** | | **21** |

**Example — Integration test:**
```python
def test_weekly_event_visible_on_repeated_date(self):
    """
    Create weekly event on 2024-03-01. RepeatedEvents generates March 8 and 15.
    Filtering March 8 must return exactly that event.
    """
    user_events = Events()
    user_events.add_item(make_event(..., repetition=3, frequency=Frequency.WEEKLY))
    repeated = RepeatedEvents(user_events, False, 2024)
    result = repeated.filter_events_that_day(MockScreen(2024, 3, 8))
    self.assertEqual(len(result.items), 1)
```

### 4.3 Branch Coverage Results

We measured branch coverage with `coverage.py --branch`:

```bash
python -m coverage run --branch -m pytest \
  tests/blackbox/test_blackbox.py \
  tests/whitebox/test_whitebox.py \
  tests/integration/test_integration.py -q
python -m coverage report -m \
  calcure/data.py calcure/calendars.py calcure/savers.py calcure/loaders.py
```

```
Name                   Stmts   Miss Branch BrPart  Cover   Missing
------------------------------------------------------------------
calcure/calendars.py      62      1     12      1    97%   96
calcure/data.py          296      8    124     19    94%   179->exit, 180->179, ...
calcure/loaders.py       327     48    108      9    85%   150, 163-165, 169-172, ...
calcure/savers.py         40      2     10      2    92%   26, 56
------------------------------------------------------------------
TOTAL                    725     59    254     31    89%
```

**Notes on uncovered areas:**
- `calcure/__main__.py`, `controls.py`, `dialogues.py` — curses/interactive UI; not unit-testable without a terminal
- `loaders.py` remains the weakest covered core module because HolidayLoader and some external-resource paths require broader environment setup
- `calendars.py` is near-completely covered after the Persian-calendar tests

---

## 5. Section 2.3 — Mutation Testing

Mutation testing systematically modifies source code to verify that tests detect changes.

### 5.1 Setup

- **Tool:** `mutmut` v2.4.4
- **Files mutated:** `calcure/data.py`, `calcure/calendars.py`
- **Test suite used:** blackbox + whitebox + integration
- **Configuration (`pyproject.toml`):**
  ```toml
  [tool.mutmut]
  paths_to_mutate = "calcure/data.py,calcure/calendars.py"
  tests_dir = "."
  runner = "python -m pytest tests/blackbox/test_blackbox.py tests/whitebox/test_whitebox.py tests/integration/test_integration.py -x -q"
  ```
- **Run command:**
  ```bash
  mutmut run
  mutmut results
  ```

### 5.2 Final Mutation Score

| Module | Locations | Detected | Survived | Score |
|---|---|---|---|---|
| `calcure/data.py` | 178 | 518 | 134 | 79.4% |
| `calcure/calendars.py` | 29 | 122 | 10 | 92.4% |
| **Total** | **207** | **640** | **144** | **81.6%** |

### 5.3 Categories of Survived Mutants

**Category 1 — Optional-field and boolean-default mutations**  
Examples: `None -> True/False` at `data.py:48`, `data.py:95`.  
These survive because tests validate high-level behavior rather than every stored optional/default field after construction.

**Category 2 — Relaxed comparator mutations near branch boundaries**  
Examples: `Eq -> GtE/LtE` and `Gt -> NotEq/GtE` at `data.py:126`, `data.py:173`, `data.py:238`, `calendars.py:39/42/91`.  
These survive when test inputs do not separate adjacent relational cases strongly enough.

**Category 3 — RRULE / EXDATE edge-path survivors**  
Examples: survivors at `data.py:382`, `data.py:396`, `data.py:405`.  
A few path variations around exclusion and slice handling still survive.

**Category 4 — Calendar arithmetic edge cases**  
Examples: `FloorDiv` substitutions at `calendars.py:76`, date arithmetic at `data.py:439-440`.

### 5.4 Mutation-Targeted Tests (`tests/mutation/test_mutation.py`)

We wrote **73 precision tests** each designed to kill one or more specific surviving mutants:

| Test Class | Targeted Mutants | Tests |
|---|---|---|
| TestDefaultFieldIdentity | `DAT-L48`, `DAT-L95` (None → False/True) | 3 |
| TestBooleanReturnIdentity | False-identity mutations across collection methods | 6 |
| TestCollectionChangedInit | `.changed` initialized to exactly `False` | 3 |
| TestTimerPassedTimeArithmetic | Day-boundary arithmetic mutations | 3 |
| TestNameLengthBoundaryPrecision | 999/1000 char boundary comparators | 4 |
| TestStatusTogglePrecision | Same-status revert logic | 4 |
| TestGenerateIdPrecision | `max+1` arithmetic mutations | 3 |
| TestSubtaskDashPrecision | `--` vs `----` prefix comparisons | 4 |
| TestWeeklyRecurrenceFormula | Weekly offset arithmetic | 4 |
| TestDailyRecurrenceFormula | Daily overflow boundary | 3 |
| TestFilterEventsYearPrecision | Year-equality comparators in filters | 3 |
| TestBirthdaysFilterPrecision | Month/day comparators (no year check) | 3 |
| TestRepeatedEventsEdgeCases | `repetition >= 1` guard and rrule branch | 2 |
| TestMonthlyRecurrenceFormula | Month-overflow arithmetic | 4 |
| TestItemExistsNotFound | `item_exists` false-return identity | 2 |
| TestCalendarLeapYearPrecision | Leap-year formula comparators | 6 |
| **Total** | | **73** |

The final rerun kills **640 of 784** generated mutations — an **81.6% mutation score**.

---

## 6. Section 2.4 — Alternate Testing: CLI Testing

CLI testing exercises calcure's command-line interface by launching it as a real subprocess. Calcure's CLI surface has two tiers:

- **Tier 1** — flags processed before curses starts (`-v`, `--folder`, `--config`, unknown flags): tested with a plain subprocess (no TTY needed)
- **Tier 2** — flags processed inside `main(stdscr)` (`--task`, `--event`): tested with Python's built-in `pty` module to provide a real pseudo-terminal so `curses.initscr()` succeeds

| Test Class | Scenario | Tests |
|---|---|---|
| TestVersionFlag | `-v` outputs version string, exits 0, creates no files | 3 |
| TestFolderFlag | `--folder` creates dir, routes CSVs, handles unwritable path | 4 |
| TestConfigFlag | `--config` creates/reads config, handles corrupt config | 3 |
| TestTaskFlag | `--task` writes to CSV, empty name, no side-effects on events CSV | 4 |
| TestEventFlag | `--event` writes to CSV, malformed input, Feb 30 / month 13 stored without validation | 5 |
| TestInvalidFlags | Unknown long/short flags, extra positional args don't crash | 3 |
| TestCombinedInvocations | No args, `--privacy` + `--folder`, `-v` + `--folder` | 3 |
| TestDataIntegrity | Bad flag doesn't corrupt existing data; atomic `.bak` write | 2 |
| **Total** | | **27** |

**Example — Tier 1 (subprocess):**
```python
def test_version_flag_exits_zero(self):
    result = subprocess.run(CALCURE + ["-v"], capture_output=True, text=True, env=env)
    assert result.returncode == 0
    assert re.search(r"\d+\.\d+", result.stdout)
```

**Example — Tier 2 (PTY):**
```python
def test_task_flag_writes_csv(self):
    output = run_with_pty(["--task", "Buy milk", "2", "2024", "4", "10"])
    tasks = list(csv.reader(open(tasks_csv)))
    assert any("Buy milk" in row[0] for row in tasks)
```

---

## 7. Overall Test Results Summary

### 7.1 Final Test Count

| File | Tests | Pass | Fail | Notes |
|---|---|---|---|---|
| `tests/blackbox/test_blackbox.py` | 117 | 115 | **2** | Failures reveal 2 real faults |
| `tests/whitebox/test_whitebox.py` | 86 | 86 | 0 | |
| `tests/integration/test_integration.py` | 21 | 21 | 0 | |
| `tests/mutation/test_mutation.py` | 73 | 73 | 0 | |
| `tests/cli/test_cli.py` | 27 | 27 | 0 | |
| **Total** | **324** | **322** | **2** | |

### 7.2 Coverage Summary

| Module | Stmts | Miss | Branch | BrPart | Cover |
|---|---|---|---|---|---|
| `calcure/calendars.py` | 62 | 1 | 12 | 1 | 97% |
| `calcure/data.py` | 296 | 8 | 124 | 19 | 94% |
| `calcure/loaders.py` | 327 | 48 | 108 | 9 | 85% |
| `calcure/savers.py` | 40 | 2 | 10 | 2 | 92% |
| **Total** | **725** | **59** | **254** | **31** | **89%** |

### 7.3 Mutation Testing Summary

| Metric | Value |
|---|---|
| Tool | mutmut v2.4.4 |
| Files mutated | `data.py`, `calendars.py` |
| Mutation locations exercised | 207 |
| Total mutation runs | 784 |
| Killed / detected | 640 |
| Survived | 144 |
| **Mutation Score** | **81.6%** |

### 7.4 Before vs. After

| Metric | Before (repo baseline) | After (this project) |
|---|---|---|
| Test files | 0 | **5** |
| Test lines | 0 | **4,000+** |
| Tests | 0 | **324** |
| Core coverage (`data/calendars/loaders/savers`) | ~0% | **89%** |
| Mutation score | 0% | **81.6%** |
| **Real faults found** | 0 | **2** |

---

## 8. Faults Discovered

We discovered **2 confirmed faults** in the SUT. Both are exposed by failing tests in the blackbox suite.

### Fault 1 — Whitespace-Only Task Names Accepted (data.py)

| Field | Detail |
|---|---|
| **Test** | `test_add_task_whitespace_only_name_rejected` (TestTaskManagement) |
| **Result** | ❌ FAILS — reveals the fault |
| **Location** | `calcure/data.py`, `Collection.add_item()` |
| **Root cause** | The input guard is `1000 > len(item.name) > 0`. A name of `"   "` (3 spaces) has `len=3 > 0`, so it passes the check and is accepted. |
| **Expected** | Names consisting only of whitespace should be rejected (equivalent to empty name from the user's perspective). |
| **Fix** | Change guard to `1000 > len(item.name.strip()) > 0`. |
| **Severity** | Medium — a user can create invisible-looking tasks that cannot be found by name search. |

### Fault 2 — Malformed CSV Crashes EventLoaderCSV (loaders.py)

| Field | Detail |
|---|---|
| **Test** | `test_event_loader_malformed_csv_does_not_crash` (TestDataPersistence) |
| **Result** | ❌ FAILS — reveals the crash |
| **Location** | `calcure/loaders.py`, `EventLoaderCSV.load()` |
| **Root cause** | `year = int(row[1])` raises `ValueError` when a CSV row has a non-numeric value in the year column. There is no try/except around this conversion. |
| **Expected** | Malformed rows should be silently skipped; loading should continue for the remaining rows. |
| **Fix** | Wrap the integer conversion in a try/except block or add a pre-check. |
| **Severity** | High — any manually edited or externally corrupted events CSV crashes the loader on startup. |

---

## 9. How to Run the Tests

### Prerequisites

```bash
pip install icalendar python-dateutil jdatetime holidays pytest pytest-cov mutmut backports.tarfile
```

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Run With Branch Coverage Report

```bash
python -m coverage run --branch -m pytest \
  tests/blackbox/test_blackbox.py \
  tests/whitebox/test_whitebox.py \
  tests/integration/test_integration.py -q
python -m coverage report -m \
  calcure/data.py calcure/calendars.py calcure/savers.py calcure/loaders.py
```

### Run Mutation Testing

```bash
mutmut run
mutmut results
```

### Run Individual Sections

```bash
python -m pytest tests/blackbox/test_blackbox.py       -v  # 2.1 — Blackbox
python -m pytest tests/whitebox/test_whitebox.py       -v  # 2.2 — Whitebox unit
python -m pytest tests/integration/test_integration.py -v  # 2.2 — Integration
python -m pytest tests/mutation/test_mutation.py       -v  # 2.3 — Mutation-targeted
python -m pytest tests/cli/test_cli.py                 -v  # 2.4 — CLI
```

---

## 10. Lessons Learned

1. **Blackbox testing works well when specs are implicit in code comments.** Calcure has no formal API docs, so we used function names, docstrings, and README behavior descriptions as specifications.

2. **Branch coverage of UI code is impractical without headless testing.** `__main__.py` and `controls.py` account for ~1,400 lines and are entirely uncoverable with unit tests. This is expected for curses applications.

3. **Mutation testing reveals gaps that coverage doesn't.** Even with **89% core coverage**, we still had **144 surviving mutations**. Most survivors came from optional/default fields and relaxed comparator changes, which normal coverage numbers alone would not reveal.

4. **CLI testing catches integration-level bugs invisible to unit tests.** By launching calcure as a real subprocess with a PTY, we validated that Tier-2 flags (`--task`, `--event`) correctly write to CSV files and do not corrupt existing data — something no amount of unit testing could have verified.
