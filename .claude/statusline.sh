#!/usr/bin/env bash
input=$(cat)

# Colors
CY='\033[0;36m'   # cyan
GR='\033[0;32m'   # green
YL='\033[0;33m'   # yellow
RD='\033[0;31m'   # red
DM='\033[0;90m'   # dim/gray
BD='\033[1m'      # bold
RS='\033[0m'      # reset

# Bar: ▪▪▪▫▫▫ (always exactly w characters)
bar() {
  local pct=${1:-0} w=${2:-25} i
  local f=$(( pct * w / 100 ))
  local c="$GR"
  [ "$pct" -ge 50 ] && c="$YL"
  [ "$pct" -ge 80 ] && c="$RD"
  printf "${c}"
  for (( i=0; i<f; i++ )); do printf '▪'; done
  printf "${DM}"
  for (( i=f; i<w; i++ )); do printf '▫'; done
  printf "${RS}"
}

# --- Extract fields ---
model_id=$(echo "$input" | jq -r '.model.id // ""')
effort=$(echo "$input" | jq -r '.output_style.name // "default"')

ctx_size=$(echo "$input" | jq -r '.context_window.context_window_size // 0')
cr=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')
cc=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
it=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0')
ot=$(echo "$input" | jq -r '.context_window.current_usage.output_tokens // 0')
used=$(( cr + cc + it ))
remain=$(( ctx_size - used ))
[ "$remain" -lt 0 ] && remain=0
pct=0; [ "$ctx_size" -gt 0 ] && pct=$(( used * 100 / ctx_size ))

# Per-bucket percentages (relative to ctx_size)
cr_pct=0; cc_pct=0; it_pct=0
[ "$ctx_size" -gt 0 ] && cr_pct=$(( cr * 100 / ctx_size ))
[ "$ctx_size" -gt 0 ] && cc_pct=$(( cc * 100 / ctx_size ))
[ "$ctx_size" -gt 0 ] && it_pct=$(( it * 100 / ctx_size ))

five_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // 0')
five_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // 0')
week_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // 0')
week_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // 0')

fk() {
  local k=$(awk "BEGIN {printf \"%.1f\", $1/1000}")
  echo "$k" | sed 's/\.0$//'
}

countdown() {
  local t=$1 now=$(date +%s)
  [ "$t" -le 0 ] 2>/dev/null && echo "-" && return
  local d=$(( t - now ))
  [ "$d" -le 0 ] && echo "now" && return
  local days=$(( d / 86400 )) hrs=$(( (d % 86400) / 3600 )) mins=$(( (d % 3600) / 60 ))
  if [ "$days" -gt 0 ]; then echo "${days}d ${hrs}h"
  elif [ "$hrs" -gt 0 ]; then echo "${hrs}h ${mins}m"
  else echo "${mins}m"
  fi
}

case "$model_id" in
  *sonnet-4-6*|*sonnet-4.6*) mdl="Sonnet 4.6" ;;
  *opus-4-6*|*opus-4.6*)     mdl="Opus 4.6" ;;
  *haiku-4-5*|*haiku-4.5*)   mdl="Haiku 4.5" ;;
  *)                          mdl=$(echo "$input" | jq -r '.model.display_name // "?"') ;;
esac

used_k=$(fk "$used")
ctx_k=$(fk "$ctx_size")
remain_k=$(fk "$remain")
cr_k=$(fk "$cr")
cc_k=$(fk "$cc")
it_k=$(fk "$it")
ot_k=$(fk "$ot")
five_cd=$(countdown "$five_reset")
week_cd=$(countdown "$week_reset")

# --- Output ---
# Column layout:
#   label(10)  pct(4)  gap(2)  bar(25)  gap(3)  detail
#
# context    7%  ▪▪▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫   77.2k / 1000k   922.8k free
# current    2%  ▪▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫   resets 4h 51m
# weekly    12%  ▪▪▪▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫   resets 3d 21h

# Pad label to fixed width (no ANSI in the padding math)
pad=19
label1="${mdl} (${effort})"
label2="current"
label3="weekly"
pad1=$(( pad - ${#label1} ))
pad2=$(( pad - ${#label2} ))
pad3=$(( pad - ${#label3} ))
[ "$pad1" -lt 0 ] && pad1=0
[ "$pad2" -lt 0 ] && pad2=0
[ "$pad3" -lt 0 ] && pad3=0

# Line 1: context
printf "${CY}${BD}%s${RS} ${DM}(%s)${RS}%*s" "$mdl" "$effort" "$pad1" ""
printf "%3s%%  " "$pct"
bar "$pct" 25
printf "   %sk / %sk ${GR}(%sk free)${RS}" "$used_k" "$ctx_k" "$remain_k"
printf "\n"

# Line 1b: token bucket breakdown (cache-read | cache-write | live-input | output)
# NOTE: the per-category breakdown shown by /context (system prompt, tools, memory
# files, etc.) is NOT exposed in the statusLine JSON.  The closest available split
# is the API token buckets: cached (read), new-to-cache (write), uncached live
# input, and output.  cached ≈ system+tools+memory; live ≈ recent messages.
if [ "$ctx_size" -gt 0 ]; then
  printf "${DM}  ctx breakdown%*s" "5" ""
  printf "${GR}cached-r ${RS}%*s ${DM}(%s%%)${RS}  " "-7" "${cr_k}k" "$cr_pct"
  printf "${YL}cached-w ${RS}%*s ${DM}(%s%%)${RS}  " "-7" "${cc_k}k" "$cc_pct"
  printf "${CY}live-in  ${RS}%*s ${DM}(%s%%)${RS}  " "-7" "${it_k}k" "$it_pct"
  printf "${DM}out %sk${RS}" "$ot_k"
  printf "\n"
fi

# Line 2: current
printf "${DM}%s${RS}%*s" "$label2" "$pad2" ""
printf "%3s%%  " "$five_pct"
bar "$five_pct" 25
printf "   ${DM}resets %s${RS}" "$five_cd"
printf "\n"

# Line 3: weekly
printf "${DM}%s${RS}%*s" "$label3" "$pad3" ""
printf "%3s%%  " "$week_pct"
bar "$week_pct" 25
printf "   ${DM}resets %s${RS}" "$week_cd"
