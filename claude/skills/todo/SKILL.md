---
name: todo
description: Capture a todo as a file in docs/todo/, or pick up the top todo and implement it. With arguments, creates a new todo. Without arguments, picks the highest-priority most-recent todo and makes the change. Supports --prio flag (1-5, default 3).
argument-hint: [--prio N] <description>
---

# Todo: $ARGUMENTS

## Usage

```
/todo                                    # Pick up top todo and implement it
/todo fix the typo in the readme         # Create todo (priority 3)
/todo --prio 1 fix login crash on iOS    # Create todo (priority 1)
/todo --prio 5 consider adding dark mode # Create todo (priority 5)
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--prio` | `3` | Priority 1-5 (1 = highest, 5 = lowest) |

## Workflow

### 0. Route

If $ARGUMENTS is empty or blank → go to **Pick Up Todo** workflow below.
Otherwise → continue to step 1 (Create Todo).

---

## Create Todo

### 1. Parse

Extract `--prio` value (default 3) and the todo description from $ARGUMENTS.

### 2. Assess Complexity

- **Simple** (clear, self-contained, single concern): Skip to step 4
- **Complex** (multiple areas, ambiguous scope, needs context): Continue to step 3

### 3. Expand (complex only)

Ask clarifying questions via AskUserQuestion if the intent is ambiguous. Then gather context:
- Check `docs/` for related documentation
- Read relevant source files to understand the current state
- Identify affected areas

Write a short expanded description focused on what the change looks like for the user — not technical implementation details. Include a `## Context` section listing relevant files or areas.

### 4. Write File

Create `docs/todo/` if it doesn't exist. Write to:

```
docs/todo/{priority}-{YYYY-MM-DD}-{slug}.md
```

Where `{slug}` is the description lowercased, spaces replaced with hyphens, non-alphanumeric characters removed.

**Simple format:**
```markdown
# {Description}
```

**Complex format:**
```markdown
# {Description}

{Expanded description of what the user-facing change is}

## Context
- {relevant files or areas}
```

### 5. Confirm

Print a one-liner to the conversation: the file path and the priority level.

---

## Pick Up Todo

### 1. Find Top Todo

List files in `docs/todo/` sorted by filename (lowest priority number first, then most recent date). The first file is the top todo. If `docs/todo/` is empty or doesn't exist, tell the user there are no todos.

### 2. Read and Present

Read the todo file. Print a short summary of what you're about to do and ask the user to confirm.

### 3. Mark In Progress

Prepend `> **Status: In Progress**` to the todo file (before the `#` heading). This makes the file appear in `git status` as a visible reminder.

### 4. Implement

Make the change described in the todo. Follow normal development workflow — read relevant code, ask clarifying questions if needed, implement, and verify.

When creating implementation tasks (TaskCreate), always include a final task: **"Remove todo file `{path}`"** — this ensures cleanup is tracked and won't be forgotten.

### 5. Clean Up

When all tasks are complete and changes are verified, delete the todo file from `docs/todo/`.
