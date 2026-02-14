---
name: todo
description: Capture a todo in Todoist, or pick up the top todo and implement it. With arguments, creates a new task. Without arguments, picks the highest-priority oldest task and makes the change. Supports --prio flag (1-4, default 3).
argument-hint: [--prio N] <description>
---

# Todo: $ARGUMENTS

## Usage

```
/todo                                    # Pick up top todo and implement it
/todo fix the typo in the readme         # Create todo (priority 3)
/todo --prio 1 fix login crash on iOS    # Create todo (priority 1)
/todo --prio 4 consider adding dark mode # Create todo (priority 4)
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--prio` | `3` | Priority 1-4 (1 = highest, 4 = lowest). Maps directly to Todoist p1-p4. |

## Project Mapping

Resolve the Todoist project by running `git remote get-url origin` and matching against this table:

| Git origin contains | Todoist project ID | Project name |
|---------------------|-------------------|--------------|
| `nielsmadan/juggler` | `6g2Rr8C5MjJQhQm6` | juggler |

If no match is found, ask the user which Todoist project to use.

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

### 4. Resolve Project

Run `git remote get-url origin` and match against the Project Mapping table above. If no match, ask the user.

### 5. Create Task

Call `mcp__todoist__add-tasks` with:
- `content`: the todo description (title)
- `description`: for simple todos, empty. For complex todos, the expanded description and context as Markdown.
- `priority`: `p{prio}` where `{prio}` is the parsed priority value
- `projectId`: resolved from the mapping table

### 6. Confirm

Print a one-liner: the task title and priority level.

---

## Pick Up Todo

### 1. Find Top Todo

Resolve the project ID from the Project Mapping table. Call `mcp__todoist__find-tasks` with the `projectId` and `limit: 50`.

From the results, filter out any tasks with the `in-progress` label. Sort the remaining by:
1. Priority (p1 first, then p2, p3, p4)
2. Task ID ascending (oldest first)

Pick the first task. If no tasks are found, tell the user there are no todos.

### 2. Read and Present

Show the task title and description (if any). Print a short summary of what you're about to do and ask the user to confirm.

### 3. Mark In Progress

Call `mcp__todoist__update-tasks` to add the `in-progress` label to the task.

### 4. Implement

Make the change described in the todo. Follow normal development workflow — read relevant code, ask clarifying questions if needed, implement, and verify.

When creating implementation tasks (TaskCreate), always include a final task: **"Complete Todoist task `{task ID}`"** — this ensures cleanup is tracked and won't be forgotten.

### 5. Clean Up

When all tasks are complete and changes are verified, call `mcp__todoist__complete-tasks` with the task ID to mark it done.
