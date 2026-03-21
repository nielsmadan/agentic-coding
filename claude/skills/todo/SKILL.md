---
name: todo
description: Capture a todo in Todoist, or pick up the top todo and implement it. With arguments, creates a new task. Without arguments, picks the highest-priority oldest task and makes the change. Supports -c (complex), -i (interactive), --prio (1-4, default 3), and --list.
argument-hint: [-i] [-c] [--prio N] [--list] <description>
---

# Todo: $ARGUMENTS

## Usage

```
/todo                                    # Pick up top todo and implement it
/todo fix the typo in the readme         # Create simple todo (priority 3)
/todo --prio 1 fix login crash on iOS    # Create simple todo (priority 1)
/todo -c redesign the settings screen    # Create complex todo with deep research
/todo -ic redesign the settings screen   # Complex + interactive (can ask questions)
/todo --list                             # List todos and pick one to tackle
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--prio` | `3` | Priority 1-4 (1 = highest, 4 = lowest). Maps directly to Todoist p1-p4. |
| `-c` | off | Complex mode. Deep research: reads docs, source files, identifies affected areas. |
| `-i` | off | Interactive mode. Allows asking clarifying questions via AskUserQuestion. |
| `--list` | off | List all development todos for the current project sorted by priority and choose which to implement. |

## Interactive Mode

- **With `-i`:** May use AskUserQuestion for clarifications. If project can't be resolved, ask the user.
- **Without `-i` (default):** **Never** use AskUserQuestion — the session is running in background with no user to respond. If there are ambiguities, add them under a `## Open Questions` section in the task description. If the project can't be resolved from git origin, fall back to Inbox.

## Gotchas
- Non-interactive mode falls back to Inbox when the project can't be resolved. But the pick-up flow filters by `#ProjectName & @development` — Inbox tasks are invisible to `/todo` and `/todo --list`.
- If a session ends before the implementation is complete, the task stays labeled `in-progress` and is filtered out of all future pick-up runs, silently losing it.

## Todoist Integration

Use the Todoist MCP tools (prefixed `mcp__todoist__`). Key tools:

**Create task:**
```
mcp__todoist__add_tasks
```
Parameters: `tasks` array with objects containing `content` (title), `description`, `project_id`, `priority` (1-4), `labels` (array of strings).

**Find tasks:**
```
mcp__todoist__find_tasks
```
Parameters: `filter` (Todoist filter string, e.g. `#ProjectName & @development`).

**Update task:**
```
mcp__todoist__update_tasks
```
Parameters: `tasks` array with objects containing `task_id`, `labels`, etc.

**Complete task:**
```
mcp__todoist__complete_tasks
```
Parameters: `task_ids` array of task IDs.

**Find projects:**
```
mcp__todoist__find_projects
```
Use to look up project IDs by name.

Use these MCP tools directly — do not shell out to `td` CLI.

## Project Mapping

Resolve the Todoist project by running `git remote get-url origin`, then read `~/.claude/skills/todo/projects.local.md` and match the origin against the table there. This file is gitignored — create it locally with your own mappings:

```markdown
| Git origin contains | Todoist project ID | Project name |
|---------------------|-------------------|--------------|
| `your-org/your-repo` | `your-todoist-project-id` | project-name |
```

Use the **project name** to find the project via `mcp__todoist__find_projects`, then use the returned **project ID** when creating or filtering tasks.

If the file doesn't exist or no match is found, ask the user which Todoist project to use.

## Workflow

### 0. Route

If `--list` flag is present → go to **List Todos** workflow below.
If $ARGUMENTS is empty or blank → go to **Pick Up Todo** workflow below.
Otherwise → continue to step 1 (Create Todo).

---

## Create Todo

### 1. Parse

Extract `-i`, `-c`, `--prio` value (default 3), and the todo description from $ARGUMENTS. Flags can be combined (e.g. `-ic` or `-ci`).

### 2. Research

- **Without `-c` (cursory):** Quick glance at relevant file or area names based on the description. Don't deep-read files. If anything relevant is spotted, add a brief note to the task description.
- **With `-c` (deep):** Gather context thoroughly:
  - Check `docs/` for related documentation
  - Read relevant source files to understand the current state
  - Identify affected areas
  - Write a short expanded description focused on what the change looks like for the user — not technical implementation details. Include a `## Context` section listing relevant files or areas.
  - If there are ambiguities and `-i` is set, ask clarifying questions via AskUserQuestion. If `-i` is not set, add them under `## Open Questions` in the description.

