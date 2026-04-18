# Software Testing & Design — Final Testing Report
## Calcure: Terminal Calendar & Task Manager

**Team:** Yash Salunke · Harshal Gajjar  
**Date:** April 2026  
**Repository:** https://github.com/anufrievroman/calcure

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

Per the course requirements, we conducted **four** types of testing:

| Type | File | Tests | Section |
|---|---|---|---|
| Blackbox (EP + BA + EG + CT) | `test_blackbox.py` | 115 | 2.1 |
| Whitebox Unit Tests | `test_whitebox.py` | 86 | 2.2 |
| Whitebox Integration Tests | `test_integration.py` | 21 | 2.2 |
| Mutation Testing | `mutatest` on `data.py`, `calendars.py` | 784 runs, 81.6% score | 2.3 |
| Alternate — Mock Testing | `test_mock.py` | 17 | 2.4 |
| **Total** | | **239 tests** | |

Blackbox tests are tagged where relevant with EP/BA/EG/CT labels, and the whitebox/integration suites use docstrings to explain the intent of each test.

---

## 3. Section 2.1 — Blackbox Testing

Blackbox tests treat each component as an opaque box: only inputs and outputs are observed, with no knowledge of the internal implementation.

### 3.1 Techniques Applied

#### Equivalence Partitioning (EP)
We divided inputs into **valid** and **invalid** partitions and wrote one representative test per partition.

| Component | Valid Partition | Invalid Partition |
|---|---|---|
| Task name | 1–999 characters | 0 chars, ≥1000 chars |
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
| TestTaskManagement | 23 | EP, BA, EG | ✅ All pass |
| TestEventManagement | 11 | EP, BA, EG | ✅ All pass |
| TestTimerBehavior | 8 | EP, BA | ✅ All pass |
| TestCollectionBehavior | 9 | EP, BA, EG | ✅ All pass |
| TestFilteringBehavior | 9 | EP, EG | ✅ All pass |
| TestCalendarBehavior | 15 | EP, BA | ✅ All pass |
| TestRepeatedEventsBehavior | 10 | EP | ✅ All pass |
| TestDataPersistence | 10 | EP, EG | ✅ All pass |
| TestICSImportBehavior | 3 | EP, EG | ✅ All pass |
| TestCombinatorialTesting | 17 | CT | ✅ All pass |
| **Total** | **115** | | **✅ 115/115** |

---

## 4. Section 2.2 — Whitebox Testing

Whitebox tests are written with full knowledge of the source code — they target specific branches, algorithms, and implementation details.

### 4.1 Unit Tests (`test_whitebox.py`)

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

### 4.2 Integration Tests (`test_integration.py`)

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

We measured branch coverage with `coverage.py --branch`. The latest whitebox additions were designed specifically to improve the previously weakest areas:

- `calendars.py` Persian-calendar branches and conversion helpers
- `loaders.py` old-format CSV handling, BirthdayLoader branches, and Task/Event ICS parsing
- real `.ics` integration pipelines for recurring events and VTODO import

The final coverage run for the 4 main test files used:

```bash
python -m coverage run --branch -m pytest \
  test_blackbox.py test_whitebox.py test_integration.py test_mock.py -q
python -m coverage report -m \
  calcure/data.py calcure/calendars.py calcure/savers.py calcure/loaders.py
```

The resulting coverage table is:

```
Name                   Stmts   Miss Branch BrPart  Cover   Missing
------------------------------------------------------------------
calcure/calendars.py      62      1     14      1    97%   96
calcure/data.py          296      8    128     19    94%   179->exit, 180->179, 190->exit, 191->190, 199->198, 264->exit, 279->exit, 280->279, 287->exit, 288->287, 298->297, 332->exit, 333->332, 340->exit, 341->340, 383-385, 390-392, 396->405, 420->432, 422-423
calcure/loaders.py       327     48    116      9    84%   150, 163-165, 169-172, 177-211, 246, 263->267, 283-284, 299-300, 342->349, 386-387, 423, 435, 440-442, 447->452, 469, 497-498
calcure/savers.py         40      2     10      2    92%   26, 56
------------------------------------------------------------------
TOTAL                    725     59    268     31    89%
```

**Notes on uncovered areas from the final run:**
- `calcure/__main__.py`, `controls.py`, `dialogues.py` — curses/interactive UI; not unit-testable without a terminal
- `loaders.py` remains the weakest covered core module because HolidayLoader and some external-resource paths still require broader environment setup
- `calendars.py` is now near-completely covered after the added Persian-calendar tests

---

## 5. Section 2.3 — Mutation Testing

Mutation testing systematically modifies source code to verify that tests detect changes.

### 5.1 Setup

