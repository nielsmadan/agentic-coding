---
name: review-logs
description: Analyze Claude Code session transcripts for failure patterns (retry loops, permission denials, command failures) and suggest concrete fixes. Use when user says "review logs", "session analysis", "failure patterns", or wants to analyze Claude Code error trends.
argument-hint: [--days N] [--project <name>] [--verbose]
---

# Review Logs

Scan recent Claude Code session transcripts for recurring failure patterns and generate actionable recommendations.

## Usage

```
/review-logs
/review-logs --days 7
/review-logs --project juggler
/review-logs --days 30 --verbose
```

## Workflow

### Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- `--days N` — lookback window (default: 14)
- `--project <name>` — filter to a specific project
- `--verbose` — include problematic session IDs for manual review

### Step 2: Run Extraction Script

Find the script using Glob:

```
Glob pattern: **/review-logs/scripts/extract_signals.py
Path: ~/.claude
```

Run the extraction with the discovered path:

```bash
python3 <discovered-path>/extract_signals.py --days <N> [--project <name>] --output /tmp/review-logs-output.json
```

### Step 3: Read and Analyze Output

Read `/tmp/review-logs-output.json` and present findings in severity order:

| Priority | Category | What to Present |
|----------|----------|-----------------|
| Critical | High-frequency retry loops | What's making the model stuck; suggest CLAUDE.md guidance to prevent it |
| Critical | Permission denials (unexpected) | Suggest specific `settings.json` allowlist additions with exact JSON |
| Actionable | Top failing commands | Distinguish fixable patterns from expected failures |
| Actionable | Misbehavior patterns | Suggest CLAUDE.md rules or hook scripts |
| Informational | Error distribution by project | Where problems concentrate |
| Informational | Problematic sessions | Only with `--verbose`; session IDs for manual review |

### Step 4: Generate Recommendations

For each finding, produce a **concrete fix** — not vague advice. Examples:

**Permission denial fix:**
> Add to `settings.json` allowlist:
> ```json
> "Bash(npm run build:*)"
> ```

**Retry loop fix:**
> Add to `CLAUDE.md`:
> ```
> When X fails, do not retry. Instead, check Y first.
> ```

**Misbehavior fix:**
> Add to `CLAUDE.md`:
> ```
> Do not use `gh api` for issue comments. Use `gh issue view <num> --comments` instead.
> ```

### Step 5: Summary

End with a quick stats line:

```
Scanned {N} sessions across {M} projects ({date_range}). Found {errors} errors, {retries} retry loops, {denials} permission denials.
```

## Examples

**Basic 14-day scan:**
```
/review-logs
```
Typical output:
```
## Critical: Retry Loops (3 patterns)
1. `npm run build` retried 4+ times in 6 sessions — model keeps re-running after TypeScript errors instead of fixing them
   → Add to CLAUDE.md: "When `npm run build` fails with type errors, fix the type errors before re-running."

## Actionable: Permission Denials (2 patterns)
1. `Bash(docker compose up)` denied 12 times across 4 sessions
   → Add to settings.json allowlist: "Bash(docker compose *)"

Scanned 47 sessions across 3 projects (2026-02-05 to 2026-02-19). Found 31 errors, 3 retry loops, 14 permission denials.
```

**Project-filtered scan with longer window:**
```
/review-logs --days 30 --project my-app --verbose
```

## Troubleshooting

**No sessions found:**
- Check `--days` value — default is 14, increase if sessions are older
- Check `--project` filter — must match the project directory name exactly (case-sensitive)
- Verify sessions exist at `~/.claude/projects/`

**Script not found:**
- The extraction script lives at `<skill-dir>/scripts/extract_signals.py`
- If Glob finds nothing, the skill may not be installed — re-clone or copy the `review-logs` skill folder into `~/.claude/*/claude/skills/`

**Output too noisy:**
- Expected failures (e.g., git write commands blocked by read-only policy) can dominate results
- Use `--project` to narrow scope to the project you care about
- The script already applies top-N limits, but very active users may still see long output

## Notes

- The extraction script uses only Python stdlib — no dependencies to install
- Sessions are at `~/.claude/projects/*/UUID.jsonl`
- Script filters by file mtime before opening files, so large directories are fast
- Output is capped at ~200-400 lines via top-N limits and truncation
