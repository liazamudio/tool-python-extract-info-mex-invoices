# Lector de CFDIs XML

Convierte lotes de CFDI (XML) del SAT en un CSV y un DataFrame de pandas listos para analizar, para quien concentra facturas fiscales mexicanas mes a mes y necesita un consolidado sin abrir archivo por archivo.

![demo](docs/demo.gif)
<!-- COMPLETAR: no se encontró GIF ni captura en el repositorio. Agrega una imagen de la salida en consola (print_cfdi) o del CSV/DataFrame resultante en docs/demo.gif -->

## Problema / Motivación

Revisar CFDI en XML uno por uno para sacar totales, IVA o emisores es lento y propenso a error cuando se acumulan varias facturas por periodo. Este script automatiza la extracción: recorre carpetas y subcarpetas de XMLs, homologa los datos (soporta CFDI 3.3 y 4.0, que usan namespaces distintos) y entrega un CSV consolidado más un resumen estadístico en consola.

<!-- COMPLETAR: motivación personal/de negocio detrás del proyecto — para qué caso de uso específico lo usas (declaración de impuestos, control de gastos personal, contabilidad de un negocio, etc.) y qué lo disparó -->

## Demo

<!-- COMPLETAR: no hay demo pública (herramienta de uso local vía CLI/notebook, sin despliegue). Si quieres, agrega aquí un GIF de la ejecución o un link a un notebook de ejemplo (Colab, nbviewer, etc.) -->

## Stack técnico

- **Frontend:** N/A — herramienta de línea de comandos, sin interfaz web
- **Backend:** Python 3.13, `xml.etree.ElementTree` (parsing XML de la librería estándar) + `pandas` 2.3 para transformación y exportación
- **Base de datos:** N/A — no usa base de datos; persiste resultados como CSV en `procesados/processed-data/`
- **Infraestructura/Deploy:** N/A — ejecución local. No se detectó Dockerfile, workflow de CI/CD ni configuración de despliegue en el repositorio

## Características principales

- Lectura recursiva de archivos `.xml` en una carpeta y todas sus subcarpetas
- Compatible con CFDI 3.3 y 4.0 (detección automática de namespace vía wildcard `{*}`)
- Extrae comprobante, emisor, receptor, conceptos, impuestos (IVA vs. otros impuestos) y UUID del Timbre Fiscal Digital
- Captura además cualquier atributo no estándar del nodo `Comprobante` como columna dinámica en el CSV
- Exporta a CSV con nombre por timestamp (`procesados/processed-data/YYYYMMDD_HHMMSS_info_cfdis.csv`)
- Imprime resumen estadístico en consola: total facturado, IVA, promedio por factura, emisores y subcarpetas únicos
- Lógica de extracción centralizada en el paquete [modules/](modules/) (`processing.py`, `export.py`), reutilizada tanto por el script como por el notebook
- Notebook equivalente ([extract-info-of-xmls.ipynb](extract-info-of-xmls.ipynb)) para correr el mismo pipeline de forma interactiva

## Cómo correrlo localmente

Requiere Python 3.13+.

```bash
# 1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd project

# 2. Crear y activar entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python extract-info-of-xmls.py
```

<!-- COMPLETAR: este checkout local no tiene remote configurado (`git remote -v` vacío). Reemplaza <URL_DEL_REPOSITORIO> por la URL real una vez que publiques el repositorio -->

No requiere variables de entorno: no hay `.env`/`.env.example` en el repositorio ni lectura de `os.environ` en el código.

Al ejecutarlo, el script pide por consola la ruta de la carpeta con los XML a procesar, por ejemplo:

```text
Ruta de la carpeta: (por ejemplo: ./procesados/data-to-process/202601-pers)
```

Coloca los XML a procesar dentro de `procesados/data-to-process/` (una subcarpeta por periodo). El CSV resultante se guarda con nombre por timestamp en `procesados/processed-data/`, carpeta que el script crea automáticamente si no existe.

## Decisiones técnicas relevantes

- **`xml.etree.ElementTree` de la librería estándar en lugar de `lxml`**: evita una dependencia binaria externa; suficiente para el volumen de XMLs que procesa el script.
- **Namespace resuelto con wildcard `{*}`** en vez de mapear namespaces fijos por versión: permite parsear CFDI 3.3 y 4.0 (namespaces distintos entre sí) sin bifurcar el código en dos parsers.
- **Salida a CSV plano, una fila por comprobante,** en lugar de una base de datos: prioriza portabilidad e importación directa a Excel/Sheets sobre consultabilidad.

<!-- COMPLETAR: trade-offs adicionales que hayas evaluado (por ejemplo, por qué no se valida el CFDI contra el XSD del SAT, o por qué los conceptos no se exportan en filas separadas) -->

## Estado del proyecto

**Activo.** Último commit: 13 de agosto de 2026 (`Se agregó .gitignore y LICENSE`). El historial muestra desarrollo incremental continuo desde el commit inicial.

## Autor / Rol

**Alexandro Ivan Zamudio Romero** — autor y único mantenedor (todos los commits del repositorio corresponden a este autor).

<!-- COMPLETAR: si quieres, agrega tu rol profesional, LinkedIn/portafolio o el contexto en el que usas esta herramienta (freelance, negocio propio, etc.) -->

## Licencia

MIT — ver [LICENSE](LICENSE).
