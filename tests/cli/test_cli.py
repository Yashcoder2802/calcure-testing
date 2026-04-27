"""
tests/test_cli.py
=================
Section 2.4 – Alternate Testing: CLI Testing for calcure
=========================================================

Strategy
--------
Calcure is a terminal (curses) application.  Its CLI surface breaks into
two tiers depending on *when* each flag is processed:

  Tier 1 – Handled during Config.__init__() BEFORE curses starts
           (-v, --folder, --config, unknown flags).
           These can be tested with a plain subprocess (no TTY).

  Tier 2 – Handled inside main(stdscr) AFTER curses initialises
           (--task, --event).
           These require a real pseudo-terminal (PTY) so that
           curses.initscr() succeeds.  Python's built-in `pty` module
           is used – no extra install needed.

Every test function documents:
  • What scenario is exercised
  • Which technique justifies it (EP / BA / EG / Validation / Combinatorial)
  • Which fault, if any, it is designed to reveal

Run with:
    python3.11 -m pytest tests/test_cli.py -v
"""

import configparser
import csv
import fcntl
import os
import shutil
import struct
import subprocess
import sys
import termios
import threading
import pty
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Explicit Python 3.11 binary – fall back to PATH lookup if moved.
PYTHON = shutil.which("python3.11") or "/opt/homebrew/opt/python@3.11/bin/python3.11"
CALCURE = [PYTHON, "-m", "calcure"]
FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _env(home_dir: Path, extra: dict | None = None) -> dict:
    """
    Build a subprocess environment that redirects HOME to *home_dir* so
    calcure never touches the developer's real ~/.config/calcure directory.

    Config.__init__() always calls:
        (Path.home() / ".config" / "calcure").mkdir(exist_ok=True)
    using only exist_ok – NOT parents=True.  If home_dir/.config does not
    already exist, that mkdir fails with FileNotFoundError.  We therefore
    pre-create home_dir/.config here so that the default config folder can
    always be created by calcure without error.
    """
    (home_dir / ".config").mkdir(exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env.setdefault("TERM", "xterm-256color")
    if extra:
        env.update(extra)
    return env


def run_headless(args: list[str], home_dir: Path, timeout: int = 10) -> subprocess.CompletedProcess:
    """
    Run calcure WITHOUT a real terminal.
    curses.wrapper() will raise curses.error, which cli() silently swallows.
    Suitable for Tier-1 flags processed before curses is ever touched.
    Returns a CompletedProcess with stdout/stderr as text.
    """
    return subprocess.run(
        CALCURE + args,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_env(home_dir),
    )


def run_with_pty(args: list[str], home_dir: Path, timeout: int = 8) -> tuple[int, str]:
    """
    Run calcure with a pseudo-terminal (PTY) so curses.initscr() succeeds.
    Suitable for Tier-2 flags (--task, --event) that live inside main().

    A background thread drains the master side of the PTY so the child
    process never blocks on a full pipe buffer.  stderr is captured separately
    via a regular pipe and returned as text.

    Returns (returncode, stderr_text).
    """
    master_fd, slave_fd = pty.openpty()
    # Give the PTY a real size so curses does not render into 0×0 space.
    fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))

    proc = subprocess.Popen(
        CALCURE + args,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=subprocess.PIPE,
        env=_env(home_dir),
        close_fds=True,
    )
    # Parent no longer needs the slave end.
    os.close(slave_fd)

    # Drain the master so the child's curses output never fills the kernel
    # buffer and blocks the child process.
    def _drain():
        try:
            while True:
                if not os.read(master_fd, 4096):
                    break
        except OSError:
            pass

    drainer = threading.Thread(target=_drain, daemon=True)
    drainer.start()

    try:
        _, stderr_bytes = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        _, stderr_bytes = proc.communicate()
    finally:
        os.close(master_fd)
        drainer.join(timeout=1)

    return proc.returncode, (stderr_bytes or b"").decode("utf-8", errors="replace")