### 3. Resolve Project

Run `git remote get-url origin` and match against the Project Mapping table above. Use `mcp__todoist__find_projects` to get the project ID.

### 4. Create Task

Use `mcp__todoist__add_tasks` with:
- `content`: Task title
- `description`: Research notes
- `project_id`: From step 3
- `priority`: From parsed `--prio` value
- `labels`: `["development"]`

### 5. Confirm

Print a one-liner: the task title and priority level.

---

## Pick Up Todo

### 1. Find Top Todo

Resolve the project name from the Project Mapping table. Fetch tasks using `mcp__todoist__find_tasks` with a filter like `#ProjectName & @development`.

From the results, filter out any tasks with the `in-progress` label. Sort the remaining by:
1. Priority (p1 first, then p2, p3, p4)
2. Task ID ascending (oldest first)

Pick the first task. If no tasks are found, tell the user there are no todos.

### 2. Read and Present

Show the task title and description (if any). Print a short summary of what you're about to do and ask the user to confirm.

### 3. Mark In Progress

Use `mcp__todoist__update_tasks` to set labels to `["development", "in-progress"]`.

### 4. Implement

Make the change described in the todo. Follow normal development workflow — read relevant code, ask clarifying questions if needed, implement, and verify.

When creating implementation tasks (TaskCreate), always include a final task: **"Complete Todoist task `{task ID}`"** — this ensures cleanup is tracked and won't be forgotten.

### 5. Clean Up

When all tasks are complete and changes are verified:

Use `mcp__todoist__complete_tasks` with the task ID.

## List Todos

### 1. Resolve Project

Run `git remote get-url origin` and match against the Project Mapping table.

### 2. Fetch Tasks

Use `mcp__todoist__find_tasks` with a filter like `#ProjectName & @development`.

Filter out any tasks with the `in-progress` label. Sort the remaining by:
1. Priority (p1 first, then p2, p3, p4)
2. Task ID ascending (oldest first)

If no tasks are found, tell the user there are no todos.

### 3. Display List

Print all tasks as a numbered list showing priority and title for each:

```
1. [p1] Fix login crash on iOS
2. [p2] Redesign settings screen
3. [p3] Update onboarding copy
4. [p3] Add dark mode toggle
```

### 4. Choose Task

Use AskUserQuestion to let the user pick which task to work on. Present up to 4 top tasks as options (AskUserQuestion supports 2-4 options). If there are more than 4 tasks, the full list from step 3 gives context and the user can select "Other" to specify by number.

### 5. Implement

Once the user picks a task, continue with the **Pick Up Todo** workflow from step 2 onwards (Read and Present → Mark In Progress → Implement → Clean Up).

---

## Examples

**Pick up top priority task and implement it:**
> /todo

Fetches all development-labeled tasks for the current project, filters out in-progress items, and picks the highest-priority oldest task. Presents the task for confirmation, marks it in-progress, implements the change, and completes it in Todoist when done.

**Browse todos and pick one to work on:**
> /todo --list

Fetches all development-labeled tasks for the current project, displays them sorted by priority, and asks which one to tackle. Once chosen, marks it in-progress, implements the change, and completes it in Todoist when done.

**Create a rich task with deep context:**
> /todo -c redesign the settings screen

Reads internal docs and relevant source files to understand the current settings implementation. Creates a Todoist task with an expanded description including affected files, a Context section, and any open questions -- all without interrupting the user.

## Troubleshooting

### Todoist MCP server not connected
**Solution:** Check `/mcp` in Claude Code. Ensure `TODOIST_API_TOKEN` is exported in your shell environment. Get your API token from Todoist Settings > Integrations > Developer > API token.

### Cannot resolve project name to Todoist project
**Solution:** Check that the git remote origin URL matches an entry in the Project Mapping table. If the repository is not mapped, add a new row to `claude/skills/todo/projects.local.md`, or use the `-i` flag so the skill can ask you which project to use.
