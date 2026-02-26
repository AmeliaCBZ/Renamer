import re
import sys
import threading

import pdfplumber
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk
from PyInstaller.building import splash


def resource_path(relative_path: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))

    if not (base / "Resources").exists():
        p = base
        for _ in range(4):
            p = p.parent
            if (p / "Resources").exists():
                base = p
                break
    return (base / relative_path).resolve()

LOGO1 = resource_path("Resources/SplashScreen/logo1.png")
LOGO2 = resource_path("Resources/SplashScreen/logo2.png")
FONDO = resource_path("Resources/SplashScreen/fondo.png")
ICONO = resource_path("Resources/icono.ico")

def mostrar_splash(root, imagen_path , duracion=2000, callback=None, ):
    splash = tk.Toplevel(root)
    splash.geometry("1920x1080")
    splash.configure(bg="white")

    try:
        if imagen_path.exists():
            img = Image.open(imagen_path)
            img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
            logo_img = ImageTk.PhotoImage(img)
            label = tk.Label(splash, image=logo_img, bg="white")
            label.image = logo_img
            label.pack(expand=True, fill="both")
        else:
            raise FileNotFoundError(imagen_path)
    except Exception as e:
        print(f"Could not load splash image {imagen_path}: {e}")
        tk.Label(splash, text="Rename Me!", font=("Arial", 36), bg="white").pack(expand=True)

    def cerrar():
        try:
            splash.destroy()
        except Exception:
            pass
        if callback:
            callback()
    root.after(duracion, cerrar)

# -------- Selección de carpeta --------
def seleccionar_fichero():
    return filedialog.askdirectory(title="Selecciona la carpeta con los PDFs")

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


def nombre_unico(destino: Path) -> Path:
    if not destino.exists():
        return destino
    base = destino.stem
    suf = 1
    while True:
        nuevo = destino.with_name(f"{base}_{suf}{destino.suffix}")
        if not nuevo.exists():
            return nuevo
        suf += 1


def renombrar_pdfs(fichero_path: str)-> dict:
    fichero = Path(fichero_path)
    renombrados = 0
    sin_coincidencia = 0
    errores = 0
    detalles_renombrados = []
    detalles_errores = []

    for archivo in fichero.iterdir():
        if archivo.is_file() and archivo.suffix.lower() == ".pdf":
            texto = extraer_texto_pdf(archivo)
            match = re.search(r"Contrato\s+(\d+)", texto, re.IGNORECASE)
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

    return{
        "renombrados": renombrados,
        "sin_coincidencia": sin_coincidencia,
        "errores": errores,
        "detalles_renombrados": detalles_renombrados,
        "detalles_errores": detalles_errores
    }


# -------- Pantalla principal --------
def iniciar_app(root):
    # ventana principal
    ventana = tk.Toplevel(root)
    ventana.geometry("600x500")
    ventana.resizable(False, False)
    ventana.title("Rename Me!")

    try:
        if ICONO.exists():
            ventana.iconbitmap(str(ICONO))
    except Exception as e:
        print(f"Could not load icon: {e}")


    canvas = tk.Canvas(ventana,width=600, height=500, highlightthickness=0)
    canvas.place(x=0, y=0, relwidth=1, relheight=1)

    try:
        if FONDO.exists():
            img = Image.open(FONDO)
            img = img.resize((600, 500), Image.Resampling.LANCZOS)
            fondo = ImageTk.PhotoImage(img)
            canvas.create_image(0, 0, image=fondo, anchor="nw")
            canvas.fondo = fondo  # keep reference ventana.fondo = fondo
            ventana.fondo = fondo
        else:
            raise FileNotFoundError(FONDO)
    except Exception as e:
        print(f"Could not load background image: {e}")
        canvas.configure(bg="#333")
    canvas.create_text(300, 110, text="Selecciona una carpeta de archivos", font=("Times New Roman", 24, "bold"), fill="white", anchor="center")
    boton = tk.Button(ventana, text="Seleccionar carpeta", font=("Times New Roman", 20),
                      command=lambda: ejecutar_renombrado_async(ventana))
    canvas.create_window(300, 260, window=boton, anchor="center")

def ejecutar_renombrado_async(ventana):
    fichero = seleccionar_fichero()
    if not fichero:
        return

    def worker():
        resumen = renombrar_pdfs(fichero)
        ventana.after(0, lambda: mostrar_resultado(ventana, resumen))

    threading.Thread(target=worker, daemon=True).start()

def mostrar_resultado(ventana, resumen):
    texto = (
        f"Renombrados: {resumen['renombrados']}\n"
        f"" f"Sin coincidencia: {resumen['sin_coincidencia']}\n" 
        f"Errores: {resumen['errores']}")
    messagebox.showinfo("Resultado del renombrado", texto)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    print("cwd:", Path.cwd())
    print("LOGO1:", LOGO1, "exists:", LOGO1.exists())
    print("LOGO2:", LOGO2, "exists:", LOGO2.exists())
    print("FONDO:", FONDO, "exists:", FONDO.exists())
    print("ICONO:", ICONO, "exists:", ICONO.exists())

    try:
        # Show splash screens using resource paths
        mostrar_splash(root, LOGO1, 1500)
        root.after(1500, lambda: mostrar_splash(root, LOGO2, 1500, callback=lambda: iniciar_app(root)))
        root.mainloop()
    except KeyboardInterrupt:
        print("Interrupción por teclado recibida. Cerrando...")
        try:
            root.destroy()
        except Exception:
            pass# Oculta la ventana raíz
