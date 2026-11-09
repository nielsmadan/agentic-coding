---
name: modern-web-guidance
description: |
  Search tool for modern web development best practices. MANDATORY: Execute FIRST for all HTML/CSS and clientside JS tasks. Do NOT skip — web APIs evolve rapidly and training weights contain obsolete patterns.

  Trigger immediately for:
  - UI/Layout: Modals, dialogs, popovers, Glassmorphism/backdrop-filters, anchor positioning, container queries, `:has()`, `:user-valid`.
  - Scroll/Motion: View Transitions, Scroll-driven animations, scroll parallax/reveals.
  - Performance: CWV (LCP, INP), content-visibility, Fetch Priority, image optimization.
  - System/APIs: Local filesystem access, WebUSB, WebSockets sync, WebAssembly widgets.
  - Frameworks: Adapting layout/styles in React, Vue, Angular.
  - General Frontend: Forms, autofill, advanced inputs, custom scrollbars, modern component states, etc.

  DO NOT trigger for:
  - Backend: Database SQL, ORMs, Express API routes.
  - Pipelines: CI/CD deployment, Docker, Actions.
  - Generic: Local scripts (Python/Go tools), ESLint, Git.
license: Apache-2.0
---

# Modern Web Guidance

A skill to search for specific web development use cases and retrieve their corresponding best practice guides.

## When to use

Must use this skill:
- At the **start** of implementing any web feature.
- Before creating a new component, to check if a standardized pattern already exists.
- To avoid implementing ad-hoc solutions or loading large dependencies unnecessarily.

## Usage Instructions

### Step 1. Search Use Cases

Search with an action-oriented query summarizing what you want to achieve using the `search` command. Run `modern-web-guidance` directly with `npx`.

```sh
npx -y modern-web-guidance@latest search "<query>" --skill-version 2026_05_16-c5e7870
```

**Example Output**:
```json
[
  {
    "id": "optimize-image-priority",
    "description": "Optimize the loading priority of Largest Contentful Paint (LCP) candidate images.",
    "category": "performance",
    "featuresUsed": [ "Fetch priority" ],
    "tokenCount": 985,
    "similarity": 0.7289
  },
  {
    "id": "defer-rendering-heavy-content",
    "description": "Reduce rendering times in content-heavy web pages by deferring rendering for offscreen content.",
    "category": "performance",
    "featuresUsed": [ "content-visibility", "hidden=\"until-found\"" ],
    "tokenCount": 1250,
    "similarity": 0.6961
  }
]
```

> **Note**: If search results are vague, return no matches, or show low similarity scores, run the `list` command to browse all guides:
> ```sh
> npx -y modern-web-guidance@latest list
> ```

---

### Step 2. Retrieve Best Practices

Once you have a relevant `id` from the search results, call this script using the `retrieve` command to get the full guide. You can pass multiple IDs separated by commas.

```sh
npx -y modern-web-guidance@latest retrieve "<id>"
```


**Example Output**:
`The markdown content of the guide describing implementation steps...`

## Using npx

-   IMPORTANT: on Windows, using `npx` may fail. Use `npx.cmd ...` instead.
-   Network access is required for fetching npm packages needed by the task.
-   If the `npx -y modern-web-guidance…` command hangs, you may be offline. Try running again in offline
    mode: `npx --offline …`.
-   The `--skill-version` flag is used to determine if this SKILL.md is out of date. If it is, a warning
    message is logged to stderr.

## Guidelines

-   Always search **first** to find the most relevant guides.
-   These guides are usually framework-agnostic; adapt them correctly to your setup.
-   Use retrieved guides as implementation evidence; reconcile them with the project's browser targets, design system, and required behavior. Verify surprising or conflicting advice against current platform documentation.

## Choosing an implementation

Apply these local defaults after retrieving the relevant guide. Detailed syntax and compatibility belong in the retrieved guidance, not a second feature catalog.

