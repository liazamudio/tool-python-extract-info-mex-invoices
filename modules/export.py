"""Impresión/formato de CFDIs y exportación de resultados a CSV."""
from typing import Any, Dict, List

import pandas as pd


def print_cfdi(data: Dict[str, Any]) -> None:
    """
    Imprime en consola un resumen legible de un CFDI ya parseado.

    Args:
        data: Diccionario con los datos del CFDI, tal como lo retorna `parse_cfdi`
            (debe incluir las claves file, version, serie, folio, fecha,
            emisor_nombre, emisor_rfc, emisor_regimen, receptor_nombre,
            receptor_rfc, uso_cfdi, subtotal, descuento, iva, otros_impuestos,
            total y conceptos).

    Returns:
        None.
    """
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
    """
    Exporta un CSV 'plano' a nivel comprobante y retorna el DataFrame.

    Args:
        cfdis: Lista de diccionarios de CFDIs, tal como los retorna `parse_cfdi`
            (con la clave adicional `subcarpeta` agregada por el llamador).
        csv_path: Ruta del archivo CSV de salida.

    Returns:
        DataFrame de pandas con los datos exportados, con una columna por cada
        campo estándar más una por cada atributo personalizado detectado en los
        comprobantes. DataFrame vacío si `cfdis` está vacío (en ese caso no se
        escribe ningún archivo).
    """
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
    custom_keys = sorted({k for d in cfdis for k in d.get("custom_comprobante_attrs", {})})
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
