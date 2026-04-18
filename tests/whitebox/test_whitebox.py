#!/usr/bin/env python3
"""
Whitebox Tests (Section 2.2) — Calcure Calendar & Task Manager
==============================================================
Whitebox testing exploits knowledge of the INTERNAL implementation:
data structures, algorithms, edge cases derived from reading the source code.
Each test references the specific code path or invariant it is exercising.
"""

import sys
import os
import time
import datetime
import tempfile
import unittest

import icalendar

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

from calcure.data import (
    Task, UserEvent, Event, Timer, Tasks, Events, Birthdays,
    Status, Frequency, RepeatedEvents, Collection
)
from calcure.calendars import Calendar

try:
    import jdatetime
    HAS_JDATETIME = True
except ImportError:
    HAS_JDATETIME = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_timer(stamps=None):
    return Timer(stamps or [])


def make_task(item_id=0, name="Task", status=Status.NORMAL,
              privacy=False, year=0, month=0, day=0):
    return Task(item_id, name, status, make_timer(), privacy, year, month, day)


def make_event(item_id=0, year=2024, month=3, day=1, name="Event",
               repetition=1, frequency=Frequency.ONCE,
               status=Status.NORMAL, privacy=False):
    return UserEvent(item_id, year, month, day, name, repetition,
                     frequency, status, privacy)


class MockScreen:
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day


# ===========================================================================
# 1. TIMER INTERNALS
# ===========================================================================

class TestTimerInternals(unittest.TestCase):
    """
    Whitebox: Timer.is_counting uses `len(stamps) % 2 == 1`.
    Timer.passed_time sums consecutive (stop - start) pairs.
    """

    # --- is_counting: odd/even stamp count ---

    def test_zero_stamps_not_counting(self):
        """len([]) % 2 == 0  →  not counting."""
        self.assertFalse(Timer([]).is_counting)

    def test_one_stamp_is_counting(self):
        """len([t0]) % 2 == 1  →  counting."""
        self.assertTrue(Timer([1000]).is_counting)

    def test_two_stamps_not_counting(self):
        """len([t0, t1]) % 2 == 0  →  not counting (paused)."""
        self.assertFalse(Timer([1000, 1060]).is_counting)

    def test_three_stamps_counting(self):
        """len([t0, t1, t2]) % 2 == 1  →  counting again (resumed)."""
        self.assertTrue(Timer([1000, 1060, 1120]).is_counting)

    def test_four_stamps_not_counting(self):
        """len([t0..t3]) % 2 == 0  →  paused."""
        self.assertFalse(Timer([1000, 1060, 1120, 1180]).is_counting)

    # --- is_started: truthiness of list ---

    def test_empty_list_is_falsy_not_started(self):
        """bool([]) is False  →  not started."""
        self.assertFalse(Timer([]).is_started)

    def test_nonempty_list_is_truthy_started(self):
        """bool([x]) is True  →  started."""
        self.assertTrue(Timer([1000]).is_started)

    # --- passed_time: pair summation ---

    def test_passed_time_paused_sums_one_interval(self):
        """
        stamps = [base, base+30] → one interval of 30 s.
        Implementation: for index=1 (odd): time_passed += stamps[1] - stamps[0].
        Timer is not counting, so no live contribution added.
        """
        base = 1_000_000
        t = Timer([base, base + 30])
        result = t.passed_time
        self.assertEqual(result, "00:30")

    def test_passed_time_paused_two_intervals(self):
        """
        stamps = [base, base+10, base+20, base+40]
        Interval 1: 10 s (index 1), Interval 2: 20 s (index 3) → total 30 s.
        """
        base = 1_000_000
        t = Timer([base, base + 10, base + 20, base + 40])
        result = t.passed_time
        self.assertEqual(result, "00:30")

    def test_passed_time_format_changes_at_one_hour(self):
        """
        Implementation switches format string at exactly 60*60 seconds.
        Below 1 h → %M:%S; at or above → %H:%M:%S.
        """
        base = 1_000_000
        just_under = Timer([base, base + 3599])   # 59:59
        at_one_hour = Timer([base, base + 3600])  # 01:00:00
        self.assertRegex(just_under.passed_time, r"^\d{2}:\d{2}$")
        self.assertRegex(at_one_hour.passed_time, r"^\d{2}:\d{2}:\d{2}$")

    def test_passed_time_format_one_day(self):
        """Implementation prepends '1 day ' when 1 day < time < 2 days."""
        base = 1_000_000
        one_day_one_sec = Timer([base, base + 86401])
        result = one_day_one_sec.passed_time
        self.assertTrue(result.startswith("1 day "))

    def test_passed_time_format_two_days(self):
        """Implementation prepends 'N days ' when time >= 2 days."""
        base = 1_000_000
        two_days = Timer([base, base + 2 * 86400 + 1])
        result = two_days.passed_time
        self.assertTrue(result.startswith("2 days "))


# ===========================================================================
# 2. COLLECTION INTERNALS
# ===========================================================================

