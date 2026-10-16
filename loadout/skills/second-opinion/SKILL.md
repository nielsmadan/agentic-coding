---
name: second-opinion
description: Get external AI opinions on a problem or question. Use when you want diverse perspectives from the agent CLIs you are not running (Claude, Codex, Pi, OpenCode, Droid).
compatibility: Requires pratfall (`prat`) 0.9.1 or newer on PATH plus at least one of claude, codex, pi, opencode or droid besides the one you are running as. Pi and OpenCode advisors need an OpenRouter key.
argument-hint: '[--quick] [--timeout=300] [--words=500] <question or context>'
effort: high
---

# Second Opinion Command

Get input from the available independent advisors on the current problem or question. Consult the advisor CLIs you are *not* — from `claude`, `codex`, `pi`, `opencode` and `droid`, skip whichever one you are running as, and query the rest. By default, iterates if responses lack confidence.

## Usage

```
/second-opinion <question or context>
/second-opinion --quick <question>        # Single pass, no iteration
/second-opinion --words=300 <question>    # Limit response to 300 words
/second-opinion --timeout=120 <question>  # Set timeout to 120s
/second-opinion                           # Uses current conversation context
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--quick` | off | Single pass, no iteration |
| `--timeout` | `300` | Timeout per advisor in seconds |
| `--words` | `500` | Max words per advisor response |

