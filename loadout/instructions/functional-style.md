## Functional Style

A nudge, not a paradigm. What follows are the functional-programming lessons that pay off in ordinary imperative languages; the goal is code that is easy to test and easy to reason about locally, not code that looks like Haskell.

**Push logic into functions that take their inputs and return their results.** I/O, clocks, randomness, network and database calls belong at the edges, with the decision-making in between operating only on data it was handed. Aim this at module boundaries rather than at every three-line helper — imperative languages resist purity at the smallest scale and take to it readily at medium scale.

**Say the transformation directly.** `map`, `filter`, `any`/`all` and comprehensions state what the code produces; the equivalent `for` loop makes the reader reconstruct that from an accumulator, an index and a body. Where the language has them, use them — that is the default, not a special case, and it applies to the small loops as much as the interesting ones. Three narrow exceptions: a loop needing an early exit or `break`, a rewrite that would run to four or more chained stages, and `reduce` building a dict or object, which is worse than the `for` it replaced.

**Don't reach out, and don't reach in.** A function reads what it was passed rather than mutable module-level or global state, and produces a return value rather than writing into a shared variable. Argue hardest against *new* shared mutable state; existing globals are a refactor, not a blocker.

**Don't mutate what you were given.** A function handed a list, dict or object returns a new value instead of modifying the caller's copy in place. Mutating a local you created inside the function — a loop accumulator, a builder — is fine and is not a violation of this.

**Same input, same output.** A function that needs the time, a random value or an environment variable takes it as a parameter instead of reaching for it, so its behaviour is reproducible and testable without patching.

**Return a value or change something, not both.** A function whose name reads like a question shouldn't have side effects; one that performs an action shouldn't smuggle back state the caller is expected to inspect.

**Where this stops.** No currying, point-free style or compose/pipe chains. No recursion in languages without tail calls — use a loop. No monads, lenses, or an FP utility library added to make any of this possible. Don't copy a large structure to dodge a mutation in a hot path. And don't rewrite working imperative code into this style: it governs new code you write, not code you happen to be passing through.
