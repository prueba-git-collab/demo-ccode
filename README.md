```
   ________                __        ______          __
  / ____/ /___ ___  ______/ /__     / ____/___  ____/ /__
 / /   / / __ `/ / / / __  / _ \   / /   / __ \/ __  / _ \
/ /___/ / /_/ / /_/ / /_/ /  __/  / /___/ /_/ / /_/ /  __/
\____/_/\__,_/\__,_/\__,_/\___/   \____/\____/\__,_/\___/

                     g u i a   d e   e q u i p o
```

Material de la sesión: la presentación y el proyecto que se construye en vivo.

```
presentacion/          slides.md (fuente) + slides.pdf
procesador-documentos/ el proyecto de la demo
```

---

## La presentación

`presentacion/slides.pdf` se abre tal cual. Para verla en el navegador o
editarla, hay que generarla desde `slides.md`, que es la fuente.

Está hecha con [Marp](https://marp.app/): Markdown normal, donde `---` separa
una diapositiva de la siguiente. Se edita con cualquier editor de texto.

### Generar el HTML y abrirlo

Requiere Node (`npx` viene incluido). No hace falta instalar nada de forma
permanente: `npx` descarga Marp la primera vez y lo cachea.

```bash
cd presentacion
npx @marp-team/marp-cli slides.md -o slides.html
```

Abrir el resultado en el navegador:

```bash
xdg-open slides.html     # Linux
open slides.html         # macOS
start slides.html        # Windows
```

Ya en el navegador: `→` y `←` pasan diapositivas, `F` activa pantalla
completa y `P` abre la vista de presentador con las notas.

### Verla mientras la editas

El modo servidor recarga solo al guardar. Cómodo para retocar:

```bash
npx @marp-team/marp-cli slides.md --preview     # ventana propia
npx @marp-team/marp-cli -s .                    # servidor en localhost:8080
```

### Regenerar el PDF

```bash
npx @marp-team/marp-cli slides.md --pdf --allow-local-files -o slides.pdf
```

`slides.html` no se versiona: se reconstruye con el comando de arriba.

---

## El proyecto: `procesador-documentos/`

Recibe un lote heterogéneo de documentos (extractos de banco en CSV, facturas
y contratos en PDF, correos y tickets en texto), lo normaliza a una ficha
común, lo clasifica, lo audita y genera un informe.

Sirve para ver funcionando las piezas de Claude Code: `CLAUDE.md`, permisos,
hooks, subagentes, skills, comandos y un MCP propio.

### Preparar el entorno

```bash
cd procesador-documentos
python3 -m venv .venv
.venv/bin/pip install pypdf fastmcp google-api-python-client \
    google-auth-httplib2 google-auth-oauthlib
```

Los scripts se ejecutan **siempre** con `.venv/bin/python`: el `python` del
sistema no tiene estas librerías.

### Ejecutarlo

Son dos pasos, ambos desde Claude Code abierto en la carpeta del proyecto.

**1. Traer los documentos del correo.** En lenguaje natural, sin comandos:

```
trae del correo las facturas con asunto FACTURA DEMO a data/entrada/
```

Claude reconoce que eso lo resuelve la herramienta `traer_facturas` del MCP
`gmail-facturas`, la llama y deja los adjuntos en `data/entrada/`, junto a los
documentos que ya vienen en el repo.

Este paso necesita las credenciales de Google (ver más abajo). Sin ellas se
salta: el lote del repo ya trae 27 documentos con los que probar.

**2. Procesar el lote:**

```
/procesar
```

Ese comando encadena el proceso entero: normaliza los documentos, lanza los
subagentes `clasificador` y `auditor` **en paralelo**, genera el informe y
cierra con un resumen. Si una fase falla, se detiene y lo dice.

Por el camino se ven trabajar los hooks: validan cada artefacto que se escribe,
comprueban que ningún registro se quede sin procesar y bloquean la escritura si
detectan un IBAN o un DNI en claro.

Los scripts de `src/` también se pueden lanzar sueltos con
`.venv/bin/python src/normalizar.py`, pero entonces solo corre la parte
determinista: sin clasificación ni auditoría, y el informe lo advierte.

### Qué se genera

Todo en `data/salida/`, y se puede borrar entero: se reconstruye.

| Fichero | Qué es | Quién lo escribe |
|---|---|---|
| `normalizado.json` | Todas las fichas | el código |
| `descartes.json` | Lo que no se pudo leer, con su motivo | el código |
| `clasificado.json` | Categoría y explicación | subagente `clasificador` |
| `auditado.json` | Anomalías y duplicados | subagente `auditor` |
| `informe.md` | El entregable | el código, cruzando por `id` |
| `_proceso.log` | Qué se generó y cuándo | el hook `trazar.sh` |

### El MCP de Gmail

`mcp_gmail/` es un servidor MCP propio que expone la herramienta
`traer_facturas(asunto)`: busca los correos que coinciden con ese asunto,
descarga sus adjuntos y los deja en `data/entrada/`. Solo pide permiso de
lectura sobre el buzón.

Ya está registrado en `.mcp.json`, así que Claude Code lo levanta al abrir el
proyecto. Con `/mcp` se comprueba que está conectado.

Para usarlo hacen falta **credenciales propias** de Google Cloud: habilitar la
API, configurar la pantalla de consentimiento y crear un cliente OAuth de
escritorio. El paso a paso, con las pantallas actuales de la consola, está en
[`mcp_gmail/README.md`](procesador-documentos/mcp_gmail/README.md).

Esas credenciales no se versionan nunca: `credentials/` está en el
`.gitignore` **y** en el `deny` de `.claude/settings.json`.

---

## Sobre los datos

Los documentos de `data/entrada/` son **inventados**. Los IBAN, DNI, nombres y
teléfonos que aparecen no corresponden a nadie: están puestos a propósito, con
formatos sucios y errores plantados, para que el proceso se enfrente a datos
como los de verdad.
