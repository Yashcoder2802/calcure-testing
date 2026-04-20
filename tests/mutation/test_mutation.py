#!/usr/bin/env python3
"""
Mutation Tests (Section 2.3) — Calcure Calendar & Task Manager
===============================================================
Each test in this file is a deliberate, precision test designed to kill one or
more *surviving* mutants from the baseline mutatest run.

Baseline scores (before this file):
  calcure/calendars.py  :  44 detected /  45 total  =  97.8 % mutation score
  calcure/data.py       : 518 detected / 652 total  =  79.4 % mutation score

Every test documents, in its docstring, the exact mutant (file, line, mutation)
it is designed to kill.  Tests are grouped by the source code region they target.

Mutant label key:
  [CAL-Lnn]  calendars.py line nn
  [DAT-Lnn]  data.py line nn
"""

import sys
import os
import time
import tempfile
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

from calcure.data import (
    Task, UserEvent, UserRepeatedEvent, Event, Timer,
    Tasks, Events, Birthdays, Collection,
    Status, Frequency, RepeatedEvents,
)
from calcure.calendars import Calendar


# ---------------------------------------------------------------------------
# Shared helpers (mirror the helper style used in blackbox / whitebox suites)
# ---------------------------------------------------------------------------

def make_timer(stamps=None):
    return Timer(stamps or [])


def make_task(item_id=0, name="Task", status=Status.NORMAL, privacy=False,
              year=0, month=0, day=0):
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
# 1. DEFAULT FIELD VALUE IDENTITY CHECKS
#    Kills: DAT-L48, DAT-L95  (None → False / None → True)
# ===========================================================================

class TestDefaultFieldIdentity(unittest.TestCase):
    """
    assertIsNone distinguishes None from False and True.
    The surviving mutants change the default value of calendar_number from
    None to False or True.  assertIsNone(x) fails for both False and True,
    so every variant is killed.
    """

    def test_task_calendar_number_defaults_to_none(self):
        """
        [DAT-L48] Task(calendar_number=None) default.
        Mutants: None→False, None→True.
        assertIsNone fails for False and True; assertFalse would not.
        """
        t = Task(0, "X", Status.NORMAL, Timer([]), False)
        self.assertIsNone(t.calendar_number)

    def test_user_repeated_event_calendar_number_defaults_to_none(self):
        """
        [DAT-L95] UserRepeatedEvent(calendar_number=None) default.
        Mutants: None→True, None→False.
        """
        ev = UserRepeatedEvent(0, 2024, 1, 1, "E", Status.NORMAL, False)
        self.assertIsNone(ev.calendar_number)

    def test_task_calendar_number_is_none_not_falsy(self):
        """
        [DAT-L48] Additional identity check: the value must be None, not just falsy.
        assertEqual(None) fails for False (0 == None is False in Python).
        """
        t = Task(99, "Another", Status.DONE, Timer([1000]), True)
        self.assertEqual(t.calendar_number, None)


# ===========================================================================
# 2. BOOLEAN RETURN VALUE IDENTITY  (False vs None)
#    Kills: DAT-L112, DAT-L117, DAT-L221, DAT-L252
# ===========================================================================

class TestBooleanReturnIdentity(unittest.TestCase):
    """
    The surviving mutants change literal `False` return values to `None`.
    assertFalse(None) passes (None is falsy), so existing tests miss these.
    assertIs(x, False) or assertEqual(x, False) fails for None.
    """

    def test_timer_is_counting_identity_false_for_empty_stamps(self):
        """
        [DAT-L112] `return False if not self.stamps else ...`
        Mutant: return None → assertFalse(None) passes but assertIs fails.
        """
        t = Timer([])
        self.assertIs(t.is_counting, False)

    def test_timer_is_started_identity_false_for_empty_stamps(self):
        """
        [DAT-L117] `return True if self.stamps else False`
        Mutant: False→None. assertIs(None, False) fails.
        """
        t = Timer([])
        self.assertIs(t.is_started, False)

    def test_is_valid_number_none_input_returns_false_identity(self):
        """
        [DAT-L221] `return False` in is_valid_number's None-guard.
        Mutant: False→None.
        """
        tasks = Tasks()
        tasks.add_item(make_task())
        self.assertIs(tasks.is_valid_number(None), False)

    def test_has_active_timer_false_identity_when_no_timer_running(self):
        """
        [DAT-L252] `return False` in has_active_timer's loop-exit.
        Mutant: False→None.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        self.assertIs(tasks.has_active_timer, False)

    def test_item_exists_false_identity_when_not_found(self):
        """
        [DAT-L201] `return False` at end of item_exists.
        Mutant: False→None.  assertEqual(False) distinguishes None from False.
        """
        tasks = Tasks()
        tasks.add_item(make_task(name="Present"))
        self.assertEqual(tasks.item_exists("Absent"), False)

    def test_has_active_timer_false_identity_with_paused_timer(self):
        """
        [DAT-L252] has_active_timer must be exactly False (not None) when all
        timers are paused (even stamps count → is_counting is False).
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.add_timestamp_for_task(0)   # start
        tasks.add_timestamp_for_task(0)   # pause  (2 stamps → is_counting=False)
        self.assertIs(tasks.has_active_timer, False)


# ===========================================================================
# 3. COLLECTION.CHANGED INITIALIZATION
#    Kills: DAT-L154  (False → None, False → True)
# ===========================================================================

class TestCollectionChangedInit(unittest.TestCase):
    """
    Collection.__init__ sets self.changed = False.
    Surviving mutants change that to None or True.
    assertIs(x, False) catches None; assertFalse(x) catches True.
    Using assertEqual(x, False) kills both in a single assertion.
    """

    def test_tasks_changed_initialized_to_exactly_false(self):
        """[DAT-L154] Tasks().changed must be exactly False, not None or True."""
        self.assertEqual(Tasks().changed, False)

    def test_events_changed_initialized_to_exactly_false(self):
        """[DAT-L154] Events().changed must be exactly False, not None or True."""
        self.assertEqual(Events().changed, False)

    def test_birthdays_changed_initialized_to_exactly_false(self):
        """[DAT-L154] Birthdays inherits Collection; changed must start as False."""
        self.assertEqual(Birthdays().changed, False)


# ===========================================================================
# 4. TIMER PASSED_TIME ARITHMETIC PRECISION
#    Kills: DAT-L127, DAT-L142, DAT-L144
# ===========================================================================

