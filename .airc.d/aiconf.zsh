# Project template tooling: single entry point via the /aiconf skill, which
# assesses the project and either installs a template or reconciles drift.
_aiconf() {
  case "$1" in
    help|--help|-h)
      cat <<EOF
aiconf                assess the current project — install its template if not
                      configured, otherwise compare against the template and
                      reconcile drift per artifact
aiconf <dir>          same, for <dir>
aiconf sync [dir]     skip detection, go straight to the sync path
aiconf <type> [dir]   skip detection, install <type> (flutter, react-native,
                      web, railway); still confirms before writing
aiconf help           show this message
EOF
      ;;
    *)
      claude "/aiconf${*:+ $*}"
      ;;
  esac
}
alias aiconf='noglob _aiconf'
