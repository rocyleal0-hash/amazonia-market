# ==========================================================
# AMAZONIA MARKET - App de escritorio para agregar productos
# ==========================================================
# Al ejecutar este archivo:
#   1) Se lanza la TIENDA (Streamlit) en el navegador.
#   2) Se abre una ventana de Tkinter para AGREGAR productos.
#
# Cada producto agregado se guarda en products.json y aparece
# automáticamente en la tienda (basta con recargar la página
# o pulsar "Actualizar" en la tienda).
#
# Ejecutar:
#     python agregar_producto.py
#
# Requisitos:  pip install streamlit pillow
# (Tkinter viene con Python)
# ==========================================================

import base64
import io
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

BASE_DIR   = Path(__file__).parent.resolve()
DATA_FILE  = BASE_DIR / "products.json"
IMG_DIR    = BASE_DIR / "product_images"
TIENDA_PY  = BASE_DIR / "tienda.py"
IMG_DIR.mkdir(exist_ok=True)

# Paleta de marca (igual que en la tienda)
COLOR_PRIMARY   = "#4C1D95"
COLOR_PRIMARY_2 = "#7C3AED"
COLOR_ACCENT    = "#FFD400"
COLOR_BG        = "#F5F3FF"
COLOR_CARD      = "#FFFFFF"
COLOR_TEXT      = "#0F172A"
COLOR_MUTED     = "#64748B"

# ----------------------------------------------------------
# LOGO EMBEBIDO (mismo que la tienda)
# ----------------------------------------------------------
LOGO_B64 = """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"""


def clean_logo_image() -> Image.Image:
    """Decodifica el logo, hace transparente el fondo/borde
    negro y lo recorta al contenido real."""
    raw = base64.b64decode(LOGO_B64)
    img = Image.open(io.BytesIO(raw)).convert("RGBA")
    px = img.load()
    w, h = img.size
    THRESH = 70
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if r < THRESH and g < THRESH and b < THRESH:
                px[x, y] = (0, 0, 0, 0)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    return img


# ----------------------------------------------------------
# Persistencia
# ----------------------------------------------------------
def load_products():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_products(items):
    DATA_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False),
                         encoding="utf-8")


# ----------------------------------------------------------
# Lanzador de la tienda Streamlit
# ----------------------------------------------------------
def launch_store():
    if not TIENDA_PY.exists():
        print(f"[!] No se encontró {TIENDA_PY}")
        return
    port = "8501"
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(TIENDA_PY),
        "--server.port", port,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]
    try:
        creationflags = 0
        if os.name == "nt":
            creationflags = 0x08000000  # CREATE_NO_WINDOW
        subprocess.Popen(cmd, cwd=str(BASE_DIR),
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         creationflags=creationflags)
        time.sleep(2.5)
        webbrowser.open(f"http://localhost:{port}")
    except Exception as e:
        print(f"[!] No se pudo iniciar la tienda: {e}")


