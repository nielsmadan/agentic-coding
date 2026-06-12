#!/usr/bin/env python3
"""Search past Claude Code session transcripts for a piece of context.

Claude Code stores one folder per project under ~/.claude/projects, named by
encoding the project's absolute cwd (every non-alphanumeric char -> '-'). Each
folder holds .jsonl session transcripts.

This tool finds candidate sessions that mention a query, across the current
project AND its sibling checkouts (e.g. wrksp/app/dev1, wrksp/app/dev2, ...),
so you can then read the matching transcript(s) to recover prior context.

Output is grouped by session, newest first: folder, transcript path, AI title,
git branch, timestamp range, match count, and snippets. Open the transcript
path with your file reader to read the full prior context.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

HOME = os.path.expanduser("~")
DEFAULT_PROJECTS_DIR = os.path.join(HOME, ".claude", "projects")


def encode_path(path: str) -> str:
    """Encode an absolute path the way Claude Code names project folders."""
    return re.sub(r"[^a-zA-Z0-9]", "-", path)


def resolve_folders(projects_dir, cwd, scope, app):
    """Return list of (folder_name, abs_folder_path) to search."""
    all_dirs = sorted(
        d for d in os.listdir(projects_dir)
        if os.path.isdir(os.path.join(projects_dir, d))
    )
    if app:
        sub = app.lower()
        chosen = [d for d in all_dirs if sub in d.lower()]
    elif scope == "all":
        chosen = all_dirs
    elif scope == "current":
        enc = encode_path(os.path.abspath(cwd))
        chosen = [d for d in all_dirs if d == enc]
    else:  # siblings (default): current folder + everything sharing its parent
        enc = encode_path(os.path.abspath(cwd))
        parent_enc = encode_path(os.path.dirname(os.path.abspath(cwd)))
        prefix = parent_enc + "-"
        chosen = [d for d in all_dirs if d == enc or d.startswith(prefix)]
    return [(d, os.path.join(projects_dir, d)) for d in chosen]


def text_of(rec):
    """Flatten a transcript record into searchable text."""
    parts = []
    for k in ("aiTitle", "lastPrompt", "slug"):
        v = rec.get(k)
        if isinstance(v, str):
            parts.append(v)
    msg = rec.get("message")
    if isinstance(msg, dict):
        c = msg.get("content")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            for block in c:
                if not isinstance(block, dict):
                    parts.append(str(block))
                    continue
                t = block.get("type")
                if t in ("text", "thinking"):
                    parts.append(block.get("text") or block.get("thinking") or "")
                elif t == "tool_use":
                    parts.append(block.get("name", ""))
                    parts.append(json.dumps(block.get("input", "")))
                elif t == "tool_result":
                    rc = block.get("content")
                    if isinstance(rc, str):
                        parts.append(rc)
                    elif isinstance(rc, list):
                        for b in rc:
                            if isinstance(b, dict):
                                parts.append(b.get("text", ""))
    elif isinstance(msg, str):
        parts.append(msg)
    tr = rec.get("toolUseResult")
    if isinstance(tr, str):
        parts.append(tr)
    return "\n".join(p for p in parts if p)


def snippet(text, m, ctx):
    start = max(0, m.start() - ctx)
    end = min(len(text), m.end() + ctx)
    s = text[start:end].replace("\n", " ").strip()
    if start > 0:
        s = "…" + s
    if end < len(text):
        s = s + "…"
    return re.sub(r"\s+", " ", s)


def scan_file(path, pattern, raw_substr, ctx, max_snippets):
    """Return dict of session info if the file matches, else None."""
    info = {
        "title": None, "branch": None, "cwd": None,
        "first_ts": None, "last_ts": None,
        "matches": 0, "snippets": [],
    }
    try:
        with open(path, "r", errors="replace") as fh:
            for line in fh:
                if not line.strip():
                    continue
                # Every record is parsed for metadata (title/branch/cwd are taken
                # from the first record that carries them). raw_substr is a cheap
                # literal pre-check that lets us skip the match scan on lines that
                # can't contain the query; it's only set for queries where the raw
                # line and the decoded text agree (see main()).
                skip_scan = raw_substr and (raw_substr not in line.lower())
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = rec.get("timestamp")
                if ts:
                    if info["first_ts"] is None:
                        info["first_ts"] = ts
                    info["last_ts"] = ts
                if info["title"] is None:
                    info["title"] = rec.get("aiTitle") or rec.get("slug")
                if info["branch"] is None and rec.get("gitBranch"):
                    info["branch"] = rec.get("gitBranch")
                if info["cwd"] is None and rec.get("cwd"):
                    info["cwd"] = rec.get("cwd")
                if skip_scan:
                    continue
                text = text_of(rec)
                for m in pattern.finditer(text):
                    info["matches"] += 1
                    if len(info["snippets"]) < max_snippets:
                        role = rec.get("type", "?")
                        info["snippets"].append(f"[{role}] {snippet(text, m, ctx)}")
    except OSError:
        return None
    return info if info["matches"] else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?", help="regex to search for in transcripts")
    ap.add_argument("--cwd", default=os.getcwd(), help="project dir to base sibling scope on (default: cwd)")
    ap.add_argument("--scope", choices=["siblings", "current", "all"], default="siblings",
                    help="siblings (default): current folder + sibling checkouts sharing its parent")
    ap.add_argument("--app", help="search every project folder whose name contains this substring (overrides --scope)")
    ap.add_argument("--projects-dir", default=DEFAULT_PROJECTS_DIR)
    ap.add_argument("--case-sensitive", action="store_true")
    ap.add_argument("--context", type=int, default=160, help="snippet context chars each side (default 160)")
    ap.add_argument("--max-snippets", type=int, default=3, help="snippets per session (default 3)")
    ap.add_argument("--days", type=int, help="only search transcripts modified within the last N days")
    ap.add_argument("--list-folders", action="store_true", help="print the resolved search scope and exit")
    args = ap.parse_args()

    if not os.path.isdir(args.projects_dir):
        sys.exit(f"projects dir not found: {args.projects_dir}")

    folders = resolve_folders(args.projects_dir, args.cwd, args.scope, args.app)
    if not folders:
        sys.exit("No matching project folders. Try --app NAME or --scope all.")

    broad = (not args.app and args.scope == "siblings"
             and os.path.dirname(os.path.abspath(args.cwd)) == HOME)
    if broad:
        print(f"Note: '{args.cwd}' sits directly under $HOME, so 'siblings' matches "
              f"all {len(folders)} projects. Narrow with --app NAME if you know the app.",
              file=sys.stderr)

    if args.list_folders:
        print(f"Scope: {'app=' + args.app if args.app else args.scope}  ({len(folders)} folders)")
        for name, _ in folders:
            print(f"  {name}")
        return

    if not args.query:
        ap.error("query is required (unless --list-folders)")

    flags = 0 if args.case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(args.query, flags)
    except re.error as e:
        sys.exit(f"bad regex: {e}")
    # The literal pre-filter (scan_file) tests the query against the raw JSONL
    # line, but matching runs against the *decoded* text. Only enable it when the
    # two can't diverge: case-insensitive, no regex metacharacters, and no chars
    # that JSON escapes (quotes, backslash, control chars) — otherwise the
    # pre-filter could skip a line the regex would actually match.
    raw_substr = args.query.lower()
    if (args.case_sensitive
            or re.search(r"[\\^$.|?*+()\[\]{}]", args.query)
            or re.search(r'["\t\n\r]', args.query)):
        raw_substr = None

    cutoff = None
    if args.days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    results = []
    for name, folder in folders:
        for fn in os.listdir(folder):
            if not fn.endswith(".jsonl"):
                continue
            path = os.path.join(folder, fn)
            if cutoff:
                mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
                if mtime < cutoff:
                    continue
            info = scan_file(path, pattern, raw_substr, args.context, args.max_snippets)
            if info:
                info["folder"] = name
                info["path"] = path
                results.append(info)

    results.sort(key=lambda r: r["last_ts"] or "", reverse=True)

    scope_desc = f"app={args.app}" if args.app else args.scope
    print(f"Searched {len(folders)} folder(s) [scope: {scope_desc}] for /{args.query}/")
    if not results:
        print("No matching sessions. Widen with --scope all or --app NAME, or try a different query.")
        return
    print(f"Found {len(results)} matching session(s), newest first:\n")
    for r in results:
        print("=" * 70)
        print(f"folder : {r['folder']}")
        print(f"path   : {r['path']}")
        if r["title"]:
            print(f"title  : {r['title']}")
        if r["cwd"]:
            print(f"cwd    : {r['cwd']}")
        if r["branch"]:
            print(f"branch : {r['branch']}")
        print(f"when   : {r['first_ts']}  →  {r['last_ts']}")
        print(f"matches: {r['matches']}")
        for s in r["snippets"]:
            print(f"  • {s[:400]}")
        print()


if __name__ == "__main__":
    main()
