#!/usr/bin/env python3
# Which OpenRouter model should jina-fetch use to extract answers from a fetched page?
# Grades each model on two suites of auto-checkable tasks over three real cached pages.
# usage: bench-models.py <modelfile> <suite: extract5|complex6|relevance|all> [outdir]
#   bench-models.py models.txt all .
# Writes/appends models.csv (per model+suite totals) and models-tasks.csv (per task).
# Needs OPENROUTER_API_KEY and JINA_API_KEY in env (sops-injected) and jina-fetch on PATH.

import importlib.machinery, importlib.util, json, os, pathlib, re, secrets
import subprocess, sys, time, urllib.error, urllib.request

# The prompt, temperature and message shape are imported from the tool rather
# than copied: a benchmark that calls the model differently measures nothing,
# and a copy is a copy that eventually drifts. bin/jina-fetch has no .py suffix,
# so spec_from_file_location needs an explicit loader.
_JF = pathlib.Path(__file__).resolve().parent.parent / "bin" / "jina-fetch"
_loader = importlib.machinery.SourceFileLoader("jina_fetch", str(_JF))
_spec = importlib.util.spec_from_file_location("jina_fetch", _JF, loader=_loader)
jf = importlib.util.module_from_spec(_spec)
# Must be registered before exec: @dataclass resolves its own module by name.
sys.modules["jina_fetch"] = jf
_loader.exec_module(jf)

TEMPERATURE = jf.TEMPERATURE

DOCS = {
    "redis": "https://redis.io/docs/latest/develop/data-types/",
    "so": ("https://stackoverflow.com/questions/11227809/"
           "why-is-processing-a-sorted-array-faster-than-processing-an-unsorted-array"),
    "arxiv": "https://arxiv.org/pdf/1706.03762",
}


