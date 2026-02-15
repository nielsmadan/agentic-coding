---
name: debug-log
description: Add debug logging statements to trace code execution. Use when debugging issues, understanding control flow, or investigating why code behaves unexpectedly. Supports any language (JS/TS, Python, Go, etc). Invoke with a topic/area to debug, or use conversation context.
argument-hint: <topic or area to debug>
---

# Debug Log

Add targeted debug logging to trace execution flow and variable state.

## Usage

```
/debug-log authentication flow
/debug-log                        # Uses last topic from conversation
/debug-log the checkout process
```

## Debugging Discipline

**One-Variable Rule:**
- Make ONE change at a time
- Test after EACH individual change
- If a change doesn't help, REVERT it before trying the next
- Never stack untested changes

**Circuit Breaker:**
If 3 sequential attempts fail to isolate the issue, STOP. Document findings and escalate to `/hard-fix` for parallel investigation.

## Workflow

1. **Identify target** - Use provided topic or infer from recent conversation
2. **Find relevant code** - Locate functions, handlers, and key decision points
3. **Add logs at strategic points:**
   - Function entry/exit
   - Before/after async operations
   - Inside conditionals and loops
   - Variable assignments that matter
4. **Use descriptive prefixes** - Make logs easy to trace

## Log Format by Language

**JavaScript/TypeScript:**
```js
console.log('[DEBUG][ModuleName] description:', variable);
```

**Python:**
```python
print(f"[DEBUG][module_name] description: {variable}")
```

**Go:**
```go
fmt.Printf("[DEBUG][PackageName] description: %v\n", variable)
```

**Other languages:** Adapt pattern - `[DEBUG][Context] message`

## Strategic Log Placement

Place logs at these points:

| Location | What to log |
|----------|-------------|
| Function entry | Function name, key parameters |
| Before async/await | What's about to happen |
| After async/await | Result or error |
| Conditionals | Which branch taken, why |
| Loops | Iteration count, current item |
| Error paths | Error details, state at failure |

## Example

For "debug the login flow":

```ts
async function login(email: string, password: string) {
  console.log('[DEBUG][Auth] login called with email:', email);

  const user = await findUser(email);
  console.log('[DEBUG][Auth] findUser result:', user ? 'found' : 'not found');

  if (!user) {
    console.log('[DEBUG][Auth] early return - user not found');
    return { error: 'User not found' };
  }

  const valid = await verifyPassword(password, user.hash);
  console.log('[DEBUG][Auth] password valid:', valid);

  if (!valid) {
    console.log('[DEBUG][Auth] early return - invalid password');
    return { error: 'Invalid password' };
  }

  console.log('[DEBUG][Auth] login successful, creating session');
  return { success: true, user };
}
```

## Examples

**Instrument auth flow with entry/exit and state logs:**
> /debug-log authentication flow

Locates login, token validation, and session creation functions. Adds `[DEBUG][Auth]` logs at each function entry/exit, before/after async calls like `findUser` and `verifyPassword`, and logs key state such as token presence and user lookup results.

**Trace intermittent checkout error:**
> /debug-log checkout process

Finds the checkout handler, payment processing, and cart validation code. Adds logs at each conditional branch and async boundary to capture the exact execution path and variable state when the intermittent error occurs.

## Troubleshooting

### Added logging breaks functionality
**Solution:** Revert the last logging change immediately and re-test. Ensure log statements do not alter control flow (e.g., accidentally placed inside a ternary or before a return) and that string interpolation does not call methods with side effects.

### Too many log points obscure the issue
**Solution:** Remove all but the entry/exit logs for the top-level function, then re-add logs one layer deeper at a time. Use distinct prefixes per module (e.g., `[DEBUG][Auth]` vs `[DEBUG][Cart]`) and filter output with `grep` to isolate the relevant trace.

## Notes

- Keep logs concise but informative
- Don't log sensitive data (passwords, tokens, PII)
- Use consistent prefixes for easy filtering
- Focus on the specific area requested, don't over-instrument