class TestCollectionInternals(unittest.TestCase):
    """
    Whitebox: add_item name guard, generate_id max+1 algorithm,
    toggle_item_status same-status-reverts-to-NORMAL invariant.
    """

    # --- add_item name guards ---

    def test_add_item_rejects_backslash_bracket_literal(self):
        r"""
        Source: `item.name != r"\["` guard in add_item.
        The literal string \[ must be rejected.
        """
        tasks = Tasks()
        tasks.add_item(make_task(name=r"\["))
        self.assertEqual(len(tasks.items), 0)

    def test_add_item_rejects_empty_name(self):
        """Source: `len(item.name) > 0` guard."""
        tasks = Tasks()
        tasks.add_item(make_task(name=""))
        self.assertEqual(len(tasks.items), 0)

    def test_add_item_rejects_exactly_1000_chars(self):
        """Source: `1000 > len(item.name)` — 1000 chars is NOT < 1000."""
        tasks = Tasks()
        tasks.add_item(make_task(name="a" * 1000))
        self.assertEqual(len(tasks.items), 0)

    def test_add_item_accepts_999_chars(self):
        """Source: 999 < 1000, so accepted."""
        tasks = Tasks()
        tasks.add_item(make_task(name="a" * 999))
        self.assertEqual(len(tasks.items), 1)

    def test_add_item_rejects_1001_chars(self):
        """Source: 1001 > 1000, so rejected."""
        tasks = Tasks()
        tasks.add_item(make_task(name="a" * 1001))
        self.assertEqual(len(tasks.items), 0)

    # --- generate_id: max + 1 ---

    def test_generate_id_returns_zero_for_empty(self):
        """Source: `if self.is_empty(): return 0`."""
        self.assertEqual(Tasks().generate_id(), 0)

    def test_generate_id_returns_max_plus_one(self):
        """Source: `max([item.item_id for item in self.items]) + 1`."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=3))
        tasks.add_item(make_task(item_id=7))
        tasks.add_item(make_task(item_id=1))
        self.assertEqual(tasks.generate_id(), 8)

    def test_generate_id_with_non_contiguous_ids(self):
        """generate_id picks max over entire list, even with gaps."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.add_item(make_task(item_id=100))
        tasks.add_item(make_task(item_id=50))
        self.assertEqual(tasks.generate_id(), 101)

    # --- toggle_item_status: same status reverts to NORMAL ---

    def test_toggle_same_status_reverts_to_normal(self):
        """
        Source: `if item.status == new_status: item.status = Status.NORMAL`.
        Applying the same status twice resets to NORMAL.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.toggle_item_status(0, Status.IMPORTANT)
        tasks.toggle_item_status(0, Status.IMPORTANT)
        self.assertEqual(tasks.items[0].status, Status.NORMAL)

    def test_toggle_different_status_sets_new_status(self):
        """Applying a different status sets it directly without reset."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.toggle_item_status(0, Status.DONE)
        tasks.toggle_item_status(0, Status.IMPORTANT)
        self.assertEqual(tasks.items[0].status, Status.IMPORTANT)

    # --- is_valid_number boundary conditions ---

    def test_is_valid_number_exactly_at_last_index(self):
        """Source: `0 <= number < len(self.items)` — last valid index is len-1."""
        tasks = Tasks()
        tasks.add_item(make_task())
        tasks.add_item(make_task(item_id=1))
        self.assertTrue(tasks.is_valid_number(1))
        self.assertFalse(tasks.is_valid_number(2))

    def test_is_valid_number_zero_is_valid_when_nonempty(self):
        """Index 0 is valid for a non-empty collection."""
        tasks = Tasks()
        tasks.add_item(make_task())
        self.assertTrue(tasks.is_valid_number(0))

    def test_is_valid_number_zero_is_invalid_when_empty(self):
        """Index 0 is invalid for an empty collection (0 < 0 is False)."""
        self.assertFalse(Tasks().is_valid_number(0))


# ===========================================================================
# 3. SUBTASK PREFIX ENCODING
# ===========================================================================

class TestSubtaskPrefixEncoding(unittest.TestCase):
    """
    Whitebox: add_subtask uses '--' for top-level and '----' for nested.
    toggle_subtask_state strips or adds the '--' prefix.
    """

    def _make_tasks_with(self, parent_name):
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name=parent_name))
        return tasks

    def test_add_subtask_to_top_level_gets_double_dash(self):
        """Source: `level = '----' if (items[n].name[:2] == '--') else '--'`."""
        tasks = self._make_tasks_with("Parent task")
        sub = make_task(item_id=1, name="Child")
        tasks.add_subtask(sub, 0)
        self.assertEqual(tasks.items[1].name, "--Child")

    def test_add_subtask_to_subtask_gets_quad_dash(self):
        """Source: if parent already starts with '--', use '----'."""
        tasks = self._make_tasks_with("--Subtask")
        sub = make_task(item_id=1, name="Grandchild")
        tasks.add_subtask(sub, 0)
        self.assertEqual(tasks.items[1].name, "----Grandchild")

    def test_add_subtask_inserted_after_parent(self):
        """Source: `self.items.insert(number+1, task)` — placed right after parent."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="Parent"))
        tasks.add_item(make_task(item_id=1, name="Sibling"))
        sub = make_task(item_id=2, name="Sub")
        tasks.add_subtask(sub, 0)
        self.assertEqual(tasks.items[1].name, "--Sub")
        self.assertEqual(tasks.items[2].name, "Sibling")

    def test_add_subtask_name_over_100_chars_rejected(self):
        """Source: `if 100 > len(task.name) > 0` — subtask name cap is 100."""
        tasks = self._make_tasks_with("Parent")
        sub = make_task(item_id=1, name="x" * 98)   # "--" + 98 = 100 → rejected
        tasks.add_subtask(sub, 0)
        self.assertEqual(len(tasks.items), 1)

    def test_toggle_subtask_state_adds_dash_prefix(self):
        """Source: `if item.name[:2] == '--': ... else: item.name = '--' + item.name`."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="Regular"))
        tasks.toggle_subtask_state(0)
        self.assertEqual(tasks.items[0].name, "--Regular")

    def test_toggle_subtask_state_removes_dash_prefix(self):
        """Source: `item.name = item.name[2:]` strips exactly 2 leading chars."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="--Subtask"))
        tasks.toggle_subtask_state(0)
        self.assertEqual(tasks.items[0].name, "Subtask")

    def test_toggle_subtask_state_roundtrip(self):
        """Toggling twice restores the original name."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="Original"))
        tasks.toggle_subtask_state(0)
        tasks.toggle_subtask_state(0)
        self.assertEqual(tasks.items[0].name, "Original")