def nz(s):
    """Normalise unicode whitespace/punctuation before matching.

    Not cosmetic: gpt-oss-120b answers with U+202F NARROW NO-BREAK SPACE, which made a
    correct answer ('3.5 days on eight NVIDIA P100 GPUs') fail a naive substring check.
    Every grader below compares normalised text.
    """
    for ch in (" ", " ", " ", " "):
        s = s.replace(ch, " ")
    for a, b in (("–", "-"), ("—", "-"), ("−", "-"),
                 ("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"')):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def fetch(url, path):
    if not os.path.exists(path):
        subprocess.run(["jina-fetch", "--raw", "--out", path, url, "x"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return open(path, encoding="utf-8").read()


def anchors_ok(text, doc):
    """Verbatim-anchor task: the phrases must really occur in the page.

    This is the task that separates models. gpt-oss-120b returned
    'You are a victim of branch prediction fail.' -- a plausible-sounding sentence that
    does not appear anywhere on the page.
    """
    lines = [re.sub(r"^\s*[-*\d.)`]+\s*", "", l).strip().strip('`"\'') for l in text.splitlines()]
    lines = [nz(l) for l in lines if len(l.strip()) > 12]
    if not lines:
        return False, "0 phrases"
    nd = nz(doc)
    hits = sum(1 for l in lines if l in nd)
    return hits >= 2, f"{hits}/{len(lines)} exact"


def last_int_is(n):
    def check(text, doc):
        found = re.findall(r"\d+", text)
        return (bool(found) and int(found[-1]) == n), f"final={found[-1] if found else '?'}"
    return check


DECLINED = re.compile(
    r"NO_RELEVANT_CONTENT"
    r"|(does|do|did)\s*not\s*(discuss|mention|contain|address|cover|include|appear|reference)"
    r"|(is|are|was)\s*not\s*(mentioned|discussed|present|found|referenced)"
    r"|no\s*(mention|reference|information|relevant|discussion|content|match)"
    r"|cannot\s*(find|answer|locate)|can'?t\s*(find|answer)"
    r"|nothing\s*(about|regarding|on)|not\s*present|never\s*mentions"
    r"|unable to (find|locate)|does not appear", re.I)


def suite_relevance(d):
    """Off-topic questions with NO escape hatch offered -- the production shape.

    A model that answers these has substituted real, correctly-attributed material
    from the page for an answer the page cannot give. That is the worst failure
    mode of this tool: it converts "no evidence" into "evidence" silently.
    Grade every task by whether the model DECLINED.
    """
    return [
        ("offtopic-plain", d["redis"],
         "What does this page say about Kubernetes horizontal pod autoscaling? "
         "Quote the relevant passage verbatim.",
         lambda t, doc: bool(DECLINED.search(nz(t)))),
        # The exact shape reported in production: compound question where the
        # page really does have "an accepted answer", just not on this subject.
        ("offtopic-compound", d["so"],
         "What does the accepted answer say about Augeas? Quote it verbatim.",
         lambda t, doc: bool(DECLINED.search(nz(t)))),
        ("offtopic-author", d["so"],
         "What does the top comment say about Rust's borrow checker? Quote it verbatim.",
         lambda t, doc: bool(DECLINED.search(nz(t)))),
        # Control: a model that refuses everything would ace the three above.
        ("control-answerable", d["redis"],
         "Which data types are probabilistic? List them.",
         lambda t, doc: "bloom" in t.lower()),
    ]


def suite_extract5(d):
    return [
        ("types", d["redis"],
         "List the Redis data types documented on this page, one per line, nothing else.",
         lambda t, doc: sum(k in t.lower() for k in
                            ["string", "list", "set", "hash", "stream", "json", "bitmap",
                             "geospatial"]) == 8),
        ("why", d["so"], "In one sentence, why is processing the sorted array faster?",
         lambda t, doc: "branch" in t.lower()),
        ("needle-date", d["so"],
         "On what date and at what time was this question asked? Answer exactly as shown.",
         lambda t, doc: bool(re.search(r"jun\w*\s*27,?\s*2012", t, re.I)) and "13:51" in t),
        ("needle-views", d["so"],
         "How many times has this question been viewed, exactly as shown on the page?",
         lambda t, doc: bool(re.search(r"2\.0\s*m|2,0\d\d,\d\d\d|2 million", t, re.I))),
        # No escape hatch offered on purpose. The original version of this task
        # said "if the page does not mention one, reply exactly NOT IN DOCUMENT",
        # which telegraphed the answer -- all 17 models passed and the suite
        # certified a model that then failed this exact shape in production.
        ("trap", d["so"],
         "Which Rust crate does this page recommend for branchless programming? "
         "Quote the recommendation verbatim.",
         lambda t, doc: bool(DECLINED.search(nz(t)))),
    ]


def suite_complex6(d):
    both = (f"===== SOURCE 1: stackoverflow =====\n{d['so']}\n\n"
            f"===== SOURCE 2: arxiv =====\n{d['arxiv']}")
    return [
        ("anchors", d["so"],
         "I will read the source myself. Give 3 short VERBATIM phrases (5-12 words each) "
         "copied exactly from the page that mark where the branchless/bitmask workaround is "
         "discussed. Output only the phrases, one per line, no numbering, no commentary.",
         anchors_ok),
        ("code-verbatim", d["so"],
         "Reproduce exactly the two lines of C++ that implement the branchless sum using a "
         "bitmask (the version using >> 31 and ~t). Output only the two lines of code.",
         lambda t, doc: nz("int t = (data[c] - 128) >> 31;") in nz(t)
                        and nz("sum += ~t & data[c];") in nz(t)),
        # Ground truth 4, verified with: grep -c 'Branchless - Random data' on the page.
        ("count-tables", d["so"],
         "How many separate benchmark result tables on this page contain a row labelled "
         "'Branchless - Random data'? Answer with a number only.",
         last_int_is(4)),
        ("bleu-both", d["arxiv"],
         "Give the BLEU scores the big model achieves on WMT 2014 English-to-German and "
         "English-to-French. Format: EN-DE: <n>, EN-FR: <n>",
         lambda t, doc: "28.4" in t and "41.8" in t),
        ("training-cost", d["arxiv"],
         "How long was the big model trained and on what hardware? One sentence.",
         lambda t, doc: "3.5 day" in nz(t).lower()
                        and re.search(r"(eight|8)\b[^.]{0,40}P100", nz(t), re.I) is not None),
        ("cross-doc", both,
         "These are two different documents. For EACH, name the single specific mechanism it "
         "identifies as the source of its main performance effect. Two lines, one per source.",
         lambda t, doc: bool(re.search(r"branch", t, re.I))
                        and bool(re.search(r"attention|parallel", t, re.I))),
    ]


def call(model, doc, prompt, timeout=300):
    nonce = secrets.token_hex(8)
    body = {"model": model, "temperature": TEMPERATURE,
            "messages": jf.build_messages(jf.fence_document(doc, nonce), prompt, nonce),
            "usage": {"include": True}}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
                 "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r), time.time() - t0, None
    except urllib.error.HTTPError as e:
        return None, time.time() - t0, f"HTTP {e.code} {e.read().decode()[:80]}"
    except Exception as e:
        return None, time.time() - t0, str(e)[:80]


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: bench-models.py <modelfile> <extract5|complex6|relevance|all> [outdir]")
    modelfile, which = sys.argv[1], sys.argv[2]
    outdir = sys.argv[3] if len(sys.argv) > 3 else "."
    models = []
    for line in open(modelfile):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        models.append(line.split("|")[-1])

    os.makedirs(f"{outdir}/pages", exist_ok=True)
    docs = {k: fetch(u, f"{outdir}/pages/{k}.md") for k, u in DOCS.items()}
    suites = {"extract5": suite_extract5(docs), "complex6": suite_complex6(docs),
              "relevance": suite_relevance(docs)}
    if which != "all":
        suites = {which: suites[which]}

    totals, rows = [], []
    for model in models:
        for sname, tasks in suites.items():
            passed, secs, cost = 0, 0.0, 0.0
            for name, doc, prompt, check in tasks:
                payload, el, err = call(model, doc, prompt)
                secs += el
                if err:
                    rows.append((model, sname, name, "error"))
                    print(f"{model:36s} {sname:9s} {name:14s} ERR  {el:6.1f}s {err[:40]}")
                    continue
                text = payload["choices"][0]["message"]["content"].strip()
                cost += (payload.get("usage") or {}).get("cost") or 0.0
                res = check(text, doc)
                note = ""
                if isinstance(res, tuple):
                    res, note = res
                passed += int(bool(res))
                rows.append((model, sname, name, "pass" if res else "fail"))
                print(f"{model:36s} {sname:9s} {name:14s} "
                      f"{'PASS' if res else 'FAIL'} {el:6.1f}s {note:12s}| {nz(text)[:50]}")
            totals.append((model, sname, passed, len(tasks), secs, cost))
            print(f"{model:36s} {sname:9s} {'TOTAL':14s} {passed}/{len(tasks)} "
                  f"{secs:6.1f}s ${cost:.6f}\n")

    for path, header, data in (
        (f"{outdir}/models.csv", "model|suite|passed|of|time|cost",
         [f"{m}|{s}|{p}|{o}|{t:.1f}|{c:.6f}" for m, s, p, o, t, c in totals]),
        (f"{outdir}/models-tasks.csv", "model|suite|task|result",
         ["|".join(r) for r in rows]),
    ):
        new = not os.path.exists(path)
        with open(path, "a") as f:
            if new:
                f.write(header + "\n")
            f.write("\n".join(data) + "\n")
    print(f"wrote {outdir}/models.csv and {outdir}/models-tasks.csv")


if __name__ == "__main__":
    main()