- **Tool:** `mutatest` v3.1.0
- **Files mutated:** `calcure/data.py`, `calcure/calendars.py`
- **Test suite used:** all 4 main test files (the current suite contains 239 tests)
- **Run commands:**
  ```bash
  mutatest -s calcure/data.py -m f -n 9999 \
    -t "python -m pytest test_blackbox.py test_whitebox.py test_integration.py test_mock.py -q" \
    -o mutatest_data_full.rst

  mutatest -s calcure/calendars.py -m f -n 9999 \
    -t "python -m pytest test_blackbox.py test_whitebox.py test_integration.py test_mock.py -q" \
    -o mutatest_calendars_full.rst
  ```

The final mutation run used **full-location mode** for both target files:
- `data.py`: `178/178` mutation locations exercised
- `calendars.py`: `29/29` mutation locations exercised

### 5.2 Final Mutation Score

| Module | Locations | Detected | Survived | Score |
|---|---|---|---|---|
| `calcure/data.py` | 178 | 518 | 134 | 79.4% |
| `calcure/calendars.py` | 29 | 122 | 10 | 92.4% |
| **Total** | **207** | **640** | **144** | **81.6%** |

### 5.3 Categories of Survived Mutants

**Category 1 — Optional-field and boolean-default mutations**  
Examples: `None -> True/False` at `data.py:48`, `data.py:95`, and `True/False -> None` at several task/event state fields.  
These survive because the tests validate high-level behavior more often than every stored optional/default field after construction.

**Category 2 — Relaxed comparator mutations near branch boundaries**  
Examples: `Eq -> GtE/LtE` and `Gt -> NotEq/GtE` at lines such as `data.py:126`, `data.py:173`, `data.py:238`, and `calendars.py:39/42/91`.  
These survive when the current test inputs do not separate adjacent relational cases strongly enough.

**Category 3 — RRULE / EXDATE edge-path survivors**  
Examples: survivors remain at `data.py:382`, `data.py:396`, and `data.py:405`.  
This area improved substantially because many RRULE-related mutations were killed, but a few path variations around exclusion and slice handling still survive.

**Category 4 — Calendar arithmetic edge cases**  
Examples: surviving `FloorDiv` / arithmetic substitutions at `calendars.py:76` and date arithmetic variants at `data.py:439-440`.  
These indicate that a small number of week-number and elapsed-time calculations still need tighter assertions.

### 5.4 Action Taken to Improve Mutation Score

We added **targeted tests** to kill the most impactful survived mutants:

1. **calendar_number propagation** — added assertions on `calendar_number` in constructor tests
2. **`getDatetime()` method** — added a test for `UserEvent.getDatetime()` return value
3. **Persian calendar logic** — added targeted branch tests for conversions, `last_day`, and week computations
4. **ICS parsing and RRULE handling** — added parser-level and integration-level `.ics` tests, including `RRULE` + `EXDATE`

The final rerun kills **640 of 784** generated mutations across the two target modules.

---

## 6. Section 2.4 — Alternate Testing: Mock Testing

Mock testing was chosen as the alternate testing type because Calcure interacts with the file system, network (weather/ICS URLs), and system clock — all of which benefit from being replaced with controlled fakes.

### 6.1 What Was Mocked

| Mock Target | Technique | Purpose |
|---|---|---|
| `time.time()` | `@patch("calcure.data.time.time")` | Deterministic timer elapsed-time calculation |
| `builtins.open` + IOError | `mock_open` | Test LoaderCSV fallback when file is missing |
| `urllib.request.urlopen` + HTTPError | `patch` + side_effect | Test ICS URL loader handles HTTP 404 gracefully |
| `urllib.request.urlopen` + URLError | `patch` + side_effect | Test ICS URL loader handles no-internet gracefully |
| `pathlib.Path.replace` | `MagicMock` | Verify atomic write pattern in savers |
| `calcure.calendars.datetime` | `patch` | Verify `Calendar.first_day()` delegates to `datetime.date` |

### 6.2 Mock Test Results

| Test Class | Tests | Result |
|---|---|---|
| TestTimerWithMockedTime | 4 | ✅ All pass |
| TestLoaderCSVWithMockedFile | 6 | ✅ All pass |
| TestCollectionInteractions | 3 | ✅ All pass |
| TestSaverAtomicWrite | 2 | ✅ All pass |
| TestCalendarWithMockedDatetime | 2 | ✅ All pass |
| **Total** | **17** | **✅ 17/17** |

**Example — Mock test (mocked time.time for determinism):**
```python
@patch("calcure.data.time.time", return_value=1_000_000.0)
def test_timer_passed_time_while_counting_uses_mocked_time(self, mock_time):
    """Timer started at 999_940 (60s ago) must report exactly 01:00."""
    t = Timer([999_940])
    self.assertEqual(t.passed_time, "01:00")
```

---

## 7. Overall Test Results Summary

### 7.1 Final Test Count

