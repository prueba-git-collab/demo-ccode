"""Genera el informe del lote (data/salida/informe.md).

Sigue la skill `informe`: junta por `id` los artefactos del pipeline
(normalizado + clasificado + auditado), agrega y formatea. No recalcula
categorías ni anomalías: solo las reúne.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SALIDA = BASE / "data" / "salida"


def _cargar(nombre: str) -> list[dict]:
    f = SALIDA / nombre
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def _dec(x) -> Decimal:
    return Decimal(x) if x else Decimal("0")


def main() -> None:
    base = _cargar("normalizado.json")
    if not base:
        print("No hay normalizado.json. Ejecuta antes la normalización.")
        return

    clasif = {r["id"]: r for r in _cargar("clasificado.json")}
    audit = {r["id"]: r for r in _cargar("auditado.json")}

    # Cruce por id
    for r in base:
        if r["id"] in clasif:
            r["categoria"] = clasif[r["id"]].get("categoria")
            r["explicacion"] = clasif[r["id"]].get("explicacion")
        if r["id"] in audit:
            r["anomalias"] = audit[r["id"]].get("anomalias", [])

    # Agrupa por id: el duplicado duro (mismo movimiento en dos fuentes) comparte
    # id, así que se muestra una vez citando todos sus ficheros.
    grupos: dict[str, list] = {}
    for r in base:
        grupos.setdefault(r["id"], []).append(r)

    # Los importes se suman una vez por movimiento, no por documento: un mismo
    # movimiento visto en dos extractos no es dinero que entre dos veces. Los
    # duplicados blandos tienen id distinto y sí suman: solo se avisa de ellos.
    unicos = [rs[0] for rs in grupos.values()]
    colapsados = len(base) - len(unicos)

    # Agregados
    por_fuente = defaultdict(int)
    for r in base:
        por_fuente[r["fuente"]] += 1

    total_gasto = Decimal("0")
    total_ingreso = Decimal("0")
    por_categoria: dict[str, list] = defaultdict(lambda: [0, Decimal("0")])
    for r in unicos:
        imp = _dec(r["importe"])
        if imp < 0:
            total_gasto += imp
        else:
            total_ingreso += imp
        cat = r["categoria"] or "Sin clasificar"
        por_categoria[cat][0] += 1
        por_categoria[cat][1] += imp

    # Redacción
    L = []
    L.append("# Informe del lote de documentos\n")
    L.append("## Resumen\n")
    L.append(f"- Documentos procesados: **{len(base)}**")
    L.append("- Por fuente: " + ", ".join(f"{k} ({v})" for k, v in sorted(por_fuente.items())))
    L.append(f"- Total gastos: **{total_gasto:.2f} EUR**")
    L.append(f"- Total ingresos: **{total_ingreso:.2f} EUR**")
    L.append(f"- Saldo neto: **{(total_gasto + total_ingreso):.2f} EUR**")
    if colapsados:
        detalle = ", ".join(
            f"{rs[0]['id']} ({_dec(rs[0]['importe']):.2f} EUR en "
            + ", ".join(sorted({Path(r["origen"]).name for r in rs})) + ")"
            for rs in grupos.values() if len(rs) > 1
        )
        L.append(f"- Movimientos contados una sola vez pese a aparecer en varias "
                 f"fuentes: **{colapsados}** — {detalle}. Revisar manualmente si "
                 f"se trata de operaciones distintas del mismo importe y fecha.")

    # Lo que no se pudo leer: se salta, pero se dice.
    descartes = _cargar("descartes.json")
    if descartes:
        ficheros = sorted({Path(d["origen"]).name for d in descartes})
        L.append(f"- Filas no leídas: **{len(descartes)}** "
                 f"({', '.join(ficheros)}) — detalle en `descartes.json`")
    else:
        L.append("- Filas no leídas: **0**")
    L.append("")

    hay_clasif = bool(clasif)
    L.append("## Por categoría\n")
    if hay_clasif:
        filas = sorted(por_categoria.items(), key=lambda kv: kv[1][1])
        L.append("| Categoría | Nº | Importe |")
        L.append("|---|---:|---:|")
        for cat, (n, imp) in filas:
            L.append(f"| {cat} | {n} | {imp:.2f} |")
        L.append("")
        residual = [c for c in ("Otros", "Sin clasificar") if c in por_categoria]
        if residual:
            L.append("_" + " / ".join(residual) + ": registros sin datos "
                     "suficientes para categorizar; ver anomalías._\n")
    else:
        L.append("_Pendiente: no hay clasificación (ejecuta el subagente clasificador)._\n")

    L.append("## Anomalías y duplicados\n")
    if audit:
        hubo = False
        for rs in grupos.values():
            textos = []
            for r in rs:
                for a in r["anomalias"]:
                    if a not in textos:          # une y no repite entre duplicados
                        textos.append(a)
            if not textos:
                continue
            hubo = True
            r0 = rs[0]
            contraparte = r0.get("contraparte") or "sin contraparte"
            imp = r0.get("importe")
            meta = contraparte + (f" · {imp} EUR" if imp else "")
            ficheros = ", ".join(sorted({Path(r["origen"]).name for r in rs if r["origen"]}))
            for a in textos:
                L.append(f"- {a}")
            L.append(f"  _{meta} — {ficheros}_")
        if not hubo:
            L.append("_Sin hallazgos._")
        L.append("")
    else:
        L.append("_Pendiente: no hay auditoría (ejecuta el subagente auditor)._\n")

    faltan = [n for n, ok in [("clasificación", hay_clasif), ("auditoría", bool(audit))] if not ok]
    L.append("---")
    L.append(f"_Generado {datetime.now():%Y-%m-%d %H:%M}_"
             + (f" · Fases pendientes: {', '.join(faltan)}." if faltan else "."))

    destino = SALIDA / "informe.md"
    destino.write_text("\n".join(L), encoding="utf-8")
    print(f"Informe -> {destino.relative_to(BASE)}")


if __name__ == "__main__":
    main()
