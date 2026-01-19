# Lector de XMLs CFDI

Herramienta para extraer información de archivos XML de CFDI (Comprobante Fiscal Digital por Internet) mexicanos y exportarla a formato CSV usando pandas.

## 📋 Descripción

Este proyecto lee archivos XML de facturas electrónicas CFDI (versiones 3.3 y 4.0) desde una carpeta y sus subcarpetas, extrae la información relevante y genera un archivo CSV con todos los datos estructurados. Además, muestra un DataFrame con estadísticas y resúmenes de la información procesada.

## ✨ Características

- ✅ Lectura recursiva de archivos XML en carpeta y subcarpetas
- ✅ Soporte para CFDI versión 3.3 y 4.0
- ✅ Extracción completa de datos:
  - Información del comprobante (fecha, serie, folio, moneda, etc.)
  - Datos del emisor (RFC, nombre, régimen fiscal)
  - Datos del receptor (RFC, nombre, régimen fiscal, CP, uso CFDI)
  - Conceptos detallados
  - Impuestos (IVA y otros)
  - UUID del Timbre Fiscal Digital
  - Campos personalizados adicionales
- ✅ Exportación a CSV con nomenclatura con timestamp
- ✅ Visualización de DataFrame con estadísticas
- ✅ Manejo de múltiples subcarpetas

## 📁 Estructura del Proyecto

```
project/
├── extract-info-of-xmls.py    # Script principal
├── cfdis_xml/                 # Carpeta con archivos XML (entrada)
│   ├── 04-01 HAOYUAN HUANG Comida china/
│   ├── 07-01 Flecha Roja/
│   ├── 07-01 Sumesa/
│   └── ...
├── extraidos/                 # Carpeta con CSVs generados (salida)
│   └── YYYYMMDD_HHMMSS_info_cfdis.csv
├── requirements.txt           # Dependencias del proyecto
└── README.md                  # Este archivo
```

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
git clone <url-del-repositorio>
cd project
```

### 2. Crear entorno virtual (recomendado)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 💻 Uso

### Ejecución básica

```bash
python extract-info-of-xmls.py
```

### Parámetros configurables en el código

Puedes modificar las siguientes variables en el script:

```python
# Carpeta de entrada (por defecto: "./cfdis_xml")
folder_path = "./cfdis_xml"

# Carpeta de salida (por defecto: "./extraidos")
output_dir = "./extraidos"
```

### Ejemplo de ejecución

```bash
# Con el entorno virtual activado
(.venv) PS D:\devs\utilities\lector-xml\project> python extract-info-of-xmls.py

Archivo: HUHA770101CP3FF7332.xml
CFDI 4.0 | Serie-Folio: None-7332 | Fecha: 2025-12-04T16:29:10
Emisor: HAOYUAN HUANG (HUHA770101CP3) Regimen: 612
Receptor: ALEXANDRO IVAN ZAMUDIO ROMERO (ZARA781005JK7) UsoCFDI: G03
Subtotal: 142.24  Descuento: 0.00
IVA: 22.76  Otros impuestos: 0.00
Total: 165.00
Conceptos:
  - CONSUMO DE ALIMENTOS | Cant: 1.0 | VU: 142.241379 | Importe: 142.241379
--------------------------------------------------------------------------------
...

Total de CFDIs procesados: 31
CSV generado: ./extraidos\20260119_172905_info_cfdis.csv

====================================================================================================
DATAFRAME CON INFORMACION DE LOS CFDIs:
====================================================================================================
...
```

## 📊 Salida

### CSV Generado

El archivo CSV contiene las siguientes columnas:

**Columnas estándar (23):**
- file, subcarpeta, uuid, version, fecha, serie, folio
- emisor_rfc, emisor_nombre, emisor_regimen
- receptor_rfc, receptor_nombre, receptor_regimen, receptor_cp, uso_cfdi
- moneda, tipo_comprobante, lugar_expedicion
- subtotal, descuento, iva, otros_impuestos, total

**Columnas dinámicas:**
- Campos personalizados adicionales del comprobante (Certificado, CondicionesDePago, Exportacion, FormaPago, MetodoPago, etc.)

### Estadísticas mostradas

- Total de registros procesados
- Total de columnas
- Lista de todas las columnas
- Primeros 10 registros
- Totales: subtotal, IVA, total general
- Promedio por factura
- Número de emisores únicos
- Número de subcarpetas procesadas

## 🛠️ Requisitos

- Python 3.13+
- pandas 2.3.3+
- numpy 2.4.1+

Ver archivo `requirements.txt` para la lista completa de dependencias.

## 📝 Notas Técnicas

### Compatibilidad CFDI

El script es compatible con:
- CFDI versión 3.3
- CFDI versión 4.0

Utiliza búsqueda con wildcard `{*}` para detectar automáticamente la versión del XML.

### Namespace utilizado

```python
NS = {
    "cfdi": "http://www.sat.gob.mx/cfd/4",
    "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital"
}
```

### Optimizaciones

El código incluye varias optimizaciones:
- Función `_get_float()` para conversiones numéricas eficientes
- List comprehension para extracción de conceptos
- Dict comprehension para construcción del DataFrame
- Cálculo único de subcarpeta por directorio

## 🔧 Solución de Problemas

### Error: "No such file or directory"

Verifica que:
- La carpeta `cfdis_xml/` existe
- Hay archivos `.xml` en la carpeta o subcarpetas
- El path está correctamente especificado

### Error de encoding

Los archivos se procesan con encoding UTF-8. Si tienes problemas, verifica que tus XMLs estén en UTF-8.

### DataFrame truncado

El script configura pandas para mostrar todas las columnas. Si necesitas más filas:

```python
pd.set_option('display.max_rows', 100)  # Aumentar número de filas
```

## 📄 Licencia

Este proyecto está bajo la licencia que determines.

## 👤 Autor

Alexandro Ivan Zamudio Romero

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.

## 📞 Contacto

Para preguntas o sugerencias, por favor abre un issue en el repositorio.

---

**Última actualización:** Enero 2026
