---
name: todo
description: Capture a todo in Todoist, or pick up the top todo and implement it. With arguments, creates a new task. Without arguments, picks the highest-priority oldest task and makes the change. Supports -c (complex), -i (interactive), and --prio (1-4, default 3).
argument-hint: [-i] [-c] [--prio N] <description>
---

# Todo: $ARGUMENTS

## Usage

```
/todo                                    # Pick up top todo and implement it
/todo fix the typo in the readme         # Create simple todo (priority 3)
/todo --prio 1 fix login crash on iOS    # Create simple todo (priority 1)
/todo -c redesign the settings screen    # Create complex todo with deep research
/todo -ic redesign the settings screen   # Complex + interactive (can ask questions)
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--prio` | `3` | Priority 1-4 (1 = highest, 4 = lowest). Maps directly to Todoist p1-p4. |
| `-c` | off | Complex mode. Deep research: reads docs, source files, identifies affected areas. |
| `-i` | off | Interactive mode. Allows asking clarifying questions via AskUserQuestion. |

## Interactive Mode

- **With `-i`:** May use AskUserQuestion for clarifications. If project can't be resolved, ask the user.
- **Without `-i` (default):** **Never** use AskUserQuestion — the session is running in background with no user to respond. If there are ambiguities, add them under a `## Open Questions` section in the task description. If the project can't be resolved from git origin, fall back to Inbox.

## Todoist Integration

Use the `mcp__claude_ai_Todoist__*` MCP tools directly as native tool calls. Do NOT shell out to MCP tools via Bash — they are native tool calls, not CLI commands. Do NOT check if MCP is available — assume it is.

## Project Mapping

Resolve the Todoist project by running `git remote get-url origin`, then read `claude/skills/todo/projects.local.md` and match the origin against the table there. This file is gitignored — create it locally with your own mappings:

```markdown
| Git origin contains | Todoist project ID | Project name |
|---------------------|-------------------|--------------|
| `your-org/your-repo` | `your-todoist-project-id` | project-name |
```

If the file doesn't exist or no match is found, ask the user which Todoist project to use.

## Workflow

### 0. Route

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

Run `git remote get-url origin` and match against the Project Mapping table above.

### 4. Create Task

Call `mcp__claude_ai_Todoist__add-tasks` with:
- `content`: the todo description (title)
- `description`: from cursory research, empty or a brief note. From deep research, the expanded description and context as Markdown.
- `priority`: `p{prio}` where `{prio}` is the parsed priority value
- `projectId`: resolved from the mapping table
- `labels`: `["development"]`

### 5. Confirm

Print a one-liner: the task title and priority level.

---

## Pick Up Todo

### 1. Find Top Todo

Resolve the project ID from the Project Mapping table. Call `mcp__claude_ai_Todoist__find-tasks` with the `projectId`, `labels: ["development"]`, and `limit: 50`.

From the results, filter out any tasks with the `in-progress` label. Sort the remaining by:
1. Priority (p1 first, then p2, p3, p4)
2. Task ID ascending (oldest first)

Pick the first task. If no tasks are found, tell the user there are no todos.

### 2. Read and Present

Show the task title and description (if any). Print a short summary of what you're about to do and ask the user to confirm.

### 3. Mark In Progress

Call `mcp__claude_ai_Todoist__update-tasks` to add the `in-progress` label to the task.

### 4. Implement

Make the change described in the todo. Follow normal development workflow — read relevant code, ask clarifying questions if needed, implement, and verify.

When creating implementation tasks (TaskCreate), always include a final task: **"Complete Todoist task `{task ID}`"** — this ensures cleanup is tracked and won't be forgotten.

### 5. Clean Up

When all tasks are complete and changes are verified, call `mcp__claude_ai_Todoist__complete-tasks` with the task ID to mark it done.

## Examples

**Pick up top priority task and implement it:**
> /todo

Fetches all development-labeled tasks for the current project, filters out in-progress items, and picks the highest-priority oldest task. Presents the task for confirmation, marks it in-progress, implements the change, and completes it in Todoist when done.

**Create a rich task with deep context:**
> /todo -c redesign the settings screen

Reads internal docs and relevant source files to understand the current settings implementation. Creates a Todoist task with an expanded description including affected files, a Context section, and any open questions -- all without interrupting the user.

## Troubleshooting

### Todoist API unavailable or MCP not connected
**Solution:** Verify that the Todoist MCP server is listed in your Claude Code MCP configuration and that your API token is valid. Restart Claude Code to re-initialize MCP connections if the tools are not responding.

### Cannot resolve project name to Todoist project
**Solution:** Check that the git remote origin URL matches an entry in the Project Mapping table. If the repository is not mapped, add a new row to the table in this skill file, or use the `-i` flag so the skill can ask you which project to use.
