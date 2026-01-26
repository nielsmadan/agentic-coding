---
name: review-tests
description: Review test quality for issues like missing edge cases, brittle tests, over-mocking, and test smells. Default: tests related to current context. Flags: --staged (staged test files), --all (all tests, uses parallel agents). Use after writing tests or during code review.
argument-hint: [--staged | --all]
---

# Review Tests

Review test quality for coverage gaps, test smells, and brittle patterns.

## Usage

```
/review-tests              # Tests related to current context
/review-tests --staged     # Only staged test files
/review-tests --all        # All test files (parallel agents)
```

## Workflow

### Step 1: Determine Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related tests | Find tests for recently discussed code |
| `--staged` | Staged test files | `git diff --cached --name-only -- '*test*' '*spec*'` |
| `--all` | All test files | Glob `**/*test*.{ts,js,py,dart}` etc. |

### Step 2: Get Test Files

**For default (context-based):**
1. Identify the code/feature from conversation
2. Find corresponding test files

**For --staged:**
```bash
git diff --cached --name-only | grep -E '(test|spec)'
```

**For --all:**
Find all test files by convention (`*test*`, `*spec*`, `__tests__/`, `test/`).

### Step 3: Review

**Small scope (≤5 files):** Review directly.

**Large scope (>5 files or --all):** Spawn parallel sub-agents per batch.

### Step 4: Report

```markdown
## Test Review: {scope}

### Critical Issues
- {file}:{test} - {issue}

### Coverage Gaps
- {code_file/function} - missing test for {scenario}

### Test Smells
- {file}:{test} - {smell}

### Suggestions
- {improvement}
```

## Test Smells to Detect

### Critical

**No Assertions**
```javascript
// BAD: Test always passes
test('user login', async () => {
  await loginUser('test@example.com');
  // No expect() - what are we testing?
});
```

**Testing Implementation, Not Behavior**
```javascript
// BAD: Breaks on any refactor
expect(component.state.internalFlag).toBe(true);
expect(service._privateMethod).toHaveBeenCalled();

// GOOD: Test observable behavior
expect(screen.getByText('Welcome')).toBeVisible();
expect(result.status).toBe('success');
```

### High Priority

**Over-Mocking**
```javascript
// BAD: Testing mocks, not real code
jest.mock('./database');
jest.mock('./auth');
jest.mock('./validator');
jest.mock('./logger');
// At this point, what's actually being tested?

// GOOD: Mock only external boundaries
jest.mock('./externalPaymentApi');
```

**Brittle Timing**
```javascript
// BAD: Flaky - depends on timing
await doAsyncThing();
await new Promise(r => setTimeout(r, 100));
expect(result).toBe('done');

// GOOD: Wait for actual condition
await waitFor(() => expect(result).toBe('done'));
```

**Order Dependency**
```javascript
// BAD: Tests depend on execution order
let sharedState;
test('first', () => { sharedState = setup(); });
test('second', () => { expect(sharedState.value).toBe(1); }); // Fails if run alone
```

### Medium Priority

**Magic Values**
```javascript
// BAD: What is 42? Why 'abc123'?
expect(calculate(42)).toBe(84);
expect(validate('abc123')).toBe(true);

// GOOD: Named constants explain intent
const VALID_USER_ID = 'user_12345';
const DOUBLED_VALUE = INPUT * 2;
```

**God Tests**
```javascript
// BAD: Tests too much, hard to debug failures
test('user flow', async () => {
  // 50 lines testing signup, login, profile, settings, logout
});

// GOOD: Focused tests
test('signup creates user', ...);
test('login sets session', ...);
```

**Missing Edge Cases**
- Empty inputs
- Null/undefined
- Boundary values (0, -1, MAX_INT)
- Error conditions
- Concurrent access
- Unicode/special characters

**Flaky Patterns**
- `Math.random()` in tests without seeding
- `new Date()` without mocking
- Network calls to real services
- File system dependencies
- Environment variable assumptions

## Coverage Gap Detection

For code being reviewed, check if tests exist for:

1. **Happy path** - Does basic functionality work?
2. **Error handling** - What happens when things fail?
3. **Edge cases** - Empty, null, boundary values?
4. **Integration points** - Do components work together?

Report as:
```markdown
### Coverage Gaps
- `src/auth/login.ts:validateCredentials` - no test for invalid email format
- `src/api/users.ts:deleteUser` - no test for non-existent user
- `src/utils/parse.ts` - no tests at all
```

## Notes

- Focus on actionable findings, not style nitpicks
- Consider the testing framework conventions (Jest, pytest, etc.)
- A test that never fails is as bad as no test
- Integration tests > unit tests with heavy mocking
