## Cloudflare

Use `cf-as personal <command> [args...]` for the personal Cloudflare login
(`nielsmadan@gmail.com`) and `cf-as qc <command> [args...]` for Quantumcraft
(`nielsmadan@quantumcraft.io`). These are separate logins with read-only API tokens.
Choose the account from the project's context; ask if it is unclear.

`cf-as` selects the SOPS-injected `CLOUDFLARE_API_TOKEN_PERSONAL` or
`CLOUDFLARE_API_TOKEN_QUANTUMCRAFT`, sets `CLOUDFLARE_API_TOKEN` and
`CLOUDFLARE_ACCOUNT_ID` for the child command, and fails if the token is missing.
It works in non-interactive shells and does not read the secrets store. A Wrangler
project's `account_id` must match the selected account.

Examples: `cf-as personal wrangler pages project list`, `cf-as qc wrangler whoami`,
or `cf-as personal python3 inspect-build-logs.py`. Scripts can use the selected
environment variables to call the Cloudflare API. Pages build logs are available
through its deployment logs API; `wrangler pages deployment tail` streams Functions'
runtime logs. Never print the token or run `wrangler auth token` to inspect it.