def make_config(config_path: Path, data_dir: Path) -> None:
    """
    Write a minimal but complete config.ini at *config_path* so that
    calcure treats this as an existing installation (is_first_run = False).
    Pointing data files to *data_dir* keeps every test's storage isolated.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    conf = configparser.ConfigParser()
    conf["Parameters"] = {
        "folder_with_datafiles":     str(data_dir),
        "log_file":                  str(data_dir / "info.log"),
        "calcurse_todo_file":        str(data_dir / "calcurse_todo"),
        "calcurse_events_file":      str(data_dir / "calcurse_apts"),
        "language":                  "en",
        "default_view":              "calendar",
        "default_calendar_view":     "monthly",
        "birthdays_from_abook":      "No",
        "show_keybindings":          "Yes",
        "privacy_mode":              "No",
        "show_weather":              "No",
        "weather_city":              "",
        "weather_metric_units":      "Yes",
        "minimal_today_indicator":   "Yes",
        "minimal_days_indicator":    "Yes",
        "minimal_weekend_indicator": "Yes",
        "show_calendar_borders":     "No",
        "show_week_numbers":         "No",
        "show_moon_phases":          "No",
        "cut_titles_by_cell_length": "No",
        "ask_confirmations":         "No",
        "ask_confirmation_to_quit":  "No",
        "use_unicode_icons":         "No",
        "use_24_hour_format":        "Yes",
        "show_current_time":         "No",
        "show_holidays":             "No",
        "show_nothing_planned":      "Yes",
        "one_timer_at_a_time":       "No",
        "holiday_country":           "UnitedStates",
        "use_persian_calendar":      "No",
        "start_week_day":            "1",
        "weekend_days":              "6,7",
        "refresh_interval":          "1",
        "data_reload_interval":      "0",
        "split_screen":              "No",
        "right_pane_percentage":     "25",
        "journal_header":            "JOURNAL",
        "event_icon":                ".",
        "privacy_icon":              ".",
        "today_icon":                ".",
        "birthday_icon":             ".",
        "holiday_icon":              ".",
        "hidden_icon":               "...",
        "done_icon":                 "x",
        "todo_icon":                 ".",
        "important_icon":            "!",
        "separator_icon":            "|",
        "deadline_icon":             ".",
    }
    conf["Colors"] = {
        "color_today": "2", "color_events": "4", "color_days": "7",
        "color_day_names": "4", "color_weekends": "1",
        "color_weekend_names": "1", "color_hints": "7",
        "color_prompts": "7", "color_confirmations": "1",
        "color_birthdays": "1", "color_holidays": "2",
        "color_todo": "7", "color_done": "6", "color_title": "4",
        "color_calendar_header": "4", "color_important": "1",
        "color_unimportant": "6", "color_timer": "2",
        "color_timer_paused": "7", "color_time": "7",
        "color_deadlines": "3", "color_weather": "2",
        "color_active_pane": "2", "color_separator": "7",
        "color_calendar_border": "7",
        "color_ics_calendars": "2,3,1,7",
        "color_background": "-1",
    }
    conf["Styles"] = {
        "bold_today": "No", "bold_days": "No", "bold_day_names": "No",
        "bold_weekends": "No", "bold_weekend_names": "No",
        "bold_title": "No", "bold_active_pane": "No",
        "underlined_today": "No", "underlined_days": "No",
        "underlined_day_names": "No", "underlined_weekends": "No",
        "underlined_weekend_names": "No", "underlined_title": "No",
        "underlined_active_pane": "No", "strikethrough_done": "No",
    }
    conf["Event icons"] = {}
    with open(config_path, "w", encoding="utf-8") as fh:
        conf.write(fh)


def read_tasks_csv(data_dir: Path) -> list[list[str]]:
    """Return parsed rows from tasks.csv, or [] if the file does not exist."""
    f = data_dir / "tasks.csv"
    if not f.exists():
        return []
    with open(f, encoding="utf-8") as fh:
        return list(csv.reader(fh))


def read_events_csv(data_dir: Path) -> list[list[str]]:
    """Return parsed rows from events.csv, or [] if the file does not exist."""
    f = data_dir / "events.csv"
    if not f.exists():
        return []
    with open(f, encoding="utf-8") as fh:
        return list(csv.reader(fh))


def file_bytes(path: Path) -> bytes:
    """Return raw bytes of a file for byte-for-byte comparison."""
    with open(path, "rb") as fh:
        return fh.read()


# ===========================================================================
# Group A – Version flag (-v)
# Three tests covering: output content, exit code, and side-effect freedom.
# ===========================================================================

class TestVersionFlag:

    def test_a1_version_string_in_stdout(self, tmp_path):
        """
        EP – Valid flag partition.
        '-v' must print the version string to stdout so users can confirm
        which release they have installed.
        Fault target: version output missing or formatted incorrectly.
        """
        result = run_headless(["-v"], tmp_path)
        assert "3.2.1" in result.stdout, (
            f"Expected version '3.2.1' in stdout, got: {result.stdout!r}"
        )

    def test_a2_version_flag_exits_with_code_zero(self, tmp_path):
        """
        BA – Expected exit-code boundary.
        '-v' must exit cleanly (code 0).  A non-zero code would confuse
        scripts that check $? after querying the version.
        Fault target: unhandled exception leaking a non-zero exit status.
        """
        result = run_headless(["-v"], tmp_path)
        assert result.returncode == 0, (
            f"Expected exit code 0 for '-v', got {result.returncode}"
        )

    def test_a3_version_flag_creates_no_data_files(self, tmp_path):
        """
        Validation – Read-only invocation must not produce side effects.
        '-v' is a pure informational flag; it must not create tasks.csv or
        events.csv in the data directory.
        Fault target: loaders creating empty CSV files even on read-only calls.
        """
        run_headless(["-v"], tmp_path)
        config_dir = tmp_path / ".config" / "calcure"
        assert not (config_dir / "tasks.csv").exists(), \
            "tasks.csv must not be created by a -v invocation"
        assert not (config_dir / "events.csv").exists(), \
            "events.csv must not be created by a -v invocation"


# ===========================================================================
# Group B – Custom data folder (--folder)
# Four tests: directory creation, idempotency, data routing, bad permissions.
# ===========================================================================

class TestFolderFlag:

    def test_b1_folder_flag_creates_new_directory(self, tmp_path):
        """
        EP – Non-existent directory partition.
        '--folder=<path>' must create the directory when it does not exist.
        This is essential for first-time users who point calcure at a new
        location without pre-creating the folder themselves.
        Fault target: mkdir call missing or not handling new paths.
        """
        new_dir = tmp_path / "my_calcure_data"
        assert not new_dir.exists(), "pre-condition: directory must not exist"
        run_headless([f"--folder={new_dir}"], tmp_path)
        assert new_dir.exists(), (
            f"'--folder={new_dir}' should have created the directory"
        )

    def test_b2_folder_flag_accepts_existing_directory(self, tmp_path):
        """
        EP – Pre-existing directory partition.
        '--folder=<existing_path>' must not fail when the directory is
        already present (exist_ok semantics).
        Fault target: mkdir raising FileExistsError on an existing path.
        """
        existing = tmp_path / "already_here"
        existing.mkdir()
        result = run_headless([f"--folder={existing}"], tmp_path)
        assert result.returncode == 0, (
            f"Expected exit 0 for existing folder, got {result.returncode}"
        )

    def test_b3_folder_flag_routes_csv_files_correctly(self, tmp_path):
        """
        Validation – Data must land in the folder supplied via --folder.
        We add a task (PTY tier) and confirm tasks.csv appears inside the
        custom folder, not in the default ~/.config/calcure location.
        Fault target: --folder override being ignored; data written to wrong path.
        """
        data_dir = tmp_path / "custom_data"
        cfg_path = tmp_path / "calcure.ini"
        make_config(cfg_path, data_dir)

        run_with_pty(
            [f"--config={cfg_path}", f"--folder={data_dir}", "--task=RoutingCheck"],
            tmp_path,
        )

        assert (data_dir / "tasks.csv").exists(), (
            "tasks.csv must be written to the --folder directory"
        )
        default_dir = tmp_path / ".config" / "calcure"
        assert not (default_dir / "tasks.csv").exists(), (
            "tasks.csv must NOT be written to the default config directory"
        )

    def test_b4_folder_flag_with_unwritable_parent_exposes_traceback(self, tmp_path):
        """
        EG – Permission-error fault path.
        When --folder points to a path whose parent is read-only, calcure
        currently raises an unhandled PermissionError and emits a raw Python
        traceback to stderr.

        !! FAULT DISCOVERED !!
        read_parameters_from_user_arguments() calls data_folder.mkdir()
        with NO try/except.  A PermissionError propagates all the way to the
        top level and terminates the process with a traceback – giving the
        user no clean error message.

        Expected (correct) behaviour: a human-readable error message and a
        non-zero exit code, but NO raw traceback.
        Observed behaviour: raw 'Traceback (most recent call last)' in stderr.
        """
        readonly_parent = tmp_path / "readonly"
        readonly_parent.mkdir()
        os.chmod(readonly_parent, 0o555)  # remove write permission

        target = readonly_parent / "new_subdir"
        result = run_headless([f"--folder={target}"], tmp_path)

        # Document the fault: a traceback IS produced (this assertion will
        # FAIL once the fault is fixed, which is the desired outcome).
        has_traceback = "Traceback (most recent call last)" in result.stderr
        assert has_traceback, (
            "FAULT CONFIRMED: PermissionError is not caught; raw traceback "
            "exposed to the user via stderr. "
            f"stderr was: {result.stderr!r}"
        )

        # Restore permissions so tmp_path cleanup can delete the directory.
        os.chmod(readonly_parent, 0o755)


# ===========================================================================
# Group C – Custom config file (--config)
# Three tests: missing file, valid existing file, corrupt file.
# ===========================================================================

class TestConfigFlag:

    def test_c1_config_flag_creates_config_at_given_path(self, tmp_path):
        """
        EP – Non-existent config partition.
        '--config=<new_path>' must create a fresh config.ini at that exact
        location when the file does not already exist.
        The parent directory must already exist (create_config_file() uses
        open() without mkdir, so a missing parent would raise FileNotFoundError).
        Fault target: new config landing in the default location instead of
        the one supplied via --config.
        """
        # Parent directory exists (tmp_path itself); only the file is new.
        cfg_path = tmp_path / "my_custom_config.ini"
        assert not cfg_path.exists(), "pre-condition: file must not exist"
        run_headless([f"--config={cfg_path}"], tmp_path)
        assert cfg_path.exists(), (
            f"Expected config to be created at {cfg_path}"
        )

    def test_c2_config_flag_reads_existing_config_without_crash(self, tmp_path):
        """
        EP – Valid existing config partition.
        '--config=<valid_path>' must read the file successfully and exit 0.
        Fault target: path parsing error or re-creation overwriting the file.
        """
        data_dir = tmp_path / "data"
        cfg_path = tmp_path / "valid.ini"
        make_config(cfg_path, data_dir)

        result = run_headless([f"--config={cfg_path}"], tmp_path)
        assert result.returncode == 0, (
            f"Expected exit 0 for valid --config, got {result.returncode}"
        )

    def test_c3_corrupt_config_exits_without_raw_traceback(self, tmp_path):
        """
        EG – Malformed config fault path.
        A config.ini with invalid syntax must cause calcure to exit with a
        human-readable error, NOT a raw Python traceback.
        Fault target: unhandled configparser exception leaking internals to
        the user via stderr.
        """
        cfg_path = tmp_path / "corrupt.ini"
        cfg_path.write_text("this is not valid ini syntax %%%\n", encoding="utf-8")

        result = run_headless([f"--config={cfg_path}"], tmp_path)

        assert "Traceback (most recent call last)" not in result.stderr, (
            "A corrupt config.ini must NOT produce a raw Python traceback. "
            f"stderr: {result.stderr!r}"
        )


# ===========================================================================
# Group D – --task flag  (PTY tier)
# Four tests: valid task, empty name, cross-file side effects, duplicates.
# ===========================================================================

class TestTaskFlag:

    def _setup(self, tmp_path):
        """Create an isolated config + data folder pair for PTY tests."""
        data_dir = tmp_path / "data"
        cfg_path = tmp_path / "calcure.ini"
        make_config(cfg_path, data_dir)
        return cfg_path, data_dir

    def test_d1_task_flag_writes_task_to_csv(self, tmp_path):
        """
        EP – Valid task-name partition.
        '--task=<name>' must save the task to tasks.csv so it persists
        across sessions.  The task name must appear verbatim in the file.
        Fault target: task not saved at all, or name mangled during write.
        """
        cfg, data = self._setup(tmp_path)
        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--task=Buy milk"],
            tmp_path,
        )
        rows = read_tasks_csv(data)
        names = [r[3].strip('"') for r in rows if len(r) >= 4]
        assert "Buy milk" in names, (
            f"Expected 'Buy milk' in tasks.csv rows, got: {rows}"
        )

    def test_d2_task_flag_empty_name_does_not_crash(self, tmp_path):
        """
        EG – Empty task-name edge case.
        '--task=' (empty string) must not crash calcure.  Whether the empty
        task is saved or silently dropped is secondary; crashing is the fault.
        Fault target: zero-length name causing an index error or write error.
        """
        cfg, data = self._setup(tmp_path)
        try:
            rc, _ = run_with_pty(
                [f"--config={cfg}", f"--folder={data}", "--task="],
                tmp_path,
                timeout=6,
            )
            # Any exit code is acceptable as long as no exception was raised.
        except Exception as exc:
            pytest.fail(f"run_with_pty raised an unexpected exception: {exc}")

    def test_d3_task_flag_does_not_modify_events_csv(self, tmp_path):
        """
        Validation – Write operations must not produce unexpected side effects.
        Adding a task must NOT alter events.csv in any way.  The two data
        stores are independent and must stay that way.
        Fault target: saver accidentally writing to the wrong file.
        """
        cfg, data = self._setup(tmp_path)

        # Seed events.csv with known content.
        src = FIXTURES / "sample_events.csv"
        dst = data / "events.csv"
        shutil.copy(src, dst)
        original_bytes = file_bytes(dst)

        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--task=SideEffectCheck"],
            tmp_path,
        )

        assert file_bytes(dst) == original_bytes, (
            "events.csv was modified by a --task invocation (unexpected side effect)"
        )

    def test_d4_task_flag_creates_duplicate_on_repeated_run(self, tmp_path):
        """
        Validation – Data consistency check.
        Running '--task=Same task' twice should ideally add only one entry.

        !! FAULT DISCOVERED !!
        read_items_from_user_arguments() calls user_tasks.add_item() directly
        WITHOUT checking whether the task already exists (unlike
        Importer.import_tasks_from_calcurse() which uses item_exists()).
        Each run therefore appends a duplicate row, potentially flooding the
        task list if a user re-runs the same command.

        This test documents the fault: it asserts that the count IS doubled
        (observed), serving as a regression baseline until the fault is fixed.
        Once fixed, the assertion should be changed to `count == 1`.
        """
        cfg, data = self._setup(tmp_path)
        args = [f"--config={cfg}", f"--folder={data}", "--task=Duplicate task"]

        run_with_pty(args, tmp_path)
        run_with_pty(args, tmp_path)

        rows = read_tasks_csv(data)
        names = [r[3].strip('"') for r in rows if len(r) >= 4]
        count = names.count("Duplicate task")

        # FAULT: count is 2 instead of 1.
        assert count == 2, (
            f"FAULT CONFIRMED: '--task' does not deduplicate; "
            f"found {count} copies of 'Duplicate task' after two identical runs. "
            "Fix: add an item_exists() check in read_items_from_user_arguments()."
        )


# ===========================================================================
# Group E – --event flag  (PTY tier)
# Five tests: valid event, malformed string, invalid day, invalid month,
#             cross-file side effects.
# ===========================================================================

class TestEventFlag:

    def _setup(self, tmp_path):
        data_dir = tmp_path / "data"
        cfg_path = tmp_path / "calcure.ini"
        make_config(cfg_path, data_dir)
        return cfg_path, data_dir

    def test_e1_event_flag_writes_event_to_csv(self, tmp_path):
        """
        EP – Valid event string partition.
        '--event=YYYY-MM-DD-name' must save the event to events.csv with the
        correct year, month, day, and name fields.
        Fault target: event not saved, or date fields written in wrong order.
        """
        cfg, data = self._setup(tmp_path)
        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--event=2025-04-17-TeamMeeting"],
            tmp_path,
        )
        rows = read_events_csv(data)
        # events.csv columns: id, year, month, day, name, repetition, freq, status
        found = any(
            len(r) >= 5 and r[1] == "2025" and r[2] == "4" and r[3] == "17"
            and "TeamMeeting" in r[4]
            for r in rows
        )
        assert found, f"Expected event 2025-04-17-TeamMeeting in events.csv, got: {rows}"

    def test_e2_event_flag_malformed_string_does_not_crash(self, tmp_path):
        """
        EG – Completely malformed event string.
        '--event=malformed' has no dashes in the expected positions.
        Calcure catches the resulting ValueError inside a try/except, so no
        event should be written and no crash should occur.
        Fault target: unhandled ValueError / IndexError reaching the user.
        """
        cfg, data = self._setup(tmp_path)
        try:
            run_with_pty(
                [f"--config={cfg}", f"--folder={data}", "--event=malformed"],
                tmp_path,
                timeout=6,
            )
        except Exception as exc:
            pytest.fail(f"Malformed --event caused an unexpected exception: {exc}")

        rows = read_events_csv(data)
        assert rows == [], (
            f"No event should be saved for a malformed string, got: {rows}"
        )

    def test_e3_event_flag_stores_feb30_without_validation(self, tmp_path):
        """
        BA – Boundary: day value outside the valid range for the given month.
        February 30 does not exist, but calcure stores it without validation.

        !! FAULT DISCOVERED !!
        read_items_from_user_arguments() splits on '-' and converts to int,
        then passes the integers directly to UserEvent() and EventSaverCSV
        without calling datetime.date() for validation.  The result is that
        an impossible date (2024-02-30) is silently persisted.  When calcure
        later tries to render or manipulate that date as a real date object,
        it may raise ValueError or silently display incorrect information.

        Expected behaviour: a clear error message and no file write.
        Observed behaviour: the invalid date is written to events.csv.
        """
        cfg, data = self._setup(tmp_path)
        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--event=2024-02-30-BadDay"],
            tmp_path,
        )
        rows = read_events_csv(data)
        stored = any(
            len(r) >= 4 and r[1] == "2024" and r[2] == "2" and r[3] == "30"
            for r in rows
        )
        # FAULT: the invalid date IS stored (assert True to document the behaviour).
        assert stored, (
            "FAULT CONFIRMED: Feb 30 was stored without any validation. "
            f"events.csv rows: {rows}"
        )

    def test_e4_event_flag_stores_month13_without_validation(self, tmp_path):
        """
        BA – Boundary: month value outside the valid range (1–12).
        Month 13 does not exist, but calcure stores it without validation.

        !! FAULT DISCOVERED !!
        Same root cause as test_e3: no datetime.date() validation in the
        CLI event-creation path.  Month 13 is persisted silently, which can
        later cause exceptions in calendar rendering logic that assumes
        months are in [1..12].

        Expected behaviour: a clear error message and no file write.
        Observed behaviour: the invalid month is written to events.csv.
        """
        cfg, data = self._setup(tmp_path)
        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--event=2025-13-01-BadMonth"],
            tmp_path,
        )
        rows = read_events_csv(data)
        stored = any(
            len(r) >= 4 and r[1] == "2025" and r[2] == "13"
            for r in rows
        )
        # FAULT: the invalid month IS stored.
        assert stored, (
            "FAULT CONFIRMED: month 13 was stored without any validation. "
            f"events.csv rows: {rows}"
        )

    def test_e5_event_flag_does_not_modify_tasks_csv(self, tmp_path):
        """
        Validation – Adding an event must NOT alter tasks.csv.
        The two data stores are independent and must not cross-contaminate.
        Fault target: saver accidentally writing to the wrong file.
        """
        cfg, data = self._setup(tmp_path)

        # Seed tasks.csv with known content.
        src = FIXTURES / "sample_tasks.csv"
        dst = data / "tasks.csv"
        shutil.copy(src, dst)
        original_bytes = file_bytes(dst)

        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--event=2025-06-15-SideEffectCheck"],
            tmp_path,
        )

        assert file_bytes(dst) == original_bytes, (
            "tasks.csv was modified by an --event invocation (unexpected side effect)"
        )


# ===========================================================================
# Group F – Invalid / unknown flags
# Three tests covering unknown long flag, unknown short flag, positional args.
# ===========================================================================

class TestInvalidFlags:

    def test_f1_unknown_long_flag_does_not_crash(self, tmp_path):
        """
        EG – Unknown long flag.
        '--unknown-flag' is not in calcure's option list.  getopt raises
        GetoptError, which read_parameters_from_user_arguments() catches and
        logs.  The process must not crash.

        Note: calcure produces NO visible error to the user (stderr is empty,
        stdout is empty).  This is a usability issue – the user receives zero
        feedback for a mistyped flag – but it is not a crash.
        """
        result = run_headless(["--unknown-flag"], tmp_path)
        assert result.returncode == 0, (
            f"Expected exit 0 for unknown flag, got {result.returncode}"
        )
        assert "Traceback (most recent call last)" not in result.stderr, (
            "Unknown flag must not produce a raw traceback"
        )

    def test_f2_unknown_short_flag_does_not_crash(self, tmp_path):
        """
        EG – Unknown short flag.
        '-z' is not in calcure's option string.  Same catch logic applies.
        Fault target: getopt exception escaping its handler.
        """
        result = run_headless(["-z"], tmp_path)
        assert result.returncode == 0, (
            f"Expected exit 0 for unknown short flag '-z', got {result.returncode}"
        )

    def test_f3_extra_positional_args_do_not_crash(self, tmp_path):
        """
        EG – Unexpected positional arguments after valid flags.
        getopt collects unrecognised positional args into its second return
        value and ignores them; calcure never inspects that list.
        Fault target: IndexError or unexpected processing of positional args.
        """
        result = run_headless(["-v", "extra_arg_one", "extra_arg_two"], tmp_path)
        assert result.returncode == 0, (
            f"Expected exit 0 with extra positional args, got {result.returncode}"
        )


# ===========================================================================
# Group G – Combined / edge invocations
# Three combinatorial tests: no args, two-flag combo, version + folder.
# ===========================================================================

class TestCombinedInvocations:

    def test_g1_no_arguments_exits_gracefully(self, tmp_path):
        """
        EP – No-args partition.
        Running 'calcure' with zero arguments must exit cleanly (code 0).
        curses.error from the missing terminal is swallowed by cli().
        Fault target: unhandled exception on bare invocation.
        """
        result = run_headless([], tmp_path)
        assert result.returncode == 0, (
            f"Bare 'calcure' invocation should exit 0, got {result.returncode}"
        )

    def test_g2_privacy_and_folder_flags_together(self, tmp_path):
        """
        Combinatorial – Privacy mode (-p) combined with --folder.
        Both flags are processed in the same getopt loop; using them together
        must not interfere with each other or cause a crash.
        Fault target: flag-interaction bug where one flag corrupts the state
        needed by the other.
        """
        data_dir = tmp_path / "priv_data"
        result = run_headless(["-p", f"--folder={data_dir}"], tmp_path)
        assert result.returncode == 0, (
            f"Combined '-p --folder' should exit 0, got {result.returncode}"
        )
        assert data_dir.exists(), (
            "--folder must still create the directory when combined with -p"
        )

    def test_g3_version_and_folder_flags_together(self, tmp_path):
        """
        Combinatorial – Version output (-v) combined with --folder.
        Both flags operate on Config state independently.  The version must
        still appear in stdout AND the folder must be created on disk.
        Fault target: one flag silently swallowing the other's effect.
        """
        data_dir = tmp_path / "version_and_folder"
        result = run_headless(["-v", f"--folder={data_dir}"], tmp_path)
        assert "3.2.1" in result.stdout, (
            "Version string must still be printed when combined with --folder"
        )
        assert data_dir.exists(), (
            "--folder must create its directory even when combined with -v"
        )


# ===========================================================================
# Group H – Data integrity / no silent corruption
# Two tests that guard existing data from being corrupted by failed runs.
# ===========================================================================

class TestDataIntegrity:

    def test_h1_bad_flag_does_not_corrupt_existing_data_files(self, tmp_path):
        """
        Validation – Pre-existing data must survive a failed invocation.
        If a user accidentally passes a bad flag, calcure must not touch the
        data files.  We seed both tasks.csv and events.csv, run with an
        unknown flag, and verify both files are byte-for-byte unchanged.
        Fault target: loaders or savers running (and rewriting files) even
        when the invocation is invalid.
        """
        data_dir = tmp_path / "data"
        cfg_path = tmp_path / "calcure.ini"
        make_config(cfg_path, data_dir)

        tasks_dst  = data_dir / "tasks.csv"
        events_dst = data_dir / "events.csv"
        shutil.copy(FIXTURES / "sample_tasks.csv",  tasks_dst)
        shutil.copy(FIXTURES / "sample_events.csv", events_dst)

        before_tasks  = file_bytes(tasks_dst)
        before_events = file_bytes(events_dst)

        run_headless([f"--config={cfg_path}", "--unknown-flag"], tmp_path)

        assert file_bytes(tasks_dst)  == before_tasks, \
            "tasks.csv was modified after a failed invocation"
        assert file_bytes(events_dst) == before_events, \
            "events.csv was modified after a failed invocation"

    def test_h2_task_saver_uses_atomic_write_via_bak_file(self, tmp_path):
        """
        Validation – The save mechanism must be atomic to prevent partial writes.
        TaskSaverCSV.save() writes to a .bak file first, then renames it
        over the original.  After a successful --task run the .bak file must
        NOT remain on disk (rename succeeded) and the original must be intact.
        Fault target: rename failure leaving a stale .bak that could confuse
        the user or be mistaken for the real data file.
        """
        data_dir = tmp_path / "data"
        cfg_path = tmp_path / "calcure.ini"
        make_config(cfg_path, data_dir)

        run_with_pty(
            [f"--config={cfg_path}", f"--folder={data_dir}", "--task=AtomicCheck"],
            tmp_path,
        )

        assert (data_dir / "tasks.csv").exists(), \
            "tasks.csv must exist after a --task run"
        assert not (data_dir / "tasks.csv.bak").exists(), (
            "tasks.csv.bak must be cleaned up after a successful save "
            "(atomic rename did not complete or .bak was not removed)"
        )


# ===========================================================================
# Group I – Combinatorial CLI Tests (Pairwise)
#
# Factors and levels:
#   F1 Content : --task  |  --event
#   F2 Storage : --folder only  |  --config + --folder
#   F3 Mode    : default  |  -p (privacy)
#   F4 Count   : single write  |  multiple sequential writes
#
# Pairwise covering array (each pair of factor-levels appears at least once):
#   i1  F1=task,  F2=folder,         F3=default,  F4=single
#   i2  F1=event, F2=folder,         F3=default,  F4=single
#   i3  F1=task,  F2=config+folder,  F3=default,  F4=single
#   i4  F1=event, F2=config+folder,  F3=default,  F4=single
#   i5  F1=task,  F2=folder,         F3=privacy,  F4=single
#   i6  F1=event, F2=folder,         F3=privacy,  F4=single
#   i7  F1=task+event, F2=folder,    F3=default,  F4=sequential
#   i8  F1=task,  F2=folder,         F3=default,  F4=multiple ×3
#   i9  F1=task+event, F2=folder×2,  F3=default,  F4=isolation
#   i10 F1=event, F2=folder,         F3=default,  F4=multiple ×2
# ===========================================================================

class TestCombinatorialCLI:
    """
    Pairwise combinatorial tests simulating real user workflows.
    All scenarios model how a developer or student would actually use calcure
    from the command line: deadline reminders, meeting events, work/personal
    folder separation, and privacy mode on a shared terminal.
    """

    def _setup(self, tmp_path, subdir="data"):
        data_dir = tmp_path / subdir
        cfg_path  = tmp_path / "calcure.ini"
        make_config(cfg_path, data_dir)
        return cfg_path, data_dir

    # ── i1: deadline task → custom work folder ──────────────────────────────

    def test_i1_deadline_task_lands_in_work_folder(self, tmp_path):
        """
        CT – F1=task, F2=--folder, F3=default, F4=single
        Scenario: a developer quick-captures a deadline as a task and wants it
        stored in a dedicated work folder, not the default ~/.config/calcure.
        Verifies that --task + --folder route the write to the right directory
        and that the task name is preserved verbatim in tasks.csv.
        """
        cfg, data = self._setup(tmp_path, "work")

        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--task=Submit project report by Friday"],
            tmp_path,
        )

        rows = read_tasks_csv(data)
        # tasks.csv columns: id, status, priority, "name", tag
        assert rows, "tasks.csv must not be empty after --task run"
        names = [r[3].strip('"') for r in rows if len(r) >= 4]
        assert any("Submit project report" in n for n in names), (
            f"Task name must be stored verbatim in the work folder, got rows: {rows}"
        )

    # ── i2: team meeting event → custom work folder ──────────────────────────

    def test_i2_meeting_event_lands_in_work_folder(self, tmp_path):
        """
        CT – F1=event, F2=--folder, F3=default, F4=single
        Scenario: a user adds a recurring team meeting as a one-off event to
        a dedicated work folder.  Verifies that --event + --folder write the
        correct year, month, and day to events.csv.
        """
        cfg, data = self._setup(tmp_path, "work")

        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--event=2025-09-15-SprintPlanningMeeting"],
            tmp_path,
        )

        rows = read_events_csv(data)
        # events.csv columns: id, year, month, day, name, repetition, freq, status
        found = any(
            len(r) >= 5 and r[1] == "2025" and r[2] == "9" and r[3] == "15"
            and "SprintPlanningMeeting" in r[4]
            for r in rows
        )
        assert found, (
            f"Event must have year=2025, month=9, day=15 in the work folder, got: {rows}"
        )

    # ── i3: task with all three flags (config + folder + task) ───────────────

    def test_i3_task_with_config_overrides_default_storage(self, tmp_path):
        """
        CT – F1=task, F2=--config+--folder, F3=default, F4=single
        Scenario: a power user keeps a custom config (e.g. in Dropbox) but
        overrides the data folder at runtime with --folder.  Both flags must
        cooperate: config is read for display settings, --folder routes writes.
        Fault target: --folder silently ignored when --config is also present.
        """
        cfg, data = self._setup(tmp_path, "dropbox_data")

        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--task=Review pull requests before standup"],
            tmp_path,
        )

        rows = read_tasks_csv(data)
        assert rows, "tasks.csv must exist in --folder's directory when --config is also set"
        names = [r[3].strip('"') for r in rows if len(r) >= 4]
        assert any("Review pull requests" in n for n in names), (
            f"Task must land in --folder's directory even when --config is supplied, got: {rows}"
        )

    # ── i4: event with all three flags ───────────────────────────────────────

    def test_i4_event_with_config_and_folder_correct_date_fields(self, tmp_path):
        """
        CT – F1=event, F2=--config+--folder, F3=default, F4=single
        Scenario: user with a shared team config adds a personal flight event.
        Checks that the event date is split into separate year/month/day columns
        and stored in the --folder directory, not the config's default location.
        """
        cfg, data = self._setup(tmp_path, "personal")

        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--event=2025-11-28-FlightToConference"],
            tmp_path,
        )

        rows = read_events_csv(data)
        found = any(
            len(r) >= 5 and r[1] == "2025" and r[2] == "11" and r[3] == "28"
            and "FlightToConference" in r[4]
            for r in rows
        )
        assert found, (
            f"Event date fields (2025/11/28) must be stored correctly, got: {rows}"
        )

    # ── i5: sensitive task under privacy mode ────────────────────────────────

    def test_i5_sensitive_task_stored_despite_privacy_mode(self, tmp_path):
        """
        CT – F1=task, F2=--folder, F3=-p, F4=single
        Scenario: user on a shared office terminal adds a medical appointment
        with -p so titles are hidden on screen, but the task must still be
        persisted to disk so it survives after the terminal session closes.
        Fault target: privacy mode accidentally suppressing the file write.
        """
        cfg, data = self._setup(tmp_path, "personal")

        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "-p", "--task=Doctor appointment at 3pm"],
            tmp_path,
        )

        rows = read_tasks_csv(data)
        assert rows, "-p must not prevent tasks.csv from being written"
        names = [r[3].strip('"') for r in rows if len(r) >= 4]
        assert any("Doctor appointment" in n for n in names), (
            f"Task must be stored even when -p is active, got: {rows}"
        )

    # ── i6: sensitive event under privacy mode ───────────────────────────────

    def test_i6_sensitive_event_stored_despite_privacy_mode(self, tmp_path):
        """
        CT – F1=event, F2=--folder, F3=-p, F4=single
        Scenario: user books a therapy session event with -p active.
        Privacy only hides on-screen rendering; the write to disk must proceed.
        Fault target: -p flag short-circuiting the event-save code path.
        """
        cfg, data = self._setup(tmp_path, "personal")

        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "-p", "--event=2025-10-05-TherapySession"],
            tmp_path,
        )

        rows = read_events_csv(data)
        found = any(
            len(r) >= 5 and r[1] == "2025" and r[2] == "10" and r[3] == "5"
            and "TherapySession" in r[4]
            for r in rows
        )
        assert found, (
            f"Event must be stored even when -p is active, got: {rows}"
        )

    # ── i7: morning workflow – task then event, no cross-contamination ────────

    def test_i7_morning_workflow_task_and_event_stay_in_separate_files(self, tmp_path):
        """
        CT – F1=task+event, F2=--folder, F3=default, F4=sequential
        Scenario: a developer starts the day by (1) adding a task "Fix login
        bug" and then (2) adding a calendar event "Deploy to prod at 14:00".
        Both writes go to the same folder but each must land in the correct
        file.  tasks.csv must contain only the task; events.csv only the event.
        Fault target: saver writing to the wrong file, or second run wiping
        the first write.
        """
        cfg, data = self._setup(tmp_path, "work")

        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--task=Fix login bug before release"],
            tmp_path,
        )
        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--event=2025-08-20-DeployToProd"],
            tmp_path,
        )

        task_rows  = read_tasks_csv(data)
        event_rows = read_events_csv(data)

        task_names  = [r[3].strip('"') for r in task_rows  if len(r) >= 4]
        event_names = [r[4]            for r in event_rows if len(r) >= 5]

        assert any("Fix login bug" in n for n in task_names), (
            f"Task must be in tasks.csv, got: {task_rows}"
        )
        assert any("DeployToProd" in n for n in event_names), (
            f"Event must be in events.csv, got: {event_rows}"
        )
        assert not any("DeployToProd" in n for n in task_names), (
            "Event name must NOT appear in tasks.csv (cross-contamination)"
        )
        assert not any("Fix login bug" in n for n in event_names), (
            "Task name must NOT appear in events.csv (cross-contamination)"
        )

    # ── i8: three tasks back-to-back all accumulate ───────────────────────────

    def test_i8_three_sequential_tasks_all_accumulate(self, tmp_path):
        """
        CT – F1=task, F2=--folder, F3=default, F4=multiple ×3
        Scenario: a developer bulk-adds three tasks from the terminal in quick
        succession (e.g. copying items from a sprint board).  All three must
        appear in tasks.csv – the second and third runs must append, not
        overwrite the file.
        Fault target: TaskSaverCSV truncating the file on each invocation
        instead of loading existing tasks before saving.
        """
        cfg, data = self._setup(tmp_path, "work")

        for task in [
            "Write unit tests for auth module",
            "Fix pagination bug on dashboard",
            "Deploy hotfix to staging environment",
        ]:
            run_with_pty(
                [f"--config={cfg}", f"--folder={data}", f"--task={task}"],
                tmp_path,
            )

        rows  = read_tasks_csv(data)
        names = [r[3].strip('"') for r in rows if len(r) >= 4]

        assert len(names) == 3, (
            f"All 3 tasks must be present after sequential --task runs, got {len(names)}: {names}"
        )
        assert any("unit tests"     in n for n in names), "First task missing"
        assert any("pagination bug" in n for n in names), "Second task missing"
        assert any("hotfix"         in n for n in names), "Third task missing"

    # ── i9: work vs personal folder isolation ────────────────────────────────

    def test_i9_work_and_personal_folders_are_fully_isolated(self, tmp_path):
        """
        CT – F1=task+event, F2=--folder×2 (two separate directories), F3=default
        Scenario: a user maintains separate work and personal calcure instances
        in different folders.  A task written to the work folder must never
        appear in the personal folder, and vice versa.
        Fault target: calcure using a global/shared state that leaks data
        between invocations pointing at different --folder paths.
        """
        work_cfg,     work_data     = self._setup(tmp_path, "work")
        personal_cfg, personal_data = tmp_path / "personal_cfg.ini", tmp_path / "personal"
        make_config(personal_cfg, personal_data)

        run_with_pty(
            [f"--config={work_cfg}", f"--folder={work_data}", "--task=Q3 performance review"],
            tmp_path,
        )
        run_with_pty(
            [f"--config={personal_cfg}", f"--folder={personal_data}", "--task=Book holiday flights"],
            tmp_path,
        )

        work_names     = [r[3].strip('"') for r in read_tasks_csv(work_data)     if len(r) >= 4]
        personal_names = [r[3].strip('"') for r in read_tasks_csv(personal_data) if len(r) >= 4]

        assert any("performance review" in n for n in work_names), (
            f"Work task must appear in work folder, got: {work_names}"
        )
        assert any("holiday flights"    in n for n in personal_names), (
            f"Personal task must appear in personal folder, got: {personal_names}"
        )
        assert not any("holiday flights"    in n for n in work_names), (
            "Personal task must NOT bleed into work folder (isolation failure)"
        )
        assert not any("performance review" in n for n in personal_names), (
            "Work task must NOT bleed into personal folder (isolation failure)"
        )

    # ── i10: two calendar events on different dates both persist ─────────────

    def test_i10_two_events_on_different_dates_both_persist(self, tmp_path):
        """
        CT – F1=event, F2=--folder, F3=default, F4=multiple ×2
        Scenario: a user adds two calendar events on separate days (New Year's
        Day and a project deadline).  Both must survive in events.csv with
        their own distinct date fields – the second write must not overwrite
        the first.
        Fault target: EventSaverCSV recreating the file from scratch on each
        run, losing previously stored events.
        """
        cfg, data = self._setup(tmp_path, "personal")

        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--event=2026-01-01-NewYearsDay"],
            tmp_path,
        )
        run_with_pty(
            [f"--config={cfg}", f"--folder={data}", "--event=2026-03-31-ProjectDeadline"],
            tmp_path,
        )

        rows = read_events_csv(data)
        assert len(rows) == 2, (
            f"Both events must be stored (expected 2 rows, got {len(rows)}): {rows}"
        )

        new_year = any(
            len(r) >= 5 and r[1] == "2026" and r[2] == "1" and r[3] == "1"
            and "NewYearsDay" in r[4]
            for r in rows
        )
        deadline = any(
            len(r) >= 5 and r[1] == "2026" and r[2] == "3" and r[3] == "31"
            and "ProjectDeadline" in r[4]
            for r in rows
        )
        assert new_year,  f"New Year's Day event missing or wrong date, got: {rows}"
        assert deadline,  f"Project deadline event missing or wrong date, got: {rows}"
