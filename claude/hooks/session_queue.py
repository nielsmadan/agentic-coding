#!/usr/bin/env python3
"""Centralized session queue management with file locking."""

import fcntl
import sys
import os
from pathlib import Path

QUEUE_FILE = Path.home() / ".claude_session_queue"


def extract_uuid(session_id: str) -> str:
    """Extract UUID from 'w0t0p0:UUID' format."""
    return session_id.split(':', 1)[1] if ':' in session_id else session_id


def read_queue() -> list[str]:
    """Read queue with shared lock."""
    if not QUEUE_FILE.exists():
        return []
    with open(QUEUE_FILE, 'r') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        lines = f.read().strip().split('\n')
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    return [line for line in lines if line.strip()]


def write_queue(sessions: list[str]):
    """Write queue with exclusive lock."""
    with open(QUEUE_FILE, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.write('\n'.join(sessions) + '\n' if sessions else '')
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def add(session_id: str):
    """Add session to queue if not present."""
    sessions = read_queue()
    if session_id not in sessions:
        sessions.append(session_id)
        write_queue(sessions)


def remove(session_id: str):
    """Remove session from queue."""
    sessions = read_queue()
    sessions = [s for s in sessions if s != session_id]
    write_queue(sessions)


def get_next(current_session: str = None) -> str | None:
    """Get next session, skipping current."""
    sessions = read_queue()
    for s in sessions:
        if not current_session or extract_uuid(s) != extract_uuid(current_session):
            return s
    return None


def rotate(session_id: str):
    """Move session to end of queue."""
    sessions = read_queue()
    if session_id in sessions:
        sessions = [s for s in sessions if s != session_id]
        sessions.append(session_id)
        write_queue(sessions)


def count() -> int:
    """Return number of sessions in queue."""
    return len(read_queue())


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    session_id = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("ITERM_SESSION_ID")

    if cmd == "add" and session_id:
        add(session_id)
    elif cmd == "remove" and session_id:
        remove(session_id)
    elif cmd == "next":
        current = sys.argv[2] if len(sys.argv) > 2 else None
        result = get_next(current)
        if result:
            print(result)
        else:
            sys.exit(1)
    elif cmd == "rotate" and session_id:
        rotate(session_id)
    elif cmd == "count":
        print(count())
    elif cmd == "list":
        for s in read_queue():
            print(s)
    else:
        print("Usage: session_queue.py <add|remove|next|rotate|count|list> [session_id]")
        sys.exit(1)
