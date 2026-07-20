"""Valida que un JSON de salida cumple el esquema que le corresponde.

Lo usa el hook validar-salida.sh. Cada artefacto del pipeline tiene su forma:
- normalizado.json → modelo común completo.
- clasificado.json → delta {id, categoria, explicacion}.
- auditado.json    → delta {id, anomalias}.
Los agentes escriben SOLO su delta (reemitir el registro entero dispara la
salida y supera el límite de tokens); el informe los cruza por `id`. Por eso
aquí NO se exige el modelo completo a los deltas.

Sale con código != 0 y un mensaje si algún registro está mal formado.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

CAMPOS_MODELO = {"id", "fuente", "fecha", "descripcion", "importe", "moneda",
                 "contraparte", "categoria", "explicacion", "anomalias", "origen"}
FUENTES = {"banco_csv", "factura_pdf", "contrato_pdf", "ticket_txt"}
RE_IMPORTE = re.compile(r"^-?\d+\.\d{2}$")

path = sys.argv[1]
nombre = Path(path).name

try:
    datos = json.loads(open(path, encoding="utf-8").read())
except Exception as e:
    print(f"JSON ilegible: {e}")
    sys.exit(1)

if not isinstance(datos, list):
    print("La salida debe ser una lista de registros.")
    sys.exit(1)


def val_modelo(i, r):
    faltan = CAMPOS_MODELO - r.keys()
    if faltan:
        return [f"registro {i}: faltan campos {sorted(faltan)}"]
    errs = []
    if r["fuente"] not in FUENTES:
        errs.append(f"registro {i}: fuente desconocida '{r['fuente']}'")
    if r["importe"] is not None and not RE_IMPORTE.match(str(r["importe"])):
        errs.append(f"registro {i}: importe mal formado '{r['importe']}'")
    if r["fecha"] is not None:
        try:
            date.fromisoformat(r["fecha"])
        except ValueError:
            errs.append(f"registro {i}: fecha inválida '{r['fecha']}'")
    if not isinstance(r["anomalias"], list):
        errs.append(f"registro {i}: 'anomalias' debe ser lista")
    return errs


def val_clasificado(i, r):
    faltan = {"id", "categoria", "explicacion"} - r.keys()
    if faltan:
        return [f"registro {i}: faltan campos {sorted(faltan)}"]
    errs = []
    if not (isinstance(r["categoria"], str) and r["categoria"].strip()):
        errs.append(f"registro {i}: 'categoria' vacía o no es texto")
    if not isinstance(r["explicacion"], str):
        errs.append(f"registro {i}: 'explicacion' debe ser texto")
    return errs


def val_auditado(i, r):
    faltan = {"id", "anomalias"} - r.keys()
    if faltan:
        return [f"registro {i}: faltan campos {sorted(faltan)}"]
    if not isinstance(r["anomalias"], list):
        return [f"registro {i}: 'anomalias' debe ser lista"]
    if not all(isinstance(a, str) for a in r["anomalias"]):
        return [f"registro {i}: 'anomalias' debe ser lista de frases"]
    return []


# Elige el validador por nombre de fichero; desconocido → modelo completo.
validador = {
    "normalizado.json": val_modelo,
    "clasificado.json": val_clasificado,
    "auditado.json": val_auditado,
}.get(nombre, val_modelo)

errores = []
for i, r in enumerate(datos):
    if not isinstance(r, dict):
        errores.append(f"registro {i}: no es un objeto")
        continue
    errores.extend(validador(i, r))

if errores:
    print(f"{len(errores)} registro(s) no cumplen el esquema de {nombre}:")
    print("\n".join(f"  - {e}" for e in errores[:10]))
    sys.exit(1)
sys.exit(0)
