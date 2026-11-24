import fcntl
import json
import sys
import tempfile
from pathlib import Path


def would_lower_usage(previous: dict, snapshot: dict) -> bool:
    try:
        last = previous["rate_limits"]["seven_day"]
        current = snapshot["rate_limits"]["seven_day"]
        return (
            last["resets_at"] == current["resets_at"]
            and current["used_percentage"] < last["used_percentage"] <= 100
        )
    except (KeyError, TypeError):
        return False


def save_usage(path: Path, snapshot: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            previous = {}
        if would_lower_usage(previous, snapshot):
            return
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=path.parent,
            prefix=".claude-limits.",
            encoding="utf-8",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            try:
                json.dump(snapshot, handle)
                handle.flush()
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    save_usage(Path(sys.argv[1]), json.load(sys.stdin))
