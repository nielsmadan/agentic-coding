# Skill quality rubric

The judgment half of a review. `scripts/lint_skill.py` already covers the mechanical
rules (name format, length limits, XML tags, broken links, orphans, nesting, harness
prefixes, wiring), so do not re-check those by hand. Each item names its source; cite
it in the finding.

## Contents

- Sources
- 1. Triggering (frontmatter)
- 2. Context economy
- 3. Instructions
- 4. Structure and resources
- 5. Scripts
- 6. Fit with this repo
- 7. Evidence from use

## Sources

- **[BP]** Anthropic, *Skill authoring best practices*:
  https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **[SPEC]** Agent Skills specification: https://agentskills.io/specification
- **[CC]** Claude Code, *Extend Claude with skills*: https://code.claude.com/docs/en/skills
- **[CX]** OpenAI Codex, *Build skills*: https://developers.openai.com/codex/skills
- **[SC]** Anthropic's own `skill-creator` skill:
  https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md
- **[REPO]** This repo's `skill-creator` and `docs/skills-and-integration.md`.

## 1. Triggering (frontmatter)

The description is the only text read before the skill loads, so a weak one fails
silently: the skill is simply never chosen.

- States what the skill does **and** when to use it, in third person. [BP][SPEC]
- Leads with the key use case and trigger words: Claude Code truncates the listing
  entry at 1,536 chars and drops descriptions when the listing overflows its
  budget; Codex shortens descriptions first when skills exceed 2% of context.
  [CC][CX]
- Uses the phrases a user would actually type, not internal jargon. [BP][REPO]
- Names its boundaries where a neighbouring skill competes ("Do NOT use for …;
  use X instead"). Check the competing skills' descriptions too, since an overlap
  needs fixing on both sides. [CX][REPO]
- Every "when to use" fact lives in the description, not in a body section. [REPO]

## 2. Context economy

- Every paragraph earns its tokens: no explaining what the model already knows. [BP]
- Body under 500 lines; details move to `references/` loaded on demand. [BP][SPEC]
- The most important instructions sit near the top: after compaction Claude Code
  keeps only the first 5,000 tokens of a re-attached skill. [CC]
- No time-sensitive statements that will turn false; history goes in an
  "old patterns" note or the commit message. [BP]

## 3. Instructions

- Freedom matches fragility: exact commands where a mistake is costly, heuristics
  where many routes work. [BP]
- One default per decision, with an escape hatch, rather than a menu of options. [BP]
- Consistent terminology: one word per concept throughout. [BP]
- Workflows have ordered steps, say what success looks like, and include a
  validate-fix-repeat loop for quality-critical output. [BP]
- Guidance that must hold for the whole task is worded as a standing rule ("after
  every edit"), because the skill is read once and not re-read on later turns. [CC]
- Rules carry their reason. Unexplained ALWAYS/NEVER in capitals is a yellow flag;
  a rule that must hold every time belongs in a hook. [SC][CC]
- Instructions generalize. A rule written to patch one past incident ("in the
  checkout page, …") instead of the class of situation is overfitting. [SC]
- Examples are concrete (real inputs, actions, result), not abstract. [BP]
- No contradictions between sections, and no step that depends on a tool or file
  the skill never tells the agent how to get. [BP]

## 4. Structure and resources

- Every bundled file is reachable from SKILL.md and says when to read it. [BP]
- Reference files over 100 lines open with a contents list, since agents often
  preview with partial reads. [BP]
- One job per skill; a skill doing two unrelated jobs triggers poorly for both. [CX]

## 5. Scripts

- Repeated, deterministic work is a bundled script rather than prose the agent
  re-derives each run. A strong signal: transcripts show agents writing the same
  helper each time. [BP][SC]
- Scripts handle errors themselves and print actionable messages. [BP]
- No unexplained magic constants; dependencies listed and available. [BP]

## 6. Fit with this repo

- Harness-agnostic wording: no single-harness tool names or invocation syntax unless
  inside a `:::` harness block. [REPO]
- Placed in the right scope (global, kit, repo-local). Global skills stay
  free of personal strings because they publish. [REPO]
- Follows the user's global instructions it touches: functional style for new
  scripts, zero-comment default, verification policy (no unsourced "best practice"
  claims). [REPO]

## 7. Evidence from use

Static review finds what a skill says badly; only use shows what it fails to say.
Weigh these above any static finding:

- The user corrected the agent mid-run on something the skill should have covered.
- The agent declared something blocked or impossible that a reasonable step
  would have solved.
- The agent skipped or reordered a step, or re-read the same reference repeatedly
  (a sign it belongs in SKILL.md). [BP]
- A bundled file was never opened across runs (possibly unnecessary). [BP]
- The skill loaded when it should not have, or a request it fits went to another
  skill or none.