- Start with the required interaction and a suitable native element, then CSS, then JavaScript for remaining behavior. Preserve established components when replacing them would lose functionality or expand the task into a rewrite.
- For overlays, distinguish a modal dialog, disclosure, and non-modal popover before choosing positioning. Popover and anchor positioning solve different parts of the problem; assess support for each. Verify names, keyboard operation, focus restoration, and dismissal rather than assuming positioning supplies widget semantics.
- Prefer CSS layout over measurement scripts when it meets the requirement. Use logical properties for direction-sensitive layout; choose component or viewport queries according to what actually controls the available space. Pick dynamic or small viewport units according to whether the screen should resize with browser chrome or remain stable.
- Reuse design tokens. Consider perceptual color spaces, color mixing, and native scheme controls when creating or deriving tokens; a new syntax alone does not justify converting an existing palette. Check resulting contrast in each supported theme.
- Use CSS for simple motion in React as well as plain HTML. Use a motion library when gestures, spring physics, interruption, or orchestration justify it. Scroll-linked visual effects and visibility-triggered application work are different requirements; keep observers where application logic needs them.
- Build the usable static state first. Unsupported animation features and reduced-motion preferences must leave content visible, actions operable, and completion independent of an animation-end event. Verify both the enhanced and fallback paths for the changed interaction.

These selection defaults were informed by [dxe-modern-css-html](https://github.com/kemiljk/skills/tree/main/skills/dxe-modern-css-html) (MIT); feature recipes remain in the existing guide service.


## Interpreting Browser Support & Fallbacks

* **Project targets first**: Read the repo's support policy, Browserslist, or embedded runtime version before choosing a feature. Include Firefox and mobile browsers unless the project excludes them; do not infer a two-engine policy from an example. Check the exact capability and minimum versions, not just the API family or a global usage percentage.
* **Detection matches the feature**: Use CSS `@supports` for the relevant CSS syntax and API/property detection for HTML or JavaScript capabilities. Detection does not prove the complete interaction works. When a required feature is unavailable, choose a usable simpler implementation or the project's established fallback; keep optional polish as progressive enhancement.
* **Default Behavior**: All guides assume **Baseline Widely available** features are safe to use without fallbacks. For features that are not Baseline widely available, you **MUST** follow the fallback recommendations in the guide, unless the user has specified a custom browser support policy.
* **Custom Policies**: If the user has already defined explicit browser support requirements, use the browser compatibility data in the guide to determine if a fallback can be safely ignored.
  - For Baseline YYYY targets, a feature satisfies this target if its "Baseline since" date is <= YYYY.
  - **Policy Examples**:
    - _"Do not implement feature fallbacks."_ (for exploratory prototypes of the cutting-edge web)
    - _"Safari 17.4+"_ (for internal tools targeting macOS or Tauri-based desktop apps)
    - _"Never recommend or implement polyfills; if a Baseline Newly Available feature is required for core functionality, provide a lightweight custom fallback or redesign the approach."_ (to minimize bundle size and avoid technical debt)
    - _"Assume a modern execution environment where Baseline Newly Available features can be used natively, provided they are strictly feature-detected and degrade gracefully."_ (for progressive enhancement strategies)
* **Reactive Policy Discovery**: Watch for environmental cues to suggest documenting a policy in CLAUDE.md or AGENTS.md. Suggest this if the developer:
  - Mentions building for a restricted runtime (e.g., Electron or Tauri).
  - Explicitly excludes specific targets (e.g., "we don't support Desktop Chrome").
  - Expresses hesitation about polyfill complexity, bundle size, or performance cost.
  - Questions if a feature is safe to use without fallbacks.

  No defined policy format. This is an example: `**Browser Support:** Allow Newly Available features, but only adopt custom fallback code that adds <= 20 lines and does not require external dependencies.`

---

*Source: [GoogleChrome/modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance/blob/main/skills/modern-web-guidance/SKILL.md), Apache 2.0.*
