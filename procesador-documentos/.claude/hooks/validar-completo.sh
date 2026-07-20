#!/usr/bin/env bash
# Hook PostToolUse (Write|Edit): al escribir clasificado.json o auditado.json,
# comprueba que cubren TODOS los ids de normalizado.json. Puerta de
# reconciliacion: que no quede ningun registro sin clasificar ni auditar.
# Si falta algun id, devuelve la lista a Claude (exit 2) para que la complete.

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')

case "$(basename "$file")" in
  clasificado.json|auditado.json) ;;
  *) exit 0 ;;
esac
[ -f "$file" ] || exit 0

if ! err=$(python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/_validar_completo.py" "$file" 2>&1); then
  echo "Cobertura incompleta en $(basename "$file"):" >&2
  echo "$err" >&2
  exit 2
fi
exit 0
