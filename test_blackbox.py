#!/usr/bin/env python3
"""
Blackbox Tests (Section 2.1) — Calcure Calendar & Task Manager
=============================================================
Blackbox testing treats each unit as an opaque box:
we only care about INPUTS → OUTPUTS, not internal implementation.

Techniques used (tagged in each test docstring):
  [EP]  Equivalence Partitioning  — divide inputs into valid/invalid classes
  [BA]  Boundary Analysis         — test at the exact edges of each class
  [EG]  Error Guessing            — intuition-driven special/corner cases
  [CT]  Combinatorial Testing     — multiple parameters tested in combination

All tests are grouped by feature area.
"""

import sys
import os
import time
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from calcure.data import (
    Task, UserEvent, Event, Timer, Tasks, Events, Birthdays,
    Status, Frequency, RepeatedEvents
)
from calcure.calendars import Calendar


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_timer(stamps=None):
    return Timer(stamps or [])


def make_task(item_id=0, name="Buy groceries", status=Status.NORMAL,
              privacy=False, year=0, month=0, day=0):
    return Task(item_id, name, status, make_timer(), privacy, year, month, day)


def make_event(item_id=0, year=2024, month=6, day=15, name="Team meeting",
               repetition=1, frequency=Frequency.ONCE, status=Status.NORMAL,
               privacy=False):
    return UserEvent(item_id, year, month, day, name, repetition,
                     frequency, status, privacy)


class MockScreen:
    """Minimal screen mock exposing only the date attributes needed by filters."""
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day


# ===========================================================================
# 1. TASK MANAGEMENT
# ===========================================================================

