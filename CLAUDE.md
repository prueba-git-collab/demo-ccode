# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este repositorio

Material de una sesión formativa sobre Claude Code. Dos partes independientes:

- `presentacion/` — slides en Marp (`slides.md` es la fuente; `slides.pdf` el resultado).
- `procesador-documentos/` — proyecto de demostración. Tiene su **propio `CLAUDE.md`**
  con el modelo de datos y las reglas de privacidad: leerlo antes de tocar nada ahí.

## Comandos

Presentación (desde `presentacion/`):

```bash
npx @marp-team/marp-cli slides.md -o slides.html            # HTML
npx @marp-team/marp-cli slides.md --preview                 # edicion en vivo
npx @marp-team/marp-cli slides.md --pdf --allow-local-files -o slides.pdf
```

`slides.html` no se versiona. Cada `---` en `slides.md` separa una diapositiva.
Las citas `>` deben escribirse en **una sola línea**: Marp mete un salto duro por
cada línea de Markdown y la diapositiva se corta.

Proyecto (desde `procesador-documentos/`):

```bash
python3 -m venv .venv
.venv/bin/pip install pypdf fastmcp google-api-python-client \
    google-auth-httplib2 google-auth-oauthlib

.venv/bin/python src/normalizar.py    # solo la fase determinista
.venv/bin/python src/informe.py       # informe a partir de los artefactos ya generados
```

Ejecutar **siempre** con `.venv/bin/python`: el intérprete del sistema no tiene
las dependencias, y `settings.json` solo autoriza `Bash(.venv/bin/python src/*)`.

El flujo completo se lanza desde Claude Code con el comando `/procesar`.

## Arquitectura del pipeline

Cuatro fases sobre un modelo común, encadenadas por `.claude/commands/procesar.md`:

1. **Normalizar** (`src/normalizar.py` → `src/parsear.py`) — lee `data/entrada/`
   y vuelca `normalizado.json` + `descartes.json`.
2. **Clasificar y auditar en paralelo** — subagentes `clasificador` y `auditor`
   (`.claude/agents/`) leen el mismo `normalizado.json` y escriben
   `clasificado.json` y `auditado.json`. Son independientes: se lanzan a la vez.
3. **Informar** (`src/informe.py`) — cruza los tres artefactos **por `id`** y
   genera `informe.md`. No recalcula nada, solo agrega.

La pieza que sostiene todo es `Registro` en `src/modelo.py`. Su `id` es una huella
del contenido del movimiento (fecha, importe, contraparte), no del fichero: por eso
un mismo movimiento visto en dos fuentes colisiona y se detecta como duplicado, y
por eso las fases posteriores pueden cruzarse por `id`.

Consecuencia práctica: **añadir una fuente = escribir su parser**. Ni clasificar,
ni auditar, ni informar se tocan. La skill `parsear-fuente` cubre ese caso.

Todo `data/salida/` es reconstruible: borrarlo entero es la forma de repetir.

## Hooks

Configurados en `.claude/settings.json`:

- `proteger-datos.sh` (PreToolUse, matcher `Write`) — **bloquea** la escritura en
  `data/salida/` si el contenido lleva IBAN español o DNI en claro. Los datos de
  entrada llevan PII sintética, pero nada de eso puede acabar en `data/salida/`
  ni en los logs.
- `validar-salida.sh` / `validar-completo.sh` (PostToolUse, `Write|Edit`) — esquema
  de los artefactos y que ningún registro quede sin procesar.
- `trazar.sh` (PostToolUse, `Write|Edit`) — traza en `data/salida/_proceso.log`.

Requieren `jq` instalado. Sin él fallan en silencio y no se valida nada.

### Alcance real de los hooks

Los hooks interceptan **herramientas de Claude Code**, no escrituras en disco. De
ahí dos límites que conviene tener presentes:

- **Los scripts de Python no pasan por ningún hook.** `normalizar.py` e `informe.py`
  se lanzan con `Bash` y escriben con `open()`: nunca invocan `Write`, así que
  `proteger-datos.sh` no ve su contenido. Un `PreToolUse` sobre `Bash` tampoco
  serviría, porque en ese momento el fichero aún no existe. Para esa vía la
  protección vive en el código: `_redactar()` en `src/modelo.py` sanea `descripcion`
  y `contraparte` dentro de `to_dict()`, que es el único punto por el que pasa todo
  lo que se serializa.
- **Lo que sí cubre `proteger-datos.sh`** son las escrituras propias y las de los
  subagentes `clasificador` y `auditor`, que usan `Write` para sus artefactos. Es
  la parte no determinista del pipeline, donde ninguna línea de código puede
  garantizar que un modelo no transcriba un dato que ha leído.

`_redactar()` cubre IBAN español (`ES` + 22 dígitos) y DNI (8 dígitos + letra). No
cubre NIE, IBAN extranjero ni tarjetas: suficiente para el lote sintético de la
demo, insuficiente para datos reales.

## MCP de Gmail

`mcp_gmail/server.py` expone `traer_facturas(asunto)`: descarga adjuntos a
`data/entrada/`. Registrado en `.mcp.json`; Claude Code pide confiar en él la
primera vez que se abre el proyecto (si se rechaza, la herramienta no existe).

Necesita credenciales propias de Google Cloud en `credentials/`, que no se
versiona y está en el `deny` de `settings.json`. Puesta en marcha en
`mcp_gmail/README.md`. Sin credenciales el paso se salta: el lote del repo trae
27 documentos.

## Datos

Los documentos de `data/entrada/` son inventados, con formatos sucios y errores
plantados a propósito. Los IBAN, DNI y nombres no corresponden a nadie.
