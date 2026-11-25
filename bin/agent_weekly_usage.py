import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class WeeklyUsage:
    used_percent: float
    observed_at: datetime
    resets_at: datetime | None


def ringleader_usage(*args: str, timeout: int = 10) -> dict:
    command = ["rl", "usage", *args, "--json"]
    if "--refresh" in args and (sops_exec := shutil.which("sops-exec")):
        command.insert(0, sops_exec)
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
            check=False,
        )
        data = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {}
    return data if isinstance(data, dict) else {}


def window(snapshot: dict, observed: str | None, now: datetime) -> WeeklyUsage | None:
    used = snapshot.get("used_percent")
    if type(used) not in (int, float) or not 0 <= used < float("inf") or not observed:
        return None
    try:
        observed_at = datetime.fromisoformat(observed)
        reset = snapshot.get("resets_at")
        resets_at = datetime.fromisoformat(reset) if reset is not None else None
        if observed_at > now or (resets_at is not None and resets_at <= now):
            return None
    except (TypeError, ValueError):
        return None
    return WeeklyUsage(used, observed_at, resets_at)


def current_window(
    provider: str, local: dict, report: dict, now: datetime
) -> WeeklyUsage | None:
    candidates = [window(local, local.get("as_of"), now)]
    candidates.extend(
        window(snapshot, report.get("fetched_at"), now)
        for snapshot in (report.get("data") or {}).get("windows", [])
        if snapshot.get("duration_minutes") == 7 * 24 * 60
        and (
            snapshot.get("key") == "seven_day"
            if provider == "claude"
            else snapshot.get("key", "").startswith("codex:")
        )
    )
    return max(
        (sample for sample in candidates if sample is not None),
        key=lambda sample: sample.observed_at,
        default=None,
    )


def daily_balance(sample: WeeklyUsage, now: datetime, jq_dir: Path) -> str:
    if sample.resets_at is None:
        return "reset time unavailable"
    payload = {
        "used_percentage": sample.used_percent,
        "resets_at": sample.resets_at.timestamp(),
    }
    try:
        output = subprocess.check_output(
            [
                "jq",
                "-r",
                "-L",
                str(jq_dir),
                "--argjson",
                "at",
                str(now.timestamp()),
                'include "weekly-usage"; today_left($at)',
            ],
            input=json.dumps(payload),
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
        points = int(output)
    except (OSError, ValueError, subprocess.SubprocessError):
        return "pace unavailable"
    return f"{points:+d} pp today" if points else "0 pp today"


def weekly_usage_lines(refresh: bool, jq_dir: Path) -> list[str]:
    local = ringleader_usage("windows")
    remote = ringleader_usage(
        "subscription", "--refresh" if refresh else "--cached", timeout=30
    )
    reports = {report["provider"]: report for report in remote.get("results", [])}
    now = datetime.now(UTC)
    lines = []
    for provider, label in (("claude", "Anthropic"), ("codex", "OpenAI")):
        report = reports.get(provider, {})
        usage = current_window(
            provider, local.get(provider, {}).get("weekly", {}), report, now
        )
        if usage is None:
            diagnostic = report.get("diagnostic") or {}
            if diagnostic.get("code") in ("rate_limited", "backoff"):
                summary = "No current weekly snapshot (provider rate limited)"
            else:
                summary = "No current weekly snapshot"
        else:
            details = [
                f"{usage.used_percent:g}% used",
                daily_balance(usage, now, jq_dir),
            ]
            if usage.resets_at is not None:
                details.append(usage.resets_at.astimezone().strftime("resets %a %H:%M"))
            details.append(usage.observed_at.astimezone().strftime("as of %b %d %H:%M"))
            summary = "  ·  ".join(details)
        lines.append(f"  {label:<10} {summary}")
    lines.append(f"  {'Devin':<10} Open /usage in Devin")
    return lines
