import argparse
import re
import subprocess
import sys

DISCOVER = r"""for python in "$HOME"/Library/Application\ Support/iTerm2/iterm2env*/versions/*/bin/python3; do
  if [ -x "$python" ]; then printf '%s\n' "$python"; fi
done"""

GUEST = r"""
import asyncio
import json
import os
import iterm2
import iterm2.auth

async def main():
    credentials = iterm2.auth.request_cookie_and_key(
        False, "macOS VM test", iterm2.auth.AppKitApplescriptRunner)
    os.environ["ITERM2_COOKIE"], os.environ["ITERM2_KEY"] = credentials.split(" ")
    connection = await asyncio.wait_for(iterm2.Connection.async_create(), 10)
    app = await iterm2.async_get_app(connection)
    if options["action"] == "list":
        print(json.dumps([
            {"window": window.window_id, "tab": tab.tab_id,
             "session": session.session_id,
             "selectedTab": window.current_tab.tab_id == tab.tab_id,
             "currentWindow": app.current_terminal_window is not None and
                 app.current_terminal_window.window_id == window.window_id}
            for window in app.terminal_windows
            for tab in window.tabs for session in tab.sessions]))
        return
    if options["action"] == "new-tab":
        window = app.current_terminal_window
        if window is None:
            window = await iterm2.Window.async_create(connection)
            session = window.current_tab.current_session
        else:
            tab = await window.async_create_tab()
            session = tab.current_session
        print(session.session_id)
        return
    session = app.get_session_by_id(options["session"])
    if session is None:
        raise RuntimeError("Requested iTerm2 session was not found; run list again")
    if options["action"] == "screen":
        contents = await session.async_get_screen_contents()
        print("\n".join(contents.line(i).string.replace("\x00", " ")
                        for i in range(contents.number_of_lines)))
    elif options["action"] == "select":
        await app.async_activate()
        await session.async_activate(select_tab=True, order_window_front=True)
    elif options["action"] == "send":
        await session.async_send_text(options["text"])
        if options["submit"]:
            await asyncio.sleep(0.5)
            await session.async_send_text("\r")

asyncio.run(main())
"""


def runtime(vm, explicit):
    if explicit:
        candidates = [explicit]
    else:
        result = subprocess.run(
            ["tart", "exec", vm, "/bin/sh", "-c", DISCOVER],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        candidates = sorted(
            result.stdout.splitlines(),
            key=lambda path: tuple(map(int, re.findall(r"\d+", path))),
            reverse=True,
        )
    for candidate in candidates:
        result = subprocess.run(
            ["tart", "exec", vm, candidate, "-c", "import iterm2, iterm2.auth"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode == 0:
            return candidate
    raise RuntimeError(
        "No usable managed iTerm2 Python runtime; install it or pass --python"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Control guest iTerm2 through Tart and its Python API"
    )
    parser.add_argument("--vm", required=True)
    parser.add_argument(
        "--python", help="Guest interpreter path; otherwise discover a managed runtime"
    )
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("runtime")
    commands.add_parser("list")
    commands.add_parser("new-tab")
    for action in ("screen", "select", "send"):
        command = commands.add_parser(action)
        command.add_argument("--session", required=True)
        if action == "send":
            command.add_argument("--text", required=True)
            command.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    interpreter = runtime(args.vm, args.python)
    if args.action == "runtime":
        print(interpreter)
        return 0
    payload = "options = " + repr(vars(args)) + "\n" + GUEST
    result = subprocess.run(
        ["tart", "exec", "-i", args.vm, interpreter, "-"],
        check=False,
        input=payload,
        text=True,
        timeout=60,
    )
    return result.returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
