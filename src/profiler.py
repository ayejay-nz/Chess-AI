import functools
import json
import time
from contextlib import contextmanager
from pathlib import Path

_ACTIVE_PROFILER = None
ENABLE_PROFILING = False

# Number of previous profiler iterations to show in the report table.
PROFILE_COMPARE_PREVIOUS = 3

# JSON file used to persist profiler history across engine runs.
PROFILE_HISTORY_PATH = "../profile_history.json"

# Maximum number of profiler iterations to retain in history.
PROFILE_HISTORY_MAX_ENTRIES = 1000


@contextmanager
def active_profiler(profiler):
    if not ENABLE_PROFILING or profiler is None:
        yield
        return

    global _ACTIVE_PROFILER
    previous = _ACTIVE_PROFILER
    _ACTIVE_PROFILER = profiler
    try:
        yield
    finally:
        _ACTIVE_PROFILER = previous


def timed_call(label, fn, *args, **kwargs):
    if not ENABLE_PROFILING or _ACTIVE_PROFILER is None:
        return fn(*args, **kwargs)
    return _ACTIVE_PROFILER.timed_call(label, fn, *args, **kwargs)


def add_time(label, elapsed_s):
    if ENABLE_PROFILING and _ACTIVE_PROFILER is not None:
        _ACTIVE_PROFILER.add_time(label, elapsed_s)


def bump_node():
    if ENABLE_PROFILING and _ACTIVE_PROFILER is not None:
        _ACTIVE_PROFILER.bump_node()


def profiled(label=None):
    """
    Decorator that records call count and runtime for a function when an
    active profiler is installed via `active_profiler`.
    """

    def decorator(fn):
        if not ENABLE_PROFILING:
            return fn

        metric_label = label or fn.__name__

        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            profiler = _ACTIVE_PROFILER
            if profiler is None:
                return fn(*args, **kwargs)
            return profiler.timed_call(metric_label, fn, *args, **kwargs)

        return wrapped

    return decorator


