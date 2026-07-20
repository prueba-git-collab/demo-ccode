---
description: Procesa el lote de data/entrada de punta a punta (normaliza, clasifica y audita en paralelo, e informa).
---

Ejecuta el pipeline completo del procesador de documentos sobre `data/entrada/`.
Sigue estos pasos en orden y no te saltes ninguno:

1. **Normalizar**: ejecuta `.venv/bin/python src/normalizar.py`. Confirma cuántos
   registros se han volcado a `data/salida/normalizado.json`.

2. **Clasificar y auditar EN PARALELO**: lanza a la vez, en una sola tanda,
   los dos subagentes sobre `data/salida/normalizado.json`:
   - el subagente `clasificador` → escribe `data/salida/clasificado.json`.
   - el subagente `auditor` → escribe `data/salida/auditado.json`.
   Son independientes (leen el mismo input); no esperes a uno para lanzar el otro.

3. **Informar**: cuando ambos hayan terminado, ejecuta `.venv/bin/python src/informe.py`
   para generar `data/salida/informe.md`.

4. **Resumen**: muestra en 3-4 líneas el resultado: nº de documentos, total de
   gastos/ingresos, cuántas anomalías se detectaron y dónde está el informe.

Notas:
- No inventes datos: si una fase falla, dilo y detente.
- Recuerda que los hooks vigilan la escritura en `data/salida/` (esquema y PII).
