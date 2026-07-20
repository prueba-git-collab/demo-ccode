---
name: informe
description: Genera el informe mensual legible del lote procesado. Junta por id los resultados de clasificación y auditoría sobre los registros normalizados, agrega totales por categoría, gastos/ingresos y lista anomalías. Úsala al cerrar el procesamiento de un lote.
---

# Informe del lote

Objetivo: producir un informe claro (`data/salida/informe.md`) a partir de los
artefactos del pipeline. Junta la información, no la recalcula.

# Entradas

- `data/salida/normalizado.json` — base (siempre existe).
- `data/salida/clasificado.json` — aporta `categoria` y `explicacion` (si existe).
- `data/salida/auditado.json` — aporta `anomalias` (si existe).

Se cruzan por `id`. Si falta clasificación o auditoría, el informe se genera
igual y avisa de lo que falta (no rompe).

# Qué debe contener el informe

1. **Resumen**: nº de documentos, desglose por fuente, total de gastos, total
   de ingresos, saldo neto.
2. **Por categoría** (si hay clasificación): total e importe por categoría,
   ordenado por gasto.
3. **Anomalías y duplicados** (si hay auditoría): lista en lenguaje natural,
   con el documento de origen.
4. **Pie**: fecha de generación y qué fases faltaban, si alguna.

# Reglas

- Importes en Decimal; gasto negativo, ingreso positivo.
- **Nada de PII cruda** (IBAN/DNI) en el informe: refiere sin transcribir.
- Formato Markdown, legible por una persona de negocio, sin jerga técnica.

# Dónde va el código

- `src/informe.py`. El informe es un artefacto de `data/salida/`.
