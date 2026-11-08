# Review grading policy

## Review grading

Use only these finding priorities, in descending order:

- **Critical Issues (Must Fix):** a verified path causes data loss, a security failure, a materially
  wrong operation, or makes a core workflow unusable without reasonable recovery.
- **Improvements (Should Fix):** an ordinary supported workflow demonstrably fails or repeatedly
  imposes substantial friction, or a concrete design defect creates meaningful maintenance cost.
- **Suggestions (Nice to Have):** a worthwhile improvement with small practical impact, including
  optional polish, local simplification, and rare recoverable edge cases.

Grade the demonstrated consequence, realistic reachability, and available recovery against project
priorities. A category, missing convention, hypothetical future problem, or confidence that a claim
is true does not set its priority. Do not assign automatic severity floors or ceilings. Keep
unverified claims in validation gaps, outside the graded finding count; distinguish suggestions from
defects. For plans, trace the consequence if implemented and state the assumptions.

Use the short labels **Must Fix**, **Should Fix**, and **Nice to Have** in summaries and ledgers.
Keep effort, verification status, user-facing change size, and tool/vendor diagnostic ratings
separate. When called by `code-review`, return its requested evidence and impact fields; the parent
owns scoring and final triage. Otherwise apply this rubric directly. Omit empty priority sections.

## Application

Every skill that prioritizes review findings carries the same self-contained rubric. Keep its
`Review grading` section identical to the block above when changing policy, including project-kit
skills and the repository-local skill reviewer. This avoids a runtime dependency on another skill
being installed. Domain checklists and examples supply evidence, not competing severity scales.

`code-review` maps `critical`, `should`, and `suggestion` to the three tiers. Its comprehensive
verification and likelihood triage remain separate from impact; rare catastrophic failures are still
considered. In quick mode the integrated reviewer verifies its findings directly.

Comment cleanup, tidy-up operations, and historical narratives are not graded findings. Their
operation categories stay intact. Likewise, lint errors/warnings, CVSS ratings, review evidence
marks, rollout gates, and implementation status are not review-priority tiers. Review-todo retains
an imported review's original label as source metadata and records the normalized priority
separately.