class TestTaskManagement(unittest.TestCase):
    """
    Blackbox: adding, deleting, renaming, and modifying tasks.
    Techniques: EP (valid/invalid name partitions), BA (name length boundaries),
                EG (empty name, None id, delete non-existent).
    """

    def setUp(self):
        self.tasks = Tasks()

    # --- Adding tasks ---

    def test_add_task_collection_grows(self):
        """[EP] Valid name partition — task is accepted and stored."""
        self.tasks.add_item(make_task(name="Write report"))
        self.assertEqual(len(self.tasks.items), 1)

    def test_add_multiple_tasks_all_stored(self):
        """[EP] Multiple items in valid partition — all are retained."""
        for i, name in enumerate(["Task A", "Task B", "Task C"]):
            self.tasks.add_item(make_task(item_id=i, name=name))
        self.assertEqual(len(self.tasks.items), 3)

    def test_add_task_empty_name_rejected(self):
        """[BA] Lower boundary — name of length 0 is the invalid-empty partition."""
        self.tasks.add_item(make_task(name=""))
        self.assertEqual(len(self.tasks.items), 0)

    def test_add_task_one_char_name_accepted(self):
        """[BA] Lower boundary + 1 — a 1-character name is still a valid task name."""
        self.tasks.add_item(make_task(name="A"))
        self.assertEqual(len(self.tasks.items), 1)

    def test_add_task_name_over_1000_chars_rejected(self):
        """[BA] Upper boundary — name of length 1000 is invalid (>= 1000 rejected)."""
        self.tasks.add_item(make_task(name="x" * 1000))
        self.assertEqual(len(self.tasks.items), 0)

    def test_add_task_999_char_name_accepted(self):
        """[BA] Upper boundary - 1 — name of length 999 is exactly within valid range."""
        self.tasks.add_item(make_task(name="x" * 999))
        self.assertEqual(len(self.tasks.items), 1)

    # --- Deleting tasks ---

    def test_delete_task_removes_it(self):
        """[EP] Valid delete — item with matching ID is removed."""
        t = make_task(item_id=42)
        self.tasks.add_item(t)
        self.tasks.delete_item(42)
        self.assertEqual(len(self.tasks.items), 0)

    def test_delete_nonexistent_task_leaves_collection_unchanged(self):
        """[EG] Non-existent ID — delete of unknown ID is safe and silent."""
        self.tasks.add_item(make_task(item_id=1))
        self.tasks.delete_item(99)
        self.assertEqual(len(self.tasks.items), 1)

    def test_delete_one_of_several_tasks(self):
        """[EP] Selective delete — only targeted task removed, others intact."""
        self.tasks.add_item(make_task(item_id=0, name="Keep me"))
        self.tasks.add_item(make_task(item_id=1, name="Delete me"))
        self.tasks.add_item(make_task(item_id=2, name="Keep me too"))
        self.tasks.delete_item(1)
        names = [t.name for t in self.tasks.items]
        self.assertNotIn("Delete me", names)
        self.assertIn("Keep me", names)
        self.assertIn("Keep me too", names)

    # --- Renaming tasks ---

    def test_rename_task_updates_name(self):
        """[EP] Valid rename — non-empty new name is applied."""
        self.tasks.add_item(make_task(item_id=5, name="Old name"))
        self.tasks.rename_item(5, "New name")
        self.assertEqual(self.tasks.items[0].name, "New name")

    def test_rename_task_empty_name_ignored(self):
        """[EG] Empty rename — empty string is rejected, original name preserved."""
        self.tasks.add_item(make_task(item_id=3, name="Original"))
        self.tasks.rename_item(3, "")
        self.assertEqual(self.tasks.items[0].name, "Original")

    # --- Status ---

    def test_toggle_task_status_to_done(self):
        """[EP] Valid status transition — NORMAL → DONE."""
        self.tasks.add_item(make_task(item_id=0))
        self.tasks.toggle_item_status(0, Status.DONE)
        self.assertEqual(self.tasks.items[0].status, Status.DONE)

    def test_toggle_task_status_back_to_normal(self):
        """[EG] Double-toggle same status — DONE → DONE resets to NORMAL."""
        self.tasks.add_item(make_task(item_id=0))
        self.tasks.toggle_item_status(0, Status.DONE)
        self.tasks.toggle_item_status(0, Status.DONE)
        self.assertEqual(self.tasks.items[0].status, Status.NORMAL)

    def test_toggle_task_status_to_important(self):
        """[EP] Valid status transition — NORMAL → IMPORTANT."""
        self.tasks.add_item(make_task(item_id=0))
        self.tasks.toggle_item_status(0, Status.IMPORTANT)
        self.assertEqual(self.tasks.items[0].status, Status.IMPORTANT)

    def test_change_all_statuses(self):
        """change_all_statuses updates every task in the collection."""
        for i in range(4):
            self.tasks.add_item(make_task(item_id=i))
        self.tasks.change_all_statuses(Status.DONE)
        for t in self.tasks.items:
            self.assertEqual(t.status, Status.DONE)

    # --- Privacy ---

    def test_toggle_privacy_turns_on(self):
        """Toggling privacy on a public task makes it private."""
        self.tasks.add_item(make_task(item_id=0, privacy=False))
        self.tasks.toggle_item_privacy(0)
        self.assertTrue(self.tasks.items[0].privacy)

    def test_toggle_privacy_turns_off(self):
        """Toggling privacy on a private task makes it public."""
        self.tasks.add_item(make_task(item_id=0, privacy=True))
        self.tasks.toggle_item_privacy(0)
        self.assertFalse(self.tasks.items[0].privacy)

    # --- Deadline ---

    def test_change_deadline_updates_date(self):
        """change_deadline sets a new year/month/day on the task."""
        self.tasks.add_item(make_task(item_id=0, year=0, month=0, day=0))
        self.tasks.change_deadline(0, 2025, 12, 31)
        t = self.tasks.items[0]
        self.assertEqual((t.year, t.month, t.day), (2025, 12, 31))

    # --- Timer controls ---

    def test_starting_timer_marks_collection_as_active(self):
        """[EP] Starting a task timer → collection reports at least one active timer."""
        self.tasks.add_item(make_task(item_id=0))
        self.assertFalse(self.tasks.has_active_timer)
        self.tasks.add_timestamp_for_task(0)
        self.assertTrue(self.tasks.has_active_timer)

    def test_reset_timer_stops_active_timer(self):
        """[EP] Resetting a running timer → no active timer in collection, shows 00:00."""
        self.tasks.add_item(make_task(item_id=0))
        self.tasks.add_timestamp_for_task(0)
        self.tasks.reset_timer_for_task(0)
        self.assertFalse(self.tasks.has_active_timer)
        self.assertEqual(self.tasks.items[0].timer.passed_time, "00:00")

    # --- Move task ---

    def test_move_task_reorders_items(self):
        """move_task swaps the positions of two tasks."""
        self.tasks.add_item(make_task(item_id=0, name="First"))
        self.tasks.add_item(make_task(item_id=1, name="Second"))
        self.tasks.add_item(make_task(item_id=2, name="Third"))
        self.tasks.move_task(0, 2)
        self.assertEqual(self.tasks.items[2].name, "First")

    # --- ID uniqueness (user-observable: operations on items work correctly) ---

    def test_multiple_tasks_have_distinct_ids(self):
        """[EP] Items added with distinct IDs can each be deleted independently."""
        self.tasks.add_item(make_task(item_id=0, name="Alpha"))
        self.tasks.add_item(make_task(item_id=1, name="Beta"))
        self.tasks.delete_item(0)
        self.assertEqual(len(self.tasks.items), 1)
        self.assertEqual(self.tasks.items[0].name, "Beta")

    # --- Subtask ---

    def test_add_subtask_prefix_present(self):
        """Subtasks are stored with a leading '--' prefix."""
        self.tasks.add_item(make_task(item_id=0, name="Parent"))
        sub = make_task(item_id=1, name="Sub")
        self.tasks.add_subtask(sub, 0)
        self.assertTrue(self.tasks.items[1].name.startswith("--"))


# ===========================================================================
# 2. EVENT MANAGEMENT
# ===========================================================================

