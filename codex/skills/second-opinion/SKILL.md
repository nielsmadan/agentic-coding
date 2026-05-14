---
name: second-opinion
description: "Get an external AI opinion on a problem or question. Use when you want a Gemini perspective on the current approach."
argument-hint: "[--quick] [--timeout=300] [--words=500] <question or context>"
---

# Second Opinion

Get input from Gemini on the current problem or question. By default, iterate if the response lacks confidence.

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

## How It Works

### Default Flow (Iterative)

1. Summarize the current problem/question from the conversation, or use what the user provides
2. Query Gemini for its perspective
3. Evaluate confidence in the response
4. If confidence is LOW, re-query with additional context, up to 2 iterations
5. Present final results with your synthesis

### Quick Mode (`--quick`)

1. Query Gemini once
2. Present results immediately without iteration
3. Use this when fast input matters more than refinement

## Execution

### Step 1: Prepare the Context

Extract or use the user's question/problem. If not explicitly provided, summarize:
- What is the current task or problem?
- What approaches are being considered?
- Any relevant file paths or code context

Write the prompt to `.second-opinion.md` in the current working directory. Use this exact filename for all subsequent steps:

```markdown
Read-only consultation. Do not modify any files.

I need a second opinion: {problem_summary}

Give your perspective in {words} words or less. Focus on:
- Key considerations I might be missing
- Potential issues with the current approach
- Alternative approaches worth considering

If you need more context to give a confident answer, say so clearly.
```

### Step 2: Query Gemini

Run Gemini using the Bash tool timeout set to `{timeout}` seconds.

Prefix with the `command` builtin: `gemini` may be a `sops exec-env` wrapper
function that depends on an interactive-shell variable not present in the
agent's environment; `command` bypasses the wrapper and runs the real binary,
which authenticates via its own on-disk credentials. It also needs
`--skip-trust` so it doesn't refuse to run in a working directory it hasn't
been told to trust.

```bash
command gemini -p "Read the file at .second-opinion.md and follow the instructions within it." --approval-mode default --output-format text --skip-trust
```

If `gemini` is unavailable in the current environment, report that clearly rather than failing silently.

If Gemini prints status lines such as `Loaded cached credentials.` before the actual response, ignore those lines and use only the substantive model output.

### Step 3: Evaluate Confidence

After receiving responses, evaluate each for confidence level:

**High Confidence Indicators:**
- Direct, specific recommendations
- References to specific code, files, or patterns
- Clear reasoning with concrete examples
- Definitive statements about approach

**Low Confidence Indicators:**
- Hedging language such as "it depends", "possibly", "might", or "could be"
- Requests for more context
- Generic advice that could apply to any situation
- Uncertainty markers such as "I'm not sure" or "hard to say"
- Questions back to you about the problem

### Step 4: Iterate If Needed (Default Mode Only)

If confidence is LOW:

1. Identify what context is missing based on their feedback
2. Gather additional context by reading relevant files or clarifying requirements from the conversation
3. Overwrite `.second-opinion.md` with enhanced context
4. Re-query Gemini using the same file-reference command
5. Iterate at most 2 times

Skip this step entirely if `--quick` is used.

### Step 5: Present Results

Format the responses for the user:

```markdown
## Second Opinions

### Gemini
{gemini_response}

### My Take
{your brief synthesis - key takeaways and your recommendation}
```

If iteration occurred, note it:

```markdown
*Note: Re-queried {advisor} with additional context after the initial response lacked confidence.*
```

### Step 6: Clean Up

Delete `.second-opinion.md` when finished:

```bash
rm .second-opinion.md
```

## Error Handling

- If Gemini fails, inform the user and offer to retry
- If the environment blocks `gemini`, surface that explicitly instead of silently omitting it

## Examples

```
/second-opinion Should I use useCallback here or is it premature optimization?
/second-opinion Is this the right place to add error handling?
/second-opinion Review my approach to implementing this feature
/second-opinion --quick Just tell me if this pattern looks right
/second-opinion
```

## Troubleshooting

### Advisor times out or fails to respond
**Solution:** Increase the timeout with `--timeout=600` or use `--quick` to skip iteration. If one advisor consistently fails, present the other advisor's response and mention the gap.

### All advisors agree with no diversity of opinion
**Solution:** Rephrase the question to include a specific alternative you want evaluated, or provide more context about the trade-offs you are weighing.
