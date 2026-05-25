# Project template tooling: mechanical install + interactive bidirectional sync
# (repo path resolves via the ~/.airc symlink)
_aiconf() {
  local repo="${${:-$HOME/.airc}:A:h}"
  case "$1" in
    sync)
      shift
      claude "/sync-project-config $*"
      ;;
    help|--help|-h)
      cat <<EOF
aiconf <type> [dir]   install template into dir (default cwd); appends instructions
                      snippet to CLAUDE.md and AGENTS.md on first install for that
                      type (state-tracked in <dir>/.aiconf/state.json)
aiconf sync           run from a project dir: compare project against its template;
                      per-file direction (push vs pull) decided by diff + git history
aiconf sync <dir>     run from ~/ac: same comparison for <dir>
aiconf help           show this message
EOF
      ;;
    *)
      python3 "$repo/templates/deploy.py" "$@"
      ;;
  esac
}
alias aiconf='noglob _aiconf'
