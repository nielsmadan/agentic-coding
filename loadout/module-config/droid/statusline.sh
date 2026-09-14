#!/bin/bash
set -euo pipefail

exec python3 "${BASH_SOURCE[0]%/*}/statusline.py"