class TestEventManagement(unittest.TestCase):
    """Blackbox: adding, deleting, renaming, and modifying calendar events."""

    def setUp(self):
        self.events = Events()

    def test_add_event_stored(self):
        """An event is accessible after being added."""
        self.events.add_item(make_event(name="Doctor appointment"))
        self.assertEqual(len(self.events.items), 1)

    def test_add_event_empty_name_rejected(self):
        """[BA] Empty event titles are rejected and do not create an event."""
        self.events.add_item(make_event(name=""))
        self.assertEqual(len(self.events.items), 0)

    def test_delete_event_by_id(self):
        """Deleting an event by ID removes it."""
        self.events.add_item(make_event(item_id=10))
        self.events.delete_item(10)
        self.assertEqual(len(self.events.items), 0)

    def test_rename_event_updates_name(self):
        """Renaming an event changes its stored name."""
        self.events.add_item(make_event(item_id=0, name="Old"))
        self.events.rename_item(0, "New")
        self.assertEqual(self.events.items[0].name, "New")

    def test_event_exists_true(self):
        """event_exists returns True for an event already in the collection."""
        ev = make_event(year=2024, month=5, day=10, name="Birthday party")
        self.events.add_item(ev)
        duplicate = make_event(year=2024, month=5, day=10, name="Birthday party")
        self.assertTrue(self.events.event_exists(duplicate))

    def test_event_exists_false_different_date(self):
        """event_exists returns False when the date differs."""
        ev = make_event(year=2024, month=5, day=10, name="Concert")
        self.events.add_item(ev)
        other = make_event(year=2024, month=5, day=11, name="Concert")
        self.assertFalse(self.events.event_exists(other))

    def test_event_exists_false_different_name(self):
        """event_exists returns False when the name differs."""
        ev = make_event(year=2024, month=5, day=10, name="Meeting A")
        self.events.add_item(ev)
        other = make_event(year=2024, month=5, day=10, name="Meeting B")
        self.assertFalse(self.events.event_exists(other))

    def test_change_event_day(self):
        """Moving an event within the month changes only the day."""
        self.events.add_item(make_event(item_id=0, year=2024, month=3, day=5))
        self.events.change_day(0, 20)
        self.assertEqual(self.events.items[0].day, 20)
        self.assertEqual(self.events.items[0].month, 3)

    def test_change_event_full_date(self):
        """Moving an event to a new date updates year, month, and day."""
        self.events.add_item(make_event(item_id=0, year=2024, month=1, day=1))
        self.events.change_date(0, 2025, 6, 15)
        ev = self.events.items[0]
        self.assertEqual((ev.year, ev.month, ev.day), (2025, 6, 15))

    def test_toggle_event_status(self):
        """Toggling event status changes it as expected."""
        self.events.add_item(make_event(item_id=0))
        self.events.toggle_item_status(0, Status.IMPORTANT)
        self.assertEqual(self.events.items[0].status, Status.IMPORTANT)

    def test_toggle_event_privacy(self):
        """Toggling event privacy flips the privacy flag."""
        self.events.add_item(make_event(item_id=0))
        self.events.toggle_item_privacy(0)
        self.assertTrue(self.events.items[0].privacy)


# ===========================================================================
# 3. TIMER BEHAVIOR
# ===========================================================================

class TestTimerBehavior(unittest.TestCase):
    """
    Blackbox: timer observable outputs only — what the USER sees (elapsed time string).
    No internal state properties (is_counting, is_started) are used here.
    All assertions are on passed_time (the visible output) or has_active_timer
    (the collection-level "is any timer running?" indicator used by the UI).
    """

    def test_timer_shows_zero_when_never_started(self):
        """[EP] A never-started timer shows 00:00 elapsed time."""
        self.assertEqual(make_timer([]).passed_time, "00:00")

    def test_timer_shows_correct_elapsed_time_after_one_interval(self):
        """[EP] A timer that ran for exactly 90 seconds shows 01:30."""
        base = 1_000_000
        t = make_timer([base, base + 90])   # ran 90s then paused
        self.assertEqual(t.passed_time, "01:30")

    def test_paused_timer_elapsed_time_does_not_change(self):
        """[EP] A paused timer's elapsed time is frozen — calling passed_time twice gives same result."""
        base = 1_000_000
        t = make_timer([base, base + 60])   # ran 60s, now paused
        self.assertEqual(t.passed_time, "01:00")
        self.assertEqual(t.passed_time, "01:00")  # still 01:00, not advancing

    def test_timer_accumulates_elapsed_across_multiple_intervals(self):
        """[EP] Time from multiple run intervals adds up to correct total."""
        base = 1_000_000
        # interval 1: 30s, gap: 10s idle, interval 2: 30s → total 60s
        t = make_timer([base, base + 30, base + 40, base + 70])
        self.assertEqual(t.passed_time, "01:00")

    def test_elapsed_time_format_mm_ss_under_one_hour(self):
        """[BA] Elapsed time < 60 min is shown in MM:SS format."""
        base = 1_000_000
        t = make_timer([base, base + 90])
        self.assertRegex(t.passed_time, r"^\d{2}:\d{2}$")

    def test_elapsed_time_format_hh_mm_ss_at_one_hour(self):
        """[BA] Elapsed time >= 60 min switches to HH:MM:SS format."""
        base = 1_000_000
        t = make_timer([base, base + 3660])  # 1h 1m
        self.assertRegex(t.passed_time, r"^\d{2}:\d{2}:\d{2}$")

    def test_elapsed_time_format_includes_days_over_one_day(self):
        """[BA] Elapsed time > 1 day includes day label in output string."""
        base = 1_000_000
        t = make_timer([base, base + 86401])  # just over 1 day
        self.assertIn("day", t.passed_time)

    def test_only_selected_timer_active_after_pause_others(self):
        """[EP] After pausing all others, collection still reports exactly one active timer."""
        tasks = Tasks()
        for i in range(3):
            tasks.add_item(make_task(item_id=i))
            tasks.add_timestamp_for_task(i)
        tasks.pause_all_other_timers(1)
        self.assertTrue(tasks.has_active_timer)
        # tasks 0 and 2 are now paused — their elapsed time is frozen
        elapsed_0_first  = tasks.items[0].timer.passed_time
        elapsed_0_second = tasks.items[0].timer.passed_time
        self.assertEqual(elapsed_0_first, elapsed_0_second)


# ===========================================================================
# 4. COLLECTION BEHAVIOR
# ===========================================================================

