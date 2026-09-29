# Project templates

`loadout/templates/<type>.toml` selects config for a *kind* of project from a shared catalog:

```text
loadout/templates/
  mobile.toml
  flutter.toml
  react-native.toml
  web.toml
  instructions/<name>.md
  permissions/<name>.toml
  mcp/<name>.toml
  skills/<name>/SKILL.md
```

Each manifest has optional ordered `instructions`, `permissions`, `mcp`, and `skills` lists.
Entries are names without extensions, resolved within the corresponding catalog folder;
paths, symlinks, duplicate references, missing parts, and unknown categories are errors.
Edit the shared part to change its consumers; edit the manifest to change what a template
selects. A manifest and legacy directory with the same template name are ambiguous and refused.

`mobile.toml` selects shared `agent-device` instructions and shell permission. `flutter.toml`
selects those same mobile parts plus Flutter instructions, MCP servers and permissions, and
`/flutter-upgrade`. `react-native.toml` selects the mobile parts plus Metro and `rn-logs`
guidance, the `rn-logs` permission, and `/rn-upgrade`. `web.toml` selects browser automation
guidance and permissions plus its four web skills.

Keeping them here version-controls the config centrally without making it global: a template
reaches only a project that asks for it by name, so a bundled skill never pollutes sessions in
unrelated projects.

A project opts in:

```
loadout init --project --harness claude
loadout template add flutter     # templates = ["flutter"]
loadout sync
```

React Native projects declare `templates = ["react-native"]`; native mobile projects can use
`mobile` alone. Framework manifests reference the shared mobile parts directly. Existing
declarations such as `["mobile", "flutter"]` still work: shared instructions concatenate
once in first-reference order.

A template is a **source**, sitting below the project's own fragments. Later templates and
then project entries replace whole same-named skills and MCP servers. Permissions use the
existing deny-wins merge; `opencode.extra` follows last-tier precedence. Repeated permission,
skill, and MCP parts still participate at each template's position.

Declared templates (resolved from `~/ac`) update on the next project `loadout sync`. Running
`loadout template vendor <name>` instead copies the manifest and only its referenced parts
into the project's `loadout/templates/`, with one shared copy per part. Qualified names such
as `ac/flutter` place the manifest and parts under `loadout/templates/ac/`; use consistent
qualification for templates sharing parts.

`loadout template sync <name>` previews updates and checks recorded content hashes. A changed
shared part lists every affected selected vendored template and requires confirmation; a
local edit in any affected copy blocks the update. Run normal `loadout sync` afterwards to
regenerate project outputs.

**Migrating a vendored directory:** `template sync` cannot convert a directory into a catalog
manifest. Back up the existing `loadout/templates/` outside that catalog, compare local
customizations with the upstream parts, and move the old selected template directories out
of the catalog. Run `loadout template vendor <name>` for every selected template, including
`mobile` if it remains declared, then carry local customizations into the project's own
fragments and run `loadout sync`. Keep the backup until the regenerated output is verified.
Declared projects need only `loadout sync`.

Project-only skills live in `loadout/templates/skills/<name>/` and are selected by manifests,
not in `loadout/skills/`, so they are never rendered globally. Moving a skill between the two
changes where it renders — but **nothing prunes**: `loadout sync` only writes the paths it
renders, so the copies already written under `~/.claude/skills/`, `~/.codex/skills/`,
`~/.config/opencode/skills/` and `~/.pi/agent/skills/` must be deleted by hand.

Templates cover config only; machine prerequisites (e.g. `npx`, `uvx`, `dart` for the Flutter
MCP servers) must be installed separately.

**`aiconf` and `templates/deploy.py` were retired**; loadout's template mechanism replaced them.
Projects deployed by the old system keep working — their files are plain and still read — but
are no longer managed. Migrate one by running the opt-in above, then `git rm --cached` whatever
loadout now generates (`init` gitignores those paths but does not untrack them). Delete only
`.aiconf/` entirely — both `aiconf` and `aiperm`, which wrote the rest of it, are retired.

### Considered but not bundled

- **`chrome-devtools-mcp`** (Chrome DevTools for Agents v1, May 2026) — Chrome team's MCP
  server with Lighthouse audits, performance traces, heap snapshots, network/CPU throttling,
  Chrome extension dev, WebMCP debugging. Complements the `web` template's `agent-browser`
  (driving the page) with DevTools-grade *inspection* of the page. Not bundled by default
  because most web projects don't need it day-to-day and both speak CDP — running both
  against the same Chrome requires pointing chrome-devtools-mcp at agent-browser's instance
  via `--browser-url`, which is fiddly enough to opt into per-project. Install as a Claude
  Code plugin: `/plugin install chrome-devtools-mcp@chrome-devtools-plugins` after
  `/plugin marketplace add ChromeDevTools/chrome-devtools-mcp`.
