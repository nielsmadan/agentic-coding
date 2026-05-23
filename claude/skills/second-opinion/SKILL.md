---
name: second-opinion
description: Get an external AI opinion on a problem or question. Use when you want an outside perspective from Codex.
argument-hint: [--quick] [--timeout=300] [--words=500] <question or context>
---

# Second Opinion Command

Get input from Codex on the current problem or question. By default, iterates if the response lacks confidence.

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
- The `codex` CLI tool must be installed and on PATH. If it is missing, the command fails silently.

## How It Works

### Default Flow (Iterative)

1. Summarize the current problem/question from the conversation (or use what the user provides)
2. Query Codex for its perspective
3. Evaluate confidence in the response
4. If confidence is LOW, re-query with additional context (up to 2 iterations)
5. Present final results with your synthesis

### Quick Mode (`--quick`)

1. Query Codex once
2. Present results immediately without iteration
3. Useful when you just want fast input without refinement

## Execution

### Step 1: Prepare the Context

Extract or use the user's question/problem. If not explicitly provided, summarize:
- What is the current task or problem?
- What approaches are being considered?
- Any relevant file paths or code context

Write the prompt to `.second-opinion.md` in the current working directory (dotfile so it stays out of the way; in the project directory so sandboxed agents like Codex can read it). Use this exact filename for all subsequent steps:

```markdown
Read-only consultation. Do not modify any files.

I need a second opinion: {problem_summary}

Give your perspective in {words} words or less. Focus on:
- Key considerations I might be missing
- Potential issues with the current approach
- Alternative approaches worth considering

If you need more context to give a confident answer, say so clearly.
```

### Step 2: Query Codex

Run Codex using the Bash tool timeout set to `{timeout}` seconds.

Prefix with the `command` builtin: in some shells `codex` is a `sops exec-env`
wrapper function that depends on an interactive-shell variable not present in
the agent's environment; `command` bypasses the wrapper and runs the real
binary, which authenticates via its own on-disk credentials.

```bash
command codex exec -s read-only "Read the file at .second-opinion.md and follow the instructions within it."
```

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

If confidence is LOW:

1. Identify what context is missing based on Codex's feedback
2. Gather additional context (read relevant files, clarify requirements)
3. Overwrite `.second-opinion.md` with enhanced context
4. Re-query Codex using the same file-reference command
5. Can iterate up to 2 times

Skip this step entirely if `--quick` flag was used.

### Step 5: Present Results

Format the responses for the user:

```markdown
## Second Opinion

### Codex
{codex_response}

### My Take
{your brief synthesis - key takeaways and your recommendation}
```

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

Use the `{timeout}` value (default 300s) for each advisor's Bash timeout.

## Error Handling

- If Codex fails, inform the user and offer to retry

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
| Read-only | Yes (enforced) | Configurable |

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
