## Backend project tooling

### Local services

- Postgres, Redis and emulators run from the project's compose file in Docker (Colima on this
  machine). Start and stop them through the project's own scripts (`test:db:up`,
  `test:db:down`, a `just` recipe) rather than raw `docker compose`: the scripts pick the
  compose file and project name for this checkout.
- When the project has a `splashdown.toml`, ports and the compose project name are per
  checkout and live in the generated `splashdown.env`. If that file is missing, run `splash`;
  never hard-code a port another checkout may hold.
- Tear the stack down after an integration run, or the next run fights for its ports.

### Database changes

- Change the schema with a new migration from the project's own generator and apply it with
  the project's own migrate script, which may run at startup. Never edit a migration that has
  been applied anywhere, and never use a schema push (`db:push`, `drizzle-kit push`) in place
  of a migration.
- Seeds must be safe to run twice; deploys often seed on every release.
- Unit tests with a mocked data layer prove nothing about SQL. Run the integration suite for
  any change to queries, migrations or transactions.

### Deployed environments

- Migrations, seeds and scripts run against local or test databases only. Don't run a
  command that changes a deployed service or runs with its variables (`railway run`, `shell`,
  `connect`, `ssh`, `up`, `redeploy`, `variable set`) unless the user asks for that specific
  command.

### API contract

- When a route's request or response shape changes, regenerate whatever the project commits
  from it (an OpenAPI spec, a typed client) in the same change, and update the route's tests.
