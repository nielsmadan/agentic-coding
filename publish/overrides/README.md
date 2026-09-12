# Public skill variants

An override provides a separate public version of an existing published skill.
Local loadout sync uses `loadout/skills/<name>/`. The publisher prefers
`publish/overrides/<name>/` when it exists, otherwise it uses the local source.

## Create a variant

From the `agentic-coding` repository root, copy the complete skill directory:

```sh
cp -R loadout/skills/blind-spots publish/overrides/blind-spots
```

Edit the copy for public use. Keep its directory name and frontmatter `name`
identical to the original. The skill must be listed in a `[groups]` entry in
`publish/skills.toml`; adding an override does not enable publication by itself.
Its local counterpart may be gitignored or absent from a fresh clone, provided
the complete public override is present.

The override replaces the whole directory. Include every required reference,
script, asset, and license or third-party notice. Files from the local version
are not merged into it. Fixes shared by both versions must be applied to both.

Tracked files in either source tree are public. An override changes what gets
installed from the skills collection; it does not hide a committed local source.

## Validate and publish

```sh
python3 publish/sync.py --check-manifest --check-sources
python3 -m unittest publish.test_sync
```

Source checks scan the version selected for publication. The publisher also
validates the rendered instructions and supporting files. An incomplete override
or one without a matching publish group fails the checks; it does not silently
fall back to the local version. Symlinked overrides are rejected.

Commit and push the changes in `agentic-coding`. The existing workflow in
`nielsmadan/skills` publishes the selected versions on its next run, including the
public descriptions in the generated README. No edits to the generated collection
are needed.

To resume publishing the local version, remove that skill's override directory.
The next publication replaces its output with the local version and removes
files that belonged only to the override.
