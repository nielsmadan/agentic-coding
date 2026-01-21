#!/usr/bin/env python3
import asyncio
import iterm2
import subprocess
import sys


async def flash_tab(session, duration=5.0):
    """Highlight the tab color to draw attention."""
    # Turn on highlight - bright orange
    change = iterm2.LocalWriteOnlyProfile()
    change.set_tab_color(iterm2.Color(255, 165, 0))
    change.set_use_tab_color(True)
    await session.async_set_profile_properties(change)

    # Keep highlighted
    await asyncio.sleep(duration)

    # Turn off highlight
    reset = iterm2.LocalWriteOnlyProfile()
    reset.set_use_tab_color(False)
    await session.async_set_profile_properties(reset)

def extract_uuid(session_id: str) -> str:
    """Extract UUID from 'w0t0p0:UUID' format."""
    return session_id.split(':', 1)[1] if ':' in session_id else session_id


async def main(connection):
    app = await iterm2.async_get_app(connection)
    session_id = sys.argv[1] if len(sys.argv) > 1 else None

    if not session_id:
        activate_iterm_fallback()
        return

    # get_session_by_id expects just UUID, not w0t0p0:UUID format
    uuid = extract_uuid(session_id)
    session = app.get_session_by_id(uuid)
    if session:
        # First bring iTerm2 to foreground, then select the session
        await app.async_activate(raise_all_windows=False, ignoring_other_apps=True)
        await session.async_activate(select_tab=True, order_window_front=True)
        # Flash the tab to draw attention
        await flash_tab(session)
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