class TestTimerPassedTimeArithmetic(unittest.TestCase):
    """
    Precision tests against arithmetic mutations in Timer.passed_time.
    The key line is:
        time_passed += float(stamps[index]) - float(stamps[index-1])
    and the day-boundary formatting:
        if 2*one_day > time_passed > one_day:   →  "1 day " prefix
        if time_passed >= 2*one_day:             →  "N days " prefix
    """

    def test_passed_time_uses_subtraction_not_modulo(self):
        """
        [DAT-L127] stamps[index] - stamps[index-1] vs stamps[index] % stamps[index-1].
        For stamps [1000, 4000]:
          subtraction: 4000 - 1000 = 3000 s  → "50:00"
          modulo:      4000 % 1000 = 0  s     → "00:00"
        The exact string check distinguishes the two operations.
        """
        t = Timer([1000, 4000])          # 3000 seconds = 50 minutes
        self.assertEqual(t.passed_time, "50:00")

    def test_passed_time_subtraction_not_modulo_second_interval(self):
        """
        [DAT-L127] Two intervals: [100, 600, 700, 5700].
          Interval 1: 600-100=500 s.  Interval 2: 5700-700=5000 s.  Total=5500 s.
          With mod: 600%100=0, 5700%700=300.  Total=300 s → completely different.
        """
        t = Timer([100, 600, 700, 5700])   # 5500 s = 91 min 40 s
        self.assertEqual(t.passed_time, "01:31:40")

    def test_passed_time_one_day_prefix_for_90000_seconds(self):
        """
        [DAT-L142  Mult→Add]
        Original upper bound: 2 * 86400 = 172800.
        Mutant upper bound:   2 + 86400 = 86402.
        For 90000 s:  original passes (172800>90000>86400 ✓),
                      mutant fails  (86402>90000 is False → prefix missing).
        """
        base = 1_000_000
        t = Timer([base, base + 90000])    # 25 hours = 1 day 1 hour
        self.assertTrue(t.passed_time.startswith("1 day "))

    def test_passed_time_exactly_two_days_shows_days_prefix(self):
        """
        [DAT-L144  GtE→Gt]
        Original: time_passed >= 2*one_day  (includes the boundary, 172800).
        Mutant:   time_passed >  2*one_day  (excludes the boundary).
        For exactly 172800 s original adds "2 days", mutant adds nothing.
        """
        base = 1_000_000
        t = Timer([base, base + 2 * 86400])   # exactly 48 hours
        self.assertTrue(t.passed_time.startswith("2 days "))

    def test_passed_time_just_over_two_days_exact_string(self):
        """
        [DAT-L142  Gt→NotEq]
        For time_passed = 2*one_day + 1 the first `>` in the chained comparison
        becomes `!=`.  Original: `172800 > 172801` is False → line 142 skipped.
        Mutant:   `172800 != 172801` is True AND `172801 > 86400` is True →
                  adds "1 day" prefix BEFORE the "N days" prefix, corrupting
                  the string.  assertEqual to exact expected value catches this.
        """
        base = 1_000_000
        t = Timer([base, base + 2 * 86400 + 1])   # 48h 1s
        self.assertEqual(t.passed_time, "2 days 00:00:01")

    def test_passed_time_86401_seconds_shows_one_day_not_two_days(self):
        """
        [DAT-L144  Mult→Add]
        Original line 144 upper bound: 2*86400=172800.
        Mutant line 144 upper bound:   2+86400=86402.
        For 86401 s: original line 142 fires (1 day prefix), line 144 does NOT.
        Mutant: line 144 fires too (86401>=86402 is False), same result actually—
        but for 86402 s the mutant fires line 144 incorrectly.
        """
        base = 1_000_000
        t = Timer([base, base + 86402])   # 86402 s = 1 day + 2 s
        result = t.passed_time
        # Must be "1 day HH:MM:SS" — NOT "2 days ..."
        self.assertTrue(result.startswith("1 day "))
        self.assertFalse(result.startswith("2 days "))

    def test_passed_time_two_days_exact_value(self):
        """
        [DAT-L144  GtE→Gt + Mult→Add combined]
        Exact string assertion for 2 * 86400 seconds.
        Any mutation that prevents the "2 days" prefix or corrupts the string fails.
        """
        base = 1_000_000
        t = Timer([base, base + 2 * 86400])
        self.assertEqual(t.passed_time, "2 days 00:00:00")


# ===========================================================================
# 5. MULTI-ITEM ID PRECISION  (Eq → GtE / Eq → LtE killers)
#    Kills: DAT-L165, DAT-L173, DAT-L180, DAT-L191,
#           DAT-L265, DAT-L280, DAT-L288, DAT-L298, DAT-L333, DAT-L341
# ===========================================================================

class TestDeleteItemIDPrecision(unittest.TestCase):
    """[DAT-L165  Eq→GtE]  delete_item should delete only the exact ID."""

    def test_delete_item_leaves_item_with_higher_id(self):
        """
        Mutant (>=): deletes item 3 AND item 8 because 8 >= 3.
        Original (==): deletes only item 3.
        Checking that item 8 survives kills the mutant.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=3, name="Delete me"))
        tasks.add_item(make_task(item_id=8, name="Keep me"))
        tasks.delete_item(3)
        self.assertEqual(len(tasks.items), 1)
        self.assertEqual(tasks.items[0].name, "Keep me")

    def test_delete_item_leaves_item_with_lower_id(self):
        """Mutant (<=): deletes item 0 (lower ID) when targeting item 5."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="Keep me"))
        tasks.add_item(make_task(item_id=5, name="Delete me"))
        tasks.delete_item(5)
        self.assertEqual(len(tasks.items), 1)
        self.assertEqual(tasks.items[0].name, "Keep me")


class TestRenameItemIDPrecision(unittest.TestCase):
    """[DAT-L165/173  Eq→GtE, Eq→LtE]  rename_item must not touch other items."""

    def test_rename_does_not_affect_item_with_higher_id(self):
        """Mutant (>=): renames item 5 AND item 10.  Bystander (10) must be unchanged."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=5, name="Target"))
        tasks.add_item(make_task(item_id=10, name="Bystander"))
        tasks.rename_item(5, "Renamed")
        self.assertEqual(tasks.items[0].name, "Renamed")
        self.assertEqual(tasks.items[1].name, "Bystander")

    def test_rename_does_not_affect_item_with_lower_id(self):
        """Mutant (<=): renames item 0 AND item 5.  Lower ID (0) must be unchanged."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="Bystander"))
        tasks.add_item(make_task(item_id=5, name="Target"))
        tasks.rename_item(5, "Renamed")
        self.assertEqual(tasks.items[0].name, "Bystander")
        self.assertEqual(tasks.items[1].name, "Renamed")


