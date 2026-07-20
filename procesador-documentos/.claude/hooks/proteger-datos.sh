#!/usr/bin/env bash
# Hook PreToolUse (Write): antes de escribir en data/salida/, frena si el
# contenido lleva PII cruda (IBAN español o DNI). El deny estático por path no
# vale aquí: hay que mirar el CONTENIDO, y eso es justo lo que hace un hook.

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
content=$(printf '%s' "$input" | jq -r '.tool_input.content // empty')

case "$file" in
  */data/salida/*) ;;
  *) exit 0 ;;
esac

# IBAN español (ES + 22 dígitos) o DNI (8 dígitos + letra)
if printf '%s' "$content" | grep -qE 'ES[0-9]{22}|\b[0-9]{8}[A-Za-z]\b'; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"Bloqueado: el contenido a escribir en data/salida/ contiene PII cruda (IBAN/DNI). Anonimízala (p. ej. ****last4) antes de escribir."}}'
  exit 0
fi
exit 0
