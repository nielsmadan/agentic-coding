#!/usr/bin/env python3
import iterm2
import subprocess
import sys

async def main(connection):
    app = await iterm2.async_get_app(connection)
    session_id = sys.argv[1] if len(sys.argv) > 1 else None

    if not session_id:
        activate_iterm_fallback()
        return

    session = app.get_session_by_id(session_id)
    if session:
        # First bring iTerm2 to foreground, then select the session
        await app.async_activate(raise_all_windows=False, ignoring_other_apps=True)
        await session.async_activate(select_tab=True, order_window_front=True)
    else:
        # Session not found (closed or invalid), fall back to activating iTerm2
        activate_iterm_fallback()

def activate_iterm_fallback():
    """Fall back to just activating iTerm2 without selecting a specific session."""
    subprocess.run([
        "osascript", "-e",
        'tell application "iTerm2" to activate'
    ], capture_output=True)

if __name__ == "__main__":
    try:
        iterm2.run_until_complete(main)
    except Exception:
        # If Python API fails (not enabled, package missing, etc.), fall back
        activate_iterm_fallback()
