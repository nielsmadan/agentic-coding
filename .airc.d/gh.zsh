# Fine-grained PATs are single-owner, so one token cannot cover both a personal
# account and an org. bin/gh picks GH_TOKEN_<OWNER> from the repo's owner and
# execs the real gh.
#
# Needed in two forms. Inside the sandbox _agent_sandboxed puts ac's bin/ first on
# PATH, so the shim wins there. In an interactive shell it cannot: mise
# re-prepends its own bin dirs on every prompt, pushing ac's bin/ far down. A
# function outranks PATH entirely, so it covers the shell.
: ${AC_DIR:=${0:A:h:h}}
gh() { "$AC_DIR/bin/gh" "$@"; }