class SearchProfiler:
    """
    Lightweight per-turn search profiler.
    """

    def __init__(self, enabled=False):
        self.enabled = enabled
        self.times = {}
        self.calls = {}
        self.max_times = {}
        self.nodes = 0

    def add_time(self, label, elapsed_s):
        if not self.enabled:
            return
        self.times[label] = self.times.get(label, 0.0) + elapsed_s
        self.calls[label] = self.calls.get(label, 0) + 1
        self.max_times[label] = max(self.max_times.get(label, 0.0), elapsed_s)

    def timed_call(self, label, fn, *args, **kwargs):
        if not ENABLE_PROFILING or not self.enabled:
            return fn(*args, **kwargs)
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            self.add_time(label, time.perf_counter() - start)

    def bump_node(self):
        if ENABLE_PROFILING and self.enabled:
            self.nodes += 1

    def reset(self):
        self.times = {}
        self.calls = {}
        self.max_times = {}
        self.nodes = 0

    def get_stats(self):
        stats = []
        for label, total in self.times.items():
            calls = self.calls.get(label, 0)
            avg = (total / calls) if calls else 0.0
            stats.append(
                {
                    "label": label,
                    "calls": calls,
                    "total_s": total,
                    "avg_s": avg,
                    "max_s": self.max_times.get(label, 0.0),
                }
            )
        return sorted(stats, key=lambda row: row["total_s"], reverse=True)

    @staticmethod
    def _history_file():
        history_path = Path(PROFILE_HISTORY_PATH)
        if history_path.is_absolute():
            return history_path
        return Path(__file__).resolve().parent / history_path

    def _load_history(self):
        history_file = self._history_file()
        if not history_file.exists():
            return []

        try:
            with history_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError, TypeError):
            return []

        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            entries = payload.get("entries")
            if isinstance(entries, list):
                return entries
        return []

    def _save_history(self, entries):
        history_file = self._history_file()
        payload = {"version": 1, "entries": entries}

        try:
            history_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = history_file.with_suffix(history_file.suffix + ".tmp")
            with tmp_file.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
            tmp_file.replace(history_file)
        except OSError:
            return

    def _snapshot(self, total_time_s, depth, rows, move_number=None):
        nps = int(self.nodes / total_time_s) if total_time_s > 0 else 0
        functions = {}

        for row in rows:
            functions[row["label"]] = {
                "calls": row["calls"],
                "total_ms": row["total_s"] * 1000.0,
                "avg_ms": row["avg_s"] * 1000.0,
                "max_ms": row["max_s"] * 1000.0,
            }

        snapshot = {
            "timestamp": int(time.time()),
            "depth": str(depth),
            "nodes": self.nodes,
            "nps": nps,
            "total_ms": total_time_s * 1000.0,
            "functions": functions,
        }

        if move_number is not None:
            snapshot["move_number"] = move_number

        return snapshot

    @staticmethod
    def _compare_count():
        try:
            return max(0, int(PROFILE_COMPARE_PREVIOUS))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _history_metric(entry, label, metric):
        if not isinstance(entry, dict):
            return "-"

        functions = entry.get("functions")
        if not isinstance(functions, dict):
            return "-"

        function_data = functions.get(label)
        if not isinstance(function_data, dict):
            return "-"

        value = function_data.get(metric)
        if not isinstance(value, (int, float)):
            return "-"

        return f"{value:.3f}"

    @staticmethod
    def _as_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _select_previous_entries(self, history, compare_count, move_number):
        if compare_count <= 0:
            return []

        if move_number is None:
            selected = history[-compare_count:]
            return list(reversed(selected))

        expected = self._as_int(move_number)
        if expected is None:
            selected = history[-compare_count:]
            return list(reversed(selected))

        matching = []
        for entry in history:
            if not isinstance(entry, dict):
                continue
            if self._as_int(entry.get("move_number")) == expected:
                matching.append(entry)

        return list(reversed(matching[-compare_count:]))

    def print_report(self, total_time_s, depth, move_number=None):
        if not ENABLE_PROFILING or not self.enabled:
            return

        nps = int(self.nodes / total_time_s) if total_time_s > 0 else 0
        move_suffix = f" move={move_number}" if move_number is not None else ""
        print(
            f"[PROFILE] total={total_time_s:.4f}s depth={depth} nodes={self.nodes} nps={nps}{move_suffix}",
            flush=True,
        )
        rows = self.get_stats()
        if not rows:
            print("[PROFILE] no function timings recorded", flush=True)
            return

        history = self._load_history()
        compare_count = self._compare_count()
        previous_entries = self._select_previous_entries(history, compare_count, move_number)
        while len(previous_entries) < compare_count:
            previous_entries.append(None)

        headers = ["Function", "Calls", "Total (ms)", "Avg (ms)", "Max (ms)"]
        for idx in range(compare_count):
            headers.extend([f"Prev-{idx + 1} Tot", f"Prev-{idx + 1} Avg"])
        table_rows = []

        for row in rows:
            values = [
                row["label"],
                str(row["calls"]),
                f"{row['total_s'] * 1000.0:.3f}",
                f"{row['avg_s'] * 1000.0:.3f}",
                f"{row['max_s'] * 1000.0:.3f}",
            ]
            for entry in previous_entries:
                values.extend(
                    [
                        self._history_metric(entry, row["label"], "total_ms"),
                        self._history_metric(entry, row["label"], "avg_ms"),
                    ]
                )
            table_rows.append(values)

        widths = [len(col) for col in headers]
        for row in table_rows:
            for i, value in enumerate(row):
                widths[i] = max(widths[i], len(value))

        align = ["<"] + [">"] * (len(headers) - 1)

        def render_line(values):
            formatted = []
            for i, value in enumerate(values):
                formatted.append(f"{value:{align[i]}{widths[i]}}")
            return "| " + " | ".join(formatted) + " |"

        separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"

        print(f"[PROFILE] {separator}", flush=True)
        print(f"[PROFILE] {render_line(headers)}", flush=True)
        print(f"[PROFILE] {separator}", flush=True)
        for row in table_rows:
            print(f"[PROFILE] {render_line(row)}", flush=True)
        print(f"[PROFILE] {separator}", flush=True)

        snapshot = self._snapshot(total_time_s, depth, rows, move_number=move_number)
        history.append(snapshot)

        if PROFILE_HISTORY_MAX_ENTRIES > 0 and len(history) > PROFILE_HISTORY_MAX_ENTRIES:
            history = history[-PROFILE_HISTORY_MAX_ENTRIES:]

        self._save_history(history)
