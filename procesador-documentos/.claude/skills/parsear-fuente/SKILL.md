---
name: parsear-fuente
description: Normaliza un documento de entrada (CSV de banco, PDF de factura/contrato, correo o ticket en texto) al modelo común Registro. Úsala al añadir soporte para una fuente nueva o al arreglar el parseo de una existente.
---

# Parsear una fuente al modelo común

Objetivo: convertir cualquier documento de `data/entrada/` en una lista de
`Registro` (ver `src/modelo.py`). El resto del pipeline (clasificar, auditar,
informar) depende SOLO de ese modelo, nunca del formato original.

## Principios

- **No asumas formato fijo.** Encoding, separador, formato de fecha y de
  decimales cambian entre fuentes e incluso dentro de un mismo fichero.
- **Detecta, no adivines a ciegas:** sniffing de separador, prueba de
  encodings (`utf-8` y `latin-1`), y varios formatos de fecha.
- **Falla claro:** si una fila no se puede parsear, regístrala y sigue; no
  tires todo el fichero por una línea rota.

## Checklist al añadir/arreglar un parser

1. Identifica la fuente y su `fuente` en el modelo (`banco_csv`, `factura_pdf`,
   `contrato_pdf`, `ticket_txt`).
2. Resuelve encoding y separador antes de leer.
3. Mapea cada columna/campo del origen al `Registro`:
   - `fecha` (parsea el formato real), `importe` (Decimal, negativo = gasto,
     normaliza coma/punto decimal), `descripcion`, `contraparte`, `moneda`.
   - `origen` = ruta del fichero.
4. No rellenes `categoria`/`explicacion`/`anomalias`: eso es de fases posteriores.
5. Añade un test con un fragmento representativo (incluye el caso sucio).

## Convenciones de importe

- Gasto → importe negativo. Ingreso → positivo.
- Decimal siempre (nunca float): `Decimal("-186.29")`.
- Coma decimal española (`-186,29`) → normaliza a punto antes de `Decimal`.

## Dónde va el código

- Parsers en `src/parsear.py`, uno por familia de fuente.
- Un despachador elige el parser por extensión / heurística del contenido.