class TestToggleStatusIDPrecision(unittest.TestCase):
    """[DAT-L180  Eq→GtE, If_Statement→If_True]  toggle_item_status."""

    def test_toggle_status_does_not_affect_item_with_higher_id(self):
        """
        Mutant GtE: toggling id=3 also toggles id=7 (7>=3).
        Bystander at id=7 must remain NORMAL.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=3))
        tasks.add_item(make_task(item_id=7))
        tasks.toggle_item_status(3, Status.DONE)
        self.assertEqual(tasks.items[0].status, Status.DONE)
        self.assertEqual(tasks.items[1].status, Status.NORMAL)

    def test_toggle_status_does_not_affect_item_with_lower_id(self):
        """Mutant LtE: toggling id=5 also toggles id=0 (0<=5)."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.add_item(make_task(item_id=5))
        tasks.toggle_item_status(5, Status.IMPORTANT)
        self.assertEqual(tasks.items[0].status, Status.NORMAL)
        self.assertEqual(tasks.items[1].status, Status.IMPORTANT)

    def test_toggle_status_if_true_mutant_affects_all_items(self):
        """
        [DAT-L180  If_Statement→If_True]  The guard is always True → every
        item gets toggled.  Three-item collection with one target: only the
        target must change status; the other two must stay NORMAL.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.add_item(make_task(item_id=1))
        tasks.add_item(make_task(item_id=2))
        tasks.toggle_item_status(1, Status.DONE)
        self.assertEqual(tasks.items[0].status, Status.NORMAL)
        self.assertEqual(tasks.items[1].status, Status.DONE)
        self.assertEqual(tasks.items[2].status, Status.NORMAL)


class TestTogglePrivacyIDPrecision(unittest.TestCase):
    """[DAT-L191  Eq→GtE, If_Statement→If_True]  toggle_item_privacy."""

    def test_toggle_privacy_does_not_affect_higher_id(self):
        """Only item 2's privacy flips; item 8 (higher id) stays unchanged."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=2, privacy=False))
        tasks.add_item(make_task(item_id=8, privacy=False))
        tasks.toggle_item_privacy(2)
        self.assertTrue(tasks.items[0].privacy)
        self.assertFalse(tasks.items[1].privacy)

    def test_toggle_privacy_does_not_affect_lower_id(self):
        """Only item 5's privacy flips; item 1 (lower id) stays unchanged."""
        tasks = Tasks()
        tasks.add_item(make_task(item_id=1, privacy=False))
        tasks.add_item(make_task(item_id=5, privacy=False))
        tasks.toggle_item_privacy(5)
        self.assertFalse(tasks.items[0].privacy)
        self.assertTrue(tasks.items[1].privacy)


class TestResetTimerIDPrecision(unittest.TestCase):
    """[DAT-L280  Eq→GtE]  reset_timer_for_task targets only the exact ID."""

    def test_reset_timer_does_not_clear_higher_id_timer(self):
        """
        Mutant (>=): resetting id=0 also resets id=5 (5>=0).
        After reset(0), task with id=5 must still have its stamps.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.add_item(make_task(item_id=5))
        tasks.add_timestamp_for_task(0)
        tasks.add_timestamp_for_task(5)
        stamps_before = len(tasks.items[1].timer.stamps)
        tasks.reset_timer_for_task(0)
        self.assertEqual(tasks.items[0].timer.stamps, [])
        self.assertEqual(len(tasks.items[1].timer.stamps), stamps_before)


class TestChangeDeadlineIDPrecision(unittest.TestCase):
    """[DAT-L288  Eq→GtE]  change_deadline targets only the exact ID."""

    def test_change_deadline_does_not_affect_higher_id(self):
        """
        Mutant (>=): setting deadline for id=1 also changes id=5 (5>=1).
        Task at id=5 must retain its original deadline of (0,0,0).
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=1, year=0, month=0, day=0))
        tasks.add_item(make_task(item_id=5, year=0, month=0, day=0))
        tasks.change_deadline(1, 2025, 12, 31)
        self.assertEqual((tasks.items[0].year, tasks.items[0].month, tasks.items[0].day),
                         (2025, 12, 31))
        self.assertEqual((tasks.items[1].year, tasks.items[1].month, tasks.items[1].day),
                         (0, 0, 0))