| File | Tests | Pass | Fail |
|---|---|---|---|
| `test_blackbox.py` | 115 | 115 | 0 |
| `test_whitebox.py` | 86 | 86 | 0 |
| `test_integration.py` | 21 | 21 | 0 |
| `test_mock.py` | 17 | 17 | 0 |
| **Total** | **239** | **239** | **0** |

### 7.2 Coverage Summary

Fresh coverage results for the 4 main test files:

| Module | Stmts | Miss | Branch | BrPart | Cover |
|---|---|---|---|---|---|
| `calcure/calendars.py` | 62 | 1 | 14 | 1 | 97% |
| `calcure/data.py` | 296 | 8 | 128 | 19 | 94% |
| `calcure/loaders.py` | 327 | 48 | 116 | 9 | 84% |
| `calcure/savers.py` | 40 | 2 | 10 | 2 | 92% |
| **Total** | **725** | **59** | **268** | **31** | **89%** |

The remaining misses are concentrated in `loaders.py` and in a few recurrence/time-edge branches inside `data.py`.

### 7.3 Mutation Testing Summary

| Metric | Value |
|---|---|
| Files mutated | `data.py`, `calendars.py` |
| Mutation locations exercised | 207 |
| Total mutation runs | 784 |
| Killed / detected | 640 |
| Survived | 144 |
| **Mutation Score** | **81.6%** |

### 7.4 Before vs. After

| Metric | Before (repo baseline) | After (this project) |
|---|---|---|
| Test files | 2 | 6 |
| Test lines | ~67 | **3,200+** |
| Tests | ~5 | **239** |
| Core coverage (`data/calendars/loaders/savers`) | ~0% | **89%** |
| Mutation score | 0% | **81.6%** |

---

## 8. Faults Discovered

During testing we did **not** discover crashing bugs in the core logic. However, we identified the following **potential issues and edge cases**:

| Issue | Location | Severity | Notes |
|---|---|---|---|
| `ONCE` frequency with `repetition > 1` creates duplicate events on same date | `data.py:RepeatedEvents` | Low | Unusual input combination — UI prevents this |
| `is_task_format_old` crashes on empty file | `loaders.py:50-55` | Medium | `text[0]` raises IndexError if CSV is empty |
| Missing `DTSTART` in imported VEVENT creates default date `0/1/1` and time `00:00` | `loaders.py:418-465` | Low | Safe fallback, but semantically odd for imported calendar data |
| `getDatetime()` not tested for timezone edge cases | `data.py:88-89` | Low | Local timezone used implicitly |

---

## 9. How to Run the Tests

### Prerequisites

```bash
# Install dependencies
pip install icalendar python-dateutil jdatetime holidays pytest coverage mutatest backports.tarfile
```

### Run All Tests

```bash
python -m pytest test_blackbox.py test_whitebox.py test_integration.py test_mock.py -v
```

### Run With Branch Coverage Report

```bash
python -m coverage run --branch -m pytest \
  test_blackbox.py test_whitebox.py test_integration.py test_mock.py -q
python -m coverage report -m \
  calcure/data.py calcure/calendars.py calcure/savers.py calcure/loaders.py
```

### Run Mutation Testing

```bash
mutatest -s calcure/data.py -m f -n 9999 \
  -t "python -m pytest test_blackbox.py test_whitebox.py test_integration.py test_mock.py -q" \
  -o mutatest_data_full.rst

mutatest -s calcure/calendars.py -m f -n 9999 \
  -t "python -m pytest test_blackbox.py test_whitebox.py test_integration.py test_mock.py -q" \
  -o mutatest_calendars_full.rst
```

### Run Individual Test Types

```bash
python -m pytest test_blackbox.py   -v  # Section 2.1 — Blackbox
python -m pytest test_whitebox.py   -v  # Section 2.2 — Whitebox (unit)
python -m pytest test_integration.py -v # Section 2.2 — Whitebox (integration)
python -m pytest test_mock.py       -v  # Section 2.4 — Alternate (mock)
```

---

## 10. Lessons Learned

1. **Blackbox testing works well when specs are implicit in code comments.** Calcure has no formal API docs, so we used function names, docstrings, and README behavior descriptions as specifications.

2. **Branch coverage of UI code is impractical without headless testing.** `__main__.py` and `controls.py` account for ~1,400 lines and are entirely uncoverable with unit tests. This is expected for curses applications.

3. **Mutation testing reveals gaps that coverage doesn't.** Even with **89% core coverage**, we still had **144 surviving mutations**. Most survivors came from optional/default fields and relaxed comparator changes, which normal coverage numbers alone would not reveal.

4. **Mock testing is essential for I/O-heavy code.** Without mocking `time.time()`, timer tests would be non-deterministic. Without mocking `urllib`, ICS URL tests would require internet access.
