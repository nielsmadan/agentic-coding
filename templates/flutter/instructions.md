## Flutter project tooling

This project ships with a Flutter-aware Claude setup deployed by `aiconf flutter` —
MCP servers and a project-scoped skill. Use them where they help.

### When to reach for the deployed MCPs

- **`dart-mcp`** — analyzing Dart code, surfacing static analyzer findings, and running
  tests/individual test files. Prefer it over shell `dart analyze` / `flutter test` when you
  want structured results you can then act on (e.g., locate a failing assertion in source).
- **`ios-sim`** — driving the booted iOS simulator: screenshots, view tree dumps, taps,
  swipes, text input, point-to-element introspection. Use it for UI smoke checks and
  reproducing visual issues after a code change.
- **`android`** — analogous control over Android devices/emulators when working on the
  Android target.

If a question is about Dart syntax or framework APIs rather than this project's code, use
`/research-code` instead — `dart-mcp` is for analyzing *this* codebase.

### When to reach for the deployed skill

- **`/flutter-upgrade`** — bumping the Flutter SDK or a major Flutter package across the
  project, or resolving the breaking-change surface after such an upgrade. Don't invoke it for
  routine dependency bumps (`flutter pub upgrade` on minor versions is plain shell work).

### Notes

- These MCPs and the skill arrive via `aiconf flutter`. Re-running it refreshes their config
  but leaves this CLAUDE.md section alone — use `aiconf sync` to mirror edits back to the
  template or pull template changes into this section.
- Only the `ios-sim` tools are pre-approved in `.claude/settings.local.json`. The first call
  to a `dart-mcp` or `android` tool will trigger a permission prompt — approve there, and add
  the specific tool name to `permissions.allow` if you want it auto-approved going forward.
- Machine prerequisites (`npx`, `uvx`, `dart`) must be installed for the MCP servers to
  actually start.