# ===========================================================================
# 4. CALENDAR INTERNALS
# ===========================================================================

class TestCalendarInternals(unittest.TestCase):
    """
    Whitebox: leap year formula, itermonthdays padding, first_day weekday.
    Source of leap year check:
        `year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)`
    """

    def setUp(self):
        self.cal = Calendar(0, False)

    # --- Leap year formula ---

    def test_year_2000_is_leap_divisible_400(self):
        """2000 % 400 == 0 → leap → Feb = 29."""
        self.assertEqual(self.cal.last_day(2000, 2), 29)

    def test_year_1900_not_leap_divisible_100_not_400(self):
        """1900 % 100 == 0 but 1900 % 400 != 0 → not leap → Feb = 28."""
        self.assertEqual(self.cal.last_day(1900, 2), 28)

    def test_year_2024_is_leap_divisible_4_not_100(self):
        """2024 % 4 == 0 and 2024 % 100 != 0 → leap → Feb = 29."""
        self.assertEqual(self.cal.last_day(2024, 2), 29)

    def test_year_2023_not_leap(self):
        """2023 % 4 != 0 → not leap → Feb = 28."""
        self.assertEqual(self.cal.last_day(2023, 2), 28)

    def test_year_2100_not_leap(self):
        """2100 % 100 == 0, 2100 % 400 != 0 → not leap → Feb = 28."""
        self.assertEqual(self.cal.last_day(2100, 2), 28)

    def test_year_2400_is_leap(self):
        """2400 % 400 == 0 → leap → Feb = 29."""
        self.assertEqual(self.cal.last_day(2400, 2), 29)

    # --- itermonthdays: total always divisible by 7 ---

    def test_itermonthdays_total_multiple_of_7(self):
        """Source pads both before and after to fill complete weeks."""
        for month in range(1, 13):
            days = list(self.cal.itermonthdays(2024, month))
            self.assertEqual(len(days) % 7, 0,
                             f"Month {month} has {len(days)} days, not a multiple of 7")

    def test_itermonthdays_leading_zeros_before_first_day(self):
        """
        Source: `days_before = (first_day - self.firstweekday) % 7`.
        Jan 2024 starts on Monday (weekday 0). With firstweekday=0 (Mon),
        days_before = (0 - 0) % 7 = 0 → no leading zeros.
        """
        cal_monday = Calendar(0, False)
        days = list(cal_monday.itermonthdays(2024, 1))
        self.assertEqual(days[0], 1)

    def test_itermonthdays_leading_zeros_for_wednesday_start(self):
        """
        Mar 2023 starts on Wednesday (weekday 2). With firstweekday=0 (Mon),
        days_before = (2 - 0) % 7 = 2 → two leading zeros.
        """
        cal = Calendar(0, False)
        days = list(cal.itermonthdays(2023, 3))
        self.assertEqual(days[0], 0)
        self.assertEqual(days[1], 0)
        self.assertEqual(days[2], 1)

    def test_itermonthdays_no_actual_days_missing(self):
        """Every day from 1..last_day appears exactly once."""
        for month in range(1, 13):
            last = self.cal.last_day(2024, month)
            days = [d for d in self.cal.itermonthdays(2024, month) if d != 0]
            self.assertEqual(days, list(range(1, last + 1)))

    # --- first_day known values ---

    def test_first_day_jan_2024_is_monday(self):
        """2024-01-01 is a Monday (weekday 0)."""
        self.assertEqual(self.cal.first_day(2024, 1), 0)

    def test_first_day_feb_2024_is_thursday(self):
        """2024-02-01 is a Thursday (weekday 3)."""
        self.assertEqual(self.cal.first_day(2024, 2), 3)

    def test_first_day_mar_2024_is_friday(self):
        """2024-03-01 is a Friday (weekday 4)."""
        self.assertEqual(self.cal.first_day(2024, 3), 4)


