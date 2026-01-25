# /review-comments

Reviews all comments in the codebase and suggests improvements based on comment quality guidelines.

## Usage
```
/review-comments
```

## Implementation
Use the Task tool with the `general-purpose` agent and this prompt:

```
Review all comments in the codebase and suggest improvements following the comment quality guidelines in CLAUDE.md. Focus on identifying "what" comments that should be "why" comments or extracted into descriptive function names.
```

## What It Does
1. **Scans all source code files** for comments
2. **Identifies problematic comments** such as:
   - "What" comments that just describe syntax
   - Obvious comments that restate the code
   - Comments that could be replaced with better function names
3. **Suggests specific improvements** for each issue found
4. **Prioritizes files** that need the most attention

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

**Note:** These principles apply to any programming language - the examples use pseudocode to demonstrate concepts that work in JavaScript, TypeScript, Python, Java, C#, Go, Rust, Swift, Kotlin, etc.

### ❌ Bad Comment
```
// Loop through numbers and add valid ones to the list
for each num in numbers:
  if num >= 6 and num <= 19 and num != 10:
    validNumbers.add(num)
```

### ✅ Good Refactor
```
// Extract to descriptive function instead of comment
validNumbers.addAll(filterArithmeticNumbers(numbers))

function filterArithmeticNumbers(numbers):
  return numbers.filter(num => num >= 6 and num <= 19 and num != 10)
```

### ✅ Good Comment (when needed)
```
// Use exponential backoff to prevent overwhelming the server during outages
await delay(retryCount * 1000)
```

This tool helps maintain high code quality by ensuring comments add real value to the codebase.