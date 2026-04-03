import os
import csv
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

# Namespaces típicos CFDI 3.3 / 4.0
NS = {
    "cfdi": "http://www.sat.gob.mx/cfd/4",
    "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital"
}

def _get_attr(elem, attr, default=None):
    """Obtiene atributo de elemento XML de forma segura."""
    return elem.attrib.get(attr, default) if elem is not None else default

def _get_float(elem, attr, default=0.0):
    """Obtiene atributo numérico de elemento XML."""
    value = _get_attr(elem, attr)
    return float(value) if value else default

def parse_cfdi(xml_path: str) -> Dict[str, Any]:
    """Parse un archivo CFDI XML y extrae la información relevante."""
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
    emisor = root.find("{*}Emisor") if use_wildcard else root.find("cfdi:Emisor", NS)
    data["emisor_rfc"] = _get_attr(emisor, "Rfc")
    data["emisor_nombre"] = _get_attr(emisor, "Nombre")
    data["emisor_regimen"] = _get_attr(emisor, "RegimenFiscal")

    # Receptor
    receptor = root.find("{*}Receptor") if use_wildcard else root.find("cfdi:Receptor", NS)
    data["receptor_rfc"] = _get_attr(receptor, "Rfc")
    data["receptor_nombre"] = _get_attr(receptor, "Nombre")
    data["receptor_regimen"] = _get_attr(receptor, "RegimenFiscalReceptor")
    data["receptor_cp"] = _get_attr(receptor, "DomicilioFiscalReceptor")
    data["uso_cfdi"] = _get_attr(receptor, "UsoCFDI")

    # Conceptos
    conceptos_node = root.find("{*}Conceptos") if use_wildcard else root.find("cfdi:Conceptos", NS)
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
        for c in (conceptos_node.findall("{*}Concepto") if use_wildcard else conceptos_node.findall("cfdi:Concepto", NS))
    ] if conceptos_node is not None else []

    # Impuestos (totales)
    impuestos_node = root.find("{*}Impuestos") if use_wildcard else root.find("cfdi:Impuestos", NS)
    total_iva = 0.0
    total_otros_impuestos = 0.0

    if impuestos_node is not None:
        traslados_node = impuestos_node.find("{*}Traslados") if use_wildcard else impuestos_node.find("cfdi:Traslados", NS)
        if traslados_node is not None:
            traslados = traslados_node.findall("{*}Traslado") if use_wildcard else traslados_node.findall("cfdi:Traslado", NS)
            for t in traslados:
                importe = _get_float(t, "Importe")
                if _get_attr(t, "Impuesto") == "002":  # IVA
                    total_iva += importe
                else:
                    total_otros_impuestos += importe

    data["iva"] = total_iva
    data["otros_impuestos"] = total_otros_impuestos

    # UUID del TimbreFiscalDigital
    complemento = root.find("{*}Complemento") if use_wildcard else root.find("cfdi:Complemento", NS)
    tfd = complemento.find("{*}TimbreFiscalDigital") if complemento is not None else None
    data["uuid"] = _get_attr(tfd, "UUID")

    # Campos personalizados (cualquier atributo no estándar en Comprobante)
    standard_attrs = {"Version", "Fecha", "Serie", "Folio", "Moneda", "TipoDeComprobante",
                     "LugarExpedicion", "SubTotal", "Descuento", "Total"}
    data["custom_comprobante_attrs"] = {k: v for k, v in root.attrib.items() if k not in standard_attrs}

    return data


def print_cfdi(data: Dict[str, Any]) -> None:
    print(f"Archivo: {data['file']}")
    print(f"CFDI {data['version']} | Serie-Folio: {data.get('serie')}-{data.get('folio')} | Fecha: {data.get('fecha')}")
    print(f"Emisor: {data.get('emisor_nombre')} ({data.get('emisor_rfc')}) Regimen: {data.get('emisor_regimen')}")
    print(f"Receptor: {data.get('receptor_nombre')} ({data.get('receptor_rfc')}) UsoCFDI: {data.get('uso_cfdi')}")
    print(f"Subtotal: {data['subtotal']:.2f}  Descuento: {data['descuento']:.2f}")
    print(f"IVA: {data['iva']:.2f}  Otros impuestos: {data['otros_impuestos']:.2f}")
    print(f"Total: {data['total']:.2f}")
    print("Conceptos:")
    for c in data["conceptos"]:
        print(f"  - {c['descripcion']} | Cant: {c['cantidad']} | VU: {c['valor_unitario']} | Importe: {c['importe']}")


def export_cfdi_to_csv(cfdis: List[Dict[str, Any]], csv_path: str) -> pd.DataFrame:
    """Exporta un CSV 'plano' a nivel comprobante y retorna el DataFrame."""
    if not cfdis:
        return pd.DataFrame()

    # Columnas estándar
    fieldnames = [
        "file", "subcarpeta", "uuid", "version", "fecha", "serie", "folio",
        "emisor_rfc", "emisor_nombre", "emisor_regimen",
        "receptor_rfc", "receptor_nombre", "receptor_regimen",
        "receptor_cp", "uso_cfdi",
        "moneda", "tipo_comprobante", "lugar_expedicion",
        "subtotal", "descuento", "iva", "otros_impuestos", "total"
    ]

    # Obtener campos personalizados de todos los documentos
    custom_keys = sorted(set().union(*[d.get("custom_comprobante_attrs", {}).keys() for d in cfdis]))
    fieldnames.extend(custom_keys)

    # Preparar datos para el DataFrame (optimizado)
    rows = [
        {**{k: d.get(k) for k in fieldnames}, 
         **d.get("custom_comprobante_attrs", {})}
        for d in cfdis
    ]
    
    # Crear y guardar DataFrame
    df = pd.DataFrame(rows, columns=fieldnames)
    df.to_csv(csv_path, index=False, encoding="utf-8")
    
    return df


def process_folder(folder_path: str, output_dir: str = "./extraidos") -> pd.DataFrame:
    """Procesa todos los archivos XML en la carpeta y subcarpetas."""
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
    
    # Crear carpeta extraidos si no existe
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


if __name__ == "__main__":
    # Ejemplo de uso:
    # carpeta_xml = r"./cfdis_xml"
    carpeta_xml = r"./cfdis_xml/202601-pers"
    df_cfdis = process_folder(carpeta_xml)