class TestPersianCalendarInternals(unittest.TestCase):
    """Whitebox: explicitly cover the `use_persian_calendar=True` branches."""

    @unittest.skipUnless(HAS_JDATETIME, "jdatetime not installed")
    def test_gregorian_to_persian_and_back_round_trip(self):
        """
        Source: top-level convert helpers dispatch to jdatetime.
        A known Gregorian date should survive a Persian round-trip unchanged.
        """
        from calcure.calendars import convert_to_persian_date, convert_to_gregorian_date

        persian = convert_to_persian_date(2024, 3, 20)
        gregorian = convert_to_gregorian_date(*persian)
        self.assertEqual(gregorian, (2024, 3, 20))

    @unittest.skipUnless(HAS_JDATETIME, "jdatetime not installed")
    def test_persian_last_day_uses_jdatetime_leap_logic(self):
        """
        Source: Calendar.last_day() uses jdatetime.isleap() for Persian month 12.
        This test executes that branch and checks the derived month length.
        """
        cal = Calendar(0, True)
        expected = 30 if jdatetime.date(1403, 1, 1).isleap() else 29
        self.assertEqual(cal.last_day(1403, 12), expected)

    @unittest.skipUnless(HAS_JDATETIME, "jdatetime not installed")
    def test_persian_week_number_first_day_is_one(self):
        """
        Source: Persian week_number computes days since year start and adds 1.
        Therefore the first day of the Persian year must be week 1.
        """
        cal = Calendar(0, True)
        self.assertEqual(cal.week_number(1403, 1, 1), 1)

    @unittest.skipUnless(HAS_JDATETIME, "jdatetime not installed")
    def test_persian_month_week_numbers_match_calendar_rows(self):
        """Persian month_week_numbers() returns one number per rendered week row."""
        cal = Calendar(0, True)
        rows = cal.monthdayscalendar(1403, 1)
        week_numbers = cal.month_week_numbers(1403, 1)
        self.assertEqual(len(rows), len(week_numbers))


# ===========================================================================
# 5. REPEATED EVENTS INTERNALS
# ===========================================================================

