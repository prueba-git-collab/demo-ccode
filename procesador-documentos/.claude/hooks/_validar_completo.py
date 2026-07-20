"""Comprueba que un delta cubre TODOS los ids de normalizado.json.

Puerta de reconciliacion del pipeline: clasificado.json y auditado.json deben
contener, como minimo, todos los ids presentes en normalizado.json. Si falta
alguno, sale != 0 con la lista, para que el agente complete SOLO lo que dejo
suelto (no tiene que rehacer el resto).

La comparacion es por `id`, no por numero de filas: los duplicados por
contenido colapsan al mismo id y no falsean la cobertura.
"""

import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
norm = path.parent / "normalizado.json"
if not norm.exists():
    sys.exit(0)  # sin base con la que comparar, no bloquea


def ids(p: Path) -> set[str]:
    try:
        datos = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"{p.name} ilegible: {e}")
        sys.exit(1)
    return {r["id"] for r in datos if isinstance(r, dict) and "id" in r}


esperados = ids(norm)
faltan = esperados - ids(path)
if faltan:
    muestra = sorted(faltan)
    print(f"faltan {len(faltan)} de {len(esperados)} id(s) de normalizado.json:")
    print("  " + ", ".join(muestra[:12]) + (" ..." if len(muestra) > 12 else ""))
    sys.exit(1)
sys.exit(0)
