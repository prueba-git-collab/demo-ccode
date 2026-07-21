"""Modelo de datos común. Cualquier fuente se normaliza a `Registro`.

Es la fuente de verdad del proyecto: si añades una fuente nueva, solo
escribes un parser que devuelva `Registro`; clasificar, auditar e informar
no se tocan.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

_IBAN = re.compile(r"\bES\d{22}\b", re.IGNORECASE)
_DNI = re.compile(r"\b(?:DNI\s+)?(\d{8}[A-Za-z])\b", re.IGNORECASE)


def _redactar(texto: str | None) -> str | None:
    """Sustituye IBAN y DNI por una referencia parcial.

    Se aplica solo al serializar: el valor crudo sigue en memoria para que `id`
    mantenga la misma huella y los duplicados se sigan detectando.
    """
    if not texto:
        return texto
    texto = _IBAN.sub(lambda m: f"cuenta terminada en {m.group(0)[-4:]}", texto)
    return _DNI.sub(lambda m: f"DNI terminado en {m.group(1)[-4:]}", texto)


@dataclass
class Registro:
    fuente: str                    # banco_csv, factura_pdf, contrato_pdf, ticket_txt
    fecha: date | None
    descripcion: str
    importe: Decimal | None        # negativo = gasto, positivo = ingreso
    moneda: str = "EUR"
    contraparte: str | None = None
    origen: str = ""               # ruta al documento crudo (trazabilidad)

    # Rellenados por fases posteriores del pipeline
    categoria: str | None = None
    explicacion: str | None = None
    anomalias: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        """Huella estable del contenido, para detectar duplicados.

        Se basa en lo que identifica al movimiento (fecha, importe, contraparte
        o descripción), no en el fichero de origen: así un mismo movimiento que
        aparece en dos fuentes distintas produce el mismo id.
        """
        clave = "|".join([
            self.fecha.isoformat() if self.fecha else "",
            f"{self.importe:.2f}" if self.importe is not None else "",
            (self.contraparte or self.descripcion or "").strip().lower(),
        ])
        return hashlib.sha1(clave.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> dict:
        """Forma serializable (JSON): Decimal -> str, date -> ISO."""
        return {
            "id": self.id,
            "fuente": self.fuente,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "descripcion": _redactar(self.descripcion),
            "importe": f"{self.importe:.2f}" if self.importe is not None else None,
            "moneda": self.moneda,
            "contraparte": _redactar(self.contraparte),
            "categoria": self.categoria,
            "explicacion": self.explicacion,
            "anomalias": self.anomalias,
            "origen": self.origen,
        }
