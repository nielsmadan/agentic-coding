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
@sh "dir_name=\(.workspace.current_dir // .cwd | split("/") | last) current_dir=\(.workspace.current_dir // .cwd) model_name=\(.model.display_name // "Unknown Model") ctx_pct=\(.context_window.used_percentage // 0 | floor) effort=\(.effort.level // "") fast_mode=\(if .fast_mode then "1" else "" end) seven_d=\(.rate_limits.seven_day | used) seven_pace=\(.rate_limits.seven_day | pace) seven_left=\(.rate_limits.seven_day | left)"')"

E=$'\033'
sep_str="${E}[2m │ ${E}[0m"

pct_color() {
  if [ "$1" -ge 80 ]; then printf '\033[31m'
  elif [ "$1" -ge 50 ]; then printf '\033[33m'
  else printf '\033[32m'; fi
}

ctx_color() {
  if [ "$1" -ge 90 ]; then printf '\033[38;5;167m'
  elif [ "$1" -ge 70 ]; then printf '\033[38;5;173m'
  elif [ "$1" -ge 45 ]; then printf '\033[38;5;179m'
  else printf '\033[38;5;108m'; fi
}

ctx_bar() {
  local pct=$1 width=10 filled empty fill pad
  filled=$((pct * width / 100))
  [ "$filled" -gt "$width" ] && filled=$width
  empty=$((width - filled))
  [ "$filled" -gt 0 ] && printf -v fill "%${filled}s"
  [ "$empty" -gt 0 ] && printf -v pad "%${empty}s"
  printf '%s%s\033[0m\033[2m%s\033[0m' "$(ctx_color "$pct")" "${fill// /▓}" "${pad// /░}"
}

fmt_left() {
  local d=$(($1 / 86400)) h=$((($1 % 86400) / 3600)) m=$((($1 % 3600) / 60))
  if [ "$d" -gt 0 ]; then printf '%dd%dh' "$d" "$h"
  elif [ "$h" -gt 0 ]; then printf '%dh%02dm' "$h" "$m"
  else printf '%dm' "$m"; fi
}

window() {
  local pct=$1 pace=$2 left=$3 l
  window_out="$(pct_color "$pct")${pct}%${E}[0m"
  window_w=$((${#pct} + 1))
  if [ -n "$pace" ]; then
    if [ "$pace" -gt 0 ]; then window_out+=" ${E}[32m+${pace}${E}[0m"; window_w=$((window_w + 2 + ${#pace}))
    elif [ "$pace" -le -10 ]; then window_out+=" ${E}[31m${pace}${E}[0m"; window_w=$((window_w + 1 + ${#pace}))
    elif [ "$pace" -lt 0 ]; then window_out+=" ${E}[33m${pace}${E}[0m"; window_w=$((window_w + 1 + ${#pace}))
    else window_out+=" ${E}[36m0${E}[0m"; window_w=$((window_w + 2)); fi
  fi
  if [ -n "$left" ]; then
    l=$(fmt_left "$left")
    window_out+=" ${E}[37m${l}${E}[0m"
    window_w=$((window_w + 1 + ${#l}))
  fi
}

# prio 100 is pinned; lower values are dropped first when two lines will not fit
segs=(); widths=(); prios=()
add_seg() { prios+=("$1"); widths+=("$2"); segs+=("$3"); }

if [ -n "$AGENT_SANDBOX" ]; then
  add_seg 100 10 "${E}[32m🔒 sandbox${E}[0m"
else
  add_seg 100 6 "${E}[31m🥩 raw${E}[0m"
fi

add_seg 90 $((3 + ${#dir_name})) "${E}[34m📁 ${dir_name}${E}[0m"

if [ -f "$current_dir/pubspec.yaml" ]; then
  if grep -q "flutter:" "$current_dir/pubspec.yaml" 2>/dev/null; then
    add_seg 30 10 "${E}[35m📱 Flutter${E}[0m"
  else
    add_seg 30 10 "${E}[35m🎯 Flutter${E}[0m"
  fi
fi

model_seg="${E}[33m🤖 ${model_name}${E}[0m"
model_w=$((3 + ${#model_name}))
if [ -n "$fast_mode" ]; then
  model_seg+=" ${E}[33m⚡${E}[0m"
  model_w=$((model_w + 3))
fi
if [ -n "$effort" ]; then
  model_seg+=" ${E}[35m${effort}${E}[0m"
  model_w=$((model_w + 1 + ${#effort}))
fi
add_seg 60 "$model_w" "$model_seg"

add_seg 80 $((3 + 10 + 1 + ${#ctx_pct} + 1)) \
  "🧠 $(ctx_bar "$ctx_pct")$(ctx_color "$ctx_pct") ${ctx_pct}%${E}[0m"

if [ -n "$seven_d" ]; then
  window "$seven_d" "$seven_pace" "$seven_left"
  add_seg 70 $((3 + window_w)) "⏳ ${window_out}"
fi

# greedy left-to-right pack into at most $max_lines rows; sets line_of[] and lines_used
max_lines=2
pack() {
  local avail=$1 i w cur=0 line=0
  lines_used=1
  for i in "${!segs[@]}"; do
    [ -z "${segs[$i]}" ] && continue
    w=${widths[$i]}
    if [ "$cur" -eq 0 ]; then cur=$w
    elif [ $((cur + 3 + w)) -le "$avail" ]; then cur=$((cur + 3 + w))
    else line=$((line + 1)); lines_used=$((lines_used + 1)); cur=$w; fi
    line_of[$i]=$line
  done
}

line_of=()
if [ -n "$COLUMNS" ]; then
  while :; do
    pack $((COLUMNS - 2))
    [ "$lines_used" -le "$max_lines" ] && break
    victim=-1 low=100
    for i in "${!segs[@]}"; do
      [ -z "${segs[$i]}" ] && continue
      if [ "${prios[$i]}" -lt "$low" ]; then low=${prios[$i]} victim=$i; fi
    done
    [ "$victim" -lt 0 ] && break
    segs[$victim]=""
  done
else
  for i in "${!segs[@]}"; do line_of[$i]=0; done
fi

first=1 prev_line=-1
for i in "${!segs[@]}"; do
  [ -z "${segs[$i]}" ] && continue
  if [ "${line_of[$i]}" -ne "$prev_line" ]; then
    [ "$first" -eq 0 ] && printf '\n'
    prev_line=${line_of[$i]}
  else
    printf '%s' "$sep_str"
  fi
  printf '%s' "${segs[$i]}"
  first=0
done
printf '%s' "${E}[0m"
