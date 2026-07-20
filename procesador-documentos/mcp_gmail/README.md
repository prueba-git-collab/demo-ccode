# MCP `gmail-facturas`

Servidor MCP propio (FastMCP) que trae los adjuntos de facturas del correo a
`data/entrada/`. Nace para cubrir lo que el conector de Gmail de fabrica de
Claude NO hace: **descargar el adjunto binario**.

Tool que expone: `traer_facturas(asunto="FACTURA DEMO")`.

## Setup de credenciales (una vez)

Consola de Google Cloud (los nombres cambian cada poco; esto es lo vigente).
Ignora el banner del credito de $300: la Gmail API no necesita facturacion.

1. [Google Cloud Console](https://console.cloud.google.com/) → crear un proyecto
   y dejarlo seleccionado arriba.
2. **APIs y servicios → Biblioteca** → buscar "Gmail API" → **Habilitar**.
3. **APIs y servicios → Credenciales**. Sale un aviso amarillo con el boton
   **"Configurar pantalla de consentimiento"** → pulsalo (es OBLIGATORIO antes
   de crear el cliente OAuth). En el asistente (Google Auth Platform):
   - Informacion de la app: nombre + tu correo.
   - Audience / Publico: **External**.
   - Datos de contacto: tu correo. Finalizar.
   - En **Publico → Usuarios de prueba**: anade tu propia direccion de Gmail.
4. Configurar la pantalla te saca de la seccion, asi que **vuelve a APIs y
   servicios → Credenciales**. Ahora si: **Crear credenciales → ID de cliente
   de OAuth** → tipo **Aplicacion de escritorio** → Crear → **Descargar JSON**.
5. Guardalo como `credentials/credentials.json` (esta carpeta esta en
   `.gitignore`; nunca va al repo).

## Primer arranque

Genera el token una vez (abre el navegador para autorizar):

```bash
.venv/bin/python -c "from mcp_gmail.server import _servicio; _servicio(); print('token OK')"
```

- Al aceptar se crea `credentials/token.json` (login cacheado); ya no vuelve a
  pedir login.
- Pantalla "Google no ha verificado esta app": es normal en modo Testing →
  *Configuracion avanzada* → *Ir a (no seguro)* → continuar.
- **Error 403 access_denied**: la cuenta con la que autorizas NO esta en la
  lista de testers. Anadela en **Pantalla de consentimiento → Publico →
  Usuarios de prueba** (debe ser la MISMA cuenta con la que abres el navegador),
  guarda, espera ~1 min y reintenta.

## Registro en el proyecto

Ya declarado en `.mcp.json`. Ver estado con `/mcp`; las tools aparecen como
`mcp__gmail-facturas__traer_facturas`.

## Dependencias

```bash
.venv/bin/pip install fastmcp google-api-python-client \
  google-auth google-auth-oauthlib
```