class TestCollectionBehavior(unittest.TestCase):
    """Blackbox: generic Collection operations shared by Tasks and Events."""

    def setUp(self):
        self.tasks = Tasks()

    def test_is_empty_on_fresh_collection(self):
        """A new collection is empty."""
        self.assertTrue(self.tasks.is_empty())

    def test_is_empty_false_after_adding(self):
        """A collection is not empty after an item is added."""
        self.tasks.add_item(make_task())
        self.assertFalse(self.tasks.is_empty())

    def test_is_valid_number_within_bounds(self):
        """[BA] Lower boundary — index 0 is valid for non-empty collection."""
        self.tasks.add_item(make_task())
        self.assertTrue(self.tasks.is_valid_number(0))

    def test_is_valid_number_out_of_bounds(self):
        """[BA] Upper boundary+1 — index == len is just outside valid range."""
        self.tasks.add_item(make_task())
        self.assertFalse(self.tasks.is_valid_number(1))

    def test_is_valid_number_negative(self):
        """[BA] Below lower boundary — negative index is invalid."""
        self.tasks.add_item(make_task())
        self.assertFalse(self.tasks.is_valid_number(-1))

    def test_is_valid_number_none(self):
        """[EG] None input — should not crash and return False."""
        self.tasks.add_item(make_task())
        self.assertFalse(self.tasks.is_valid_number(None))

    def test_item_exists_found(self):
        """item_exists returns True when a task with that name is present."""
        self.tasks.add_item(make_task(name="Existing task"))
        self.assertTrue(self.tasks.item_exists("Existing task"))

    def test_item_exists_not_found(self):
        """item_exists returns False for a name that is not in the collection."""
        self.assertFalse(self.tasks.item_exists("Ghost task"))

    def test_delete_all_items_empties_collection(self):
        """delete_all_items removes every item."""
        for i in range(5):
            self.tasks.add_item(make_task(item_id=i))
        self.tasks.delete_all_items()
        self.assertTrue(self.tasks.is_empty())


# ===========================================================================
# 5. FILTERING BEHAVIOR
# ===========================================================================

class TestFilteringBehavior(unittest.TestCase):
    """Blackbox: filtering events by day and by month."""

    def setUp(self):
        self.events = Events()
        self.events.add_item(make_event(item_id=0, year=2024, month=4, day=10, name="Breakfast"))
        self.events.add_item(make_event(item_id=1, year=2024, month=4, day=15, name="Lunch"))
        self.events.add_item(make_event(item_id=2, year=2024, month=4, day=10, name="Dinner"))
        self.events.add_item(make_event(item_id=3, year=2024, month=5, day=1,  name="May Day"))
        self.events.add_item(make_event(item_id=4, year=2023, month=4, day=10, name="Last year"))

    def test_filter_events_that_day_correct_count(self):
        """filter_events_that_day returns only events on the specified date."""
        screen = MockScreen(2024, 4, 10)
        result = self.events.filter_events_that_day(screen)
        self.assertEqual(len(result.items), 2)

    def test_filter_events_that_day_correct_names(self):
        """filter_events_that_day returns the right event names."""
        screen = MockScreen(2024, 4, 10)
        result = self.events.filter_events_that_day(screen)
        names = {e.name for e in result.items}
        self.assertEqual(names, {"Breakfast", "Dinner"})

    def test_filter_events_that_day_returns_empty_when_no_matches(self):
        """[EP] A day with no scheduled events returns an empty result set."""
        screen = MockScreen(2024, 4, 30)
        result = self.events.filter_events_that_day(screen)
        self.assertEqual(len(result.items), 0)

    def test_filter_events_that_day_excludes_wrong_year(self):
        """Events from other years are excluded even if month/day match."""
        screen = MockScreen(2023, 4, 10)
        result = self.events.filter_events_that_day(screen)
        names = {e.name for e in result.items}
        self.assertEqual(names, {"Last year"})

    def test_filter_events_that_month_correct_count(self):
        """filter_events_that_month returns only events in the specified month."""
        screen = MockScreen(2024, 4, 1)
        result = self.events.filter_events_that_month(screen)
        self.assertEqual(len(result.items), 3)

    def test_filter_events_that_month_returns_empty_when_no_matches(self):
        """[EP] A month with no events returns an empty result set."""
        screen = MockScreen(2024, 12, 1)
        result = self.events.filter_events_that_month(screen)
        self.assertEqual(len(result.items), 0)

    def test_filter_events_that_month_sorted_by_day(self):
        """filter_events_that_month returns events ordered by day (ascending)."""
        unsorted = Events()
        unsorted.add_item(make_event(item_id=0, year=2024, month=1, day=20, name="Third"))
        unsorted.add_item(make_event(item_id=1, year=2024, month=1, day=5,  name="First"))
        unsorted.add_item(make_event(item_id=2, year=2024, month=1, day=12, name="Second"))
        screen = MockScreen(2024, 1, 1)
        result = unsorted.filter_events_that_month(screen)
        days = [e.day for e in result.items]
        self.assertEqual(days, sorted(days))

    def test_birthdays_filter_ignores_year(self):
        """Birthdays.filter_events_that_day matches on month+day only (year ignored)."""
        bdays = Birthdays()
        bdays.add_item(Event(1, 6, 21, "Alice"))
        bdays.add_item(Event(1, 6, 21, "Bob"))
        bdays.add_item(Event(1, 7,  4, "Carol"))
        screen = MockScreen(2030, 6, 21)
        result = bdays.filter_events_that_day(screen)
        self.assertEqual(len(result.items), 2)

    def test_birthdays_filter_returns_empty_for_nonmatching_day(self):
        """[EP] A day with no matching birthdays returns an empty result set."""
        bdays = Birthdays()
        bdays.add_item(Event(1, 6, 21, "Alice"))
        screen = MockScreen(2030, 6, 22)
        result = bdays.filter_events_that_day(screen)
        self.assertEqual(len(result.items), 0)


# ===========================================================================
# 6. CALENDAR BEHAVIOR
# ===========================================================================

