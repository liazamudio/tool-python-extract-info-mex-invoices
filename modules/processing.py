"""Procesamiento de archivos XML de CFDI: parseo, extracción de datos y recorrido de carpetas."""
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from .export import export_cfdi_to_csv, print_cfdi

# Namespaces típicos CFDI 3.3 / 4.0
NS = {
    "cfdi": "http://www.sat.gob.mx/cfd/4",
    "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital"
}


def validar_ruta(carpeta_xml: str) -> str:
    """
    Valida que la ruta de carpeta proporcionada no esté vacía y exista en disco.

    Args:
        carpeta_xml: Ruta (relativa o absoluta) de la carpeta a validar.

    Returns:
        La ruta de carpeta recibida, sin espacios en los extremos.

    Raises:
        ValueError: Si la ruta está vacía o solo contiene espacios.
        FileNotFoundError: Si la ruta no corresponde a una carpeta existente.
    """
    carpeta_xml = carpeta_xml.strip() if carpeta_xml else ""

    if not carpeta_xml:
        raise ValueError("Debes indicar una ruta de carpeta.")
    if not os.path.isdir(carpeta_xml):
        raise FileNotFoundError(f"La carpeta no existe: {carpeta_xml}")

    return carpeta_xml


def _get_attr(elem: Optional[ET.Element], attr: str, default: Optional[str] = None) -> Optional[str]:
    """
    Obtiene atributo de elemento XML de forma segura.

    Args:
        elem: Elemento XML del que se quiere leer el atributo (puede ser None).
        attr: Nombre del atributo a leer.
        default: Valor a devolver si el elemento es None o no tiene el atributo.

    Returns:
        El valor del atributo como string, o `default` si no está disponible.
    """
    return elem.attrib.get(attr, default) if elem is not None else default


def _get_float(elem: Optional[ET.Element], attr: str, default: float = 0.0) -> float:
    """
    Obtiene atributo numérico de elemento XML.

    Args:
        elem: Elemento XML del que se quiere leer el atributo (puede ser None).
        attr: Nombre del atributo a leer.
        default: Valor a devolver si el atributo no está presente o está vacío.

    Returns:
        El valor del atributo convertido a float, o `default` si no está disponible.
    """
    value = _get_attr(elem, attr)
    return float(value) if value else default


def _find(node: Optional[ET.Element], tag: str, use_wildcard: bool) -> Optional[ET.Element]:
    """
    Busca un hijo directo respetando el namespace CFDI 3.3/4.0 (None si no aplica).

    Args:
        node: Nodo XML donde buscar (puede ser None).
        tag: Nombre de la etiqueta a buscar.
        use_wildcard: Si es True, busca con wildcard de namespace `{*}tag`;
            si es False, busca usando el namespace `cfdi` declarado en NS.

    Returns:
        El primer elemento hijo que coincide, o None si no se encuentra o si
        `node` es None.
    """
    if node is None:
        return None
    return node.find(f"{{*}}{tag}") if use_wildcard else node.find(f"cfdi:{tag}", NS)


def _find_all(node: Optional[ET.Element], tag: str, use_wildcard: bool) -> List[ET.Element]:
    """
    Busca todos los hijos directos respetando el namespace CFDI 3.3/4.0.

    Args:
        node: Nodo XML donde buscar (puede ser None).
        tag: Nombre de la etiqueta a buscar.
        use_wildcard: Si es True, busca con wildcard de namespace `{*}tag`;
            si es False, busca usando el namespace `cfdi` declarado en NS.

    Returns:
        Lista de elementos hijo que coinciden. Lista vacía si no hay
        coincidencias o si `node` es None.
    """
    if node is None:
        return []
    return node.findall(f"{{*}}{tag}") if use_wildcard else node.findall(f"cfdi:{tag}", NS)


