# Clean Code Principles Reference

Code quality principles and patterns used by review agents to evaluate code.

## Early Returns / Avoid Deep Nesting

```javascript
// BAD: Deep nesting
function process(user) {
  if (user) {
    if (user.isActive) {
      if (user.hasPermission) {
        return doWork(user);
      }
    }
  }
  return null;
}

// GOOD: Guard clauses
function process(user) {
  if (!user) return null;
  if (!user.isActive) return null;
  if (!user.hasPermission) return null;
  return doWork(user);
}
```

## Small Functions

```javascript
// BAD: Section comments indicate function does too much
function processOrder(order) {
  // Validate order
  if (!order.items) throw new Error('No items');
  if (!order.customer) throw new Error('No customer');
  // Calculate totals
  let subtotal = 0;
  for (const item of order.items) {
    subtotal += item.price * item.quantity;
  }
  const tax = subtotal * 0.1;
  // Save
  db.orders.save({ ...order, subtotal, tax });
}

// GOOD: Split into focused functions
function processOrder(order) {
  validateOrder(order);
  const totals = calculateTotals(order);
  saveOrder(order, totals);
}
```

## Meaningful Names

```javascript
// BAD: Cryptic names
const d = new Date() - u.c;
if (d > 86400000) { ... }

// GOOD: Self-documenting
const millisSinceCreation = Date.now() - user.createdAt;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;
if (millisSinceCreation > ONE_DAY_MS) { ... }
```

## Other Principles

Apply judgment:

- **Single Responsibility**: Each function/class should do one thing well
- **DRY**: Extract repeated logic into reusable units
- **KISS**: Prefer simple solutions over clever ones
- **Fail Fast**: Validate inputs early
- **Immutability**: Prefer immutable data where practical
- **Encapsulation**: Hide implementation details

## Functional Programming Preferences

These are preferred patterns, not strict rules. Use judgment — sometimes imperative code is clearer.

**Declarative Over Imperative:**
```javascript
// Imperative (verbose)
const activeUsers = [];
for (const user of users) {
  if (user.isActive) {
    activeUsers.push(user.name);
  }
}

// Declarative (preferred when clear)
const activeUsers = users
  .filter(u => u.isActive)
  .map(u => u.name);
```

**Other preferences:**
- **Minimize Global State**: Prefer passing data explicitly over shared mutable state
- **Pure Functions**: Prefer functions without side effects
- **Avoid Mutation**: Prefer creating new objects over modifying existing ones
- **Compose Small Functions**: Build complex behavior from simple, focused functions

Note: If a `for` loop is more readable or performant, that's fine. The goal is clarity, not dogma.

## Comments Philosophy

- **"Why" over "What"**: Comments should explain *why* something is done, not *what* the code does
- **Code should be self-documenting**: If you need a "what" comment, consider instead:
  - Renaming variables/functions to be more descriptive
  - Extracting a well-named function
  - Simplifying the logic
- **Good comment**: `// Using insertion sort here because n < 10 and it's cache-friendly`
- **Bad comment**: `// Loop through the array and add each item to the result`
- **Avoid comment cruft**: Don't leave commented-out code, TODO comments that will never be addressed, or redundant doc comments