# ==========================================================
# APP TKINTER
# ==========================================================
class AddProductApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Amazonia Market · Agregar producto")
        self.geometry("520x900")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)

        self.image_path: Path | None = None
        self._preview_ref = None
        self._logo_ref = None

        self._build_ui()

    # -------------------- UI --------------------
    def _build_ui(self):
        # Hero morado con el logo grande
        hero = tk.Frame(self, bg=COLOR_PRIMARY, height=170)
        hero.pack(fill="x")
        hero.pack_propagate(False)

        logo = clean_logo_image()
        # escalar respetando aspecto para que ocupe la banda morada
        max_h = 130
        ratio = max_h / logo.height
        new_size = (int(logo.width * ratio), max_h)
        logo = logo.resize(new_size, Image.LANCZOS)
        self._logo_ref = ImageTk.PhotoImage(logo)
        tk.Label(hero, image=self._logo_ref, bg=COLOR_PRIMARY).pack(
            expand=True, pady=10
        )

        # Card del formulario
        card = tk.Frame(self, bg=COLOR_CARD, bd=0, highlightthickness=0)
        card.pack(fill="both", expand=True, padx=22, pady=22)

        tk.Label(card, text="Nuevo producto",
                 font=("Segoe UI", 16, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=20, pady=(18, 4))
        tk.Label(card, text="Completa los datos y presiona Agregar producto.",
                 font=("Segoe UI", 10), fg=COLOR_MUTED,
                 bg=COLOR_CARD).pack(anchor="w", padx=20, pady=(0, 14))

        # ---- Imagen ----
        self._label(card, "Imagen del producto")
        img_row = tk.Frame(card, bg=COLOR_CARD)
        img_row.pack(fill="x", padx=20, pady=(0, 12))

        self.preview = tk.Label(img_row, text="Sin imagen",
                                width=14, height=7,
                                bg="#F1F5F9", fg=COLOR_MUTED,
                                font=("Segoe UI", 9), bd=0,
                                relief="flat")
        self.preview.pack(side="left")

        btn_img = tk.Button(img_row, text="📷  Insertar imagen",
                            command=self.pick_image,
                            bg=COLOR_PRIMARY_2, fg="white",
                            activebackground=COLOR_PRIMARY,
                            activeforeground="white",
                            font=("Segoe UI", 10, "bold"),
                            relief="flat", bd=0, cursor="hand2",
                            padx=16, pady=10)
        btn_img.pack(side="left", padx=12)

        # ---- Nombre ----
        self._label(card, "Nombre del producto")
        self.entry_name = self._entry(card)

        # ---- Precio ----
        self._label(card, "Precio")
        self.entry_price = self._entry(card)

        # ---- Botón agregar ----
        add_btn = tk.Button(card, text="＋  Agregar producto",
                            command=self.add_product,
                            bg=COLOR_PRIMARY, fg="white",
                            activebackground=COLOR_PRIMARY_2,
                            activeforeground="white",
                            font=("Segoe UI", 12, "bold"),
                            relief="flat", bd=0, cursor="hand2",
                            pady=14)
        add_btn.pack(fill="x", padx=20, pady=(20, 10))

        # ---- Estado / contador ----
        self.status = tk.Label(card, text=self._count_text(),
                               font=("Segoe UI", 9),
                               fg=COLOR_MUTED, bg=COLOR_CARD)
        self.status.pack(anchor="w", padx=20, pady=(4, 14))

        open_btn = tk.Button(card, text="🌐  Abrir la tienda en el navegador",
                             command=lambda: webbrowser.open("http://localhost:8501/?admin=1"),
                             bg=COLOR_CARD, fg=COLOR_PRIMARY,
                             activebackground=COLOR_BG,
                             activeforeground=COLOR_PRIMARY,
                             font=("Segoe UI", 10, "underline"),
                             relief="flat", bd=0, cursor="hand2")
        open_btn.pack(pady=(0, 10))

        # ---- Botón para abrir la ventana de eliminar productos ----
        sep = tk.Frame(card, bg="#E2E8F0", height=1)
        sep.pack(fill="x", padx=20, pady=(4, 10))

        del_open_btn = tk.Button(card,
                                 text="🗑️  ELIMINAR PRODUCTO",
                                 command=self._open_delete_window,
                                 bg="#DC2626", fg="white",
                                 activebackground="#B91C1C",
                                 activeforeground="white",
                                 font=("Segoe UI", 12, "bold"),
                                 relief="flat", bd=0, cursor="hand2",
                                 pady=14,
                                 highlightthickness=0)
        del_open_btn.pack(fill="x", padx=20, pady=(0, 16))

        # Referencias a los widgets de la ventana de eliminar (se crean bajo demanda)
        self.delete_window = None
        self.list_canvas = None
        self.list_inner = None

    def _refresh_list(self):
        # actualizar contador siempre
        if hasattr(self, "status"):
            self.status.configure(text=self._count_text())

        # solo redibujar la lista si la ventana de eliminar está abierta
        if not self.list_inner or not self.list_inner.winfo_exists():
            return

        for w in self.list_inner.winfo_children():
            w.destroy()

        items = load_products()
        if not items:
            tk.Label(self.list_inner,
                     text="Aún no hay productos.",
                     font=("Segoe UI", 10, "italic"),
                     fg=COLOR_MUTED, bg=COLOR_CARD).pack(anchor="w", pady=6)
        else:
            for prod in items:
                self._product_row(prod)

    def _open_delete_window(self):
        # si ya está abierta, traerla al frente
        if self.delete_window and self.delete_window.winfo_exists():
            self.delete_window.lift()
            self.delete_window.focus_force()
            return

        win = tk.Toplevel(self)
        win.title("Eliminar productos - Amazonia Market")
        win.configure(bg=COLOR_BG)
        win.geometry("520x600")
        self.delete_window = win

        # cabecera roja
        header = tk.Frame(win, bg="#DC2626", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🗑️  Eliminar productos",
                 font=("Segoe UI", 16, "bold"),
                 fg="white", bg="#DC2626").pack(pady=18)

        body = tk.Frame(win, bg=COLOR_CARD)
        body.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(body, text="Presiona 🗑️ para eliminar un producto.",
                 font=("Segoe UI", 10), fg=COLOR_MUTED,
                 bg=COLOR_CARD).pack(anchor="w", padx=8, pady=(4, 8))

        list_wrap = tk.Frame(body, bg=COLOR_CARD)
        list_wrap.pack(fill="both", expand=True, padx=4, pady=4)

        self.list_canvas = tk.Canvas(list_wrap, bg=COLOR_CARD,
                                     highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_wrap, orient="vertical",
                                  command=self.list_canvas.yview)
        self.list_inner = tk.Frame(self.list_canvas, bg=COLOR_CARD)
        self.list_inner.bind(
            "<Configure>",
            lambda e: self.list_canvas.configure(
                scrollregion=self.list_canvas.bbox("all")
            ),
        )
        self.list_canvas.create_window((0, 0), window=self.list_inner, anchor="nw")
        self.list_canvas.configure(yscrollcommand=scrollbar.set)
        self.list_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_close():
            self.delete_window = None
            self.list_canvas = None
            self.list_inner = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", _on_close)

        self._refresh_list()

    def _product_row(self, prod):
        # ── Tarjeta con sombra envolvente ──
        # El frame de fondo (shadow) es la sombra; el card va dentro
        # con margen derecho e inferior para dejar ver la sombra.
        shadow = tk.Frame(self.list_inner, bg="#475569", bd=0)
        shadow.pack(fill="x", pady=10, padx=6)

        card = tk.Frame(shadow, bg="#FFFFFF", bd=0,
                        highlightbackground="#CBD5E1",
                        highlightthickness=1)
        card.pack(fill="x", expand=True, padx=(0, 5), pady=(0, 5))

        # nombre + precio
        info = tk.Frame(card, bg="#FFFFFF")
        info.pack(side="left", fill="x", expand=True, padx=12, pady=10)

        tk.Label(info, text=prod.get("nombre", "(sin nombre)"),
                 font=("Segoe UI", 11, "bold"),
                 fg=COLOR_TEXT, bg="#FFFFFF",
                 anchor="w").pack(anchor="w")

        precio = prod.get("precio", 0)
        try:
            precio_txt = f"${float(precio):.2f}"
        except Exception:
            precio_txt = f"${precio}"
        tk.Label(info, text=precio_txt,
                 font=("Segoe UI", 10, "bold"),
                 fg="#FFFFFF", bg="#16A34A",
                 padx=10, pady=3).pack(anchor="w", pady=(4, 0))

        # botón eliminar
        del_btn = tk.Button(card, text="🗑️",
                            command=lambda p=prod: self._delete_product(p),
                            bg="#DC2626", fg="white",
                            activebackground="#B91C1C",
                            activeforeground="white",
                            font=("Segoe UI", 12, "bold"),
                            relief="flat", bd=0, cursor="hand2",
                            padx=14, pady=8)
        del_btn.pack(side="right", padx=12, pady=10)


    def _delete_product(self, prod):
        nombre = prod.get("nombre", "este producto")
        if not messagebox.askyesno("Eliminar producto",
                                   f"¿Seguro que quieres eliminar '{nombre}'?"):
            return
        items = load_products()
        pid = prod.get("id")
        items = [p for p in items if p.get("id") != pid]
        save_products(items)

        # borrar imagen asociada
        img_rel = prod.get("imagen", "")
        if img_rel:
            try:
                img_path = BASE_DIR / img_rel
                if img_path.exists():
                    img_path.unlink()
            except Exception:
                pass

        self._refresh_list()

    def _label(self, parent, text):
        tk.Label(parent, text=text, font=("Segoe UI", 10, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=20, pady=(6, 4))

    def _entry(self, parent):
        e = tk.Entry(parent, font=("Segoe UI", 12),
                     bg="#F8FAFC", fg=COLOR_TEXT,
                     relief="flat", bd=0,
                     highlightthickness=1,
                     highlightbackground="#E2E8F0",
                     highlightcolor=COLOR_PRIMARY_2)
        e.pack(fill="x", padx=20, ipady=10, pady=(0, 6))
        return e

    def _count_text(self):
        return f"Productos en la tienda: {len(load_products())}"

    # -------------------- Acciones --------------------
    def pick_image(self):
        path = filedialog.askopenfilename(
            title="Selecciona una imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"),
                       ("Todos los archivos", "*.*")],
        )
        if not path:
            return
        try:
            img = Image.open(path)
            img.thumbnail((140, 140))
            self._preview_ref = ImageTk.PhotoImage(img)
            self.preview.configure(image=self._preview_ref, text="",
                                   width=140, height=140, bg=COLOR_CARD)
            self.image_path = Path(path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la imagen:\n{e}")

    def add_product(self):
        name = self.entry_name.get().strip()
        price_raw = self.entry_price.get().strip().replace(",", ".")
        if not name:
            messagebox.showwarning("Falta información", "Escribe el nombre del producto.")
            return
        try:
            price = float(price_raw)
        except ValueError:
            messagebox.showwarning("Precio inválido", "Escribe un precio válido, ej: 19.90")
            return
        if not self.image_path:
            messagebox.showwarning("Falta imagen", "Inserta una imagen del producto.")
            return

        # copiar imagen al folder del proyecto
        ext = self.image_path.suffix.lower() or ".png"
        new_name = f"{uuid.uuid4().hex}{ext}"
        dest = IMG_DIR / new_name
        try:
            shutil.copy(self.image_path, dest)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la imagen:\n{e}")
            return

        items = load_products()
        items.append({
            "id": uuid.uuid4().hex,
            "nombre": name,
            "precio": price,
            "imagen": f"product_images/{new_name}",
        })
        save_products(items)
        self._refresh_list()

        # limpiar
        self.entry_name.delete(0, "end")
        self.entry_price.delete(0, "end")
        self.image_path = None
        self._preview_ref = None
        self.preview.configure(image="", text="Sin imagen",
                               width=14, height=7, bg="#F1F5F9")
        self.status.configure(text=self._count_text())
        messagebox.showinfo("Producto agregado",
                            f"'{name}' se agregó a la tienda.\n"
                            f"Actualiza el navegador para verlo.")


# ==========================================================
# Main
# ==========================================================
def main():
    # 1) lanzar la tienda en un hilo aparte
    threading.Thread(target=launch_store, daemon=True).start()
    # 2) abrir la ventana de escritorio
    app = AddProductApp()
    app.mainloop()


if __name__ == "__main__":
    main()
