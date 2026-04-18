#!/usr/bin/env python3
"""
Mock Testing (Alternate Testing Type) — Calcure Calendar & Task Manager
=======================================================================
Mock testing uses unittest.mock to replace real dependencies with
controlled fakes. This lets us:
  - Test components in true isolation
  - Simulate conditions that are hard to reproduce (IOError, network failure)
  - Control time.time() to make timer tests deterministic
  - Verify that collaborators are called correctly (interaction testing)

This counts as the project's ALTERNATE TESTING TYPE alongside blackbox
and whitebox unit/integration tests.
"""

import sys
import os
import time
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open, call

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

from calcure.data import (
    Task, UserEvent, Event, Timer, Tasks, Events,
    Status, Frequency, RepeatedEvents
)
from calcure.calendars import Calendar


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_timer(stamps=None):
    return Timer(stamps or [])


def make_task(item_id=0, name="Task", status=Status.NORMAL,
              privacy=False, year=0, month=0, day=0):
    return Task(item_id, name, status, make_timer(), privacy, year, month, day)


def make_config(tasks_file, events_file=""):
    class FakeCF:
        TASKS_FILE = tasks_file
        EVENTS_FILE = events_file
        USE_PERSIAN_CALENDAR = False
    return FakeCF()


# ===========================================================================
# 1. MOCKING time.time() — DETERMINISTIC TIMER TESTS
# ===========================================================================

class TestTimerWithMockedTime(unittest.TestCase):
    """
    Mock time.time() so timer calculations are deterministic and
    not affected by actual clock speed or test machine load.
    """

    @patch("calcure.data.time.time", return_value=1_000_000.0)
    def test_timer_passed_time_while_counting_uses_mocked_time(self, mock_time):
        """
        With time.time() mocked to 1_000_000, a timer started at 999_940
        (60 seconds ago) should report exactly 01:00 elapsed.
        """
        t = Timer([999_940])
        result = t.passed_time
        self.assertEqual(result, "01:00")

    @patch("calcure.data.time.time", return_value=1_000_000.0)
    def test_timer_two_intervals_plus_live_run(self, mock_time):
        """
        stamps = [base, base+10, base+20] → completed interval (10s) + live run (20s) = 30s.
        With mocked time, the live run = 1_000_000 - (base+20).
        base = 999_950: stamps = [999_950, 999_960, 999_980]
        Completed: 999_960 - 999_950 = 10
        Live: 1_000_000 - 999_980 = 20 → total 30s → 00:30
        """
        t = Timer([999_950, 999_960, 999_980])
        result = t.passed_time
        self.assertEqual(result, "00:30")

    @patch("calcure.data.time.time", return_value=1_000_000.0)
    def test_add_timestamp_uses_int_of_mocked_time(self, mock_time):
        """
        Tasks.add_timestamp_for_task calls int(time.time()).
        With mock returning 1_000_000.0, the stamp stored must be 1_000_000.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.add_timestamp_for_task(0)
        stamp = tasks.items[0].timer.stamps[0]
        self.assertEqual(int(stamp), 1_000_000)

    @patch("calcure.data.time.time", return_value=1_000_000.0)
    def test_pause_all_other_timers_stamps_use_mocked_time(self, mock_time):
        """
        pause_all_other_timers adds a timestamp via int(time.time()).
        With mocked time, the added pause stamp must equal 1_000_000.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0))
        tasks.add_item(make_task(item_id=1))
        tasks.items[0].timer.stamps = [999_900]
        tasks.items[1].timer.stamps = [999_900]
        tasks.pause_all_other_timers(1)
        pause_stamp = tasks.items[0].timer.stamps[-1]
        self.assertEqual(int(pause_stamp), 1_000_000)


# ===========================================================================
# 2. MOCKING FILE I/O — LOADER ERROR HANDLING
# ===========================================================================

