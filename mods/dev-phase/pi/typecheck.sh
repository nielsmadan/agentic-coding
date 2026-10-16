#!/usr/bin/env bash
# Type-checks the pi extension against the installed pi's own declarations.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
modules="$(mise where npm:@earendil-works/pi-coding-agent)/node_modules"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cat >"$tmp/tsconfig.json" <<EOF
{
  "compilerOptions": {
    "target": "es2023",
    "lib": ["es2023"],
    "module": "esnext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noEmit": true,
    "skipLibCheck": true,
    "types": ["node"],
    "typeRoots": ["$modules/.mise/node_modules/@types"],
    "paths": {
      "@earendil-works/pi-coding-agent": ["$modules/@earendil-works/pi-coding-agent/dist/index.d.ts"],
      "@earendil-works/*": ["$modules/.mise/node_modules/@earendil-works/*"]
    }
  },
  "files": ["$here/api-check.ts"]
}
EOF

npx -y -p typescript@5.9.3 tsc -p "$tmp/tsconfig.json"
