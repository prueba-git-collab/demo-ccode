#!/usr/bin/env bash
# Hook PostToolUse (Write|Edit): traza en un log cada artefacto de salida que
# se escribe. Da una auditoría del propio pipeline: qué se generó y cuándo.

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')

case "$file" in
  */data/salida/*.json) ;;
  *) exit 0 ;;
esac

log="$CLAUDE_PROJECT_DIR/data/salida/_proceso.log"
printf '%s  escrito  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$(basename "$file")" >> "$log"
exit 0
