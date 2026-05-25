# Prepend repo's bin/ to PATH (idempotent).
_acbin="${0:A:h:h}/bin"
[[ ":$PATH:" != *":$_acbin:"* ]] && export PATH="$_acbin:$PATH"
unset _acbin
