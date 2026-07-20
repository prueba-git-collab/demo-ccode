"""Parsers: convierten cada fuente al modelo común `Registro`.

Sigue la skill `parsear-fuente`: no asume formato fijo (resuelve encoding y
separador, normaliza fecha y decimales), y no tira el fichero por una fila rota.

Cubre extractos de banco en CSV/TSV, facturas y contratos en PDF, y tickets
y correos en texto plano.
"""

from __future__ import annotations

import csv
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pypdf import PdfReader

from modelo import Registro

# --- utilidades tolerantes a datos sucios -------------------------------------

def _leer_texto(path: Path) -> str:
    """Prueba encodings habituales; los extractos vienen en utf-8 o latin-1."""
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def _sniff_delimitador(cabecera: str) -> str:
    for d in ("\t", ";", ","):
        if d in cabecera:
            return d
    return ","


def _a_fecha(txt: str) -> date | None:
    txt = txt.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y", "%d/%m/%y", "%d-%m-%Y"):
        try:
            return datetime.strptime(txt, fmt).date()
        except ValueError:
            continue
    return None


def _a_importe(txt: str) -> Decimal | None:
    txt = txt.strip().replace(" ", "")
    if not txt:
        return None
    # coma decimal española -> punto (solo si no hay ya punto decimal)
    if "," in txt and "." not in txt:
        txt = txt.replace(",", ".")
    try:
        return Decimal(txt)
    except InvalidOperation:
        return None


# --- mapeo de cabeceras (cada banco las llama distinto) -----------------------

_ROLES = {
    "fecha": {"fecha", "date", "booking date"},
    "descripcion": {"concepto", "description", "payee"},
    "importe": {"importe", "amount", "importe(eur)", "amount (eur)"},
    "moneda": {"moneda", "currency"},
}


def _roles_de_cabecera(cols: list[str]) -> dict[str, int]:
    """Asocia cada rol del modelo con el índice de columna del fichero."""
    roles: dict[str, int] = {}
    for i, c in enumerate(cols):
        norm = c.strip().lower()
        for rol, alias in _ROLES.items():
            if norm in alias and rol not in roles:
                roles[rol] = i
    return roles


# Descartes: filas que no se han podido leer. Se salta la fila, pero NO en
# silencio: queda el rastro para que el informe lo pueda contar.
DESCARTES: list[dict] = []


def _descartar(path: Path, nlinea: int, motivo: str) -> None:
    DESCARTES.append({"origen": str(path), "linea": nlinea, "motivo": motivo})


def parsear_banco_csv(path: Path) -> list[Registro]:
    texto = _leer_texto(path)
    lineas = [l for l in texto.splitlines() if l.strip()]
    if not lineas:
        return []
    delim = _sniff_delimitador(lineas[0])
    lector = csv.reader(lineas, delimiter=delim)
    filas = list(lector)
    cabecera = filas[0]
    roles = _roles_de_cabecera(cabecera)

    registros: list[Registro] = []
    for n, fila in enumerate(filas[1:], start=2):
        # deriva de formato: si reaparece la cabecera a mitad del fichero, la saltamos
        if fila and fila[0].strip().lower() in _ROLES["fecha"]:
            _descartar(path, n, "cabecera repetida a mitad del fichero")
            continue
        if "importe" not in roles or "fecha" not in roles:
            _descartar(path, n, "faltan columnas obligatorias (fecha/importe)")
            continue
        try:
            importe = _a_importe(fila[roles["importe"]])
            fecha = _a_fecha(fila[roles["fecha"]])
            desc = fila[roles["descripcion"]].strip() if "descripcion" in roles else ""
            moneda = fila[roles["moneda"]].strip() if "moneda" in roles and roles["moneda"] < len(fila) else "EUR"
        except IndexError:
            # fila rota: la saltamos, no tiramos el fichero, pero dejamos rastro
            _descartar(path, n, "fila incompleta")
            continue
        registros.append(Registro(
            fuente="banco_csv",
            fecha=fecha,
            descripcion=desc,
            importe=importe,
            moneda=moneda or "EUR",
            contraparte=desc or None,
            origen=str(path),
        ))
    return registros


# --- PDF: facturas y contratos ------------------------------------------------