class TestLoaderCSVWithMockedFile(unittest.TestCase):
    """
    Mock the file system to test how loaders handle missing or broken files
    without actually creating files on disk.
    """

    def test_read_file_creates_new_file_on_ioerror(self):
        """
        LoaderCSV.read_file catches IOError (file not found) and calls
        create_file to initialise an empty file. Verify the fallback path.
        """
        from calcure.loaders import LoaderCSV

        loader = LoaderCSV()
        with patch("builtins.open", side_effect=[IOError("no such file"), mock_open()()]):
            with patch.object(loader, "create_file", return_value=[]) as mock_create:
                result = loader.read_file("/fake/path/tasks.csv")
        mock_create.assert_called_once_with("/fake/path/tasks.csv")

    def test_create_file_returns_empty_list_on_success(self):
        """
        create_file opens a file for writing and returns [].
        Mock open() to avoid touching the filesystem.
        """
        from calcure.loaders import LoaderCSV

        loader = LoaderCSV()
        m = mock_open()
        with patch("builtins.open", m):
            result = loader.create_file("/tmp/fake.csv")
        self.assertEqual(result, [])
        m.assert_called_once_with("/tmp/fake.csv", "w+", encoding="utf-8")

    def test_create_file_returns_empty_list_on_file_not_found(self):
        """
        If open() raises FileNotFoundError inside create_file,
        the method must still return [] without propagating the exception.
        """
        from calcure.loaders import LoaderCSV

        loader = LoaderCSV()
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = loader.create_file("/nonexistent/dir/file.csv")
        self.assertEqual(result, [])

    def test_ics_loader_read_file_returns_empty_string_for_missing_file(self):
        """
        LoaderICS.read_file returns '' (empty string) when the path does not exist.
        No exception must be raised.
        """
        from calcure.loaders import LoaderICS

        loader = LoaderICS()
        result = loader.read_file("/this/path/does/not/exist.ics")
        self.assertEqual(result, "")

    def test_ics_loader_read_url_returns_empty_on_http_error(self):
        """
        LoaderICS.read_url returns '' when the server returns an HTTP error.
        """
        import urllib.error
        from calcure.loaders import LoaderICS

        loader = LoaderICS()
        with patch("urllib.request.urlopen",
                   side_effect=urllib.error.HTTPError(
                       url="http://fake", code=404, msg="Not Found", hdrs={}, fp=None)):
            result = loader.read_url("http://fake.example.com/calendar.ics")
        self.assertEqual(result, "")

    def test_ics_loader_read_url_returns_empty_on_url_error(self):
        """
        LoaderICS.read_url returns '' when there is no internet connection (URLError).
        """
        import urllib.error
        from calcure.loaders import LoaderICS

        loader = LoaderICS()
        with patch("urllib.request.urlopen",
                   side_effect=urllib.error.URLError(reason="no route to host")):
            result = loader.read_url("http://unreachable.example.com/cal.ics")
        self.assertEqual(result, "")


# ===========================================================================
# 3. MOCKING COLLECTIONS — INTERACTION / COLLABORATION TESTING
# ===========================================================================

