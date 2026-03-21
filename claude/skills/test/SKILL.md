---
name: test
description: "Test review and generation. Modes: --review (check test quality, default), --generate (create tests for code). Scope: --staged, --all, or context-based. Use for test quality and creation."
argument-hint: "[--review | --generate <target>] [--staged | --all]"
---

# Test

Review and generate tests following consistent principles.

## Usage

```
/test                              # Review tests related to current context (default)
/test --review                     # Explicit review mode
/test --review --staged            # Review staged test files
/test --review --all               # Review all tests (parallel agents)
/test --generate <target>          # Generate tests for file/module/feature
/test --generate --staged          # Generate tests for staged code changes
```

## Testing Principles

Both review and generate modes follow these principles. Review checks conformance; generate applies them.

### 1. Test Behavior, Not Implementation

Assert observable outputs and side effects — not internal state or private methods.

### 2. Mock Only External Boundaries

Mock third-party services and I/O; keep internal modules real so the test exercises actual code.

### 3. Meaningful Assertions

Every test must have at least one `expect` that can fail; a test with no assertions proves nothing.

### 4. No Brittle Timing

Never use `setTimeout`/`sleep` to wait for async work; wait for the actual condition instead.

### 5. Independent Tests

Each test must set up its own state and not rely on execution order or shared mutable state.

### 6. Cover Edge Cases

- Empty inputs
- Null/undefined
- Boundary values (0, -1, MAX_INT)
- Error conditions
- Concurrent access
- Unicode/special characters

### 7. Focused Tests

One concern per test — avoid multi-step flows that test several behaviors in a single `it` block.

### 8. Named Constants Over Magic Values

Use named constants for test inputs and expected values so the intent is clear at a glance.

For BAD/GOOD code examples of each principle, see `references/principles-examples.md`.

---

## Gotchas
- `--staged` review filters by filename pattern (`*test*`, `*spec*`). A test file in `__tests__/payment.ts` (no "test" in the filename) is missed by the glob.
- Red-Green Verification (run → green, revert → red, re-apply → green) is described for bug fixes only, but is equally important for new feature tests to confirm the test actually validates the implementation.

## Review Mode (`--review`)

Default mode. Checks tests against the principles above.

### Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related tests | Find tests for recently discussed code |
| `--staged` | Staged test files | `git diff --cached --name-only -- '*test*' '*spec*'` |
| `--all` | All test files | Glob `**/*test*.{ts,js,py,dart}` etc. |

### Workflow

1. **Get file list** based on scope
2. **Review** (directly if ≤5 files, parallel sub-agents if more)
3. **Report findings** by priority

### Checklist

For the review checklist, see `references/generate-templates.md`.

### Coverage Check

If a coverage script exists, run it to identify gaps:

```bash
# Check for coverage scripts
grep -E "coverage|test:cov" package.json 2>/dev/null
cat pyproject.toml 2>/dev/null | grep -A5 "pytest"
```

**Common coverage commands:**
- `npm run test:coverage` or `npm run coverage`
- `pytest --cov`
- `go test -cover`
- `flutter test --coverage`

Report uncovered lines/branches for files in scope.

### Output Format

```markdown
## Test Review: {scope}

### Critical Issues
- {file}:{test} - {issue}

### Completeness Gaps
- {code_file}:{function} - no tests found
- {code_file}:{function} - missing test for error case
- {code_file}:{function} - missing test for edge case: {scenario}

### Coverage Report
(if coverage script available)
- Overall: {X}% statements, {Y}% branches
- Uncovered in scope:
  - {file}:{lines} - {description}

### Pattern Violations (--staged)
- {test_file} - setup pattern differs from existing tests
- {test_file} - mocking approach inconsistent with {example_file}

### Test Smells
- {file}:{test} - {smell}

### Suggestions
- {improvement}
```

---

## Generate Mode (`--generate`)

Create tests for code following the principles above.

### Red-Green Verification (for bug fixes)

When generating tests for a bug fix, verify the test actually catches the bug:

1. Run the new test with the fix applied -- confirm PASS (green)
2. Temporarily revert the fix
3. Run the test again -- confirm FAIL (red)
4. Re-apply the fix
5. Run the test -- confirm PASS again (green)

Only claim the test is valid if it fails without the fix and passes with it. This prevents tests that pass for unrelated reasons.

### Scope

| Flag | Scope | Method |
|------|-------|--------|
| `<target>` | Specific file/function/module | Read the code, generate tests |
| `--staged` | Staged code changes | Generate tests for what changed |

### Workflow

1. **Detect framework** - Jest, pytest, go test, vitest, etc. from project
2. **Analyze existing test patterns** - read 2-3 existing test files to learn:
   - File naming and location conventions
   - Describe/it structure and nesting style
   - Setup/teardown patterns (beforeEach, fixtures, factories)
   - Mocking approach (jest.mock, manual mocks, DI)
   - Assertion style and common matchers
   - Test data patterns (inline, fixtures, builders)
3. **Read the code** - understand what needs testing
4. **Check existing tests** - avoid duplicates, extend if needed
5. **Generate tests** following both principles AND project patterns

For framework detection rules and cross-framework terminology, see `references/framework-mapping.md`.

### Test File Placement

Follow project conventions:
- `__tests__/` directory (common in JS/TS)
- `*.test.ts` or `*.spec.ts` alongside source
- `test/` directory at project root
- `*_test.py` alongside source or in `tests/`

### What to Generate

For generate templates (function, component, service, staged changes), see `references/generate-templates.md`.

### Output

Generate test files directly, matching project patterns:
- Place in location matching existing test file structure
- Use same describe/it nesting style as other tests
- Match setup/teardown patterns (beforeEach, fixtures, etc.)
- Use same mocking approach as existing tests
- Match assertion style and matchers
- Use consistent test data patterns (inline, fixtures, builders)
- Add brief comments for non-obvious test cases

**Before generating, show the patterns found:**
```markdown
## Detected Test Patterns

**Location:** `__tests__/` alongside source
**Structure:** `describe` per class/module, `it` per behavior
**Setup:** `beforeEach` with factory functions
**Mocking:** jest.mock for external, DI for internal
**Assertions:** jest matchers, testing-library queries

Generating tests following these patterns...
```

---

## Examples

**Generate tests for a payment function:**
> /test --generate lib/services/payment.ts

Detects the project's test framework and patterns, then generates a test file covering happy path (successful charge), error handling (declined card, network failure), and edge cases (zero amount, currency mismatch). Places the file following existing test conventions.

**Review staged tests catches over-mocking:**
> /test --review --staged

Reviews staged test files against the testing principles. Flags tests that mock internal modules instead of only external boundaries, and identifies tests with no meaningful assertions that would pass regardless of behavior.

## Troubleshooting

### Generated tests fail immediately on first run
**Solution:** Verify the correct test framework was detected by checking the "Detected Test Patterns" output. If imports or setup are wrong, point `--generate` at an existing passing test file so the generator can match its patterns exactly.

### Cannot detect the project's test framework
**Solution:** Ensure a framework config file exists (`jest.config.*`, `vitest.config.*`, `pytest.ini`, or `pyproject.toml` with pytest section). If the project uses a non-standard setup, run `test --generate <target>` and specify the framework in your prompt.

## Notes

- Default is review mode with context-based scope
- Both modes use the same principles - review checks, generate applies
- Use `--staged` before commits to catch issues or generate missing tests
- Use `--all` periodically for comprehensive review
- Sub-agents parallelize large reviews/generations
- Integration tests > unit tests with heavy mocking