class TestRepeatedEventsInternals(unittest.TestCase):
    """
    Whitebox: RepeatedEvents skips the first occurrence (range(1, repetition)),
    calculate_recurring_events handles month/year overflow.
    """

    def test_first_occurrence_not_in_repeated_list(self):
        """
        Source: `for rep in range(1, event.repetition)` — rep=0 (original date)
        is never added to repeated list.
        """
        ue = Events()
        ev = make_event(year=2024, month=3, day=1, repetition=3, frequency=Frequency.WEEKLY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        dates = [(r.year, r.month, r.day) for r in reps.items]
        self.assertNotIn((2024, 3, 1), dates)

    def test_weekly_event_correct_dates(self):
        """
        Weekly event on 2024-03-01 with repetition=3:
        rep=1: day=1+7=8  → March 8
        rep=2: day=1+14=15 → March 15
        """
        ue = Events()
        ev = make_event(year=2024, month=3, day=1, repetition=3, frequency=Frequency.WEEKLY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        dates = sorted([(r.year, r.month, r.day) for r in reps.items])
        self.assertEqual(dates, [(2024, 3, 8), (2024, 3, 15)])

    def test_biweekly_event_correct_dates(self):
        """
        Biweekly event on 2024-03-01 with repetition=3:
        rep=1: day=1+14=15 → March 15
        rep=2: day=1+28=29 → March 29
        """
        ue = Events()
        ev = make_event(year=2024, month=3, day=1, repetition=3, frequency=Frequency.BIWEEKLY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        dates = sorted([(r.year, r.month, r.day) for r in reps.items])
        self.assertEqual(dates, [(2024, 3, 15), (2024, 3, 29)])

    def test_daily_event_crosses_month_boundary(self):
        """
        Daily event on 2024-03-30 with repetition=3:
        rep=1: day=31 → March 31
        rep=2: day=32 → calculate_recurring_events → April 1
        """
        ue = Events()
        ev = make_event(year=2024, month=3, day=30, repetition=3, frequency=Frequency.DAILY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        dates = sorted([(r.year, r.month, r.day) for r in reps.items])
        self.assertIn((2024, 3, 31), dates)
        self.assertIn((2024, 4, 1), dates)

    def test_monthly_event_crosses_year_boundary(self):
        """
        Monthly event on 2024-11-01 with repetition=3:
        temp_month = 11+1=12 → Dec 1
        temp_month = 11+2=13 → calculate_recurring_events → Jan 1, 2025
        """
        ue = Events()
        ev = make_event(year=2024, month=11, day=1, repetition=3, frequency=Frequency.MONTHLY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        dates = sorted([(r.year, r.month, r.day) for r in reps.items])
        self.assertIn((2024, 12, 1), dates)
        self.assertIn((2025, 1, 1), dates)

    def test_yearly_event_increments_year_only(self):
        """
        Source: `temp_year = event.year + rep*(freq == YEARLY)`.
        Month and day stay constant; only year advances.
        """
        ue = Events()
        ev = make_event(year=2024, month=7, day=4, repetition=3, frequency=Frequency.YEARLY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        for r in reps.items:
            self.assertEqual(r.month, 7)
            self.assertEqual(r.day, 4)

    def test_zero_repetition_event_no_reps(self):
        """
        Source: `if event.repetition >= 1` — repetition=0 skips the loop.
        Also, rrule is None, so nothing is generated.
        """
        ue = Events()
        ev = make_event(repetition=0, frequency=Frequency.WEEKLY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        self.assertEqual(len(reps.items), 0)

    def test_weekly_crosses_feb_leap_year_boundary(self):
        """
        Weekly event on 2024-02-25 with repetition=2:
        rep=1: day=25+7=32 → calculate_recurring_events:
          March has 31 days; 32 > 29 (Feb has 29 in 2024), so new_day=3, new_month=3.
        """
        ue = Events()
        ev = make_event(year=2024, month=2, day=25, repetition=2, frequency=Frequency.WEEKLY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        self.assertEqual(len(reps.items), 1)
        r = reps.items[0]
        self.assertEqual((r.year, r.month, r.day), (2024, 3, 3))


# ===========================================================================
# 6. CSV LOADING INTERNALS
# ===========================================================================

class TestCSVLoadingInternals(unittest.TestCase):
    """
    Whitebox: old-format detection via text[0] == '"',
    privacy dot-prefix stripping, timer stamp parsing from CSV columns.
    """

    def _make_config(self, tasks_file, events_file):
        class FakeCF:
            TASKS_FILE = tasks_file
            EVENTS_FILE = events_file
            USE_PERSIAN_CALENDAR = False
        return FakeCF()

    def test_task_privacy_dot_prefix_stripped_from_name(self):
        """
        Source: `if row[0+shift][0] == '.': name = row[0+shift][1:]; is_private = True`.
        The leading dot is removed from the stored name.
        """
        from calcure.savers import TaskSaverCSV
        from calcure.loaders import TaskLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            tasks = Tasks()
            tasks.add_item(Task(0, "Secret", Status.NORMAL, Timer([]), True, 0, 0, 0))
            cf = self._make_config(filepath, filepath)
            TaskSaverCSV(tasks, cf).save()

            # Verify the raw CSV has a dot prefix
            with open(filepath, "r") as f:
                content = f.read()
            self.assertIn(".Secret", content)

            # Verify the loader strips it
            loaded = TaskLoaderCSV(cf).load()
            self.assertEqual(loaded.items[0].name, "Secret")
            self.assertTrue(loaded.items[0].privacy)
        finally:
            os.unlink(filepath)
            if os.path.exists(filepath + ".bak"):
                os.unlink(filepath + ".bak")

    def test_task_timer_stamps_stored_as_extra_csv_columns(self):
        """
        Source: `f.write(f',{str(stamp)}')` appends stamps as extra columns.
        Loader: `stamps = row[(2+shift):]` reads them back.
        """
        from calcure.savers import TaskSaverCSV
        from calcure.loaders import TaskLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            tasks = Tasks()
            tasks.add_item(Task(0, "Timed", Status.NORMAL, Timer([1000, 2000, 3000]), False, 0, 0, 0))
            cf = self._make_config(filepath, filepath)
            TaskSaverCSV(tasks, cf).save()

            loaded = TaskLoaderCSV(cf).load()
            stamps = loaded.items[0].timer.stamps
            self.assertEqual(len(stamps), 3)
        finally:
            os.unlink(filepath)
            if os.path.exists(filepath + ".bak"):
                os.unlink(filepath + ".bak")

    def test_task_old_format_csv_defaults_date_fields_to_zero(self):
        """
        Source: old-format detection uses text[0] == '"', then shift=0 and
        year/month/day default to 0.
        """
        from calcure.loaders import TaskLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w",
                                         encoding="utf-8") as f:
            f.write('"Legacy task",normal,1000,2000\n')
            filepath = f.name

        try:
            class FakeCF:
                TASKS_FILE = filepath
                USE_PERSIAN_CALENDAR = False

            loaded = TaskLoaderCSV(FakeCF()).load()
            task = loaded.items[0]
            self.assertEqual((task.year, task.month, task.day), (0, 0, 0))
            self.assertEqual(task.timer.stamps, ["1000", "2000"])
        finally:
            os.unlink(filepath)

    @unittest.skipUnless(HAS_JDATETIME, "jdatetime not installed")
    def test_task_loader_converts_nonzero_dates_for_persian_calendar(self):
        """
        Source: `if self.use_persian_calendar and year != 0: ...`.
        Non-zero Gregorian task dates are converted on load.
        """
        from calcure.loaders import TaskLoaderCSV
        from calcure.calendars import convert_to_persian_date

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w",
                                         encoding="utf-8") as f:
            f.write('2024,3,20,"Nowruz task",normal\n')
            filepath = f.name

        try:
            class FakeCF:
                TASKS_FILE = filepath
                USE_PERSIAN_CALENDAR = True

            loaded = TaskLoaderCSV(FakeCF()).load()
            expected = convert_to_persian_date(2024, 3, 20)
            self.assertEqual((loaded.items[0].year, loaded.items[0].month, loaded.items[0].day), expected)
        finally:
            os.unlink(filepath)

    def test_event_privacy_dot_prefix_in_csv(self):
        """
        Source: `name = f'{"."*ev.privacy}{ev.name}'` prepends dot when private.
        """
        from calcure.savers import EventSaverCSV
        from calcure.loaders import EventLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            events = Events()
            events.add_item(UserEvent(0, 2024, 3, 1, "Hidden", 1,
                                      Frequency.ONCE, Status.NORMAL, True))
            cf = self._make_config(filepath, filepath)
            EventSaverCSV(events, cf).save()

            with open(filepath, "r") as f:
                raw = f.read()
            self.assertIn(".Hidden", raw)

            loaded = EventLoaderCSV(cf).load()
            self.assertEqual(loaded.items[0].name, "Hidden")
            self.assertTrue(loaded.items[0].privacy)
        finally:
            os.unlink(filepath)
            if os.path.exists(filepath + ".bak"):
                os.unlink(filepath + ".bak")

    def test_event_frequency_old_format_d_w_m_y(self):
        """
        Source: CSV uses single-char codes 'd','w','m','y' for frequency.
        EventLoaderCSV maps these to Frequency enum values.
        """
        from calcure.loaders import EventLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w",
                                         encoding="utf-8") as f:
            # Write CSV directly in old single-char frequency format
            f.write('0,2024,1,1,"Weekly meeting",4,w,normal\n')
            f.write('1,2024,2,1,"Daily standup",7,d,normal\n')
            f.write('2,2024,3,1,"Monthly review",12,m,normal\n')
            f.write('3,2024,1,1,"Yearly review",2,y,normal\n')
            filepath = f.name

        try:
            class FakeCF:
                EVENTS_FILE = filepath
                USE_PERSIAN_CALENDAR = False

            loaded = EventLoaderCSV(FakeCF()).load()
            freqs = {ev.name: ev.frequency for ev in loaded.items}
            self.assertEqual(freqs["Weekly meeting"], Frequency.WEEKLY)
            self.assertEqual(freqs["Daily standup"], Frequency.DAILY)
            self.assertEqual(freqs["Monthly review"], Frequency.MONTHLY)
            self.assertEqual(freqs["Yearly review"], Frequency.YEARLY)
        finally:
            os.unlink(filepath)

    def test_event_status_loaded_from_csv_column(self):
        """
        Source: `status = Status[row[7].upper()]` reads 8th column.
        """
        from calcure.loaders import EventLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w",
                                         encoding="utf-8") as f:
            f.write('0,2024,5,10,"Important meeting",1,once,important\n')
            filepath = f.name

        try:
            class FakeCF:
                EVENTS_FILE = filepath
                USE_PERSIAN_CALENDAR = False

            loaded = EventLoaderCSV(FakeCF()).load()
            self.assertEqual(loaded.items[0].status, Status.IMPORTANT)
        finally:
            os.unlink(filepath)

    def test_event_old_format_without_repetition_defaults(self):
        """
        Source: `if len(row) > 5: ... else: repetition = '1'; frequency = Frequency.ONCE`.
        A row with only 5 columns (no repetition/frequency) defaults to repetition=1, ONCE.
        """
        from calcure.loaders import EventLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w",
                                         encoding="utf-8") as f:
            f.write('0,2024,6,15,"Old event"\n')
            filepath = f.name

        try:
            class FakeCF:
                EVENTS_FILE = filepath
                USE_PERSIAN_CALENDAR = False

            loaded = EventLoaderCSV(FakeCF()).load()
            ev = loaded.items[0]
            self.assertEqual(ev.repetition, '1')
            self.assertEqual(ev.frequency, Frequency.ONCE)
        finally:
            os.unlink(filepath)


class TestAuxiliaryLoaderInternals(unittest.TestCase):
    """Whitebox: BirthdayLoader early returns and file parsing branches."""

    def test_birthday_loader_disabled_returns_empty(self):
        """Source: if birthdays are disabled, load() returns immediately."""
        from calcure.loaders import BirthdayLoader

        class FakeCF:
            USE_PERSIAN_CALENDAR = False
            BIRTHDAYS_FROM_ABOOK = False

        loader = BirthdayLoader(FakeCF())
        self.assertEqual(len(loader.load().items), 0)

    def test_birthday_loader_missing_file_returns_empty(self):
        """Source: nonexistent abook path triggers the missing-file early return."""
        from calcure.loaders import BirthdayLoader
        from pathlib import Path

        class FakeCF:
            USE_PERSIAN_CALENDAR = False
            BIRTHDAYS_FROM_ABOOK = True

        loader = BirthdayLoader(FakeCF())
        loader.abook_file = Path(tempfile.gettempdir()) / "definitely_missing_abook"
        self.assertEqual(len(loader.load().items), 0)

    def test_birthday_loader_parses_birthday_and_anniversary_entries(self):
        """
        Source: BirthdayLoader iterates config sections and accepts both
        `birthday` and `anniversary` keys.
        """
        from calcure.loaders import BirthdayLoader
        from pathlib import Path

        class FakeCF:
            USE_PERSIAN_CALENDAR = False
            BIRTHDAYS_FROM_ABOOK = True

        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as f:
            f.write("[1]\nname = Alice\nbirthday = 1990-06-21\n")
            f.write("[2]\nname = Bob\nanniversary = 2010-12-05\n")
            filepath = f.name

        try:
            loader = BirthdayLoader(FakeCF())
            loader.abook_file = Path(filepath)
            loaded = loader.load()
            dates = {(ev.name, ev.month, ev.day) for ev in loaded.items}
            self.assertIn(("Alice", 6, 21), dates)
            self.assertIn(("Bob", 12, 5), dates)
        finally:
            os.unlink(filepath)


class TestICSLoaderInternals(unittest.TestCase):
    """Whitebox: directly exercise TaskLoaderICS and EventLoaderICS control flow."""

    def test_task_loader_returns_empty_when_no_ics_files_configured(self):
        """Source: `if self.ics_task_files is None: return self.user_ics_tasks`."""
        from calcure.loaders import TaskLoaderICS

        class FakeCF:
            ICS_TASK_FILES = None
            USE_PERSIAN_CALENDAR = False

        loaded = TaskLoaderICS(FakeCF()).load()
        self.assertEqual(len(loaded.items), 0)

    def test_parse_task_cancelled_item_is_skipped(self):
        """Source: status CANCELLED returns before any task is added."""
        from calcure.loaders import TaskLoaderICS

        class FakeCF:
            ICS_TASK_FILES = []
            USE_PERSIAN_CALENDAR = False

        loader = TaskLoaderICS(FakeCF())
        todo = icalendar.Todo()
        todo.add("summary", "Cancelled task")
        todo.add("status", "CANCELLED")

        loader.parse_task(todo, 0)
        self.assertEqual(len(loader.user_ics_tasks.items), 0)

    def test_parse_task_priority_maps_to_important_and_unimportant(self):
        """
        Source: priority < 5 -> IMPORTANT, priority > 5 -> UNIMPORTANT.
        This executes both nested priority branches.
        """
        from calcure.loaders import TaskLoaderICS

        class FakeCF:
            ICS_TASK_FILES = []
            USE_PERSIAN_CALENDAR = False

        loader = TaskLoaderICS(FakeCF())

        important = icalendar.Todo()
        important.add("summary", "High priority")
        important.add("priority", 1)

        unimportant = icalendar.Todo()
        unimportant.add("summary", "Low priority")
        unimportant.add("priority", 9)

        loader.parse_task(important, 0)
        loader.parse_task(unimportant, 0)

        statuses = {task.name: task.status for task in loader.user_ics_tasks.items}
        self.assertEqual(statuses["High priority"], Status.IMPORTANT)
        self.assertEqual(statuses["Low priority"], Status.UNIMPORTANT)

    def test_parse_task_completed_overrides_priority_and_preserves_due_date(self):
        """
        Source: COMPLETED status overrides any priority-derived status and
        the due-date branch reads `.dt`.
        """
        from calcure.loaders import TaskLoaderICS

        class FakeCF:
            ICS_TASK_FILES = []
            USE_PERSIAN_CALENDAR = False

        loader = TaskLoaderICS(FakeCF())
        todo = icalendar.Todo()
        todo.add("summary", "Completed task")
        todo.add("status", "COMPLETED")
        todo.add("priority", 1)
        todo.add("due", datetime.date(2024, 4, 15))

        loader.parse_task(todo, 7)
        task = loader.user_ics_tasks.items[0]
        self.assertEqual(task.status, Status.DONE)
        self.assertEqual((task.year, task.month, task.day), (2024, 4, 15))
        self.assertEqual(task.calendar_number, 7)

    def test_event_loader_returns_empty_when_no_ics_files_configured(self):
        """Source: `if self.ics_event_files is None: return self.user_ics_events`."""
        from calcure.loaders import EventLoaderICS

        class FakeCF:
            ICS_EVENT_FILES = None
            USE_PERSIAN_CALENDAR = False

        loaded = EventLoaderICS(FakeCF()).load()
        self.assertEqual(len(loaded.items), 0)

    def test_parse_event_all_day_multiday_sets_daily_repetition(self):
        """
        Source: the all-day branch uses `dt_end - dt` and sets DAILY frequency
        when the event spans multiple whole days.
        """
        from calcure.loaders import EventLoaderICS

        class FakeCF:
            ICS_EVENT_FILES = []
            USE_PERSIAN_CALENDAR = False

        loader = EventLoaderICS(FakeCF())
        event = icalendar.Event()
        event.add("summary", "Conference")
        event.add("dtstart", datetime.date(2024, 3, 1))
        event.add("dtend", datetime.date(2024, 3, 3))

        loader.parse_event(event, 1, 2)
        loaded = loader.user_ics_events.items[0]
        self.assertEqual(loaded.frequency, Frequency.DAILY)
        self.assertEqual(loaded.repetition, 2)
        self.assertIsNone(loaded.hour)
        self.assertIsNone(loaded.minute)

    def test_parse_event_missing_dtstart_defaults_zero_date_and_zero_time(self):
        """
        Source: missing dtstart falls into the AttributeError handler,
        producing year=0, month=1, day=1, then non-all-day branch sets 0:00.
        """
        from calcure.loaders import EventLoaderICS

        class FakeCF:
            ICS_EVENT_FILES = []
            USE_PERSIAN_CALENDAR = False

        loader = EventLoaderICS(FakeCF())
        event = icalendar.Event()
        event.add("summary", "Missing start")

        loader.parse_event(event, 1, 0)
        loaded = loader.user_ics_events.items[0]
        self.assertEqual((loaded.year, loaded.month, loaded.day), (0, 1, 1))
        self.assertEqual((loaded.hour, loaded.minute), (0, 0))

    def test_parse_event_rrule_sets_repetition_zero_and_keeps_metadata(self):
        """
        Source: when an RRULE is present, parse_event stores the RRULE string,
        EXDATE metadata, and forces repetition=0.
        """
        from calcure.loaders import EventLoaderICS

        class FakeCF:
            ICS_EVENT_FILES = []
            USE_PERSIAN_CALENDAR = False

        loader = EventLoaderICS(FakeCF())
        event = icalendar.Event()
        event.add("summary", "Recurring")
        event.add("dtstart", datetime.date(2024, 3, 1))
        event.add("dtend", datetime.date(2024, 3, 2))
        event.add("rrule", {"freq": ["weekly"], "count": [3]})
        event.add("exdate", datetime.date(2024, 3, 8))

        loader.parse_event(event, 1, 0)
        loaded = loader.user_ics_events.items[0]
        self.assertEqual(loaded.repetition, 0)
        self.assertIn("FREQ=WEEKLY", loaded.rrule)
        self.assertIn("COUNT=3", loaded.rrule)
        self.assertIsNotNone(loaded.exdate)


# ===========================================================================
# 8. FILTER INTERNALS
# ===========================================================================

class TestFilterInternals(unittest.TestCase):
    """
    Whitebox: filter_events_that_month sorts by day (implementation detail);
    Birthdays.filter_events_that_day omits year check entirely.
    """

    def test_filter_events_that_month_sort_is_stable_for_same_day(self):
        """
        Source: `sorted(..., key=lambda item: item.day)` is a stable sort.
        Two events on the same day keep insertion order relative to each other.
        """
        events = Events()
        events.add_item(make_event(item_id=0, year=2024, month=1, day=5, name="First"))
        events.add_item(make_event(item_id=1, year=2024, month=1, day=5, name="Second"))
        screen = MockScreen(2024, 1, 1)
        result = events.filter_events_that_month(screen)
        self.assertEqual(result.items[0].name, "First")
        self.assertEqual(result.items[1].name, "Second")

    def test_filter_events_that_day_requires_year_match(self):
        """
        Source: `event.year == screen.year` — Events collection checks year.
        The same month/day in a different year is excluded.
        """
        events = Events()
        events.add_item(make_event(item_id=0, year=2022, month=4, day=10, name="Old"))
        events.add_item(make_event(item_id=1, year=2024, month=4, day=10, name="New"))
        screen = MockScreen(2024, 4, 10)
        result = events.filter_events_that_day(screen)
        names = [e.name for e in result.items]
        self.assertIn("New", names)
        self.assertNotIn("Old", names)

    def test_birthdays_filter_does_not_check_year(self):
        """
        Source Birthdays.filter_events_that_day:
        `if event.month == screen.month and event.day == screen.day`
        No year comparison → any year birthday matches.
        """
        bdays = Birthdays()
        bdays.add_item(Event(1999, 12, 25, "Christmas birthday"))
        screen = MockScreen(2050, 12, 25)
        result = bdays.filter_events_that_day(screen)
        self.assertEqual(len(result.items), 1)

    def test_filter_events_that_month_excludes_other_years(self):
        """
        Source: `event.year == screen.year` check also applies in month filter.
        """
        events = Events()
        events.add_item(make_event(item_id=0, year=2023, month=3, day=15, name="Past"))
        events.add_item(make_event(item_id=1, year=2024, month=3, day=15, name="Current"))
        screen = MockScreen(2024, 3, 1)
        result = events.filter_events_that_month(screen)
        names = [e.name for e in result.items]
        self.assertNotIn("Past", names)
        self.assertIn("Current", names)


# ===========================================================================
# 9. MOVE TASK INTERNALS
# ===========================================================================

class TestMoveTaskInternals(unittest.TestCase):
    """
    Whitebox: move_task uses list.pop + list.insert which is O(n),
    and the destination index is applied AFTER the pop shifts indices.
    """

    def test_move_task_from_start_to_end(self):
        """
        Source: `self.items.insert(number_to, self.items.pop(number_from))`.
        Moving index 0 to index 2 on a 3-item list.
        After pop: ['B', 'C'], insert at 2 → ['B', 'C', 'A'].
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="A"))
        tasks.add_item(make_task(item_id=1, name="B"))
        tasks.add_item(make_task(item_id=2, name="C"))
        tasks.move_task(0, 2)
        names = [t.name for t in tasks.items]
        self.assertEqual(names, ["B", "C", "A"])

    def test_move_task_from_end_to_start(self):
        """
        After pop: ['A', 'B'], insert at 0 → ['C', 'A', 'B'].
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="A"))
        tasks.add_item(make_task(item_id=1, name="B"))
        tasks.add_item(make_task(item_id=2, name="C"))
        tasks.move_task(2, 0)
        names = [t.name for t in tasks.items]
        self.assertEqual(names, ["C", "A", "B"])

    def test_move_task_marks_changed(self):
        """move_task always marks the collection as changed."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="A"))
        tasks.add_item(make_task(item_id=1, name="B"))
        tasks.changed = False
        tasks.move_task(0, 1)
        self.assertTrue(tasks.changed)


# ===========================================================================
# 10. PAUSE ALL OTHER TIMERS INTERNALS
# ===========================================================================

class TestPauseAllOtherTimersInternals(unittest.TestCase):
    """
    Whitebox: pause_all_other_timers appends one timestamp to every timer
    that is currently counting (odd stamp count) EXCEPT the selected task.
    """

    def test_non_running_timer_not_affected(self):
        """
        Source: `if item.timer.is_counting and item.item_id != selected_task_id`.
        A non-running timer is untouched even if its ID is different.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))  # not counting
        tasks.add_item(make_task(item_id=1))  # not counting
        tasks.add_timestamp_for_task(1)        # start task 1
        stamps_before = len(tasks.items[0].timer.stamps)
        tasks.pause_all_other_timers(1)
        self.assertEqual(len(tasks.items[0].timer.stamps), stamps_before)

    def test_selected_timer_not_paused(self):
        """The timer belonging to selected_task_id is never touched."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.add_timestamp_for_task(0)
        stamps_before = len(tasks.items[0].timer.stamps)
        tasks.pause_all_other_timers(0)
        self.assertEqual(len(tasks.items[0].timer.stamps), stamps_before)

    def test_other_running_timers_get_one_extra_stamp(self):
        """Each other running timer receives exactly one additional stamp."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.add_item(make_task(item_id=1))
        tasks.add_item(make_task(item_id=2))
        tasks.add_timestamp_for_task(0)
        tasks.add_timestamp_for_task(1)
        tasks.add_timestamp_for_task(2)
        tasks.pause_all_other_timers(0)
        # Tasks 1 and 2 should each have 2 stamps (started + paused)
        self.assertEqual(len(tasks.items[1].timer.stamps), 2)
        self.assertEqual(len(tasks.items[2].timer.stamps), 2)
        # Task 0 still has 1 stamp (not paused)
        self.assertEqual(len(tasks.items[0].timer.stamps), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
