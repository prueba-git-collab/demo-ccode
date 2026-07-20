# Procesador de documentos entrantes

Normaliza documentos heterogéneos (CSV de banco, PDF de facturas/contratos,
correos y tickets en texto) a un modelo común, los clasifica con explicación,
detecta duplicados y anomalías, y genera un informe.

## Modelo de datos común (fuente de verdad)

Todo parser debe devolver registros con esta forma. Si añades una fuente,
escribes solo su parser; el resto del pipeline no se toca.

- `id`: huella del contenido (para detectar duplicados)
- `fuente`: origen (`banco_csv`, `factura_pdf`, `contrato_pdf`, `ticket_txt`)
- `fecha`, `descripcion`, `importe` (Decimal, negativo = gasto), `moneda`
- `contraparte`, `categoria`, `explicacion`, `anomalias` (lista), `origen` (ruta)

## Convenciones

- Los parsers no asumen formato fijo: encoding, separador, fecha y decimales
  varían entre fuentes. Trátalo como datos sucios.
- La clasificación razona; no reglas rígidas por palabra clave.
- Nada de dependencias pesadas sin acordarlo antes.

## Datos y privacidad

- `data/entrada/` contiene documentos con PII (DNI, IBAN, nombres). Son datos
  sintéticos, así que el lote de ejemplo sí se versiona.
- La regla que importa es la de **salida**: nunca vuelques PII cruda a
  `data/salida/` ni a los logs. Ni el informe ni los artefactos intermedios
  pueden transcribir un IBAN o un DNI; refiérete al dato sin copiarlo
  (p. ej. "cuenta terminada en 5433").

## Entorno

- Código en `src/`, tests en `tests/`.
- Las dependencias viven en `.venv/`. Ejecuta SIEMPRE los scripts con
  `.venv/bin/python ...` (el `python`/`python3` del sistema no tiene pypdf,
  faker ni el MCP y fallará).
