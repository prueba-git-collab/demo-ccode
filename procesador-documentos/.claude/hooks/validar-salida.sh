#!/usr/bin/env bash
# Hook PostToolUse (Write|Edit): cuando se escribe un JSON en data/salida/,
# valida que cada registro cumple el modelo común. Puerta de calidad de datos
# propia del proceso (no es algo que haga el harness).
# Si algún registro está roto, devuelve el detalle a Claude (exit 2).

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')

case "$file" in
  */data/salida/*.json) ;;
  *) exit 0 ;;
esac
[ -f "$file" ] || exit 0

if ! err=$(python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/_validar_salida.py" "$file" 2>&1); then
  echo "Salida inválida en $(basename "$file"):" >&2
  echo "$err" >&2
  exit 2
fi
exit 0