## Gotchas
- `.second-opinion.md` is written to the project directory and is NOT gitignored by default. If cleanup is skipped (error, timeout), it can be accidentally committed.
- The advisor CLIs must be installed. If one is missing or fails, the command continues with the others and that advisor's input is simply absent from the synthesis.
- **The advisors are meant to read the code** — that's the point. Claude, Pi, OpenCode and Droid run with read-only tool sets, so they can read/explore the repo but cannot modify it. Codex has no read-only mode that works inside the nono sandbox, so it runs without one and nono is its boundary; the prompt still tells it not to modify files. Point them at the relevant files in the prompt; reading them stays fast (~15–25s).
- **Every advisor runs through [pratfall](https://github.com/nielsmadan/pratfall) (`prat`).** It normalizes the prompt file, timeout and output across the five CLIs, so this skill does not repeat each one's flags. `prat` execs the real binary off PATH, so no `command` prefix is needed.
- **Still close stdin with `</dev/null` on every advisor command.** prat prepends redirected stdin to the `-f` prompt, so an open-but-silent stdin makes it block *before launching the agent* — and `--timeout` does not fire there, so the call hangs until the Bash tool kills it. Measured: the same command answers in ~13s with `</dev/null` and hangs indefinitely without it.
- **The read-only guards are not in this file.** They live in the `advisor-*` profiles in `~/.config/pratfall/config.toml` (`native_args`, `tools`), because a flag the skill has to retype is a flag the skill can drop. Read that file before changing an advisor, and never invoke a bare `prat cc` / `prat cx` / `prat pi` / `prat oc` / `prat dr` here — `prat cx` in particular renders a plain `codex exec` with **no** sandbox.
- **If the Claude advisor reports `Not logged in · Please run /login`, prefix that one command with `sops-exec`.** `prat` execs the real binary, and Claude Code does not pass its own credential down to subprocesses, so a nested `claude` finds nothing. The other advisors inherit theirs from the session environment and need no prefix. This only bites when `/second-opinion` runs *from* a Claude Code session — where the Claude advisor is skipped anyway.
- **The advisor's identity is the model, not the CLI.** The Pi and OpenCode profiles pin models from two different labs, so their opinions stay independent of each other.
- **Pi** warns `Model "…" not found for provider "openrouter". Using custom model id.` when the model is newer than its cached catalog, then works normally — that warning is not a failure.
- **OpenCode** bills through OpenRouter, so its profile pins an `openrouter/`-prefixed model (`opencode/*` is OpenCode Zen, which has no payment method and errors out). The profile's `--agent plan` is not enough on its own — plan mode can still delegate, which is why the command below also sets `OPENCODE_CONFIG_CONTENT`. prat profiles have no `env` field, so that one stays inline.
- **Headless gotcha:** OpenCode evaluates each part of a compound (`;`/`&&`/`|`) bash command separately and takes the least-permitted verdict; with stdin closed there's no TTY to answer an `ask` prompt, so the whole call is auto-rejected and the run terminates before producing any prose. The classic trigger is a benign `echo ---` separator inside an otherwise-allowed read chain. The prompt template already tells the advisor to avoid chaining; if a run still dies with no output, suspect a chained command hitting an un-allowlisted token.

## How It Works

### Default Flow (Iterative)

1. Summarize the current problem/question from the conversation (or use what the user provides)
2. Query advisors in parallel for their perspectives
3. Evaluate confidence in all responses
4. If confidence is LOW for any advisor, re-query with additional context (up to 2 iterations)
5. Present final results with your synthesis

### Quick Mode (`--quick`)

1. Query all advisors once
2. Present results immediately without iteration
3. Useful when you just want fast input without refinement

## Execution

### Step 1: Prepare the Context

Extract or use the user's question/problem. If not explicitly provided, summarize:
- What is the current task or problem?
- What approaches are being considered?
- **The relevant file paths** — list them so the advisors know where to look. This is what makes the opinion code-aware rather than generic; spend effort here.

Write the prompt to `.second-opinion.md` in the current working directory (dotfile so it stays out of the way; in the project directory so the advisors can read both it and the code it points to). Use this exact filename for all subsequent steps:

```markdown
Read-only consultation. Do not modify any files — but DO read the relevant code in this project before answering.

Do not dispatch subagents or launch other agent CLIs; answer this consultation yourself.

Shell use: prefer your built-in file-reading tool. If you do run shell commands, run ONE simple command at a time — do NOT chain with `;`, `&&`, or `|` and do NOT add `echo` separators. This is a headless session, so any command that would need confirmation is auto-declined, and a single declined command ends the run before you can answer. A chain is only as permitted as its least-permitted part.

I need a second opinion: {problem_summary}

Relevant files/areas to look at: {file_paths}

Read those (and anything else in the project you need) and give your perspective in {words} words or less. Reference specific functions/files so I know what you looked at. Focus on:
- Key considerations I might be missing
- Potential issues with the current approach
- Alternative approaches worth considering

If you need more context to give a confident answer, say so clearly.
```

### Step 2: Query Advisors (in parallel)

Run the advisor commands in parallel — skipping the CLI you are running as. Each
names a `prat` profile that already carries that advisor's model, reasoning level
and read-only guards, and reads the prompt with `-f .second-opinion.md`. All
advisors read the files the prompt points them at, typically answering in
~15–25s; allow longer for a question that spans many files.

Pass `--timeout {timeout}` so prat enforces the deadline itself and reports which
advisor ran out, and give the Bash tool a slightly longer timeout so prat is the
one that trips first. `--timeout` covers the agent run, **not** prat's stdin read,
so it is not a backstop for a missing `</dev/null`.

**Claude:**
```bash
prat advisor-claude --timeout {timeout} -f .second-opinion.md </dev/null
```

**Codex:**
```bash
prat advisor-codex --timeout {timeout} -f .second-opinion.md </dev/null
```

**Pi:**
```bash
prat advisor-pi --timeout {timeout} -f .second-opinion.md </dev/null
```

**OpenCode:** the inline config denies plan mode's task tool and applies only to this process:
```bash
OPENCODE_CONFIG_CONTENT='{"agent":{"plan":{"permission":{"task":"deny"}}}}' prat advisor-opencode --timeout {timeout} -f .second-opinion.md </dev/null
```

**Droid:** the profile pins Gemini 4 Argon at high effort and permits only file reading and search:
```bash
prat advisor-droid --timeout {timeout} -f .second-opinion.md </dev/null
```

Use the profiles as configured, including in `--quick` mode. Change an advisor's
model or reasoning level only when the user explicitly requests it, and change it
in `~/.config/pratfall/config.toml` rather than by adding a `--model` / `--effort`
flag here. If a selected model or reasoning level is unavailable, report that
advisor as unavailable and continue with the others.

If `prat` is missing, say so and stop rather than falling back to raw CLI
invocations — the read-only guards live in its profiles.

### Step 3: Evaluate Confidence

After receiving responses, evaluate each for confidence level:

**High Confidence Indicators:**
- Direct, specific recommendations
- References to specific code, files, or patterns
- Clear reasoning with concrete examples
- Definitive statements about approach

**Low Confidence Indicators:**
- Hedging language: "It depends", "possibly", "might", "could be"
- Requests for more context: "I'd need to see", "without more context"
- Very generic advice that could apply to any situation
- Uncertainty markers: "I'm not sure", "hard to say"
- Questions back to you about the problem

### Step 4: Iterate If Needed (Default Mode Only)

If confidence is LOW for any advisor:

1. Identify what context is missing based on their feedback
2. Gather additional context (read relevant files, clarify requirements)
3. Overwrite `.second-opinion.md` with enhanced context
4. Re-query the low-confidence advisor using the same command
5. Can iterate up to 2 times per advisor

Skip this step entirely if `--quick` flag was used.

### Step 5: Present Results

Format the responses for the user:

```markdown
## Second Opinions

### {advisor 1}
{advisor_1_response}

### {advisor 2}
{advisor_2_response}

### {advisor 3}
{advisor_3_response}

### {advisor 4}
{advisor_4_response}

### My Take
{your brief synthesis - where they agree, disagree, and your recommendation}
```

Include one heading per responding advisor.

Name each advisor heading after the CLI and the model it ran (e.g. `Codex`, `Pi (<model>)`).

If iteration occurred, note it:
```markdown
*Note: Re-queried {advisor} with additional context after initial response lacked confidence.*
```

### Step 6: Clean Up

Delete `.second-opinion.md` using the Bash tool:
```bash
rm .second-opinion.md
```

## Timeouts

Pass the `{timeout}` value (default 300s) to each advisor as `prat --timeout`,
and set the Bash tool's own timeout a little higher so prat trips first and can
name the advisor that ran out. `[defaults] timeout` in the prat config is the
fallback when `--timeout` is omitted.

## Error Handling

- If one advisor fails, continue with the others
- If all fail, inform the user and offer to retry

## Key Differences from /debate

| Aspect | /second-opinion | /debate |
|--------|-----------------|---------|
| Rounds | 1-3 (with iteration) | 1-10 |
| Quick mode | Yes (`--quick`) | No |
| State files | None | Full state tracking |
| Session mgmt | No sessions | UUID tracking |
| Output files | None | rounds/, synthesis.md |
| Purpose | Quick check | Deep analysis |
| Speed | ~1-3 min | 5-30 min |
| Read-only | Enforced for Claude, Pi, OpenCode, Droid; Codex by prompt, inside nono | Configurable |

## Examples

```
/second-opinion Should I use useCallback here or is it premature optimization?
/second-opinion Is this the right place to add error handling?
/second-opinion Review my approach to implementing this feature
/second-opinion --quick Just tell me if this pattern looks right
/second-opinion  # Uses current context from conversation
```

## Troubleshooting

### Advisor times out or fails to respond
**Solution:** Increase the timeout with `--timeout=600` or use `--quick` to skip iteration.