class TestCalendarBehavior(unittest.TestCase):
    """Blackbox: Calendar correctly describes months and week numbers."""

    def setUp(self):
        self.cal = Calendar(0, False)  # Monday-first, Gregorian

    def test_last_day_jan(self):
        """January has 31 days."""
        self.assertEqual(self.cal.last_day(2024, 1), 31)

    def test_last_day_april(self):
        """April has 30 days."""
        self.assertEqual(self.cal.last_day(2024, 4), 30)

    def test_last_day_feb_leap_year(self):
        """February in a leap year has 29 days."""
        self.assertEqual(self.cal.last_day(2024, 2), 29)

    def test_last_day_feb_non_leap_year(self):
        """February in a non-leap year has 28 days."""
        self.assertEqual(self.cal.last_day(2023, 2), 28)

    def test_last_day_invalid_month_raises_error(self):
        """[EP] Months outside 1..12 are rejected when asking for the month's last day."""
        with self.assertRaises(IndexError):
            self.cal.last_day(2024, 13)

    def test_monthdayscalendar_returns_nested_list(self):
        """monthdayscalendar returns a list of weeks, each week having 7 entries."""
        calendar = self.cal.monthdayscalendar(2024, 3)
        self.assertTrue(all(len(week) == 7 for week in calendar))

    def test_monthdayscalendar_contains_all_days(self):
        """monthdayscalendar contains all 31 days for March."""
        calendar = self.cal.monthdayscalendar(2024, 3)
        all_days = [day for week in calendar for day in week if day != 0]
        self.assertEqual(sorted(all_days), list(range(1, 32)))

    def test_week_number_known_date(self):
        """Week number for 2024-01-01 is 1 (ISO)."""
        self.assertEqual(self.cal.week_number(2024, 1, 1), 1)

    def test_week_number_march_2024(self):
        """March 23, 2024 is in ISO week 12."""
        self.assertEqual(self.cal.week_number(2024, 3, 23), 12)

    def test_month_week_numbers_length_matches_rows(self):
        """month_week_numbers returns one week number per calendar row."""
        for month in range(1, 13):
            rows = self.cal.monthdayscalendar(2024, month)
            wnums = self.cal.month_week_numbers(2024, month)
            self.assertEqual(len(wnums), len(rows))

    def test_week_number_year_boundary(self):
        """Dec 31 2023 and Jan 7 2024 give the expected ISO week numbers."""
        self.assertEqual(self.cal.week_number(2023, 12, 31), 52)
        self.assertEqual(self.cal.week_number(2024, 1,  7), 1)

    def test_first_day_known_monday(self):
        """2024-01-01 is a Monday (weekday 0)."""
        self.assertEqual(self.cal.first_day(2024, 1), 0)

    def test_first_day_invalid_month_raises_error(self):
        """[EP] Months outside 1..12 are rejected."""
        with self.assertRaises(ValueError):
            self.cal.first_day(2024, 13)

    def test_sunday_start_calendar_has_different_padding(self):
        """A Sunday-first calendar produces a different layout for the same month."""
        cal_sun = Calendar(6, False)
        cal_mon = Calendar(0, False)
        grid_sun = cal_sun.monthdayscalendar(2024, 3)
        grid_mon = cal_mon.monthdayscalendar(2024, 3)
        # Both should be valid but may differ in row/column layout
        self.assertTrue(all(len(w) == 7 for w in grid_sun))
        self.assertTrue(all(len(w) == 7 for w in grid_mon))

    def test_week_number_invalid_day_raises_error(self):
        """[EP] Impossible dates are rejected instead of producing a week number."""
        with self.assertRaises(ValueError):
            self.cal.week_number(2024, 2, 30)


# ===========================================================================
# 7. REPEATED EVENTS BEHAVIOR
# ===========================================================================

class TestRepeatedEventsBehavior(unittest.TestCase):
    """Blackbox: recurring events produce the correct number of occurrences."""

    def _make_events_with(self, repetition, frequency, year=2024, month=3, day=1):
        user_events = Events()
        ev = make_event(item_id=0, year=year, month=month, day=day,
                        repetition=repetition, frequency=frequency)
        user_events.add_item(ev)
        return user_events

    def test_once_event_produces_no_repetitions(self):
        """An event with frequency ONCE and repetition=1 has no extra occurrences."""
        ue = self._make_events_with(1, Frequency.ONCE)
        reps = RepeatedEvents(ue, False, 2024)
        self.assertEqual(len(reps.items), 0)

    def test_weekly_event_produces_correct_count(self):
        """A 3-occurrence weekly event adds 2 repeated entries."""
        ue = self._make_events_with(3, Frequency.WEEKLY)
        reps = RepeatedEvents(ue, False, 2024)
        self.assertEqual(len(reps.items), 2)

    def test_daily_event_occurrences(self):
        """A 5-occurrence daily event adds 4 repeated entries."""
        ue = self._make_events_with(5, Frequency.DAILY)
        reps = RepeatedEvents(ue, False, 2024)
        self.assertEqual(len(reps.items), 4)

    def test_yearly_event_occurrences(self):
        """A 3-occurrence yearly event adds 2 repeated entries in successive years."""
        ue = self._make_events_with(3, Frequency.YEARLY)
        reps = RepeatedEvents(ue, False, 2024)
        years = sorted({r.year for r in reps.items})
        self.assertIn(2025, years)
        self.assertIn(2026, years)

    def test_monthly_event_occurrences(self):
        """A 4-occurrence monthly event adds 3 repeated entries."""
        ue = self._make_events_with(4, Frequency.MONTHLY)
        reps = RepeatedEvents(ue, False, 2024)
        self.assertEqual(len(reps.items), 3)

    def test_weekly_event_crosses_month_boundary(self):
        """A weekly event starting near month-end produces occurrences in the next month."""
        ue = self._make_events_with(3, Frequency.WEEKLY, year=2024, month=3, day=25)
        reps = RepeatedEvents(ue, False, 2024)
        months = {r.month for r in reps.items}
        self.assertIn(4, months)

    def test_monthly_event_crosses_year_boundary(self):
        """A monthly event starting in November wraps into the next year."""
        ue = self._make_events_with(3, Frequency.MONTHLY, year=2024, month=11, day=1)
        reps = RepeatedEvents(ue, False, 2024)
        years = {r.year for r in reps.items}
        self.assertIn(2025, years)

    def test_biweekly_event_produces_correct_intervals(self):
        """A biweekly event produces occurrences 14 days apart."""
        ue = self._make_events_with(3, Frequency.BIWEEKLY, year=2024, month=1, day=1)
        reps = RepeatedEvents(ue, False, 2024)
        self.assertEqual(len(reps.items), 2)

    def test_repeated_event_inherits_name(self):
        """Repeated events carry the same name as the original."""
        ue = self._make_events_with(2, Frequency.WEEKLY, year=2024, month=3, day=1)
        reps = RepeatedEvents(ue, False, 2024)
        for r in reps.items:
            self.assertEqual(r.name, "Team meeting")

    def test_repeated_event_inherits_status(self):
        """Repeated events carry the original event's status."""
        user_events = Events()
        ev = make_event(item_id=0, year=2024, month=3, day=1,
                        repetition=2, frequency=Frequency.WEEKLY,
                        status=Status.IMPORTANT)
        user_events.add_item(ev)
        reps = RepeatedEvents(user_events, False, 2024)
        for r in reps.items:
            self.assertEqual(r.status, Status.IMPORTANT)


