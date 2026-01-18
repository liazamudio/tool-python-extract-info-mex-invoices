import os
import csv
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

# Namespaces típicos CFDI 3.3 / 4.0
NS = {
    "cfdi": "http://www.sat.gob.mx/cfd/4",
    "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital"
}

def _get_attr(elem, attr, default=None):
    return elem.attrib.get(attr, default) if elem is not None else default

def parse_cfdi(xml_path: str) -> Dict[str, Any]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Ajuste de namespace si viene CFDI 3.3
    if root.tag.endswith("Comprobante") and "cfdi" not in root.tag:
        # fallback: sin prefijo, pero misma lógica
        NS_local = {}
    else:
        NS_local = NS

    # Nodo Comprobante
    comp = root

    data: Dict[str, Any] = {
        "file": os.path.basename(xml_path),
        "version": _get_attr(comp, "Version"),
        "fecha": _get_attr(comp, "Fecha"),
        "serie": _get_attr(comp, "Serie"),
        "folio": _get_attr(comp, "Folio"),
        "moneda": _get_attr(comp, "Moneda"),
        "tipo_comprobante": _get_attr(comp, "TipoDeComprobante"),
        "lugar_expedicion": _get_attr(comp, "LugarExpedicion"),
        "subtotal": float(_get_attr(comp, "SubTotal", "0") or 0),
        "descuento": float(_get_attr(comp, "Descuento", "0") or 0),
        "total": float(_get_attr(comp, "Total", "0") or 0),
    }

    # Emisor
    emisor = comp.find("cfdi:Emisor", NS_local) if NS_local else comp.find("{*}Emisor")
    data.update({
        "emisor_rfc": _get_attr(emisor, "Rfc"),
        "emisor_nombre": _get_attr(emisor, "Nombre"),
        "emisor_regimen": _get_attr(emisor, "RegimenFiscal"),
    })

    # Receptor
    receptor = comp.find("cfdi:Receptor", NS_local) if NS_local else comp.find("{*}Receptor")
    data.update({
        "receptor_rfc": _get_attr(receptor, "Rfc"),
        "receptor_nombre": _get_attr(receptor, "Nombre"),
        "receptor_regimen": _get_attr(receptor, "RegimenFiscalReceptor"),
        "receptor_cp": _get_attr(receptor, "DomicilioFiscalReceptor"),
        "uso_cfdi": _get_attr(receptor, "UsoCFDI"),
    })

    # Conceptos
    conceptos_node = comp.find("cfdi:Conceptos", NS_local) if NS_local else comp.find("{*}Conceptos")
    conceptos: List[Dict[str, Any]] = []
    if conceptos_node is not None:
        for c in conceptos_node.findall("cfdi:Concepto", NS_local) if NS_local else conceptos_node.findall("{*}Concepto"):
            conceptos.append({
                "clave_prod_serv": _get_attr(c, "ClaveProdServ"),
                "no_identificacion": _get_attr(c, "NoIdentificacion"),
                "cantidad": float(_get_attr(c, "Cantidad", "0") or 0),
                "clave_unidad": _get_attr(c, "ClaveUnidad"),
                "unidad": _get_attr(c, "Unidad"),
                "descripcion": _get_attr(c, "Descripcion"),
                "valor_unitario": float(_get_attr(c, "ValorUnitario", "0") or 0),
                "importe": float(_get_attr(c, "Importe", "0") or 0),
                "descuento": float(_get_attr(c, "Descuento", "0") or 0),
            })
    data["conceptos"] = conceptos

    # Impuestos (totales)
    impuestos_node = comp.find("cfdi:Impuestos", NS_local) if NS_local else comp.find("{*}Impuestos")
    total_iva = 0.0
    total_otros_impuestos = 0.0

    if impuestos_node is not None:
        # Totales a nivel comprobante
        total_traslados = impuestos_node.attrib.get("TotalImpuestosTrasladados")
        total_retenciones = impuestos_node.attrib.get("TotalImpuestosRetenidos")

        # Detalle de traslados
        traslados_node = impuestos_node.find("cfdi:Traslados", NS_local) if NS_local else impuestos_node.find("{*}Traslados")
        if traslados_node is not None:
            for t in traslados_node.findall("cfdi:Traslado", NS_local) if NS_local else traslados_node.findall("{*}Traslado"):
                impuesto = _get_attr(t, "Impuesto")
                importe = float(_get_attr(t, "Importe", "0") or 0)
                if impuesto == "002":  # IVA
                    total_iva += importe
                else:
                    total_otros_impuestos += importe

    data["iva"] = total_iva
    data["otros_impuestos"] = total_otros_impuestos

    # Campos personalizados (cualquier atributo no estándar en Comprobante)
    standard_attrs = {
        "Version", "Fecha", "Serie", "Folio", "Moneda", "TipoDeComprobante",
        "LugarExpedicion", "SubTotal", "Descuento", "Total"
    }
    custom_fields = {
        k: v for k, v in comp.attrib.items() if k not in standard_attrs
    }
    data["custom_comprobante_attrs"] = custom_fields

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


def export_cfdi_to_csv(cfdis: List[Dict[str, Any]], csv_path: str) -> None:
    """
    Exporta un CSV 'plano' a nivel comprobante.
    Si quieres detalle por concepto, se puede hacer otro CSV aparte.
    """
    if not cfdis:
        return

    # Definimos columnas estándar
    fieldnames = [
        "file", "subcarpeta", "version", "fecha", "serie", "folio",
        "emisor_rfc", "emisor_nombre", "emisor_regimen",
        "receptor_rfc", "receptor_nombre", "receptor_regimen",
        "receptor_cp", "uso_cfdi",
        "moneda", "tipo_comprobante", "lugar_expedicion",
        "subtotal", "descuento", "iva", "otros_impuestos", "total"
    ]

    # Agregamos campos personalizados del comprobante como columnas dinámicas
    custom_keys = set()
    for d in cfdis:
        custom_keys.update(d.get("custom_comprobante_attrs", {}).keys())
    custom_keys = sorted(custom_keys)
    fieldnames.extend(custom_keys)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for d in cfdis:
            row = {k: d.get(k) for k in fieldnames}
            # Rellenar campos personalizados
            for ck in custom_keys:
                row[ck] = d.get("custom_comprobante_attrs", {}).get(ck)
            writer.writerow(row)


def process_folder(folder_path: str, csv_path: str) -> None:
    cfdis: List[Dict[str, Any]] = []
    
    # Recorrer recursivamente todas las subcarpetas
    for root, dirs, files in os.walk(folder_path):
        for fname in files:
            if fname.lower().endswith(".xml"):
                full_path = os.path.join(root, fname)
                try:
                    data = parse_cfdi(full_path)
                    # Agregar información de la subcarpeta
                    rel_path = os.path.relpath(root, folder_path)
                    data["subcarpeta"] = rel_path if rel_path != "." else ""
                    cfdis.append(data)
                    print_cfdi(data)
                    print("-" * 80)
                except Exception as e:
                    print(f"Error procesando {fname} en {root}: {e}")

    print(f"\n✓ Total de CFDIs procesados: {len(cfdis)}")
    export_cfdi_to_csv(cfdis, csv_path)
    print(f"✓ CSV generado: {csv_path}")


if __name__ == "__main__":
    # Ejemplo de uso:
    carpeta_xml = r"./cfdis_xml"
    salida_csv = r"./cfdis_consolidados.csv"
    process_folder(carpeta_xml, salida_csv)