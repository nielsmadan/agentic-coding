#!/usr/bin/env python3
"""Rank Artificial Analysis models by agentic index vs cost per task and resolve
OpenRouter ids, so a low / mid / high-main / high-fallback trio can be chosen.

The /models page server-renders a full per-model dataset into its RSC payload
(self.__next_f). That payload — not the rendered chart — is the data source.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request

AA_URL = "https://artificialanalysis.ai/models"
OR_URL = "https://openrouter.ai/api/v1/models"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

# Never selectable, per standing instruction.
BANNED_CREATORS = {"xai"}
BANNED_NAME_RE = re.compile(r"grok", re.I)

# Eligible, but only win a tier when clearly ahead of the best alternative.
BIG_LABS = {"openai", "anthropic", "google"}

CACHE_TTL = 6 * 3600


def cache_dir():
    d = os.path.join(os.environ.get("TMPDIR", "/tmp"), "agent-models")
    os.makedirs(d, exist_ok=True)
    return d


def fetch(url, name, no_cache=False, ttl=CACHE_TTL):
    path = os.path.join(cache_dir(), name)
    if not no_cache and os.path.exists(path) and time.time() - os.path.getmtime(path) < ttl:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return body


def rsc_payload(html):
    chunks = re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)</script>', html, re.S)
    out = []
    for c in chunks:
        try:
            out.append(json.loads(c))
        except ValueError:
            pass
    return "".join(out)


def enclosing_object(s, pos):
    depth = 0
    i = pos
    start = None
    while i > 0:
        if s[i] == "}":
            depth += 1
        elif s[i] == "{":
            if depth == 0:
                start = i
                break
            depth -= 1
        i -= 1
    if start is None:
        return None
    depth = 0
    j = start
    instr = False
    esc = False
    while j < len(s):
        ch = s[j]
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
        else:
            if ch == '"':
                instr = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return s[start:j + 1]
        j += 1
    return None


def aa_models(no_cache=False):
    payload = rsc_payload(fetch(AA_URL, "aa-models.html", no_cache))
    seen = set()
    out = []
    for m in re.finditer(r'"agenticIndex"', payload):
        blob = enclosing_object(payload, m.start())
        if not blob:
            continue
        try:
            rec = json.loads(blob)
        except ValueError:
            continue
        if rec.get("id") in seen:
            continue
        seen.add(rec.get("id"))
        out.append(rec)
    return out


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def tokens(s):
    return tuple(sorted(re.findall(r"[a-z0-9]+", (s or "").lower())))


def or_index(no_cache=False):
    data = json.loads(fetch(OR_URL, "openrouter.json", no_cache))["data"]
    exact, entries = {}, []
    for m in data:
        mid = m["id"]
        # ":free" / ":batch" style suffixes are separate SKUs; prefer the bare id.
        if ":" in mid or mid.startswith("~"):
            continue
        name = (m.get("name") or "")
        bare = name.split(":", 1)[1] if ":" in name else name
        exact.setdefault(norm(bare), mid)
        exact.setdefault(norm(mid.split("/", 1)[-1]), mid)
        entries.append({"id": mid, "norm": norm(bare), "tokens": tokens(bare)})
    return {"exact": exact, "entries": entries}


def resolve(rec, idx):
    rel = (rec.get("release") or {})
    cands = [rel.get("name"),
             re.sub(r"\s*\([^)]*\)\s*$", "", rec.get("name") or ""),
             rec.get("slug"), rel.get("slug")]

    for c in cands:
        hit = idx["exact"].get(norm(c))
        if hit:
            return hit

    # Fallback 1: OpenRouter appends a size/variant suffix the AA name omits
    # ("Muse Glimmer" -> "Muse Glimmer 30B"). Only the AA name may be the prefix,
    # never the reverse — otherwise "DeepSeek V4 Pro 0813" would match the 0423
    # build listed as plain "DeepSeek V4 Pro". Must be unambiguous.
    for c in cands:
        n = norm(c)
        if len(n) < 6:
            continue
        hits = {e["id"] for e in idx["entries"] if e["norm"].startswith(n)}
        if len(hits) == 1:
            return hits.pop()

    # Fallback 2: same words, different order ("Claude 4.5 Haiku" vs
    # "Claude Haiku 4.5"). A differing version token still blocks a match.
    for c in cands:
        t = tokens(c)
        if len(t) < 2:
            continue
        hits = {e["id"] for e in idx["entries"] if e["tokens"] == t}
        if len(hits) == 1:
            return hits.pop()

    return None


def cost_per_task(rec):
    v = (rec.get("intelligenceIndexCostPerTask") or {}).get("cost") or {}
    return v.get("total")


def flatten(rec, idx):
    creator = rec.get("creator") or {}
    effort = rec.get("effort") or {}
    return {
        "name": rec.get("name"),
        "release": (rec.get("release") or {}).get("name"),
        "creator": creator.get("slug"),
        "creator_name": creator.get("name"),
        "effort": effort.get("slug"),
        "agentic": rec.get("agenticIndex"),
        "intelligence": rec.get("intelligenceIndex"),
        "cost_per_task": cost_per_task(rec),
        "price_in": rec.get("price1mInputTokens"),
        "price_out": rec.get("price1mOutputTokens"),
        "context": rec.get("contextWindowTokens"),
        "open_weights": rec.get("isOpenWeights"),
        "deprecated": bool(rec.get("deprecated")),
        "aa_url": "https://artificialanalysis.ai/models/" + (rec.get("slug") or ""),
        "openrouter_id": resolve(rec, idx),
    }


def eligible(m):
    """Reasons this model cannot be picked, or [] if it can."""
    why = []
    if m["creator"] in BANNED_CREATORS or BANNED_NAME_RE.search(m["name"] or ""):
        why.append("grok/xai excluded")
    if m["deprecated"]:
        why.append("deprecated")
    if not m["openrouter_id"]:
        why.append("no OpenRouter id")
    if not m["agentic"] or not m["cost_per_task"]:
        why.append("missing agentic index or cost")
    return why


def pareto(models):
    """Frontier on (cost per task ascending, agentic index strictly increasing)."""
    front = []
    best = -1.0
    for m in sorted(models, key=lambda x: x["cost_per_task"]):
        if m["agentic"] > best:
            front.append(m)
            best = m["agentic"]
    return front


def marginals(front):
    out = []
    for a, b in zip(front, front[1:]):
        dc = b["cost_per_task"] - a["cost_per_task"]
        da = b["agentic"] - a["agentic"]
        out.append((a, b, dc / da if da else float("inf")))
    return out


def fmt_table(models, front_ids):
    hdr = (f"{'model':38} {'creator':12} {'eff':5} {'agent':>6} {'intel':>6} "
           f"{'$/task':>7} {'in$':>6} {'out$':>6} {'ctx':>7}  openrouter id")
    lines = [hdr, "-" * len(hdr)]
    for m in models:
        mark = "*" if id(m) in front_ids else " "
        ctx = m["context"] or 0
        lines.append(
            f"{mark}{str(m['name'])[:36]:37} {str(m['creator'])[:11]:12} "
            f"{str(m['effort'] or '-')[:5]:5} {m['agentic']:6.1f} "
            f"{(m['intelligence'] or 0):6.1f} {m['cost_per_task']:7.3f} "
            f"{(m['price_in'] or 0):6.2f} {(m['price_out'] or 0):6.2f} "
            f"{ctx // 1000:6d}k  {m['openrouter_id']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--no-cache", action="store_true", help="bypass the 6h fetch cache")
    ap.add_argument("--all", action="store_true",
                    help="include excluded models in the table")
    args = ap.parse_args()

    idx = or_index(args.no_cache)
    raw = [flatten(r, idx) for r in aa_models(args.no_cache)]

    ok, excluded = [], []
    for m in raw:
        why = eligible(m)
        if why:
            m["excluded_because"] = why
            excluded.append(m)
        else:
            ok.append(m)
    ok.sort(key=lambda m: -m["agentic"])

    front = pareto(ok)
    front_ids = {id(m) for m in front}
    marg = marginals(front)

    if args.json:
        json.dump({
            "candidates": ok,
            "excluded": excluded,
            "frontier": [m["name"] for m in front],
            "frontier_marginal_cost_per_agentic_point": [
                {"from": a["name"], "to": b["name"], "usd_per_point": r}
                for a, b, r in marg],
            "big_labs": sorted(BIG_LABS),
        }, sys.stdout, indent=1)
        print()
        return

    print(f"{len(ok)} selectable models  ({len(excluded)} excluded)")
    print("* = on the cost/agentic Pareto frontier\n")
    print(fmt_table(ok if not args.all else ok + excluded, front_ids))

    print("\nFrontier, cheapest first — marginal cost per agentic index point:")
    for a, b, rate in marg:
        print(f"  {a['name'][:34]:35} -> {b['name'][:34]:35} "
              f"+{b['agentic'] - a['agentic']:5.1f} pts for "
              f"+${b['cost_per_task'] - a['cost_per_task']:.3f}  = ${rate:8.3f}/pt")
    if marg:
        rates = sorted(r for *_, r in marg)
        median = rates[len(rates) // 2]
        cliffs = [(a, b, r) for a, b, r in marg if r > 5 * median]
        if cliffs:
            print("\nCost cliffs (>5x median marginal rate) — do not buy past these:")
            for a, b, r in cliffs:
                print(f"  after {a['name']}: {b['name']} costs ${r:.2f} per extra point")

    if excluded and not args.all:
        print("\nExcluded:")
        for m in excluded:
            print(f"  {str(m['name'])[:44]:45} {', '.join(m['excluded_because'])}")


if __name__ == "__main__":
    main()
