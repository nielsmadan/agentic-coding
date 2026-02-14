---
name: perf-test
description: Set up and run performance tests (profiling, load testing, or E2E scenarios). Use when measuring code or endpoint performance, or before/after optimization work.
argument-hint: <target: file, function, endpoint, or service>
---

# Performance Test

Set up, run, and analyze performance tests with an iterative improvement cycle.

## Usage

```
/perf-test src/utils/parser.ts           # Profile a file/module
/perf-test calculateTotal                 # Profile a specific function
/perf-test /api/users                     # Load test an endpoint
/perf-test checkout-flow                  # E2E scenario test
/perf-test                                # Ask what to test
```

## Workflow

### Phase 1: Understanding

Ask clarifying questions:

1. **What type of test?**
   - Code profiling (execution time, memory)
   - Load testing (requests/sec, latency, concurrency)
   - E2E scenario (full workflow with state setup)

2. **What metrics matter?**
   - Execution time / latency
   - Throughput (ops/sec, requests/sec)
   - Memory usage
   - P50/P95/P99 latencies

3. **What are the success criteria?**
   - Specific thresholds (e.g., <100ms p95)
   - Relative improvement (e.g., 20% faster)
   - No regressions from baseline

4. **Detect project context:**
   ```bash
   # Detect language/framework
   ls package.json 2>/dev/null && echo "node"
   ls requirements.txt pyproject.toml 2>/dev/null && echo "python"
   ls go.mod 2>/dev/null && echo "go"
   ls Cargo.toml 2>/dev/null && echo "rust"
   ```

**Do NOT skip phases:**
- "I can skip the proposal and just write the test" -- The proposal ensures we measure the right things
- "The results look fine, no need to analyze" -- Subtle regressions hide in apparently fine results
- "One iteration is enough" -- Statistical significance requires multiple runs

### Phase 2: Proposal

Present a testing plan:

```markdown
## Performance Test Proposal

**Target:** {target}
**Type:** {profiling | load testing | e2e scenario}
**Tool:** {selected tool}

### Metrics to Collect
- {metric 1}
- {metric 2}

### Test Configuration
- {iterations/duration}
- {concurrency if load test}
- {warmup settings}

### Success Criteria
- {threshold 1}
- {threshold 2}

### Files to Create
- {test file path}
- {config file if needed}

Proceed with this plan?
```

### Phase 3: Implementation

Select the appropriate template from [references/templates.md](references/templates.md) based on language and test type:
- **Code profiling:** JS (benchmark.js), Python (timeit), Go (testing.B)
- **Load testing:** hey (universal), autocannon (Node.js)
- **E2E scenarios:** Custom scripts with state setup/teardown and per-step timing

Adapt the template to the specific target, configuring iterations, concurrency, and metrics collection as specified in the proposal.

### Phase 4: Execution

Run tests and capture output:

```bash
# Node.js benchmark
node perf-tests/{target}.bench.js

# Python benchmark
python perf-tests/{target}_bench.py

# Go benchmark
go test -bench=. -benchmem ./...

# Load test
hey -n 1000 -c 50 {url}
```

### Phase 5: Analysis

Parse results and identify concerns:

```markdown
## Performance Results

### Summary
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Mean latency | 45ms | <100ms | Pass |
| P95 latency | 120ms | <150ms | Pass |
| P99 latency | 450ms | <200ms | Fail |
| Throughput | 850 req/s | >500 | Pass |

### Concerning Findings
1. **P99 latency spike** - 450ms exceeds 200ms threshold
   - Likely cause: {analysis}
   - Affected code: {file:line}

2. **Memory growth** - {if detected}
```

### Phase 6: Recommendations

```markdown
## Optimization Recommendations

### High Impact
1. **{Recommendation}**
   - Current: {metric}
   - Expected improvement: {estimate}
   - Implementation: {brief description}

### Medium Impact
2. **{Recommendation}**
   ...

Which recommendations would you like to implement?
```

### Phase 7: Improvement Cycle

After user selects recommendations:

1. **Implement** the accepted optimizations
2. **Re-run** the same performance tests
3. **Compare** results:

```markdown
## Before/After Comparison

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Mean latency | 45ms | 32ms | -29% |
| P95 latency | 120ms | 85ms | -29% |
| P99 latency | 450ms | 150ms | -67% |
| Throughput | 850/s | 1100/s | +29% |

### Summary
- {X} metrics improved
- {Y} metrics unchanged
- {Z} metrics regressed (if any)
```

4. Ask if further optimization needed

### Documentation

Save test setup for future replication:

**File:** `docs/perf/{target}/README.md`

```markdown
# Performance Tests: {target}

## Setup
{installation instructions}

## Running Tests
{command to run}

## Baseline Metrics
| Metric | Value | Date |
|--------|-------|------|
| {metric} | {value} | {date} |

## Thresholds
- {threshold 1}
- {threshold 2}

## History
| Date | Change | Impact |
|------|--------|--------|
| {date} | {optimization} | {improvement %} |
```

## Tool Reference

| Language | Profiling | Load Testing | E2E Scenario |
|----------|-----------|--------------|--------------|
| JS/TS | benchmark.js, console.time | autocannon, k6 | custom scripts, k6 scenarios |
| Python | timeit, cProfile, pytest-benchmark | locust | locust sequences, pytest |
| Go | testing.B (built-in) | hey, vegeta | custom test harness |
| Rust | criterion | hey | custom scripts |
| Any CLI | hyperfine | hey, ab | shell scripts with timing |

## Notes

- Always run multiple iterations for statistical significance
- Include warmup runs to avoid cold-start bias
- For load tests, ensure the service is running locally or in a controlled environment
- For E2E scenarios, reset state between iterations for reproducible results
- Use isolated test databases, never production data
- Document baseline metrics before optimizing
- Compare against the same test configuration for valid before/after comparison
