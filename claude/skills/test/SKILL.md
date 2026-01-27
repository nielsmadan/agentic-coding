---
name: test
description: Test review and generation. Modes: --review (check test quality, default), --generate (create tests for code). Scope: --staged, --all, or context-based. Use for test quality and creation.
argument-hint: [--review | --generate <target>] [--staged | --all]
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

```javascript
// BAD: Breaks on any refactor
expect(component.state.internalFlag).toBe(true);
expect(service._privateMethod).toHaveBeenCalled();

// GOOD: Test observable behavior
expect(screen.getByText('Welcome')).toBeVisible();
expect(result.status).toBe('success');
```

### 2. Mock Only External Boundaries

```javascript
// BAD: Testing mocks, not real code
jest.mock('./database');
jest.mock('./auth');
jest.mock('./validator');
jest.mock('./logger');
// What's actually being tested?

// GOOD: Mock only external boundaries
jest.mock('./externalPaymentApi');
```

### 3. Meaningful Assertions

```javascript
// BAD: Test always passes
test('user login', async () => {
  await loginUser('test@example.com');
  // No expect() - what are we testing?
});

// GOOD: Verify outcomes
test('user login', async () => {
  const result = await loginUser('test@example.com');
  expect(result.token).toBeDefined();
  expect(result.user.email).toBe('test@example.com');
});
```

### 4. No Brittle Timing

```javascript
// BAD: Flaky - depends on timing
await doAsyncThing();
await new Promise(r => setTimeout(r, 100));
expect(result).toBe('done');

// GOOD: Wait for actual condition
await waitFor(() => expect(result).toBe('done'));
```

### 5. Independent Tests

```javascript
// BAD: Tests depend on execution order
let sharedState;
test('first', () => { sharedState = setup(); });
test('second', () => { expect(sharedState.value).toBe(1); }); // Fails if run alone

// GOOD: Each test sets up its own state
test('first', () => { const state = setup(); /* ... */ });
test('second', () => { const state = setup(); expect(state.value).toBe(1); });
```

### 6. Cover Edge Cases

- Empty inputs
- Null/undefined
- Boundary values (0, -1, MAX_INT)
- Error conditions
- Concurrent access
- Unicode/special characters

### 7. Focused Tests

```javascript
// BAD: Tests too much, hard to debug failures
test('user flow', async () => {
  // 50 lines testing signup, login, profile, settings, logout
});

// GOOD: One concern per test
test('signup creates user', ...);
test('login sets session', ...);
```

### 8. Named Constants Over Magic Values

```javascript
// BAD: What is 42? Why 'abc123'?
expect(calculate(42)).toBe(84);
expect(validate('abc123')).toBe(true);

// GOOD: Named constants explain intent
const VALID_USER_ID = 'user_12345';
const DOUBLED_VALUE = INPUT * 2;
```

---

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

**Principles:**
- [ ] Tests verify behavior, not implementation
- [ ] Mocks limited to external boundaries
- [ ] All tests have meaningful assertions
- [ ] No brittle timing (setTimeout, sleep)
- [ ] Tests are independent (no shared state)
- [ ] Edge cases covered
- [ ] Tests are focused (one concern each)

**Flaky Patterns:**
- [ ] No unseeded `Math.random()`
- [ ] No unmocked `new Date()`
- [ ] No network calls to real services
- [ ] No file system dependencies without cleanup
- [ ] No environment variable assumptions

**Completeness (for code being reviewed):**
- [ ] All public functions/methods have tests
- [ ] All exported components have tests
- [ ] Error paths are tested, not just happy paths
- [ ] Edge cases identified in code have corresponding tests

**Pattern Conformance (for --staged/new tests):**
- [ ] File naming matches project convention
- [ ] Test organization matches existing tests (describe/it structure)
- [ ] Setup/teardown patterns match (beforeEach, fixtures, factories)
- [ ] Mocking approach consistent (manual mocks, jest.mock, dependency injection)
- [ ] Assertion style matches (expect vs assert, matchers used)

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

### Framework Detection

Check for:
- `jest.config.*`, `package.json` with jest → Jest
- `vitest.config.*` → Vitest
- `pytest.ini`, `pyproject.toml` with pytest → pytest
- `*_test.go` files → Go testing
- `*_test.dart` files → Flutter test

### Test File Placement

Follow project conventions:
- `__tests__/` directory (common in JS/TS)
- `*.test.ts` or `*.spec.ts` alongside source
- `test/` directory at project root
- `*_test.py` alongside source or in `tests/`

### What to Generate

**For a function:**
```javascript
describe('{functionName}', () => {
  it('returns expected result for valid input', () => {
    // Happy path
  });

  it('handles empty input', () => {
    // Edge case
  });

  it('throws on invalid input', () => {
    // Error handling
  });

  it('handles boundary value', () => {
    // Edge case: 0, MAX, etc.
  });
});
```

**For a component:**
```javascript
describe('{ComponentName}', () => {
  it('renders with required props', () => {
    // Happy path
  });

  it('responds to user interaction', () => {
    // User events
  });

  it('displays error state', () => {
    // Error handling
  });

  it('handles loading state', () => {
    // Async states
  });
});
```

**For a service/API:**
```javascript
describe('{ServiceName}', () => {
  it('returns data on success', () => {
    // Happy path
  });

  it('handles errors gracefully', () => {
    // Error handling
  });

  it('validates input', () => {
    // Input validation
  });
});
```

**For staged changes:**
1. Identify what changed (new function, modified behavior, etc.)
2. Find or create relevant test file
3. Generate tests for the changes
4. Ensure edge cases are covered

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

## Notes

- Default is review mode with context-based scope
- Both modes use the same principles - review checks, generate applies
- Use `--staged` before commits to catch issues or generate missing tests
- Use `--all` periodically for comprehensive review
- Sub-agents parallelize large reviews/generations
- Integration tests > unit tests with heavy mocking
