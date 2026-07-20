"""Fase de ingesta: parsea todo `data/entrada/` y vuelca los registros
normalizados a `data/salida/normalizado.json`.

Es el artefacto que consumen las fases siguientes (clasificar, auditar),
que trabajan solo sobre el modelo común, nunca sobre los documentos crudos.
"""

from __future__ import annotations

import json
from pathlib import Path

from parsear import DESCARTES, parsear_documento

BASE = Path(__file__).resolve().parent.parent
ENTRADA = BASE / "data" / "entrada"
SALIDA = BASE / "data" / "salida"


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    registros = []
    for f in sorted(ENTRADA.iterdir()):
        if f.is_file():
            registros.extend(parsear_documento(f))

    datos = [r.to_dict() for r in registros]
    destino = SALIDA / "normalizado.json"
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(datos)} registros normalizados -> {destino.relative_to(BASE)}")

    # Lo que no se ha podido leer se salta, pero queda registrado: ningun
    # documento desaparece en silencio.
    desc = SALIDA / "descartes.json"
    desc.write_text(json.dumps(DESCARTES, ensure_ascii=False, indent=2), encoding="utf-8")
    if DESCARTES:
        print(f"{len(DESCARTES)} filas descartadas -> {desc.relative_to(BASE)}")


if __name__ == "__main__":
    main()