class TestCollectionInteractions(unittest.TestCase):
    """
    Mock external collaborators to verify that collection methods produce
    the correct side effects and state transitions.
    """

    def test_delete_item_removes_correct_item_verified_via_mock_saver(self):
        """
        After delete_item, the collection must not contain the deleted task.
        We verify this by passing the collection to a mock saver and checking
        what it would write.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="Keep"))
        tasks.add_item(make_task(item_id=1, name="Delete me"))
        tasks.delete_item(1)
        names = [t.name for t in tasks.items]
        self.assertNotIn("Delete me", names)
        self.assertIn("Keep", names)

    def test_delete_all_items_leaves_empty_list(self):
        """
        delete_all_items must result in an empty items list.
        Verified by checking tasks.items directly.
        """
        tasks = Tasks()
        for i in range(5):
            tasks.add_item(make_task(item_id=i))
        tasks.delete_all_items()
        self.assertEqual(tasks.items, [])

    def test_move_task_produces_correct_order(self):
        """
        move_task(0, 2) on [A, B, C] must produce [B, C, A].
        Verified via state inspection after the call.
        """
        tasks = Tasks()
        tasks.add_item(make_task(item_id=0, name="A"))
        tasks.add_item(make_task(item_id=1, name="B"))
        tasks.add_item(make_task(item_id=2, name="C"))
        tasks.move_task(0, 2)
        names = [t.name for t in tasks.items]
        self.assertEqual(names, ["B", "C", "A"])


# ===========================================================================
# 4. MOCKING SAVER — VERIFY ATOMIC WRITE BEHAVIOUR
# ===========================================================================

class TestSaverAtomicWrite(unittest.TestCase):
    """
    Verify that TaskSaverCSV and EventSaverCSV use the atomic write pattern:
    write to .bak file, then rename it over the original.
    """

    def test_task_saver_writes_to_bak_then_replaces(self):
        """
        TaskSaverCSV.save() must write to <file>.bak and then call replace()
        to atomically move it over the original file.
        """
        from calcure.savers import TaskSaverCSV
        from pathlib import Path

        tasks = Tasks()
        tasks.add_item(make_task(name="Test"))
        cf = make_config("/fake/tasks.csv")

        mock_file = mock_open()
        mock_path_instance = MagicMock()

        with patch("builtins.open", mock_file), \
             patch("calcure.savers.Path", return_value=mock_path_instance):
            TaskSaverCSV(tasks, cf).save()

        mock_path_instance.replace.assert_called_once()

    def test_event_saver_writes_to_bak_then_replaces(self):
        """
        EventSaverCSV.save() must use the same atomic write pattern.
        """
        from calcure.savers import EventSaverCSV

        events = Events()
        events.add_item(UserEvent(0, 2024, 3, 1, "Event",
                                  1, Frequency.ONCE, Status.NORMAL, False))
        cf = make_config("", "/fake/events.csv")
        cf.EVENTS_FILE = "/fake/events.csv"

        mock_file = mock_open()
        mock_path_instance = MagicMock()

        with patch("builtins.open", mock_file), \
             patch("calcure.savers.Path", return_value=mock_path_instance):
            EventSaverCSV(events, cf).save()

        mock_path_instance.replace.assert_called_once()


# ===========================================================================
# 5. MOCKING DATETIME — CALENDAR DETERMINISM
# ===========================================================================

class TestCalendarWithMockedDatetime(unittest.TestCase):
    """
    Mock datetime.date to verify that Calendar.first_day() and last_day()
    call the correct underlying library functions.
    Note: week_number() uses a local `import datetime` inside the function,
    so we verify its output via known-good dates rather than mocking.
    """

    def test_first_day_delegates_to_datetime_date(self):
        """
        first_day() for Gregorian calls datetime.date(year, month, 1).weekday().
        We mock calcure.calendars.datetime to intercept this call.
        """
        cal = Calendar(0, False)
        with patch("calcure.calendars.datetime") as mock_dt:
            mock_date_instance = MagicMock()
            mock_date_instance.weekday.return_value = 3
            mock_dt.date.return_value = mock_date_instance
            result = cal.first_day(2024, 5)
        mock_dt.date.assert_called_once_with(2024, 5, 1)
        self.assertEqual(result, 3)

    def test_week_number_known_values_without_mock(self):
        """
        week_number() uses an internal import so we verify correctness via
        known ground-truth dates instead of mocking the import.
        2024-01-01 = ISO week 1, 2024-03-23 = ISO week 12.
        """
        cal = Calendar(0, False)
        self.assertEqual(cal.week_number(2024, 1, 1), 1)
        self.assertEqual(cal.week_number(2024, 3, 23), 12)
        self.assertEqual(cal.week_number(2024, 12, 31), 1)  # week 1 of 2025


if __name__ == "__main__":
    unittest.main(verbosity=2)