class TestToggleSubtaskStateIDPrecision(unittest.TestCase):
    """[DAT-L298  Eq→GtE]  toggle_subtask_state targets only the exact ID."""

    def test_toggle_subtask_does_not_affect_higher_id(self):
        """
        Mutant (>=): toggling id=0 also modifies id=5 name (5>=0).
        Item at id=5 must remain unchanged.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="Regular"))
        tasks.add_item(make_task(item_id=5, name="Also regular"))
        tasks.toggle_subtask_state(0)
        self.assertEqual(tasks.items[0].name, "--Regular")
        self.assertEqual(tasks.items[1].name, "Also regular")


class TestEventChangesDayDateIDPrecision(unittest.TestCase):
    """[DAT-L333, DAT-L341  Eq→GtE]  Events.change_day / change_date."""

    def test_change_day_does_not_affect_higher_id(self):
        """Only event at id=0 should have its day changed; event at id=7 must not."""
        events = Events()
        events.add_item(make_event(item_id=0, day=5))
        events.add_item(make_event(item_id=7, day=10))
        events.change_day(0, 25)
        self.assertEqual(events.items[0].day, 25)
        self.assertEqual(events.items[1].day, 10)

    def test_change_date_does_not_affect_higher_id(self):
        """
        [DAT-L341  Eq→GtE] Only event at id=0 should have its date changed.
        """
        events = Events()
        events.add_item(make_event(item_id=0, year=2024, month=1, day=1))
        events.add_item(make_event(item_id=6, year=2024, month=1, day=1))
        events.change_date(0, 2025, 6, 15)
        self.assertEqual(
            (events.items[0].year, events.items[0].month, events.items[0].day),
            (2025, 6, 15))
        self.assertEqual(
            (events.items[1].year, events.items[1].month, events.items[1].day),
            (2024, 1, 1))


# ===========================================================================
# 6. CHANGED FLAG TRUTHINESS AFTER EACH OPERATION
#    Kills: DAT-L167, L175, L185, L193, L207, L212, L260, L267, L275,
#           L282, L292, L303, L335, L345
# ===========================================================================

class TestChangedFlagAfterOperations(unittest.TestCase):
    """
    Surviving mutants change `self.changed = True` to `None` or `False`.
    assertTrue(None) fails; assertTrue(False) fails.  Both are killed.
    We reset `changed = False` before the operation under test so that
    the only way the assertion can pass is if the operation sets it correctly.
    """

    def _fresh_tasks(self, *items):
        tasks = Tasks()
        for item in items:
            tasks.add_item(item)
        tasks.changed = False
        return tasks

    def _fresh_events(self, *items):
        events = Events()
        for item in items:
            events.add_item(item)
        events.changed = False
        return events

    # --- delete_item ---
    def test_delete_item_sets_changed(self):
        """[DAT-L167] True→None/False in delete_item."""
        tasks = self._fresh_tasks(make_task(item_id=0))
        tasks.delete_item(0)
        self.assertTrue(tasks.changed)

    # --- rename_item ---
    def test_rename_item_sets_changed(self):
        """[DAT-L175] True→None/False in rename_item."""
        tasks = self._fresh_tasks(make_task(item_id=0))
        tasks.rename_item(0, "New name")
        self.assertTrue(tasks.changed)

    # --- toggle_item_status ---
    def test_toggle_status_sets_changed(self):
        """[DAT-L185] True→None/False in toggle_item_status."""
        tasks = self._fresh_tasks(make_task(item_id=0))
        tasks.toggle_item_status(0, Status.DONE)
        self.assertTrue(tasks.changed)

    # --- toggle_item_privacy ---
    def test_toggle_privacy_sets_changed(self):
        """[DAT-L193] True→None/False in toggle_item_privacy."""
        tasks = self._fresh_tasks(make_task(item_id=0))
        tasks.toggle_item_privacy(0)
        self.assertTrue(tasks.changed)

    # --- change_all_statuses ---
    def test_change_all_statuses_sets_changed(self):
        """[DAT-L207] True→None/False in change_all_statuses."""
        tasks = self._fresh_tasks(make_task(item_id=0))
        tasks.change_all_statuses(Status.DONE)
        self.assertTrue(tasks.changed)

    # --- delete_all_items ---
    def test_delete_all_items_sets_changed(self):
        """[DAT-L212] True→None/False in delete_all_items."""
        tasks = self._fresh_tasks(make_task(item_id=0))
        tasks.delete_all_items()
        self.assertTrue(tasks.changed)

    # --- add_subtask ---
    def test_add_subtask_sets_changed(self):
        """[DAT-L260] True→None/False in add_subtask."""
        tasks = self._fresh_tasks(make_task(item_id=0, name="Parent"))
        tasks.add_subtask(make_task(item_id=1, name="Sub"), 0)
        self.assertTrue(tasks.changed)

    # --- add_timestamp_for_task ---
    def test_add_timestamp_sets_changed(self):
        """[DAT-L267] True→None/False in add_timestamp_for_task."""
        tasks = self._fresh_tasks(make_task(item_id=0))
        tasks.add_timestamp_for_task(0)
        self.assertTrue(tasks.changed)

    # --- pause_all_other_timers ---
    def test_pause_all_other_timers_sets_changed(self):
        """[DAT-L275] True→None/False in pause_all_other_timers."""
        tasks = self._fresh_tasks(make_task(item_id=0), make_task(item_id=1))
        tasks.add_timestamp_for_task(0)
        tasks.add_timestamp_for_task(1)
        tasks.changed = False
        tasks.pause_all_other_timers(1)
        self.assertTrue(tasks.changed)

    # --- reset_timer_for_task ---
    def test_reset_timer_sets_changed(self):
        """[DAT-L282] True→None/False in reset_timer_for_task."""
        tasks = self._fresh_tasks(make_task(item_id=0))
        tasks.add_timestamp_for_task(0)
        tasks.changed = False
        tasks.reset_timer_for_task(0)
        self.assertTrue(tasks.changed)

    # --- change_deadline ---
    def test_change_deadline_sets_changed(self):
        """[DAT-L292] True→None/False in change_deadline."""
        tasks = self._fresh_tasks(make_task(item_id=0))
        tasks.change_deadline(0, 2025, 1, 1)
        self.assertTrue(tasks.changed)

    # --- toggle_subtask_state ---
    def test_toggle_subtask_state_sets_changed(self):
        """[DAT-L303] True→None/False in toggle_subtask_state."""
        tasks = self._fresh_tasks(make_task(item_id=0, name="Task"))
        tasks.toggle_subtask_state(0)
        self.assertTrue(tasks.changed)

    # --- Events.change_day ---
    def test_change_day_sets_changed(self):
        """[DAT-L335] True→None/False in Events.change_day."""
        events = self._fresh_events(make_event(item_id=0))
        events.change_day(0, 20)
        self.assertTrue(events.changed)

    # --- Events.change_date ---
    def test_change_date_sets_changed(self):
        """[DAT-L345] True→None/False in Events.change_date."""
        events = self._fresh_events(make_event(item_id=0))
        events.change_date(0, 2025, 7, 4)
        self.assertTrue(events.changed)


# ===========================================================================
# 7. EVENT_EXISTS MULTI-FIELD PRECISION
#    Kills: DAT-L323, L324, L325, L326, L328
# ===========================================================================

class TestEventExistsFieldPrecision(unittest.TestCase):
    """
    event_exists checks name AND year AND month AND day simultaneously.
    Surviving mutants change individual == comparisons to >=, allowing events
    that differ in one field to be incorrectly matched.
    """

    def test_event_exists_false_for_earlier_year(self):
        """
        [DAT-L324  year Eq→GtE] event stored at 2025; query at 2020.
        Mutant (>=): 2025 >= 2020 → found.  Original (==): 2025 != 2020 → not found.
        """
        events = Events()
        events.add_item(make_event(year=2025, month=3, day=10, name="Conference"))
        query = make_event(year=2020, month=3, day=10, name="Conference")
        self.assertFalse(events.event_exists(query))

    def test_event_exists_false_for_later_year(self):
        """
        [DAT-L324  year Eq→LtE] event stored at 2020; query at 2025.
        Mutant (<=): 2020 <= 2025 → found.  Original: 2020 != 2025 → not found.
        """
        events = Events()
        events.add_item(make_event(year=2020, month=3, day=10, name="Conference"))
        query = make_event(year=2025, month=3, day=10, name="Conference")
        self.assertFalse(events.event_exists(query))

    def test_event_exists_false_for_earlier_month(self):
        """
        [DAT-L325  month Eq→GtE] event in month 6; query for month 3.
        Mutant: 6 >= 3 → found.  Original: 6 != 3 → not found.
        """
        events = Events()
        events.add_item(make_event(year=2024, month=6, day=10, name="Workshop"))
        query = make_event(year=2024, month=3, day=10, name="Workshop")
        self.assertFalse(events.event_exists(query))

    def test_event_exists_false_for_later_month(self):
        """[DAT-L325  month Eq→LtE] stored month 3; query month 6."""
        events = Events()
        events.add_item(make_event(year=2024, month=3, day=10, name="Workshop"))
        query = make_event(year=2024, month=6, day=10, name="Workshop")
        self.assertFalse(events.event_exists(query))

    def test_event_exists_false_for_earlier_day(self):
        """
        [DAT-L326  day Eq→GtE] event on day 15; query for day 5.
        Mutant: 15 >= 5 → found.  Original: 15 != 5 → not found.
        """
        events = Events()
        events.add_item(make_event(year=2024, month=3, day=15, name="Launch"))
        query = make_event(year=2024, month=3, day=5, name="Launch")
        self.assertFalse(events.event_exists(query))

    def test_event_exists_false_for_later_day(self):
        """[DAT-L326  day Eq→LtE] stored day 5; query day 15."""
        events = Events()
        events.add_item(make_event(year=2024, month=3, day=5, name="Launch"))
        query = make_event(year=2024, month=3, day=15, name="Launch")
        self.assertFalse(events.event_exists(query))

    def test_event_exists_returns_false_identity(self):
        """
        [DAT-L328  False→None] Return identity check for the negative case.
        assertFalse(None) passes; assertEqual(x, False) fails for None.
        """
        events = Events()
        self.assertEqual(events.event_exists(make_event()), False)


# ===========================================================================
# 8. FILTER EVENTS YEAR PRECISION
#    Kills: DAT-L238  (Eq→GtE in filter_events_that_month year check)
# ===========================================================================

class TestFilterEventsYearPrecision(unittest.TestCase):
    """
    filter_events_that_month uses `event.year == screen.year`.
    Mutant GtE: `event.year >= screen.year` includes future-year events.
    """

    def test_filter_month_excludes_later_year_events(self):
        """
        [DAT-L238  Eq→GtE]  An event in year 2030 must NOT appear when
        filtering for month 5 of year 2024 — even if month and name match.
        """
        events = Events()
        events.add_item(make_event(item_id=0, year=2024, month=5, day=10, name="Current"))
        events.add_item(make_event(item_id=1, year=2030, month=5, day=10, name="Future"))
        screen = MockScreen(2024, 5, 1)
        result = events.filter_events_that_month(screen)
        names = {e.name for e in result.items}
        self.assertIn("Current", names)
        self.assertNotIn("Future", names)

    def test_filter_month_excludes_earlier_year_events(self):
        """
        [DAT-L238  Eq→LtE]  An event in year 2020 must NOT appear when
        filtering for year 2024.
        """
        events = Events()
        events.add_item(make_event(item_id=0, year=2024, month=5, day=10, name="Current"))
        events.add_item(make_event(item_id=1, year=2020, month=5, day=10, name="Past"))
        screen = MockScreen(2024, 5, 1)
        result = events.filter_events_that_month(screen)
        names = {e.name for e in result.items}
        self.assertIn("Current", names)
        self.assertNotIn("Past", names)


# ===========================================================================
# 9. BIRTHDAYS FILTER PRECISION
#    Kills: DAT-L355  (Eq→GtE on month and day)
# ===========================================================================

class TestBirthdaysFilterPrecision(unittest.TestCase):
    """
    Birthdays.filter_events_that_day checks month == screen.month AND day == screen.day.
    GtE mutants would match events in months/days after the queried date.
    """

    def test_birthdays_filter_no_match_for_earlier_screen_month(self):
        """
        [DAT-L355  month Eq→GtE]
        Birthday is in month 6, screen asks for month 5.
        Mutant: event.month (6) >= screen.month (5) → found (wrong!).
        Original: 6 == 5 → not found (correct).
        """
        bdays = Birthdays()
        bdays.add_item(Event(1990, 6, 21, "Alice"))
        screen = MockScreen(2024, 5, 21)   # month 5, same day
        result = bdays.filter_events_that_day(screen)
        self.assertEqual(len(result.items), 0)

    def test_birthdays_filter_no_match_for_earlier_screen_day(self):
        """
        [DAT-L355  day Eq→GtE]
        Birthday is on day 21, screen asks for day 15.
        Mutant: event.day (21) >= screen.day (15) → found (wrong!).
        Original: 21 == 15 → not found (correct).
        """
        bdays = Birthdays()
        bdays.add_item(Event(1990, 6, 21, "Alice"))
        screen = MockScreen(2024, 6, 15)   # same month, earlier day
        result = bdays.filter_events_that_day(screen)
        self.assertEqual(len(result.items), 0)

    def test_birthdays_filter_no_match_for_later_screen_month(self):
        """
        [DAT-L355  month Eq→LtE]
        Birthday in month 5, screen asks for month 9.
        Mutant: 5 <= 9 → found.  Original: 5 != 9 → not found.
        """
        bdays = Birthdays()
        bdays.add_item(Event(1990, 5, 21, "Bob"))
        screen = MockScreen(2024, 9, 21)
        result = bdays.filter_events_that_day(screen)
        self.assertEqual(len(result.items), 0)


# ===========================================================================
# 10. REPEATED EVENTS — REPETITION BOUNDARY AND RRULE SLICE
#     Kills: DAT-L369  (GtE→Gt  on `event.repetition >= 1`)
# ===========================================================================

class TestRepeatedEventsEdgeCases(unittest.TestCase):
    """
    DAT-L369: `if event.repetition >= 1:` — the GtE→Gt mutant changes this to `> 1`.
    For repetition=1, both produce range(1,1) which is an empty loop — equivalent.
    The difference surfaces when an event has repetition=1 AND an rrule string:
      * Original (>=1): takes the if-branch, runs empty loop, skips elif-rrule.
      * Mutant    (>1) : skips the if-branch, enters elif-rrule, processes rrule.
    """

    def test_repetition_one_with_rrule_is_not_expanded(self):
        """
        [DAT-L369  GtE→Gt]
        A UserEvent with repetition=1 and an rrule string must produce 0 extra
        occurrences, because the if-branch is taken (range(1,1) is empty) and the
        elif-rrule branch is NOT entered.
        Mutant: falls into elif-rrule → processes the rrule → adds 2 extra items
        (COUNT=3, first skipped → 2 remaining). This assertion catches that.
        """
        ue = Events()
        ev = UserEvent(0, 2024, 3, 1, "Staff meeting", 1, Frequency.WEEKLY,
                       Status.NORMAL, False,
                       rrule="FREQ=WEEKLY;COUNT=3")
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        self.assertEqual(len(reps.items), 0)

    def test_repetition_zero_with_no_rrule_produces_nothing(self):
        """
        [DAT-L369  regression] repetition=0 and no rrule → 0 extra items.
        Ensures the boundary between the if and elif blocks is preserved.
        """
        ue = Events()
        ev = UserEvent(0, 2024, 3, 1, "Zero-rep", 0, Frequency.WEEKLY,
                       Status.NORMAL, False)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        self.assertEqual(len(reps.items), 0)


# ===========================================================================
# 11. MONTHLY RECURRENCE YEAR-OVERFLOW FORMULA
#     Kills: DAT-L439, DAT-L440  (arithmetic mutations in calculate_recurring_events)
# ===========================================================================

class TestMonthlyRecurrenceFormula(unittest.TestCase):
    """
    calculate_recurring_events (MONTHLY path):
      new_year  = year + (month - 1)//12          [line 439]
      new_month = month - 12*(new_year - year)    [line 440]

    Arithmetic mutations (Sub→Mod, Sub→FloorDiv, FloorDiv→Div) produce wrong
    dates.  We pin exact (year, month, day) tuples to catch any of them.
    """

    def test_monthly_overflow_two_months_into_next_year(self):
        """
        [DAT-L439/440] Monthly event starting December: +1 month → Jan next year,
        +2 months → Feb next year.  Exact date tuples kill arithmetic mutants.
        """
        ue = Events()
        ev = make_event(year=2024, month=12, day=1, repetition=3,
                        frequency=Frequency.MONTHLY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        dates = sorted([(r.year, r.month, r.day) for r in reps.items])
        self.assertEqual(dates, [(2025, 1, 1), (2025, 2, 1)])

    def test_monthly_overflow_correct_new_year_value(self):
        """
        [DAT-L439  FloorDiv→Div] (month-1)//12 vs (month-1)/12.
        For month=25 (12+13): (25-1)//12=2, (25-1)/12=2.0.  The year delta is 2.
        A three-repetition monthly event in Jan (month 1) staying within year:
        month+1=2 and month+2=3, both <=12 → no overflow.  Standard case to confirm
        the formula is even executed at all.
        """
        ue = Events()
        ev = make_event(year=2024, month=1, day=15, repetition=3,
                        frequency=Frequency.MONTHLY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        dates = sorted([(r.year, r.month, r.day) for r in reps.items])
        self.assertEqual(dates, [(2024, 2, 15), (2024, 3, 15)])

    def test_monthly_recurrence_november_start_exact_dates(self):
        """
        [DAT-L440  Sub→Mod] new_month = month - 12*(new_year-year).
        For month=13 (after Nov+2): new_year=year+1, new_month=13-12*1=1.
        Mod mutation: 13 % 12 = 1 (same here), but for month=14: 14-12=2 vs 14%12=2.
        Use month=15 (Nov=11, +4 → month=15):
          Sub: 15 - 12*1 = 3 (March).  Mod: 15 % 12 = 3 (same!).
        Use month=12+5=17 to distinguish: Sub: 17-12=5. Mod: 17%12=5. Still same.
        Use month=24: Sub: 24-12*1=12. For new_year: (24-1)//12=1.
          Mod: 24%12=0 (DIFFERENT → December vs no month → error).
        November + 13 months = December of the following year.
        """
        ue = Events()
        # Nov + 13 months = December next+1 year: month=11+13=24
        ev = make_event(year=2023, month=11, day=1, repetition=14,
                        frequency=Frequency.MONTHLY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2023)
        # rep 13 → temp_month = 11+13=24
        # new_year = 2023 + (24-1)//12 = 2023+1 = 2024
        # new_month = 24 - 12*(2024-2023) = 24-12 = 12  → December 2024
        dates_dict = {(r.year, r.month): r.day for r in reps.items}
        self.assertIn((2024, 12), dates_dict)
        self.assertEqual(dates_dict[(2024, 12)], 1)

    def test_monthly_overflow_does_not_produce_month_zero(self):
        """
        [DAT-L440  Sub→Mod] For month=12: (12-1)//12=0, new_year unchanged,
        new_month = 12 - 12*0 = 12.  Mod mutation: 12 % 12 = 0 (month 0!).
        The RepeatedEvents collection would store month=0 which is invalid.
        This test verifies all generated months are in [1..12].
        """
        ue = Events()
        ev = make_event(year=2024, month=10, day=1, repetition=5,
                        frequency=Frequency.MONTHLY)
        ue.add_item(ev)
        reps = RepeatedEvents(ue, False, 2024)
        for r in reps.items:
            self.assertGreaterEqual(r.month, 1)
            self.assertLessEqual(r.month, 12)


# ===========================================================================
# 12. ITEM_EXISTS NOT-FOUND BRANCH
#     Kills: DAT-L199  (If_Statement→If_True)
# ===========================================================================

class TestItemExistsNotFound(unittest.TestCase):
    """
    If_Statement→If_True in item_exists would make it always return True.
    A negative test (assertFalse) after adding a different-named item catches this.
    """

    def test_item_exists_false_when_collection_has_different_named_item(self):
        """[DAT-L199  If_True] Mutant returns True for any query; original returns False."""
        tasks = Tasks()
        tasks.add_item(make_task(name="Present"))
        self.assertFalse(tasks.item_exists("Absent"))

    def test_item_exists_false_for_empty_collection(self):
        """[DAT-L199] Empty collection must never report a match."""
        self.assertFalse(Tasks().item_exists("Anything"))


# ===========================================================================
# 13. CALENDARS — GREGORIAN LEAP YEAR BOUNDARY
#     Kills: CAL-L42 partial  (already high score; reinforce with precision tests)
# ===========================================================================

class TestCalendarLeapYearPrecision(unittest.TestCase):
    """
    The surviving mutant CAL-L42 col 40 (NotEq→Gt) is equivalent for positive years.
    However the following boundary tests strengthen the overall mutation score by
    pinning exact day-count values at leap-year formula boundaries.
    """

    def _cal(self):
        return Calendar(0, False)

    def test_year_divisible_4_not_100_has_leap_feb(self):
        """[CAL-L42] 2024 % 4==0, 2024 % 100!=0 → leap → Feb = 29 days."""
        self.assertEqual(self._cal().last_day(2024, 2), 29)

    def test_year_divisible_100_not_400_is_not_leap(self):
        """[CAL-L42] 1900 % 100==0, 1900 % 400!=0 → NOT leap → Feb = 28 days."""
        self.assertEqual(self._cal().last_day(1900, 2), 28)

    def test_year_divisible_400_is_leap(self):
        """[CAL-L42] 2000 % 400==0 → leap → Feb = 29 days."""
        self.assertEqual(self._cal().last_day(2000, 2), 29)

    def test_non_divisible_by_4_not_leap(self):
        """[CAL-L42] 2023 % 4 != 0 → NOT leap → Feb = 28."""
        self.assertEqual(self._cal().last_day(2023, 2), 28)

    def test_last_day_february_exact_int_value(self):
        """
        [CAL-L42] Exact integer assertion (not just assertIn) so that any arithmetic
        mutation that shifts the result by ±1 is caught.
        """
        self.assertEqual(self._cal().last_day(2024, 2), 29)   # leap
        self.assertEqual(self._cal().last_day(2025, 2), 28)   # not leap

    def test_itermonthdays_padding_exact_count_for_february_leap(self):
        """
        [CAL-L57/60] The days_before / days_after formulas must place exactly
        29 real days inside Feb 2024.  Arithmetic mutations shift the padding,
        causing real days to appear at wrong positions.
        """
        cal = self._cal()
        days = [d for d in cal.itermonthdays(2024, 2) if d != 0]
        self.assertEqual(len(days), 29)
        self.assertEqual(days[0], 1)
        self.assertEqual(days[-1], 29)


# ===========================================================================
# 14. USEREVENT NONE DEFAULTS
#     Kills: DAT-L74 (8 mutants: None→False/True for hour, minute, rrule,
#            exdate, calendar_number on UserEvent)
# ===========================================================================

class TestUserEventNoneDefaults(unittest.TestCase):
    """
    UserEvent.__init__ has five keyword args defaulting to None:
      calendar_number=None, hour=None, minute=None, rrule=None, exdate=None
    mutatest generates None→False and None→True variants for each.
    assertIsNone distinguishes None from both False and True.
    """

    def test_user_event_all_optional_fields_default_to_none(self):
        """
        [DAT-L74  c:68,79,92,104,117]  All five None-default fields.
        Creating a UserEvent with no keyword args must leave every optional
        field as exactly None (not False, not True).
        """
        ev = UserEvent(0, 2024, 3, 1, "Meeting", 1, Frequency.ONCE,
                       Status.NORMAL, False)
        self.assertIsNone(ev.calendar_number)
        self.assertIsNone(ev.hour)
        self.assertIsNone(ev.minute)
        self.assertIsNone(ev.rrule)
        self.assertIsNone(ev.exdate)

    def test_user_event_calendar_number_none_not_falsy(self):
        """[DAT-L74  c:104]  Identity check — None, not False."""
        ev = UserEvent(99, 2024, 1, 1, "E", 1, Frequency.ONCE,
                       Status.NORMAL, True)
        self.assertIs(ev.calendar_number, None)


# ===========================================================================
# 15. REVERSED-ORDER COLLECTION TESTS
#     Pattern: insert a *higher-ID* item BEFORE the target so that Eq→GtE
#     and If_Statement→If_True mutations hit the wrong (first) item.
#     Kills: DAT-L165 GtE, DAT-L180 GtE+If_True, DAT-L191 GtE,
#            DAT-L265 GtE, DAT-L280 GtE+If_True, DAT-L288 GtE+If_True,
#            DAT-L333 GtE+If_True, DAT-L341 GtE+If_True
# ===========================================================================

class TestReversedOrderCollectionMutants(unittest.TestCase):
    """
    All collection methods use `for item in self.items: if item.item_id == id: ... break`.
    When the target item is always the FIRST satisfying element, Eq→GtE and
    If_True mutations produce the same first-match behaviour.

    Fix: insert a HIGHER-ID decoy item first, then the target.
    - GtE (>=target): decoy satisfies the condition first → wrong item affected.
    - If_True:        decoy is always processed first → wrong item affected.
    """

    # ── delete_item ──────────────────────────────────────────────────────────
    def test_delete_item_gteq_hits_decoy_not_target(self):
        """
        [DAT-L165  Eq→GtE]  Decoy id=8 is FIRST; target id=3 is second.
        Mutant (>=3): deletes decoy (8>=3) and breaks → target survives.
        Original (==3): skips decoy, deletes target → decoy survives.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=8, name="decoy"))   # first
        tasks.add_item(make_task(item_id=3, name="target"))  # second
        tasks.delete_item(3)
        self.assertEqual(len(tasks.items), 1)
        self.assertEqual(tasks.items[0].name, "decoy")       # decoy must remain

    # ── toggle_item_status ───────────────────────────────────────────────────
    def test_toggle_status_gteq_and_iftrue_hit_decoy(self):
        """
        [DAT-L180  Eq→GtE, If_True]  Decoy id=7 first, target id=3 second.
        GtE/If_True both process decoy (first item) instead of target.
        Original changes items[1]; mutants change items[0].
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=7, name="decoy"))
        tasks.add_item(make_task(item_id=3, name="target"))
        tasks.toggle_item_status(3, Status.DONE)
        self.assertEqual(tasks.items[0].status, Status.NORMAL)  # decoy untouched
        self.assertEqual(tasks.items[1].status, Status.DONE)    # target changed

    # ── toggle_item_privacy ──────────────────────────────────────────────────
    def test_toggle_privacy_gteq_hits_decoy(self):
        """
        [DAT-L191  Eq→GtE]  Decoy id=9 first, target id=2 second.
        GtE: decoy (9>=2) gets toggled instead of target.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=9, privacy=False))   # decoy first
        tasks.add_item(make_task(item_id=2, privacy=False))   # target
        tasks.toggle_item_privacy(2)
        self.assertFalse(tasks.items[0].privacy)   # decoy unchanged
        self.assertTrue(tasks.items[1].privacy)    # target flipped

    # ── add_timestamp_for_task ───────────────────────────────────────────────
    def test_add_timestamp_gteq_hits_decoy(self):
        """
        [DAT-L265  Eq→GtE]  Decoy id=5 first, target id=0 second.
        GtE (>=0): decoy (5>=0) gets the timestamp stamp instead of target.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=5))   # decoy
        tasks.add_item(make_task(item_id=0))   # target
        tasks.add_timestamp_for_task(0)
        self.assertEqual(tasks.items[0].timer.stamps, [])  # decoy untouched
        self.assertEqual(len(tasks.items[1].timer.stamps), 1)

    # ── reset_timer_for_task ─────────────────────────────────────────────────
    def test_reset_timer_gteq_and_iftrue_hit_decoy(self):
        """
        [DAT-L280  Eq→GtE, If_True]  Decoy id=5, target id=0.
        After seeding both with stamps, reset(0):
          Original → target stamps cleared, decoy intact.
          Mutant   → decoy stamps cleared (wrong item), target still has stamps.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=5))
        tasks.add_item(make_task(item_id=0))
        tasks.add_timestamp_for_task(5)
        tasks.add_timestamp_for_task(0)
        decoy_stamps_before = len(tasks.items[0].timer.stamps)
        tasks.reset_timer_for_task(0)
        # decoy must still have its stamps
        self.assertEqual(len(tasks.items[0].timer.stamps), decoy_stamps_before)
        # target must be cleared
        self.assertEqual(tasks.items[1].timer.stamps, [])

    def test_reset_timer_lteq_hits_lower_id_decoy(self):
        """
        [DAT-L280  Eq→LtE]  Items in forward order [id=0, id=5], reset(5).
        LtE (<=5): id=0 satisfies 0<=5, so decoy (id=0) gets cleared first.
        Original: skips id=0, clears id=5.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.add_item(make_task(item_id=5))
        tasks.add_timestamp_for_task(0)
        tasks.add_timestamp_for_task(5)
        decoy_stamps = len(tasks.items[0].timer.stamps)
        tasks.reset_timer_for_task(5)
        self.assertEqual(len(tasks.items[0].timer.stamps), decoy_stamps)  # decoy untouched
        self.assertEqual(tasks.items[1].timer.stamps, [])                 # target cleared

    # ── change_deadline ──────────────────────────────────────────────────────
    def test_change_deadline_gteq_and_iftrue_hit_decoy(self):
        """
        [DAT-L288  Eq→GtE, If_True]  Decoy id=9, target id=1.
        GtE/If_True both modify decoy's deadline instead of target's.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=9, year=0, month=0, day=0))
        tasks.add_item(make_task(item_id=1, year=0, month=0, day=0))
        tasks.change_deadline(1, 2025, 12, 31)
        self.assertEqual(
            (tasks.items[0].year, tasks.items[0].month, tasks.items[0].day),
            (0, 0, 0))           # decoy deadline unchanged
        self.assertEqual(
            (tasks.items[1].year, tasks.items[1].month, tasks.items[1].day),
            (2025, 12, 31))      # target deadline set

    def test_change_deadline_lteq_hits_lower_id(self):
        """
        [DAT-L288  Eq→LtE]  Forward order [id=0, id=5], change_deadline(5).
        LtE: id=0 (0<=5) gets deadline changed instead of id=5.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, year=0, month=0, day=0))
        tasks.add_item(make_task(item_id=5, year=0, month=0, day=0))
        tasks.change_deadline(5, 2025, 6, 15)
        self.assertEqual(
            (tasks.items[0].year, tasks.items[0].month, tasks.items[0].day),
            (0, 0, 0))           # id=0 must not change
        self.assertEqual(
            (tasks.items[1].year, tasks.items[1].month, tasks.items[1].day),
            (2025, 6, 15))

    # ── Events.change_day ────────────────────────────────────────────────────
    def test_change_day_gteq_and_iftrue_hit_decoy(self):
        """
        [DAT-L333  Eq→GtE, If_True]  Decoy event id=9, target event id=2.
        GtE/If_True both modify decoy's day instead of target's.
        """
        events = Events()
        events.add_item(make_event(item_id=9, day=1))
        events.add_item(make_event(item_id=2, day=1))
        events.change_day(2, 28)
        self.assertEqual(events.items[0].day, 1)   # decoy unchanged
        self.assertEqual(events.items[1].day, 28)  # target updated

    def test_change_day_lteq_hits_lower_id(self):
        """
        [DAT-L333  Eq→LtE]  Forward order [id=0, id=5], change_day(5).
        LtE: id=0 (0<=5) gets its day changed instead of id=5.
        """
        events = Events()
        events.add_item(make_event(item_id=0, day=1))
        events.add_item(make_event(item_id=5, day=1))
        events.change_day(5, 20)
        self.assertEqual(events.items[0].day, 1)   # id=0 unchanged
        self.assertEqual(events.items[1].day, 20)  # id=5 updated

    # ── Events.change_date ───────────────────────────────────────────────────
    def test_change_date_gteq_and_iftrue_hit_decoy(self):
        """
        [DAT-L341  Eq→GtE, If_True]  Decoy event id=7, target event id=1.
        """
        events = Events()
        events.add_item(make_event(item_id=7, year=2024, month=1, day=1))
        events.add_item(make_event(item_id=1, year=2024, month=1, day=1))
        events.change_date(1, 2025, 6, 15)
        self.assertEqual(
            (events.items[0].year, events.items[0].month, events.items[0].day),
            (2024, 1, 1))               # decoy unchanged
        self.assertEqual(
            (events.items[1].year, events.items[1].month, events.items[1].day),
            (2025, 6, 15))              # target updated

    def test_change_date_lteq_hits_lower_id(self):
        """
        [DAT-L341  Eq→LtE]  Forward order [id=0, id=5], change_date(5).
        LtE: id=0 (0<=5) gets date changed instead of id=5.
        """
        events = Events()
        events.add_item(make_event(item_id=0, year=2024, month=1, day=1))
        events.add_item(make_event(item_id=5, year=2024, month=1, day=1))
        events.change_date(5, 2025, 6, 15)
        self.assertEqual(
            (events.items[0].year, events.items[0].month, events.items[0].day),
            (2024, 1, 1))
        self.assertEqual(
            (events.items[1].year, events.items[1].month, events.items[1].day),
            (2025, 6, 15))


# ===========================================================================
# 16. ITEM_EXISTS STRING COMPARISON  (Eq→LtE)
#     Kills: DAT-L199  c:15
# ===========================================================================

class TestItemExistsStringLtE(unittest.TestCase):
    """
    item_exists checks `item.name == item_name`.
    Eq→LtE mutant: `item.name <= item_name`.
    A stored name that is lexicographically LESS than the query satisfies <=
    but not ==, so item_exists should return False but mutant returns True.
    """

    def test_item_exists_false_when_stored_name_is_lexicographically_less(self):
        """
        [DAT-L199  Eq→LtE]  "Apple" < "Banana" in string order.
        Original: "Apple" == "Banana" → False.
        LtE mutant: "Apple" <= "Banana" → True (WRONG).
        """
        tasks = Tasks()
        tasks.add_item(make_task(name="Apple"))
        self.assertFalse(tasks.item_exists("Banana"))

    def test_item_exists_false_empty_then_alphabetically_later_query(self):
        """[DAT-L199  Eq→LtE]  'aardvark' < 'zebra'."""
        tasks = Tasks()
        tasks.add_item(make_task(name="aardvark"))
        self.assertFalse(tasks.item_exists("zebra"))


# ===========================================================================
# 17. EVENT_EXISTS NAME GtE
#     Kills: DAT-L323  c:16
# ===========================================================================

class TestEventExistsNameGtE(unittest.TestCase):
    """
    event_exists checks event.name == new_event.name (and year/month/day).
    Eq→GtE mutant: event.name >= new_event.name.
    A stored event whose name sorts AFTER the query name satisfies >= but not ==.
    """

    def test_event_exists_false_when_stored_name_sorts_after_query(self):
        """
        [DAT-L323  Eq→GtE]  "Zebra" > "Aardvark".
        Original: "Zebra" == "Aardvark" → False.
        GtE mutant: "Zebra" >= "Aardvark" → True (WRONG), same year/month/day.
        """
        events = Events()
        events.add_item(make_event(name="Zebra", year=2024, month=3, day=1))
        query = make_event(name="Aardvark", year=2024, month=3, day=1)
        self.assertFalse(events.event_exists(query))


# ===========================================================================
# 18. TOGGLE_SUBTASK_STATE LtE PRECISION
#     Kills: DAT-L298 c:15, DAT-L299 c:19
# ===========================================================================

class TestToggleSubtaskLtE(unittest.TestCase):
    """
    toggle_subtask_state has NO break, so Eq→LtE would toggle every item
    whose id <= selected_task_id instead of only the exact match.
    L298: item.item_id == selected_task_id  → LtE
    L299: item.name[:2] == '--'             → LtE (string comparison)
    """

    def test_toggle_subtask_lteq_id_only_touches_target(self):
        """
        [DAT-L298  Eq→LtE]  items [id=0 "Regular", id=5 "Regular"], toggle(5).
        Original: only id=5 becomes "--Regular".
        LtE (<=5): both id=0 and id=5 become "--Regular".
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="Regular"))
        tasks.add_item(make_task(item_id=5, name="Regular"))
        tasks.toggle_subtask_state(5)
        self.assertEqual(tasks.items[0].name, "Regular")   # id=0 unchanged
        self.assertEqual(tasks.items[1].name, "--Regular") # id=5 toggled

    def test_toggle_subtask_name_lteq_does_not_strip_normal_prefix(self):
        """
        [DAT-L299  Eq→LtE]  item.name[:2] == '--' → <= '--'.
        '!!' has ASCII 33, '-' has ASCII 45: '!!' < '--' so LtE treats '!!'
        as if it were a subtask and strips the first 2 chars.
        Original: '!!' != '--' → adds '--' prefix → '--!!task'.
        LtE mutant: '!!' <= '--' → True → strips → 'task' (WRONG).
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="!!task"))
        tasks.toggle_subtask_state(0)
        self.assertEqual(tasks.items[0].name, "--!!task")


if __name__ == "__main__":
    unittest.main(verbosity=2)