def parse_cfdi(xml_path: str) -> Dict[str, Any]:
    """
    Parsea un archivo CFDI XML y extrae la información relevante.

    Args:
        xml_path: Ruta al archivo XML del CFDI a procesar.

    Returns:
        Diccionario con los datos del comprobante (fecha, serie, folio, moneda,
        subtotal, descuento, total), del emisor y receptor, la lista de
        conceptos, los totales de IVA y otros impuestos, el UUID del timbre
        fiscal digital y los atributos personalizados adicionales del nodo
        Comprobante.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Usar búsqueda con wildcard para compatibilidad con diferentes versiones
    use_wildcard = root.tag.endswith("Comprobante") and "cfdi" not in root.tag

    data: Dict[str, Any] = {
        "file": os.path.basename(xml_path),
        "version": _get_attr(root, "Version"),
        "fecha": _get_attr(root, "Fecha"),
        "serie": _get_attr(root, "Serie"),
        "folio": _get_attr(root, "Folio"),
        "moneda": _get_attr(root, "Moneda"),
        "tipo_comprobante": _get_attr(root, "TipoDeComprobante"),
        "lugar_expedicion": _get_attr(root, "LugarExpedicion"),
        "subtotal": _get_float(root, "SubTotal"),
        "descuento": _get_float(root, "Descuento"),
        "total": _get_float(root, "Total"),
    }

    # Emisor
    emisor = _find(root, "Emisor", use_wildcard)
    data["emisor_rfc"] = _get_attr(emisor, "Rfc")
    data["emisor_nombre"] = _get_attr(emisor, "Nombre")
    data["emisor_regimen"] = _get_attr(emisor, "RegimenFiscal")

    # Receptor
    receptor = _find(root, "Receptor", use_wildcard)
    data["receptor_rfc"] = _get_attr(receptor, "Rfc")
    data["receptor_nombre"] = _get_attr(receptor, "Nombre")
    data["receptor_regimen"] = _get_attr(receptor, "RegimenFiscalReceptor")
    data["receptor_cp"] = _get_attr(receptor, "DomicilioFiscalReceptor")
    data["uso_cfdi"] = _get_attr(receptor, "UsoCFDI")

    # Conceptos
    conceptos_node = _find(root, "Conceptos", use_wildcard)
    data["conceptos"] = [
        {
            "clave_prod_serv": _get_attr(c, "ClaveProdServ"),
            "no_identificacion": _get_attr(c, "NoIdentificacion"),
            "cantidad": _get_float(c, "Cantidad"),
            "clave_unidad": _get_attr(c, "ClaveUnidad"),
            "unidad": _get_attr(c, "Unidad"),
            "descripcion": _get_attr(c, "Descripcion"),
            "valor_unitario": _get_float(c, "ValorUnitario"),
            "importe": _get_float(c, "Importe"),
            "descuento": _get_float(c, "Descuento"),
        }
        for c in _find_all(conceptos_node, "Concepto", use_wildcard)
    ]

    # Impuestos (totales)
    impuestos_node = _find(root, "Impuestos", use_wildcard)
    traslados_node = _find(impuestos_node, "Traslados", use_wildcard)
    total_iva = 0.0
    total_otros_impuestos = 0.0

    for t in _find_all(traslados_node, "Traslado", use_wildcard):
        importe = _get_float(t, "Importe")
        if _get_attr(t, "Impuesto") == "002":  # IVA
            total_iva += importe
        else:
            total_otros_impuestos += importe

    data["iva"] = total_iva
    data["otros_impuestos"] = total_otros_impuestos

    # UUID del TimbreFiscalDigital
    complemento = _find(root, "Complemento", use_wildcard)
    # TimbreFiscalDigital vive en el namespace 'tfd', no en 'cfdi': siempre se busca con wildcard.
    tfd = _find(complemento, "TimbreFiscalDigital", True)
    data["uuid"] = _get_attr(tfd, "UUID")

    # Campos personalizados (cualquier atributo no estándar en Comprobante)
    standard_attrs = {"Version", "Fecha", "Serie", "Folio", "Moneda", "TipoDeComprobante",
                     "LugarExpedicion", "SubTotal", "Descuento", "Total"}
    data["custom_comprobante_attrs"] = {k: v for k, v in root.attrib.items() if k not in standard_attrs}

    return data


def process_folder(folder_path: str, output_dir: str = "./procesados/output") -> pd.DataFrame:
    """
    Procesa todos los archivos XML en la carpeta y subcarpetas.

    Recorre recursivamente `folder_path`, parsea cada XML encontrado con
    `parse_cfdi`, imprime un resumen de cada CFDI, exporta los resultados a un
    CSV con timestamp dentro de `output_dir` y muestra en consola un resumen
    estadístico (totales, promedios, emisores y subcarpetas únicos).

    Args:
        folder_path: Carpeta raíz (con subcarpetas) donde buscar los XML.
        output_dir: Carpeta donde se guardará el CSV generado. Se crea si no existe.

    Returns:
        DataFrame de pandas con la información consolidada de todos los CFDIs procesados.
    """
    cfdis: List[Dict[str, Any]] = []

    # Recorrer recursivamente todas las subcarpetas
    for root, dirs, files in os.walk(folder_path):
        # Calcular subcarpeta una vez por directorio
        rel_path = os.path.relpath(root, folder_path)
        subcarpeta = "" if rel_path == "." else rel_path

        # Filtrar solo archivos XML
        xml_files = [f for f in files if f.lower().endswith(".xml")]

        for fname in xml_files:
            full_path = os.path.join(root, fname)
            try:
                data = parse_cfdi(full_path)
                data["subcarpeta"] = subcarpeta
                cfdis.append(data)
                print_cfdi(data)
                print("-" * 80)
            except Exception as e:
                print(f"Error procesando {fname} en {root}: {e}")

    print(f"\nTotal de CFDIs procesados: {len(cfdis)}")

    # Crear carpeta de salida si no existe
    os.makedirs(output_dir, exist_ok=True)

    # Generar nombre del archivo con fecha y hora
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{timestamp}_info_cfdis.csv"
    csv_path = os.path.join(output_dir, csv_filename)

    # Exportar a CSV y obtener DataFrame
    df = export_cfdi_to_csv(cfdis, csv_path)
    print(f"CSV generado: {csv_path}")

    # Mostrar DataFrame en pantalla con configuración para ver todas las columnas
    print("\n" + "="*100)
    print("DATAFRAME CON INFORMACION DE LOS CFDIs:")
    print("="*100)

    # Configurar pandas para mostrar todas las columnas
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)

    # Mostrar información general
    print(f"\nTotal de registros: {len(df)}")
    print(f"Total de columnas: {len(df.columns)}")
    print(f"\nColumnas disponibles:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")

    # Mostrar primeros registros con las columnas principales
    print("\n" + "-"*100)
    print("PRIMEROS REGISTROS (columnas principales):")
    print("-"*100)
    columnas_principales = ['file', 'subcarpeta', 'uuid', 'fecha', 'emisor_nombre',
                           'receptor_nombre', 'subtotal', 'iva', 'total']
    if all(col in df.columns for col in columnas_principales):
        print(df[columnas_principales].head(10).to_string(index=False))

    # Mostrar estadísticas
    print("\n" + "-"*100)
    print("ESTADISTICAS:")
    print("-"*100)
    if not df.empty and 'subtotal' in df.columns:
        print(f"Total facturado (subtotal): ${df['subtotal'].sum():,.2f}")
        print(f"Total IVA: ${df['iva'].sum():,.2f}")
        print(f"Total general: ${df['total'].sum():,.2f}")
        print(f"Promedio por factura: ${df['total'].mean():,.2f}")
        print(f"\nEmisores únicos: {df['emisor_nombre'].nunique()}")
        print(f"Subcarpetas procesadas: {df['subcarpeta'].nunique()}")
    else:
        print("No hay datos para mostrar estadísticas.")

    print("\n" + "="*100)
    print(f"Datos completos guardados en: {csv_path}")
    print("="*100)

    return df
