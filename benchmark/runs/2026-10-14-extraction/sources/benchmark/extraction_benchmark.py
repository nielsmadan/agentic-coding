import concurrent.futures
import hashlib
import json
import math
import random
import secrets
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
import extraction
from extraction_cases import cases, grade


CATALOG_URL = "https://openrouter.ai/api/v1/models"


def get_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def candidate_info(ids):
    catalog = {row["id"]: row for row in get_json(CATALOG_URL)["data"]}
    result = {}
    for model in ids:
        if model not in catalog:
            raise ValueError(f"Model absent from OpenRouter catalog: {model}")
        if model.startswith("x-ai/") or "grok" in model.lower():
            raise ValueError("Grok/xAI models are excluded")
        row = catalog[model]
        if row["context_length"] < 128000:
            raise ValueError(f"Insufficient context: {model}")
        pricing = [row["pricing"], *row["pricing"].get("overrides", [])]
        result[model] = {
            "name": row["name"],
            "context_length": row["context_length"],
            "pricing": row["pricing"],
            "max_input_price": max(
                float(p.get("prompt", row["pricing"]["prompt"])) for p in pricing
            ),
            "max_output_price": max(
                float(p.get("completion", row["pricing"]["completion"]))
                for p in pricing
            ),
        }
        try:
            endpoints = get_json(f"{CATALOG_URL}/{model}/endpoints")["data"][
                "endpoints"
            ]
            result[model]["providers"] = sorted({e["provider_name"] for e in endpoints})
        except (OSError, ValueError, KeyError) as error:
            result[model]["providers"] = None
            result[model]["provider_error"] = str(error)
    return result


def reserve_cost(case, info):
    source_bytes = sum(len(text.encode()) for _, text in case.sources)
    return (source_bytes + len(case.question.encode()) + 4096) * info[
        "max_input_price"
    ] + info["context_length"] * info["max_output_price"]


def measure(model, case, repetition, timeout):
    nonce = secrets.token_hex(8)
    pages = [extraction.Page(name, name, text) for name, text in case.sources]
    fenced = extraction.fence_sources(pages, nonce)
    request = extraction.Extraction(case.question, model, timeout)
    row = {
        "model": model,
        "case": case.name,
        "repetition": repetition,
        "question": case.question,
        "expected": case.expected,
        "source_sha256": hashlib.sha256(json.dumps(case.sources).encode()).hexdigest(),
    }
    started = time.monotonic()
    try:
        payload = extraction.request_extract(fenced, request, model, nonce)
        answer = payload["choices"][0]["message"]["content"].strip()
        usage = payload.get("usage") or {}
        cost = usage.get("cost")
        if (
            not isinstance(cost, (int, float))
            or isinstance(cost, bool)
            or not math.isfinite(cost)
            or cost < 0
        ):
            cost = None
        row.update(
            answer=answer,
            passed=grade(case, answer),
            usage=usage,
            cost_usd=cost,
            response_model=payload.get("model"),
            provider=payload.get("provider"),
            response_id=payload.get("id"),
            finish_reason=payload["choices"][0].get("finish_reason"),
        )
    except extraction.ToolError as error:
        row.update(error=str(error), passed=False, cost_usd=None)
    row["latency_s"] = time.monotonic() - started
    return row


def summarize(rows, ids):
    result = []
    for model in ids:
        group = [row for row in rows if row["model"] == model]
        times = [row["latency_s"] for row in group]
        costs = [row["cost_usd"] for row in group if row["cost_usd"] is not None]
        result.append(
            {
                "model": model,
                "calls": len(group),
                "passed": sum(row["passed"] for row in group),
                "errors": sum("error" in row for row in group),
                "median_s": statistics.median(times) if times else None,
                "max_s": max(times) if times else None,
                "known_cost_usd": sum(costs),
                "unknown_cost_calls": len(group) - len(costs),
                "failures": sorted({row["case"] for row in group if not row["passed"]}),
            }
        )
    return result


def run(opts):
    if (
        opts.repeats < 1
        or opts.workers < 1
        or opts.workers > 3
        or opts.budget <= 0
        or opts.timeout < 1
    ):
        raise ValueError(
            "Require positive repeats, timeout and budget; workers must be 1–3"
        )
    ids = list(
        dict.fromkeys(
            line.strip().split("|")[-1]
            for line in Path(opts.modelfile).read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    )
    if not ids:
        raise ValueError("No candidate models")
    info = candidate_info(ids)
    out = Path(opts.outdir)
    out.mkdir(parents=True, exist_ok=False)
    tasks = [
        (model, case, rep)
        for rep in range(1, opts.repeats + 1)
        for case in cases()
        for model in ids
    ]
    random.Random(42).shuffle(tasks)
    metadata = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "models": info,
        "repeats": opts.repeats,
        "workers": opts.workers,
        "budget_usd": opts.budget,
        "timeout_s": opts.timeout,
        "seed": 42,
        "warmup_calls": 0,
        "temperature": extraction.TEMPERATURE,
        "planned_calls": len(tasks),
        "source_hashes": {
            str(p.relative_to(Path(__file__).resolve().parents[1])): hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
            for p in [
                Path(__file__).resolve(),
                Path(__file__).with_name("extraction_cases.py").resolve(),
                Path(extraction.__file__).resolve(),
            ]
        },
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (out / "fixtures.json").write_text(
        json.dumps(
            [
                {
                    "name": c.name,
                    "sources": c.sources,
                    "question": c.question,
                    "expected": c.expected,
                    "mode": c.mode,
                }
                for c in cases()
            ],
            indent=2,
        )
        + "\n"
    )
    rows = []
    charged = 0.0
    stopped = False
    with (
        concurrent.futures.ThreadPoolExecutor(max_workers=opts.workers) as pool,
        (out / "responses.jsonl").open("w") as log,
    ):
        for offset in range(0, len(tasks), opts.workers):
            batch = tasks[offset : offset + opts.workers]
            reserves = [reserve_cost(case, info[model]) for model, case, _ in batch]
            if charged + sum(reserves) > opts.budget:
                stopped = True
                break
            futures = {
                pool.submit(measure, model, case, rep, opts.timeout): reserve
                for (model, case, rep), reserve in zip(batch, reserves)
            }
            for future in concurrent.futures.as_completed(futures):
                row = future.result()
                row["budget_charge_usd"] = (
                    row["cost_usd"] if row["cost_usd"] is not None else futures[future]
                )
                charged += row["budget_charge_usd"]
                rows.append(row)
                log.write(json.dumps(row) + "\n")
                log.flush()
                print(
                    f"{len(rows)}/{len(tasks)} {row['model']} {row['case']}: {'PASS' if row['passed'] else 'ERROR' if 'error' in row else 'FAIL'} {row['latency_s']:.2f}s",
                    flush=True,
                )
    summary = {
        "complete": len(rows) == len(tasks),
        "budget_stopped": stopped,
        "budget_charge_usd": charged,
        "models": summarize(rows, ids),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if summary["complete"] else 2
