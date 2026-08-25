# Prepend repo's bin/ to PATH (idempotent).
_acbin="${0:A:h:h}/bin"
[[ ":$PATH:" != *":$_acbin:"* ]] && export PATH="$_acbin:$PATH"
unset _acbin

# Append every directory holding a tool these wrappers shell out to, so that
# sourcing ~/.airc is sufficient on its own. Interactively these are inert —
# mise has already prepended its install dirs. A non-interactive consumer never
# runs `mise activate` (it lives in ~/.zshrc, which only interactive shells
# read), so without this it finds neither sops nor nono and both wrappers fall
# through to an unsandboxed, keyless command. mise shims cover sops, nono and
# pi; the other three agent binaries are each installed somewhere else.
for _acdir in "$HOME/.local/share/mise/shims" "$HOME/.local/bin" \
              /opt/homebrew/bin "$HOME/.opencode/bin"; do
  [[ -d $_acdir && ":$PATH:" != *":$_acdir:"* ]] && export PATH="$PATH:$_acdir"
done
unset _acdir
