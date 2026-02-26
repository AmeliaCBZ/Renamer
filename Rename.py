import os
import re
import pdfplumber
import tkinter as tk
from tkinter import filedialog
from pathlib import Path


def seleccionar_fichero():
    root = tk.Tk()
    root.withdraw()
    fichero = filedialog.askdirectory(title="Selecciona la carpeta con los PDFs")
    root.destroy()
    return fichero

def extraer_texto_pdf(ruta_pdf: Path) -> str:
    partes = []
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    partes.append(texto)
    except Exception as e:
        print(f"Error leyendo {ruta_pdf.name}: {e}")
    return "\n".join(partes)

def nombre_unico(destino: Path)-> Path:
    if not destino.exists():
        return destino
    base = destino.stem
    suf = 1
    while True:
        nuevo = destino.with_name(f"{base}_{suf}{destino.suffix}")
        if not nuevo.exists():
            return nuevo
        suf += 1


def renombrar_pdfs(fichero_path: str):
    fichero = Path (fichero_path)
    if not fichero.is_dir():
        print("La ruta selecccionada no es una carpeta válida,")
        return
    renombrados = 0
    sin_coincidencia = 0
    errores = 0

    for archivo in fichero.iterdir():
        if archivo.is_file() and archivo.suffix.lower() == ".pdf":
            texto = extraer_texto_pdf(archivo)
            match = re.search(r"Contrato\s+(\d+)",texto, re.IGNORECASE)
            if match:
                numero = match.group(1)
                destino = fichero / f"{numero}.pdf"
                destino = nombre_unico(destino)
                try:
                    archivo.rename(destino)
                    print(f"Renombrado: {archivo.name} -> {destino.name}")
                    renombrados += 1
                except Exception as e:
                    print(f"Error renombrando {archivo.name}: {e}")
                    errores += 1
            else:
                print(f"No se encontró contrato en {archivo.name}")
                sin_coincidencia += 1

    print("\nResumen:")
    print(f" Renombrados: {renombrados}")
    print(f" Sin coincidencia: {sin_coincidencia}")
    print(f" Errores: {errores}")

if __name__ == "__main__":
    fichero = seleccionar_fichero()
    if fichero:
        renombrar_pdfs(fichero)
    else:
        print("No se seleccionó ninguna carpeta. Saliendo.")









