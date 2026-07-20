"""MCP de Gmail: trae las facturas del correo a data/entrada/.

El conector de Gmail que Claude trae de fabrica solo lee/busca; no descarga
el adjunto binario. Este servidor propio anade justo esa capacidad: una tool
que baja el fichero adjunto y lo deja en el lote de entrada del pipeline.
"""

from __future__ import annotations

import base64
from pathlib import Path

from fastmcp import FastMCP
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Rutas: credenciales fuera del repo; salida al lote de entrada del pipeline.
BASE = Path(__file__).resolve().parent.parent            # procesador-documentos/
CRED_DIR = BASE / "credentials"
CRED_FILE = CRED_DIR / "credentials.json"                # OAuth cliente (Desktop)
TOKEN_FILE = CRED_DIR / "token.json"                     # se genera al 1er login
ENTRADA = BASE / "data" / "entrada"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

mcp = FastMCP("gmail-facturas")


def _servicio():
    """Cliente autenticado de Gmail (OAuth Desktop). Cachea el token."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CRED_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _partes(payload: dict):
    """Recorre el arbol de partes del mensaje (multipart anidado incluido)."""
    yield payload
    for parte in payload.get("parts", []) or []:
        yield from _partes(parte)


def _guardar_adjuntos(service, msg_id: str) -> list[str]:
    """Baja a data/entrada/ cada adjunto (binario) del mensaje."""
    msg = service.users().messages().get(userId="me", id=msg_id).execute()
    guardados: list[str] = []
    for parte in _partes(msg.get("payload", {})):
        nombre = parte.get("filename")
        if not nombre:
            continue
        cuerpo = parte.get("body", {})
        adj_id = cuerpo.get("attachmentId")
        if adj_id:
            adj = (
                service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=msg_id, id=adj_id)
                .execute()
            )
            datos = adj["data"]
        elif cuerpo.get("data"):
            datos = cuerpo["data"]
        else:
            continue
        binario = base64.urlsafe_b64decode(datos)
        (ENTRADA / nombre).write_bytes(binario)
        guardados.append(nombre)
    return guardados


@mcp.tool
def traer_facturas(asunto: str = "FACTURA DEMO") -> dict:
    """Descarga los adjuntos de los correos cuyo asunto contiene `asunto`.

    Busca en Gmail los mensajes con ese asunto que tengan adjunto, guarda cada
    fichero binario en data/entrada/ del pipeline y devuelve que se ha traido.
    Usala cuando pidan traer facturas o documentos del correo al proyecto.
    """
    service = _servicio()
    query = f'subject:"{asunto}" has:attachment'
    res = service.users().messages().list(userId="me", q=query).execute()
    mensajes = res.get("messages", [])
    ficheros: list[str] = []
    for m in mensajes:
        ficheros.extend(_guardar_adjuntos(service, m["id"]))
    return {
        "asunto": asunto,
        "correos": len(mensajes),
        "ficheros": ficheros,
        "carpeta": str(ENTRADA),
    }


if __name__ == "__main__":
    mcp.run()