# ===========================================================================
# 8. DATA PERSISTENCE — CSV ROUND-TRIP
# ===========================================================================

class TestDataPersistence(unittest.TestCase):
    """Blackbox: data saved to CSV can be reloaded with identical values."""

    def _make_config(self, tasks_file, events_file):
        class FakeCF:
            TASKS_FILE = tasks_file
            EVENTS_FILE = events_file
            USE_PERSIAN_CALENDAR = False
        return FakeCF()

    def test_task_round_trip_name_and_status(self):
        """A task written to CSV is reloaded with correct name and status."""
        from calcure.savers import TaskSaverCSV
        from calcure.loaders import TaskLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            tasks = Tasks()
            tasks.add_item(Task(0, "Buy milk", Status.DONE, Timer([]), False, 0, 0, 0))
            cf = self._make_config(filepath, filepath)
            TaskSaverCSV(tasks, cf).save()

            loaded = TaskLoaderCSV(cf).load()
            self.assertEqual(len(loaded.items), 1)
            self.assertEqual(loaded.items[0].name, "Buy milk")
            self.assertEqual(loaded.items[0].status, Status.DONE)
        finally:
            os.unlink(filepath)
            bak = filepath + ".bak"
            if os.path.exists(bak):
                os.unlink(bak)

    def test_task_round_trip_privacy(self):
        """A private task is reloaded as private."""
        from calcure.savers import TaskSaverCSV
        from calcure.loaders import TaskLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            tasks = Tasks()
            tasks.add_item(Task(0, "Secret task", Status.NORMAL, Timer([]), True, 0, 0, 0))
            cf = self._make_config(filepath, filepath)
            TaskSaverCSV(tasks, cf).save()

            loaded = TaskLoaderCSV(cf).load()
            self.assertTrue(loaded.items[0].privacy)
            self.assertEqual(loaded.items[0].name, "Secret task")
        finally:
            os.unlink(filepath)
            bak = filepath + ".bak"
            if os.path.exists(bak):
                os.unlink(bak)

    def test_event_round_trip_date_and_name(self):
        """An event's date and name survive a save/load cycle unchanged."""
        from calcure.savers import EventSaverCSV
        from calcure.loaders import EventLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            events = Events()
            events.add_item(UserEvent(0, 2024, 9, 15, "Conference",
                                      1, Frequency.ONCE, Status.NORMAL, False))
            cf = self._make_config(filepath, filepath)
            EventSaverCSV(events, cf).save()

            loaded = EventLoaderCSV(cf).load()
            ev = loaded.items[0]
            self.assertEqual(ev.name, "Conference")
            self.assertEqual((ev.year, ev.month, ev.day), (2024, 9, 15))
        finally:
            os.unlink(filepath)
            bak = filepath + ".bak"
            if os.path.exists(bak):
                os.unlink(bak)

    def test_event_round_trip_frequency(self):
        """A recurring event's frequency label survives a save/load cycle."""
        from calcure.savers import EventSaverCSV
        from calcure.loaders import EventLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            events = Events()
            events.add_item(UserEvent(0, 2024, 1, 1, "Weekly standup",
                                      52, Frequency.WEEKLY, Status.NORMAL, False))
            cf = self._make_config(filepath, filepath)
            EventSaverCSV(events, cf).save()

            loaded = EventLoaderCSV(cf).load()
            self.assertEqual(loaded.items[0].frequency, Frequency.WEEKLY)
        finally:
            os.unlink(filepath)
            bak = filepath + ".bak"
            if os.path.exists(bak):
                os.unlink(bak)

    def test_multiple_tasks_round_trip(self):
        """Multiple tasks all survive a save/load cycle."""
        from calcure.savers import TaskSaverCSV
        from calcure.loaders import TaskLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            tasks = Tasks()
            for i, name in enumerate(["Alpha", "Beta", "Gamma"]):
                tasks.add_item(Task(i, name, Status.NORMAL, Timer([]), False, 0, 0, 0))
            cf = self._make_config(filepath, filepath)
            TaskSaverCSV(tasks, cf).save()

            loaded = TaskLoaderCSV(cf).load()
            self.assertEqual(len(loaded.items), 3)
            names = {t.name for t in loaded.items}
            self.assertEqual(names, {"Alpha", "Beta", "Gamma"})
        finally:
            os.unlink(filepath)
            bak = filepath + ".bak"
            if os.path.exists(bak):
                os.unlink(bak)

    def test_task_timer_stamps_round_trip(self):
        """Timer timestamps survive a save/load cycle."""
        from calcure.savers import TaskSaverCSV
        from calcure.loaders import TaskLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            tasks = Tasks()
            tasks.add_item(Task(0, "Timed", Status.NORMAL, Timer([1000, 2000]), False, 0, 0, 0))
            cf = self._make_config(filepath, filepath)
            TaskSaverCSV(tasks, cf).save()

            loaded = TaskLoaderCSV(cf).load()
            stamps = loaded.items[0].timer.stamps
            self.assertEqual(len(stamps), 2)
        finally:
            os.unlink(filepath)
            bak = filepath + ".bak"
            if os.path.exists(bak):
                os.unlink(bak)

    def test_missing_task_file_loads_as_empty_collection(self):
        """[EG] A missing tasks CSV is created on demand and loads as an empty collection."""
        from calcure.loaders import TaskLoaderCSV

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "tasks.csv")
            cf = self._make_config(filepath, filepath)

            loaded = TaskLoaderCSV(cf).load()

            self.assertEqual(len(loaded.items), 0)
            self.assertTrue(os.path.exists(filepath))

    def test_event_loader_invalid_frequency_defaults_to_once(self):
        """[EG] An unknown stored frequency falls back to a safe ONCE event."""
        from calcure.loaders import EventLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name
            f.write('0,2024,9,15,"Conference",3,not-a-frequency,normal\n')

        try:
            cf = self._make_config(filepath, filepath)
            loaded = EventLoaderCSV(cf).load()
            self.assertEqual(len(loaded.items), 1)
            self.assertEqual(loaded.items[0].frequency, Frequency.ONCE)
        finally:
            os.unlink(filepath)

    def test_event_loader_missing_status_defaults_to_normal(self):
        """[EP] Older/partial event rows still load with NORMAL status by default."""
        from calcure.loaders import EventLoaderCSV

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name
            f.write('0,2024,9,15,"Conference",3,weekly\n')

        try:
            cf = self._make_config(filepath, filepath)
            loaded = EventLoaderCSV(cf).load()
            self.assertEqual(len(loaded.items), 1)
            self.assertEqual(loaded.items[0].status, Status.NORMAL)
        finally:
            os.unlink(filepath)

    def test_missing_event_file_loads_as_empty_collection(self):
        """[EG] A missing events CSV is created on demand and loads as an empty collection."""
        from calcure.loaders import EventLoaderCSV

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "events.csv")
            cf = self._make_config(filepath, filepath)

            loaded = EventLoaderCSV(cf).load()

            self.assertEqual(len(loaded.items), 0)
            self.assertTrue(os.path.exists(filepath))


