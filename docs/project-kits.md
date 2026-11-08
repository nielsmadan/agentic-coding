# Project kits

`loadout/kits/<type>.toml` selects config for a *kind* of project from a shared catalog:

```text
loadout/kits/
  mobile.toml
  flutter.toml
  react-base.toml
  react-native.toml
  react-web.toml
  web.toml
  instructions/<name>.md
  permissions/<name>.toml
  mcp/<name>.toml
  skills/<name>/SKILL.md
```

Each manifest has optional ordered `instructions`, `permissions`, `mcp`, and `skills` lists.
Entries are names without extensions, resolved within the corresponding catalog folder;
paths, symlinks, duplicate references, missing parts, and unknown categories are errors.
Edit the shared part to change its consumers; edit the manifest to change what a kit
selects. A manifest and legacy directory with the same kit name are ambiguous and refused.

`mobile.toml` selects shared `agent-device` instructions and shell permission. `flutter.toml`
selects those same mobile parts plus Flutter instructions, MCP servers and permissions, and
`/flutter-upgrade`. `react-base.toml` selects shared React guidance, `/review-react` and `/review-typescript`.
`react-native.toml` selects the mobile and React parts plus Metro and JS log guidance, and
`/rn-upgrade`. `web.toml` selects browser automation guidance and
permissions plus its four web skills; `react-web.toml` selects those web parts plus the React
parts.

Keeping them here version-controls the config centrally without making it global: a kit
reaches only a project that asks for it by name, so a bundled skill never pollutes sessions in
unrelated projects.

A project opts in:

```
loadout init project --harness claude
loadout kit add flutter --linked     # kits = ["flutter"]
loadout sync
```

React Native projects declare `kits = ["react-native"]` and React web projects
`kits = ["react-web"]`; native mobile projects can use `mobile` alone. Framework manifests reference the shared mobile parts directly. Existing
declarations such as `["mobile", "flutter"]` still work: shared instructions concatenate
once in first-reference order.

A kit is a **source**, sitting below the project's own fragments. Later kits and
then project entries replace whole same-named skills and MCP servers. Permissions use the
existing deny-wins merge; `opencode.extra` follows last-tier precedence. Repeated permission,
skill, and MCP parts still participate at each kit's position.

Linked kits (resolved from `~/ac`) update on the next project `loadout sync`. Running
`loadout kit add <name> --vendored` instead copies the manifest and only its referenced parts
into the project's `loadout/kits/`, with one shared copy per part. Qualified names such
as `ac/flutter` place the manifest and parts under `loadout/kits/ac/`; use consistent
qualification for kits sharing parts.

`loadout kit sync <name>` previews updates and checks recorded content hashes. A changed
shared part lists every affected selected vendored kit and requires confirmation; a
local edit in any affected copy blocks the update. Run normal `loadout sync` afterwards to
regenerate project outputs.

**Migrating a vendored directory:** `kit sync` cannot convert a directory into a catalog
manifest. Back up the existing `loadout/kits/` outside that catalog, compare local
customizations with the upstream parts, and move the old selected kit directories out
of the catalog. Run `loadout kit add <name> --vendored` for every selected kit, including
`mobile` if it remains declared, then carry local customizations into the project's own
fragments and run `loadout sync`. Keep the backup until the regenerated output is verified.
Linked projects already using `kits` need only `loadout sync`.

**Migrating the template spelling:** loadout refuses the old names rather than accepting
aliases. In each consuming project's `loadout/config.toml`, rename `templates = [...]` to
`kits = [...]` and `[template.<name>]` provenance tables to `[kit.<name>]`. Rename any
vendored `loadout/templates/` folder to `loadout/kits/`, preserving its files and hashes.
Then run `loadout kit list`, `loadout sync`, and `loadout check` in that project.
Source catalogs use `kits/`; an explicit source `use` list must select `kits` as well.

Project-only skills live in `loadout/kits/skills/<name>/` and are selected by manifests,
not in `loadout/skills/`, so they are never rendered globally. Moving a skill between the two
changes where it renders, and the next `loadout sync` retires the copies it no longer renders:
it deletes each file it recorded writing (under `~/.config/loadout/written/`), then the skill
folder if that leaves it empty. A file loadout did not write keeps its folder, and outputs
written before that record existed were never tracked, so those still need deleting by hand.

Kits cover config only; machine prerequisites (e.g. `npx`, `uvx`, `dart` for the Flutter
MCP servers) must be installed separately.

**`aiconf` and `templates/deploy.py` were retired**; loadout's kit mechanism replaced them.
Projects deployed by the old system keep working — their files are plain and still read — but
are no longer managed. Migrate one by running the opt-in above, then `git rm --cached` whatever
loadout now generates (`init` gitignores those paths but does not untrack them). Delete only
`.aiconf/` entirely — both `aiconf` and `aiperm`, which wrote the rest of it, are retired.

### Considered but not bundled

- **`chrome-devtools-mcp`** (Chrome DevTools for Agents v1, May 2026) — Chrome team's MCP
  server with Lighthouse audits, performance traces, heap snapshots, network/CPU throttling,
  Chrome extension dev, WebMCP debugging. Complements the `web` kit's `agent-browser`
  (driving the page) with DevTools-grade *inspection* of the page. Not bundled by default
  because most web projects don't need it day-to-day and both speak CDP — running both
  against the same Chrome requires pointing chrome-devtools-mcp at agent-browser's instance
  via `--browser-url`, which is fiddly enough to opt into per-project. Install as a Claude
  Code plugin: `/plugin install chrome-devtools-mcp@chrome-devtools-plugins` after
  `/plugin marketplace add ChromeDevTools/chrome-devtools-mcp`.
