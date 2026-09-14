import fcntl
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.request
from datetime import datetime
from pathlib import Path


RESET = "\033[0m"
SEPARATOR = f"\033[2m │ {RESET}"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
LIMITS_URL = "https://api.factory.ai/api/billing/limits"


def read_json(path):
    try:
        value = json.loads(Path(path).read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def load_limits(api_key, cache_dir, now):
    if not api_key:
        return None
    identity = hashlib.sha256(api_key.encode()).hexdigest()[:16]
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        with (cache_dir / f"statusline-limits-{identity}.json").open("a+") as cache:
            fcntl.flock(cache, fcntl.LOCK_EX | fcntl.LOCK_NB)
            cache.seek(0)
            try:
                saved = json.load(cache)
            except ValueError:
                saved = {}
            checked_at = saved.get("checked_at") if isinstance(saved, dict) else None
            if number(checked_at) and 0 <= now - checked_at < 60:
                limits = saved.get("limits")
                if limits is None or isinstance(limits, dict):
                    return limits
            limits = None
            request = urllib.request.Request(
                LIMITS_URL,
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            )
            try:
                with urllib.request.urlopen(request, timeout=1.5) as response:
                    payload = json.load(response)
                if isinstance(payload, dict) and isinstance(payload.get("limits"), dict):
                    limits = payload["limits"]
            except (OSError, ValueError):
                pass
            cache.seek(0)
            cache.truncate()
            json.dump({"checked_at": now, "limits": limits}, cache)
            return limits
    except OSError:
        return None


def number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def compact(value):
    for scale, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if value >= scale:
            return f"{value / scale:.2f}".rstrip("0").rstrip(".") + suffix
    return f"{value:g}"


def color(text, code):
    return f"\033[{code}m{text}{RESET}"


def countdown(seconds):
    minutes = max(0, int(seconds)) // 60
    days, hours = divmod(minutes // 60, 24)
    if days:
        return f"{days}d{hours}h"
    if hours:
        return f"{hours}h{minutes % 60:02}m"
    return f"{minutes}m"


def window_segment(label, bucket, now, show_reset=False):
    if not isinstance(bucket, dict) or not number(bucket.get("usedPercent")):
        return color(f"{label} ?", "2")
    used = bucket["usedPercent"]
    remaining = None
    if isinstance(bucket.get("windowEnd"), str):
        try:
            remaining = datetime.fromisoformat(bucket["windowEnd"].replace("Z", "+00:00")).timestamp() - now
        except (TypeError, ValueError):
            pass
    if remaining is not None and remaining <= 0:
        return color(f"{label} ?", "2")
    code = 31 if used >= 80 else 33 if used >= 50 else 32
    text = color(f"{label} {used:g}%", code)
    if show_reset and remaining is not None:
        text += color(f" {countdown(remaining)}", 37)
    return text


def usage_segments(session, limits, now):
    standard = (limits or {}).get("standard") or {}
    if not isinstance(standard, dict):
        standard = {}
    segments = [(100, window_segment("7d", standard.get("weekly"), now, True))]
    if standard:
        segments.append((90, window_segment("5h", standard.get("fiveHour"), now)))
    usage = session.get("inclusiveTokenUsage") or session.get("tokenUsage") or {}
    if not isinstance(usage, dict):
        usage = {}
    credits = usage.get("factoryCredits")
    if number(credits):
        segments.append((80, color(f"🪙 {compact(credits)} cr", 36)))
    prompt_counts = [usage.get(key, 0) for key in ("inputTokens", "cacheCreationTokens", "cacheReadTokens")]
    if all(number(value) for value in prompt_counts) and sum(prompt_counts) > 0:
        cached = 100 * prompt_counts[2] / sum(prompt_counts)
        segments.append((70, color(f"♻ {cached:.0f}%", 36)))
    if standard:
        segments.append((30, window_segment("30d", standard.get("monthly"), now)))
    return segments


def display_width(text):
    return sum(
        0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in "WF" else 1
        for char in ANSI.sub("", text)
    )


def fit_usage(segments, width):
    while len(segments) > 1:
        text = SEPARATOR.join(segment for _, segment in segments)
        if display_width(text) <= width:
            return text
        lowest = min(range(len(segments)), key=lambda index: segments[index][0])
        segments = segments[:lowest] + segments[lowest + 1:]
    return segments[0][1]


def terminal_width():
    columns = os.environ.get("COLUMNS", "")
    if columns.isdigit() and int(columns) > 0:
        return int(columns)
    try:
        with open("/dev/tty") as terminal:
            return os.get_terminal_size(terminal.fileno()).columns or 80
    except OSError:
        return 80


def main():
    payload = json.load(sys.stdin)
    session = read_json(payload.get("session_settings_path") or "")
    now = time.time()
    limits = load_limits(os.environ.get("FACTORY_API_KEY"), Path.home() / ".factory/cache", now)
    payload["context_window"] = {"used_percentage": (payload.get("context") or {}).get("percentage", 0)}
    payload["effort"] = {"level": (payload.get("model") or {}).get("reasoning_effort", "")}
    width = terminal_width()
    renderer = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))) / "hooks/statusline.sh"
    rendered = subprocess.run(
        [str(renderer)], input=json.dumps(payload), capture_output=True, text=True,
        env={**os.environ, "COLUMNS": str(width)}, timeout=2, check=True,
    )
    print(rendered.stdout.rstrip())
    print(fit_usage(usage_segments(session, limits, now), max(1, width - 2)), end=RESET)


if __name__ == "__main__":
    main()
