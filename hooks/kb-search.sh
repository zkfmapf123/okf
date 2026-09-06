#!/usr/bin/env bash
# UserPromptSubmit hook: grep ~/.claude/kb/ for the prompt's keywords, inject top-5 paths.
# Read-only. Saving still goes through /kb-end.
set -u
KB="${OKF_KB_ROOT:-$HOME/.claude/kb}"
prompt=$(jq -r '.prompt // empty')

case "$prompt" in /*) exit 0 ;; esac          # skip slash commands
[ "${#prompt}" -lt 15 ] && exit 0             # skip short turns

kw=$(printf '%s' "$prompt" | grep -oE '[A-Za-z0-9_-]{3,}|[가-힣]{2,}' | sort -u | head -8 | paste -sd'|' -)
[ -z "$kw" ] && exit 0

hits=$(grep -rciE "$kw" "$KB" --include='*.md' 2>/dev/null \
  | grep -v ':0$' | grep -vE '/(index|log)\.md:' | sort -t: -k2 -nr | head -5 | cut -d: -f1)

[ -z "$hits" ] && exit 0                      # miss: inject nothing (new-candidate tracking is /kb only)
echo "KB 후보 (프론트매터 확인 후 필요한 것만 read, related 로 1홉 확장 가능):"
echo "$hits"
echo "이 턴부터 KB-세션 추적 유지. 저장은 /kb-end 에서."