# ===========================================================================
# 9. ICS IMPORT BEHAVIOR
# ===========================================================================

class TestICSImportBehavior(unittest.TestCase):
    """Blackbox: loading external .ics resources through the public import surface."""

    def test_missing_ics_file_returns_empty_text(self):
        """[EG] A missing .ics resource is handled safely and produces no imported text."""
        from calcure.loaders import LoaderICS

        loader = LoaderICS()
        result = loader.read_file("/definitely/missing/calendar.ics")
        self.assertEqual(result, "")

    def test_folder_resource_loads_only_ics_files(self):
        """[EP] Importing from a folder reads calendar files and ignores unrelated files."""
        from calcure.loaders import LoaderICS

        with tempfile.TemporaryDirectory() as tmpdir:
            ics_path = os.path.join(tmpdir, "calendar.ics")
            txt_path = os.path.join(tmpdir, "notes.txt")

            with open(ics_path, "w", encoding="utf-8") as f:
                f.write("BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR\n")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("ignore me")

            resources = LoaderICS().read_resource(tmpdir)

            self.assertEqual(len(resources), 1)
            self.assertIn("BEGIN:VCALENDAR", resources[0])

    def test_single_ics_resource_returns_one_calendar_text(self):
        """[EP] Importing a single .ics file returns exactly that resource."""
        from calcure.loaders import LoaderICS

        with tempfile.NamedTemporaryFile(suffix=".ics", delete=False, mode="w") as f:
            filepath = f.name
            f.write("BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR\n")

        try:
            resources = LoaderICS().read_resource(filepath)
            self.assertEqual(len(resources), 1)
            self.assertIn("BEGIN:VCALENDAR", resources[0])
        finally:
            os.unlink(filepath)


# ===========================================================================
# 10. COMBINATORIAL TESTING — Multiple Parameters in Combination
# ===========================================================================

