"""Extrae la información de CFDIs XML de una carpeta y genera un CSV consolidado."""
from modules.processing import validar_ruta, process_folder

# solicitar al usuario la ruta de la carpeta con los XML a procesar
carpeta_xml = validar_ruta(input("Ruta de la carpeta: (por ejemplo: ./procesados/data-to-process/202601-pers)"))
df_cfdis = process_folder(carpeta_xml)

print(df_cfdis.head(10))
