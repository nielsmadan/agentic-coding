---
allowed-tools: Bash(git status), Bash(git diff*), Read, Edit, MultiEdit, Grep
description: Help resolve git merge conflicts by analyzing conflicted files and providing resolution guidance
argument-hint: [optional: specific file path]
---

I'll help you resolve git merge conflicts. Let me start by checking the current status and identifying all conflicted files.

First, let me examine the current git status to see which files have conflicts:

Then I'll:
1. Analyze each conflicted file to understand the nature of the conflicts
2. Show you the conflict markers and explain what each section represents
3. Help you decide how to resolve each conflict (keep incoming, current, or merge both)
4. Edit the files to resolve conflicts by removing conflict markers
5. Once all conflicts are resolved, I'll inform you so you can run the appropriate git commands (add, commit, merge continue, etc.)

If you specified a particular file as an argument, I'll focus on that file first: $ARGUMENTS

Let's start by examining what conflicts we're dealing with.