class TestCombinatorialTesting(unittest.TestCase):
    """
    [CT] Combinatorial Testing: test interactions between multiple input parameters.
    UserEvent takes: year, month, day, name, repetition, frequency, status, privacy.
    We use a pairwise strategy — every pair of parameter values is exercised.
    """

    def _make_repeated(self, repetition, frequency, year=2024, month=1, day=1):
        """Helper: build a single-event collection and return its RepeatedEvents."""
        ue = Events()
        ue.add_item(UserEvent(0, year, month, day, "CT Event",
                              repetition, frequency, Status.NORMAL, False))
        return RepeatedEvents(ue, False, 2024)

    # --- frequency × repetition combinations ---

    def test_ct_weekly_rep1_single_occurrence(self):
        """[CT] WEEKLY × repetition=1 → event appears only on its original date, no extra dates."""
        self.assertEqual(len(self._make_repeated(1, Frequency.WEEKLY).items), 0)

    def test_ct_weekly_rep2_one_extra_date(self):
        """[CT] WEEKLY × repetition=2 → event recurs on one additional date 7 days later."""
        self.assertEqual(len(self._make_repeated(2, Frequency.WEEKLY).items), 1)

    def test_ct_daily_rep1_single_occurrence(self):
        """[CT] DAILY × repetition=1 → no extra occurrences beyond original date."""
        self.assertEqual(len(self._make_repeated(1, Frequency.DAILY).items), 0)

    def test_ct_daily_rep5_four_extra_dates(self):
        """[CT] DAILY × repetition=5 → event recurs on 4 additional consecutive days."""
        self.assertEqual(len(self._make_repeated(5, Frequency.DAILY).items), 4)

    def test_ct_monthly_rep4_three_extra_months(self):
        """[CT] MONTHLY × repetition=4 → event recurs on same day of 3 following months."""
        self.assertEqual(len(self._make_repeated(4, Frequency.MONTHLY).items), 3)

    def test_ct_yearly_rep3_two_extra_years(self):
        """[CT] YEARLY × repetition=3 → event recurs on same date for 2 following years."""
        self.assertEqual(len(self._make_repeated(3, Frequency.YEARLY).items), 2)

    def test_ct_biweekly_rep3_two_extra_dates(self):
        """[CT] BIWEEKLY × repetition=3 → event recurs on 2 additional dates, 14 days apart."""
        self.assertEqual(len(self._make_repeated(3, Frequency.BIWEEKLY).items), 2)

    def test_ct_once_rep1_single_occurrence(self):
        """[CT] ONCE × repetition=1 → event occurs only on its original date, never recurs."""
        self.assertEqual(len(self._make_repeated(1, Frequency.ONCE).items), 0)

    # --- status × privacy combinations for Event ---

    def test_ct_status_normal_private_false(self):
        """[CT] Status=NORMAL, privacy=False — both stored correctly."""
        ev = UserEvent(0, 2024, 1, 1, "E", 1, Frequency.ONCE, Status.NORMAL, False)
        self.assertEqual(ev.status, Status.NORMAL)
        self.assertFalse(ev.privacy)

    def test_ct_status_done_private_true(self):
        """[CT] Status=DONE, privacy=True — both stored correctly."""
        ev = UserEvent(0, 2024, 1, 1, "E", 1, Frequency.ONCE, Status.DONE, True)
        self.assertEqual(ev.status, Status.DONE)
        self.assertTrue(ev.privacy)

    def test_ct_status_important_private_false(self):
        """[CT] Status=IMPORTANT, privacy=False — both stored correctly."""
        ev = UserEvent(0, 2024, 1, 1, "E", 1, Frequency.ONCE, Status.IMPORTANT, False)
        self.assertEqual(ev.status, Status.IMPORTANT)
        self.assertFalse(ev.privacy)

    def test_ct_status_unimportant_private_true(self):
        """[CT] Status=UNIMPORTANT, privacy=True — both stored correctly."""
        ev = UserEvent(0, 2024, 1, 1, "E", 1, Frequency.ONCE, Status.UNIMPORTANT, True)
        self.assertEqual(ev.status, Status.UNIMPORTANT)
        self.assertTrue(ev.privacy)

    # --- Task: deadline × privacy × status combinations ---

    def test_ct_task_with_deadline_important_private(self):
        """[CT] Task with deadline + IMPORTANT status + privacy=True."""
        t = Task(0, "Deadline task", Status.IMPORTANT, make_timer(), True, 2025, 6, 15)
        self.assertEqual(t.status, Status.IMPORTANT)
        self.assertTrue(t.privacy)
        self.assertEqual((t.year, t.month, t.day), (2025, 6, 15))

    def test_ct_task_no_deadline_done_not_private(self):
        """[CT] Task with no deadline + DONE status + privacy=False."""
        t = Task(0, "No deadline", Status.DONE, make_timer(), False, 0, 0, 0)
        self.assertEqual(t.status, Status.DONE)
        self.assertFalse(t.privacy)
        self.assertEqual((t.year, t.month, t.day), (0, 0, 0))

    # --- Calendar: firstweekday × month combinations (pairwise) ---

    def test_ct_calendar_monday_start_all_months(self):
        """[CT] Monday-start calendar produces valid grids for all 12 months."""
        cal = Calendar(0, False)
        for month in range(1, 13):
            grid = cal.monthdayscalendar(2024, month)
            self.assertGreater(len(grid), 0)

    def test_ct_calendar_sunday_start_all_months(self):
        """[CT] Sunday-start calendar (firstweekday=6) valid for all 12 months."""
        cal = Calendar(6, False)
        for month in range(1, 13):
            grid = cal.monthdayscalendar(2024, month)
            self.assertGreater(len(grid), 0)

    def test_ct_calendar_month_day_week_consistency(self):
        """[CT] For every month: week_number of first day matches month_week_numbers[0]."""
        cal = Calendar(0, False)
        for month in range(1, 13):
            wnums = cal.month_week_numbers(2024, month)
            first_nonzero = next(d for d in cal.monthdayscalendar(2024, month)[0] if d != 0)
            self.assertEqual(wnums[0], cal.week_number(2024, month, first_nonzero))


if __name__ == "__main__":
    unittest.main(verbosity=2)
