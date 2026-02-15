---
name: review-perf
description: Performance analysis for algorithmic complexity, memory leaks, N+1 queries, and render issues. Use when code feels slow, after adding loops/queries, or before scaling up.
argument-hint: [--staged | --all]
---

# Review Performance

Performance analysis for common bottlenecks and inefficiencies.

## Usage

```
/review-perf                  # Review context-related code
/review-perf --staged         # Review staged changes
/review-perf --all            # Full codebase audit (parallel agents)
```

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related code | Files from recent conversation |
| `--staged` | Staged changes | `git diff --cached --name-only` |
| `--all` | Full codebase | Glob source files, parallel agents |

## Workflow

1. **Determine scope** based on flags
2. **Review** (directly if ≤5 files, parallel agents if more)
3. **Report findings** by severity (Critical = user-facing slowdown)

## Performance Checklist

### Algorithmic Complexity

**O(n²) or Worse:**
```javascript
// BAD: O(n²) nested loops
for (const item of items) {
  for (const other of items) {
    if (item.id === other.parentId) { ... }
  }
}

// GOOD: O(n) with lookup map
const parentMap = new Map(items.map(i => [i.id, i]));
for (const item of items) {
  const parent = parentMap.get(item.parentId);
}
```

**Repeated Calculations:**
```javascript
// BAD: Recalculating in loop
items.forEach(item => {
  const config = expensiveConfigLookup(); // Called n times
  process(item, config);
});

// GOOD: Calculate once
const config = expensiveConfigLookup();
items.forEach(item => process(item, config));
```

**Missing Early Exit:**
```javascript
// BAD: Always iterates entire array
function findUser(users, id) {
  let result = null;
  users.forEach(u => { if (u.id === id) result = u; });
  return result;
}

// GOOD: Exit when found
function findUser(users, id) {
  return users.find(u => u.id === id);
}
```

### Database/Query Patterns

**N+1 Queries:**
```javascript
// BAD: Query per item
const users = await db.users.findAll();
for (const user of users) {
  user.posts = await db.posts.findAll({ where: { userId: user.id } });
}

// GOOD: Single query with include
const users = await db.users.findAll({
  include: [{ model: db.posts }]
});
```

**Missing Pagination:**
```javascript
// BAD: Load all records
const allUsers = await db.users.findAll();

// GOOD: Paginate
const users = await db.users.findAll({
  limit: 50,
  offset: page * 50
});
```

**SELECT * When Few Columns Needed:**
```sql
-- BAD: Fetching everything
SELECT * FROM users WHERE active = true;

-- GOOD: Only needed columns
SELECT id, name, email FROM users WHERE active = true;
```

**Missing Indexes:**
- Columns used in WHERE clauses
- Columns used in ORDER BY
- Foreign key columns
- Columns used in JOIN conditions

### Memory Management

**Unclosed Resources:**
```javascript
// BAD: Connection never closed
const conn = await db.connect();
const data = await conn.query('...');
// conn stays open

// GOOD: Always close
const conn = await db.connect();
try {
  return await conn.query('...');
} finally {
  conn.close();
}
```

**Growing Caches:**
```javascript
// BAD: Cache grows forever
const cache = {};
function getValue(key) {
  if (!cache[key]) cache[key] = expensiveLookup(key);
  return cache[key];
}

// GOOD: LRU or TTL cache
const cache = new LRUCache({ max: 1000 });
```

**Event Listener Leaks:**
```javascript
// BAD: Never removed
useEffect(() => {
  window.addEventListener('resize', handler);
}, []);

// GOOD: Cleanup
useEffect(() => {
  window.addEventListener('resize', handler);
  return () => window.removeEventListener('resize', handler);
}, []);
```

### UI/Render Performance

**Unnecessary Re-renders (React):**
```javascript
// BAD: New object every render
<Child style={{ color: 'red' }} />
<Child onClick={() => handleClick(id)} />

// GOOD: Memoize
const style = useMemo(() => ({ color: 'red' }), []);
const handleClickMemo = useCallback(() => handleClick(id), [id]);
```

**Missing Virtualization:**
```javascript
// BAD: Render 10,000 items
{items.map(item => <Row key={item.id} {...item} />)}

// GOOD: Use virtualization
<VirtualizedList
  data={items}
  renderItem={({ item }) => <Row {...item} />}
/>
```

**Blocking Main Thread:**
```javascript
// BAD: Heavy sync computation
function processData(data) {
  return data.map(item => expensiveTransform(item)); // Blocks UI
}

// GOOD: Use web worker or chunk
async function processData(data) {
  return await worker.process(data);
}
```

### Network/IO

**Sequential Requests:**
```javascript
// BAD: Wait for each
const user = await fetchUser(id);
const posts = await fetchPosts(id);
const comments = await fetchComments(id);

// GOOD: Parallel
const [user, posts, comments] = await Promise.all([
  fetchUser(id),
  fetchPosts(id),
  fetchComments(id)
]);
```

**Missing Request Deduplication:**
```javascript
// BAD: Same request multiple times
componentA.fetchUser(123);
componentB.fetchUser(123); // Duplicate request

// GOOD: Cache or dedupe
const { data } = useSWR(`/users/${id}`, fetcher);
```

## Output Format

```markdown
## Performance Review: {scope}

### Critical (user-facing slowdown)
- {file}:{line} - {issue type}: {description}
  **Impact:** {why it matters}
  **Fix:** {solution with code example}

### High Priority
- {file}:{line} - {issue}
  **Fix:** {solution}

### Medium Priority
- {file} - {issue}

### Suggestions
- {optimization opportunity}
```

## Examples

**Staged changes introduce N+1 query:**
> /review-perf --staged

Reviews staged files and catches a new user list endpoint that queries posts per user in a loop. Reports it as Critical with the impact ("100 users = 101 queries") and provides a fix using eager loading with `include`.

**Full audit finds memory leak in dashboard:**
> /review-perf --all

Parallel agents scan the full codebase by category. Finds an event listener in the dashboard component that is never cleaned up on unmount, plus an unbounded in-memory cache growing with every API call.

## Notes

- Focus on measurable impact, not micro-optimizations
- Consider data size - O(n²) on 10 items is fine, on 10,000 is not
- For `--all`, use parallel agents per category
- Database issues often have the highest impact
- UI issues matter most for user-facing code
