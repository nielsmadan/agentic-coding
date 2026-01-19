#!/bin/bash

# Required for Raycast Script Commands
# @raycast.schemaVersion 1
# @raycast.title Next Claude Session
# @raycast.mode silent
# @raycast.icon 🤖

# Find the right Python (with iterm2 module)
PYTHON3_PATH="$(command -v python3)"
if command -v pyenv &> /dev/null; then
    PYTHON3_PATH="$(pyenv which python3 2>/dev/null || echo "$PYTHON3_PATH")"
fi

exec "$PYTHON3_PATH" - "$@" << 'PYTHON_SCRIPT'
import os
import sys
from pathlib import Path

# Try to import iterm2, but don't fail if not available
try:
    import iterm2
    HAS_ITERM2 = True
except ImportError:
    HAS_ITERM2 = False

PRIMARY_QUEUE = Path.home() / ".claude_session_queue"
COMPLETED_QUEUE = Path.home() / ".claude_completed_queue"
HOOKS_DIR = Path.home() / ".claude" / "hooks"


def read_queue(queue_file: Path) -> list[str]:
    """Read queue file and return list of session IDs (excluding empty lines)."""
    if not queue_file.exists():
        return []
    lines = queue_file.read_text().strip().split('\n')
    return [line for line in lines if line.strip()]


def write_queue(queue_file: Path, sessions: list[str]):
    """Write session IDs to queue file."""
    queue_file.write_text('\n'.join(sessions) + '\n' if sessions else '')


def rotate_to_end(sessions: list[str], session_id: str) -> list[str]:
    """Move a session to the end of the list."""
    if session_id in sessions:
        sessions = [s for s in sessions if s != session_id]
        sessions.append(session_id)
    return sessions


def extract_uuid(session_id: str) -> str:
    """Extract UUID from session ID (handles both 'w0t0p0:UUID' and plain 'UUID' formats)."""
    if ':' in session_id:
        return session_id.split(':', 1)[1]
    return session_id


def session_ids_match(id1: str, id2: str) -> bool:
    """Compare session IDs, handling different formats."""
    return extract_uuid(id1) == extract_uuid(id2)


async def get_current_session_id(connection) -> str | None:
    """Get the session ID of the currently focused iTerm2 session."""
    app = await iterm2.async_get_app(connection)
    window = app.current_terminal_window
    if window and window.current_tab:
        session = window.current_tab.current_session
        if session:
            return session.session_id
    return None


async def activate_session(connection, session_id: str):
    """Activate a specific iTerm2 session."""
    app = await iterm2.async_get_app(connection)
    # get_session_by_id expects just the UUID, not the w0t0p0: prefix
    session = app.get_session_by_id(extract_uuid(session_id))
    if session:
        await app.async_activate(raise_all_windows=False, ignoring_other_apps=True)
        await session.async_activate(select_tab=True, order_window_front=True)

        # Flash tab color for 5 seconds
        import asyncio
        change = iterm2.LocalWriteOnlyProfile()
        change.set_tab_color(iterm2.Color(255, 165, 0))
        change.set_use_tab_color(True)
        await session.async_set_profile_properties(change)

        await asyncio.sleep(5.0)

        reset = iterm2.LocalWriteOnlyProfile()
        reset.set_use_tab_color(False)
        await session.async_set_profile_properties(reset)
        return True
    return False


async def main_async(connection):
    """Main logic using iTerm2 connection."""
    # Get currently focused session
    current_session = await get_current_session_id(connection)

    # Read queues
    primary_sessions = read_queue(PRIMARY_QUEUE)
    completed_sessions = read_queue(COMPLETED_QUEUE)

    # Find next session to activate (skip current)
    target_session = None
    queue_type = None

    # Check primary queue first
    for session_id in primary_sessions:
        if not current_session or not session_ids_match(session_id, current_session):
            target_session = session_id
            queue_type = "primary"
            break

    # Fall back to completed queue (most recent = last in file)
    if not target_session:
        for session_id in reversed(completed_sessions):
            if not current_session or not session_ids_match(session_id, current_session):
                target_session = session_id
                queue_type = "completed"
                break

    if not target_session:
        print("No sessions waiting")
        return

    # Activate the session
    success = await activate_session(connection, target_session)
    if not success:
        # Session not found, remove it from queue
        if queue_type == "primary":
            primary_sessions = [s for s in primary_sessions if s != target_session]
            write_queue(PRIMARY_QUEUE, primary_sessions)
        else:
            completed_sessions = [s for s in completed_sessions if s != target_session]
            write_queue(COMPLETED_QUEUE, completed_sessions)
        print("Session not found, removed from queue")
        return

    # Update queues
    if queue_type == "primary":
        # Rotate to end
        primary_sessions = rotate_to_end(primary_sessions, target_session)
        write_queue(PRIMARY_QUEUE, primary_sessions)
    else:
        # Remove from completed queue
        completed_sessions = [s for s in completed_sessions if s != target_session]
        write_queue(COMPLETED_QUEUE, completed_sessions)

    # Show status
    primary_count = len(read_queue(PRIMARY_QUEUE))
    completed_count = len(read_queue(COMPLETED_QUEUE))

    if primary_count > 0:
        print(f"{primary_count} waiting for input")
    elif completed_count > 0:
        print(f"{completed_count} completed")
    else:
        print("Queue empty")


def main():
    if not HAS_ITERM2:
        print("iterm2 module not installed")
        sys.exit(1)

    try:
        iterm2.run_until_complete(main_async)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
PYTHON_SCRIPT
