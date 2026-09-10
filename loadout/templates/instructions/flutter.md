## Flutter project tooling

Use `templates = ["flutter"]` in `loadout/config.toml`. This template includes shared mobile
device automation, Dart analysis, simulator MCP servers, and a project-scoped upgrade skill.
Use `agent-device` for app interaction and UI verification.

### When to reach for the deployed MCPs

- **`dart-mcp`** — analyzing Dart code, surfacing static analyzer findings, and running
  tests/individual test files. Prefer it over shell `dart analyze` / `flutter test` when you
  want structured results you can then act on (e.g., locate a failing assertion in source).
- **`ios-sim`** — an alternative when an iOS simulator task needs the MCP interface:
  screenshots, view tree dumps, taps, swipes, text input, and point-to-element introspection.
- **`android`** — analogous MCP control over Android devices/emulators when working on the
  Android target.

If a question is about Dart syntax or framework APIs rather than this project's code, use
`/research-tech` instead — `dart-mcp` is for analyzing *this* codebase.

### When to reach for the deployed skill

- **`/flutter-upgrade`** — bumping the Flutter SDK or a major Flutter package across the
  project, or resolving the breaking-change surface after such an upgrade. Don't invoke it for
  routine dependency bumps (`flutter pub upgrade` on minor versions is plain shell work).

### Notes

- Run `loadout sync` in the project to refresh template instructions, permissions, skills,
  and MCP configuration for its supported configured harnesses.
- The Flutter template pre-approves its listed `ios-sim` tools. For additional MCP approvals,
  use `/loadout` to add the specific `server/tool` name to the project's permission source.
- Machine prerequisites (`npx`, `uvx`, `dart`) must be installed for the MCP servers to
  actually start. Device-automation setup is covered in the shared mobile guidance.
