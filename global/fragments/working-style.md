## Code Comments

Default to zero comments. Never write JSDoc-style `/** … */` blocks, multi-paragraph docstrings, or multi-line comment blocks — names and signatures are the documentation. Don't narrate what routine changes do (config flips, version bumps, standard fixes); that rationale belongs in the commit message, not the code. Reserve a single terse `//` line for the genuinely non-obvious: a workaround for a specific bug, a surprising invariant, a "must stay last" ordering. This governs *new* code you write — don't strip a repo's existing comments unless asked.

**Never comment on what is not there.** No note saying what was removed, what the code used to do, why an alternative was rejected, or that something is deliberately absent. That belongs in the commit message. A reader arriving later has no memory of the thing you are contrasting against, so the note costs them attention and teaches them nothing. The one exception is an absence that is load-bearing and reads as an oversight — then state the constraint in one line, never the history.

## Writing Tests

**Assert what the code does, not what it does not do.** The set of things absent from any output is infinite, so `expect(button).not.toHaveTextContent('Administrator')` pins nothing — it passes for every wrong implementation that also happens not to print that word. Write the positive assertion instead.

A negative assertion earns its place only when the absence *is* the behaviour under test and names a specific thing that would otherwise have happened: `expect(write).not.toHaveBeenCalled()` after a rejected request, or no sidebar in a no-access state. If you cannot name what would have produced the thing, do not assert it is missing.

## Preserve User Edits

When a system-reminder shows the user modified a file (especially "the change was intentional"), treat those edits as load-bearing. When you later edit that file for an unrelated reason, do not reword their comments, rename their variables, or reformat lines they chose to format a certain way. If a refactor genuinely requires changing one of their choices, flag it out loud first — never silently revert it inside a larger edit. When in doubt, keep their version.

## Questions vs. Actions

When the user's message is a question (asking for explanation, comparison, or analysis), respond with text only. Code edits require an explicit imperative ("fix this", "change X", "make Y do Z"). A stop-hook firing on a phrase inside your explanation is not authorization to start editing — at most, rephrase. Confirm the prior turn actually asked for a change before touching files.

## Finishing Tasks

When the user says to finish a task completely, drive it to actual completion — resolve every remaining item (implement it, or make and record an explicit decision) before surfacing what's next. Don't end turns by re-proposing the next phase or asking "want me to move on to X?" while the stated task is unfinished. If a genuine decision is needed to finish, ask that — don't offer to skip ahead.
