# Where the SOPS secrets store lives. The injection itself is bin/sops-exec —
# these exports exist for the callers that invoke `sops` directly (`clor`, and
# ~/rc's `sec` alias), and so that sourcing ~/.airc is enough on its own.
#
# SOPS reads the age identity from this path. macOS' default is a space-padded
# `Library/Application Support/sops/age/`; we use the XDG location instead.
export SOPS_AGE_KEY_FILE="$HOME/.config/sops/age/keys.txt"
export SOPS_SECRETS="$HOME/.config/sops/secrets.yaml"