def _texto_pdf(path: Path) -> str:
    lector = PdfReader(str(path))
    return "\n".join(pagina.extract_text() or "" for pagina in lector.pages)


_MESES = {m: i for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
     "agosto", "septiembre", "octubre", "noviembre", "diciembre"], start=1)}


def _buscar_fecha(texto: str) -> date | None:
    m = re.search(r"(\d{2}/\d{2}/\d{4})", texto)
    if m:
        return _a_fecha(m.group(1))
    # fecha larga en español: "5 de enero de 2026"
    m = re.search(r"(\d{1,2}) de (\w+) de (\d{4})", texto, re.IGNORECASE)
    if m and m.group(2).lower() in _MESES:
        return date(int(m.group(3)), _MESES[m.group(2).lower()], int(m.group(1)))
    return None


def parsear_pdf(path: Path) -> list[Registro]:
    texto = _texto_pdf(path)
    es_contrato = "CONTRATO" in texto.upper()

    if es_contrato:
        # importe anual del contrato; contraparte = quien presta el servicio
        m_imp = re.search(r"Importe:\s*([\d.,]+)\s*EUR", texto)
        m_parte = re.search(r"en representación de (.+?)\s*\(CIF", texto)
        importe = _a_importe(m_imp.group(1)) if m_imp else None
        return [Registro(
            fuente="contrato_pdf",
            fecha=_buscar_fecha(texto),
            descripcion="Contrato de prestación de servicios",
            importe=-importe if importe is not None else None,
            contraparte=m_parte.group(1).strip() if m_parte else None,
            origen=str(path),
        )]

    # factura: contraparte = emisor (primera línea), importe = TOTAL (gasto)
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    emisor = lineas[0] if lineas else None
    m_total = re.search(r"TOTAL:\s*([\d.,]+)\s*EUR", texto)
    m_fecha = re.search(r"Fecha:\s*(\d{2}/\d{2}/\d{4})", texto)
    importe = _a_importe(m_total.group(1)) if m_total else None
    return [Registro(
        fuente="factura_pdf",
        fecha=_a_fecha(m_fecha.group(1)) if m_fecha else _buscar_fecha(texto),
        descripcion=f"Factura {emisor}" if emisor else "Factura",
        importe=-importe if importe is not None else None,
        contraparte=emisor,
        origen=str(path),
    )]


# --- texto: correos y tickets -------------------------------------------------

def parsear_texto(path: Path) -> list[Registro]:
    texto = _leer_texto(path)
    m_imp = re.search(r"([\d]+[.,]\d{2})\s*EUR", texto)
    m_asunto = re.search(r"Asunto:\s*(.+)", texto)
    m_empresa = re.search(r"\ben ([A-ZÁÉÍÓÚÑ][\w .,&-]+?)[.\n]", texto)
    importe = _a_importe(m_imp.group(1)) if m_imp else None
    return [Registro(
        fuente="ticket_txt",
        fecha=_buscar_fecha(texto),
        descripcion=(m_asunto.group(1).strip() if m_asunto else path.stem),
        importe=-importe if importe is not None else None,
        contraparte=m_empresa.group(1).strip() if m_empresa else None,
        origen=str(path),
    )]


# --- despachador --------------------------------------------------------------

def parsear_documento(path: Path) -> list[Registro]:
    ext = path.suffix.lower()
    if ext in (".csv", ".tsv"):
        return parsear_banco_csv(path)
    if ext == ".pdf":
        return parsear_pdf(path)
    if ext == ".txt":
        return parsear_texto(path)
    _descartar(path, 0, f"extension no soportada ({ext or 'sin extension'})")
    return []


if __name__ == "__main__":
    entrada = Path(__file__).resolve().parent.parent / "data" / "entrada"
    todos: list[Registro] = []
    for f in sorted(entrada.iterdir()):
        regs = parsear_documento(f)
        if regs:
            print(f"{f.name:40} -> {len(regs)} registros")
            todos.extend(regs)
    print(f"\nTotal: {len(todos)} registros (banco + PDF + texto)")
    print("\nMuestra:")
    for r in todos[:3]:
        print(f"  [{r.id}] {r.fecha} {r.importe:>10} {r.moneda}  {r.descripcion[:35]}")
