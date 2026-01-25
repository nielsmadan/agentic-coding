# /review-comments-changed

Reviews comments only in files that have been changed according to git, and suggests improvements based on comment quality guidelines.

## Usage
```
/review-comments-changed
```

## Implementation
First, get the list of changed files using git, then use the Task tool with the `general-purpose` agent and this prompt:

```
1. First, identify all files that have been changed in the current git working directory using `git diff --name-only HEAD` and `git diff --cached --name-only` to get both staged and unstaged changes.

2. Then, review comments only in those changed files and suggest improvements following the comment quality guidelines below. Focus on identifying "what" comments that should be "why" comments or extracted into descriptive function/variable names.

3. If no files have been changed, report that no review is needed.

Comment Quality Guidelines:

**Good Comments (WHY)**
- Explain business logic decisions
- Document performance considerations
- Clarify non-obvious algorithms
- Explain workarounds or edge cases
- Document assumptions or constraints

**Bad Comments (WHAT)**
- Describe what the code is doing syntactically
- Restate variable names or method calls
- Explain obvious operations
- Add noise without value

**Better Alternatives**
Instead of "what" comments, prefer:
- Extracting functions with descriptive names
- Using meaningful variable names
- Writing self-documenting code
- Only adding comments for complex or non-obvious logic
```

## What It Does
1. **Identifies git-changed files** - Gets list of all modified files from git (works with any language)
2. **Scans only changed files** for comments (much faster than full codebase scan)
3. **Identifies problematic comments** such as:
   - "What" comments that just describe syntax
   - Obvious comments that restate the code
   - Comments that could be replaced with better function names
4. **Suggests specific improvements** for each issue found
5. **Focuses review** on files you're actively working on

## Comment Quality Guidelines

### Good Comments (WHY)
- Explain business logic decisions
- Document performance considerations
- Clarify non-obvious algorithms
- Explain workarounds or edge cases
- Document assumptions or constraints

### Bad Comments (WHAT)
- Describe what the code is doing syntactically
- Restate variable names or method calls
- Explain obvious operations
- Add noise without value

### Better Alternatives
Instead of "what" comments, prefer:
- Extracting functions with descriptive names
- Using meaningful variable names
- Writing self-documenting code
- Only adding comments for complex or non-obvious logic

## Examples

**Note**: The examples below use Dart for illustration, but this command works with any programming language.

### ❌ Bad Comment
```dart
// Loop through numbers and add valid ones to the list
for (final num in numbers) {
  if (num >= 6 && num <= 19 && num != 10) {
    validNumbers.add(num);
  }
}
```

### ✅ Good Refactor
```dart
// Extract to descriptive function instead of comment
validNumbers.addAll(filterArithmeticNumbers(numbers));

List<int> filterArithmeticNumbers(List<int> numbers) {
  return numbers.where((num) =>
    num >= 6 && num <= 19 && num != 10
  ).toList();
}
```

### ✅ Good Comment (when needed)
```dart
// Use exponential backoff to prevent overwhelming the server during outages
await Future.delayed(Duration(milliseconds: retryCount * 1000));
```

This tool helps maintain high code quality by ensuring comments add real value to the codebase, while focusing only on the files you're currently working on for faster feedback.
