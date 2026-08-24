#!/bin/bash
input=$(cat)
# ringleader-capture
printf '%s' "$input" | jq -c '{captured_at: (now|floor), rate_limits}' > "/Users/nielsmadan/.local/share/ringleader/claude-limits.json.tmp" 2>/dev/null && mv -f "/Users/nielsmadan/.local/share/ringleader/claude-limits.json.tmp" "/Users/nielsmadan/.local/share/ringleader/claude-limits.json";
# ringleader-capture

eval "$(printf '%s' "$input" | jq -r '
def used: if . == null or .used_percentage == null then "" else (.used_percentage | round) end;
def workday: ((. - (5 * 3600)) | strflocaltime("%Y-%m-%d") | . + "T00:00:00Z" | fromdateiso8601);
def pace: if . == null or .used_percentage == null or .resets_at == null then ""
  else (((((now | workday) - ((.resets_at - 604800) | workday)) / 86400) | floor) + 1
        | if . < 1 then 1 elif . > 7 then 7 else . end) as $day
    | (($day * 100 / 7) - .used_percentage | round) end;
def left: if . == null or .resets_at == null then ""
  else ((.resets_at - now) | if . < 0 then 0 else . end | floor) end;
@sh "dir_name=\(.workspace.current_dir // .cwd | split("/") | last) current_dir=\(.workspace.current_dir // .cwd) model_name=\(.model.display_name // "Unknown Model") output_style=\(.output_style.name // "default") ctx_pct=\(.context_window.used_percentage // 0 | floor) effort=\(.effort.level // "") fast_mode=\(if .fast_mode then "1" else "" end) seven_d=\(.rate_limits.seven_day | used) seven_pace=\(.rate_limits.seven_day | pace) seven_left=\(.rate_limits.seven_day | left)"')"

pct_color() {
  if [ "$1" -ge 80 ]; then printf '\033[31m'
  elif [ "$1" -ge 50 ]; then printf '\033[33m'
  else printf '\033[32m'; fi
}

sep() { printf '\033[2m │ '; }

fmt_left() {
  local d=$(($1 / 86400)) h=$((($1 % 86400) / 3600)) m=$((($1 % 3600) / 60))
  if [ "$d" -gt 0 ]; then printf '%dd%dh' "$d" "$h"
  elif [ "$h" -gt 0 ]; then printf '%dh%02dm' "$h" "$m"
  else printf '%dm' "$m"; fi
}

window() {
  local label=$1 pct=$2 pace=$3 left=$4
  printf '\033[36m %s \033[0m%s%s%%\033[0m' "$label" "$(pct_color "$pct")" "$pct"
  if [ -n "$pace" ]; then
    if [ "$pace" -gt 0 ]; then printf ' \033[32m+%s\033[0m' "$pace"
    elif [ "$pace" -le -10 ]; then printf ' \033[31m%s\033[0m' "$pace"
    elif [ "$pace" -lt 0 ]; then printf ' \033[33m%s\033[0m' "$pace"
    else printf ' \033[36m0\033[0m'; fi
  fi
  if [ -n "$left" ]; then printf ' \033[37m%s\033[0m' "$(fmt_left "$left")"; fi
}

project_type=""
if [ -f "$current_dir/pubspec.yaml" ]; then
  if grep -q "flutter:" "$current_dir/pubspec.yaml" 2>/dev/null; then project_type="📱"; else project_type="🎯"; fi
fi

printf '\033[34m📁 %s\033[0m' "$dir_name"
sep
if [ -n "$project_type" ]; then
  printf '\033[35m%s Flutter\033[0m' "$project_type"
  sep
fi
printf '\033[33m🤖 %s\033[0m' "$model_name"
if [ -n "$fast_mode" ]; then printf ' \033[33m⚡\033[0m'; fi
if [ -n "$effort" ]; then printf ' \033[35m%s\033[0m' "$effort"; fi
sep
printf '\033[37m✨ %s\033[0m' "$output_style"
sep
printf '🧠 %s%s%%\033[0m' "$(pct_color "$ctx_pct")" "$ctx_pct"
sep
if [ -n "$seven_d" ]; then
  printf '⏳'
  window 7d "$seven_d" "$seven_pace" "$seven_left"
  sep
fi
if [ -n "$AGENT_SANDBOX" ]; then printf '\033[32m🔒 sandbox\033[0m'; else printf '\033[31m🥩 raw\033[0m'; fi
printf '\033[0m'
