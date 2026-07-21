# ==========================================================
# AMAZONIA MARKET - Tienda Virtual (Streamlit) - Estilo Madison Center
# ==========================================================
#     streamlit run tienda.py
# Requisitos:  pip install streamlit pillow
# ==========================================================
#
# Novedades (Ultra Actualización):
#   * Barra superior azul estilo Madison Center con banner de delivery.
#   * Topbar con: MENU, LOGO, BUSQUEDA global (con boton amarillo),
#     Iniciar sesion / Mi cuenta, Loyalty Club y CARRITO con contador.
#   * Fila de circulos azules (uno por apartado) con icono y nombre.
#     Al hacer clic te lleva directo a ese apartado.
#   * En el HOME, cada apartado se muestra como una fila:
#         - Titulo del apartado a la izquierda
#         - Boton "Ver mas ->" arriba a la derecha
#         - Primeras 5 imagenes del apartado con su precio
#   * Buscador GLOBAL: busca en TODOS los apartados a la vez.
#   * Compatible con tus JSON actuales (products.json, categories.json).
#     No necesitas cambiar tu app de escritorio (agregar_producto.py).
# ==========================================================

import base64
import io
import json
import re
from pathlib import Path

import streamlit as st
from PIL import Image, ImageFilter

BASE_DIR    = Path(__file__).parent.resolve()
DATA_FILE   = BASE_DIR / "products.json"
CATS_FILE   = BASE_DIR / "categories.json"
IMG_DIR     = BASE_DIR / "product_images"
LOGO_FILE   = BASE_DIR / "logo.b64"
BANNER_FILE = BASE_DIR / "banner.png"
IMG_DIR.mkdir(exist_ok=True)

# --- Personalizacion (compatibilidad con la app de escritorio) ---
SETTINGS_FILE    = BASE_DIR / "site_settings.json"
CUSTOM_LOGO_FILE = BASE_DIR / "site_logo.png"
# Opcional: permite mapear nombre_de_apartado -> emoji/icono, para
# personalizar los circulos de la barra de categorias. Si no existe,
# se autodetecta un emoji por el nombre.
CAT_ICONS_FILE   = BASE_DIR / "category_icons.json"
CAT_STYLES_FILE  = BASE_DIR / "category_styles.json"
TITLES_FILE      = BASE_DIR / "titles_settings.json"
CART_FILE        = BASE_DIR / "cart.json"


def load_site_settings() -> dict:
    defaults = {
        "site_name": "Amazonia",
        "site_market": "MARKET",
        "site_logo_b64": "",
        # --- Personalizacion visual de la barra superior azul ---
        "topbar_bg_color":  "#2A2A9C",   # color de fondo de la barra superior
        "topbar_bg_image_b64": "",        # imagen de fondo opcional (b64)
        "topbar_bg_blur":       "0",      # 0..20 px
        "topbar_bg_brightness": "100",    # % (0..200) 100=normal
        "topbar_bg_saturation": "100",    # % (0..200) 100=normal
        "topbar_bg_opacity":    "100",    # % (0..100) sobre la imagen
        # --- Botones de la barra superior ---
        "btn_menu_bg":   "rgba(255,255,255,.08)",
        "btn_menu_fg":   "#FFFFFF",
        "btn_search_bg": "#F5B301",
        "btn_search_fg": "#0F172A",
        "btn_cart_bg":   "rgba(255,255,255,.08)",
        "btn_cart_fg":   "#FFFFFF",
        # --- Banner de delivery ---
        "delivery_text": "🚚  Delivery GRATIS en toda la zona de Coro",
        # --- Fondo completo de la pagina ---
        "page_bg_type":       "color",   # "color" | "image" | "none"
        "page_bg_color":      "#F4F5F7",
        "page_bg_image_b64":  "",
        "page_bg_blur":       "0",
        "page_bg_brightness": "100",
        "page_bg_opacity":    "100",
        # --- Ocultar el logo pequeno de la topbar ---
        "hide_logo":          "0",
        # --- Estilos globales de secciones (por si un apartado no tiene los suyos) ---
        "section_title_color": "#2A2A9C",
        "section_title_size":  "22",
        "section_more_bg":     "#2A2A9C",
        "section_more_fg":     "#FFFFFF",
        # --- Colores del CARRITO (todo personalizable) ---
        "cart_name_color":   "#0F172A",
        "cart_price_color":  "#0F172A",
        "cart_qty_color":    "#2A2A9C",
        "cart_line_bg":      "#16A34A",
        "cart_line_fg":      "#FFFFFF",
        "cart_total_color":  "#16A34A",
        "cart_pay_bg":       "#16A34A",
        "cart_pay_fg":       "#FFFFFF",
        "cart_add_bg":       "#2A2A9C",
        "cart_add_fg":       "#FFFFFF",
        "cart_del_bg":       "#EF4444",
        "cart_del_fg":       "#FFFFFF",
    }
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                defaults.update({k: v for k, v in data.items() if isinstance(v, str) and v.strip()})
        except Exception:
            pass
    return defaults


def load_category_icons() -> dict:
    if CAT_ICONS_FILE.exists():
        try:
            data = json.loads(CAT_ICONS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except Exception:
            pass
    return {}


def load_titles() -> list:
    """Lista de bloques de titulo para la topbar: [{text, font, size, color, weight}, ...].
    Retrocompatible: si no existe, usa site_name/site_market como 2 titulos."""
    if TITLES_FILE.exists():
        try:
            data = json.loads(TITLES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                out = []
                for b in data:
                    if not isinstance(b, dict): continue
                    out.append({
                        "text":   str(b.get("text",   "")),
                        "font":   str(b.get("font",   "Poppins")),
                        "size":   int(b.get("size",   28)),
                        "color":  str(b.get("color",  "#FFFFFF")),
                        "weight": str(b.get("weight", "700")),
                    })
                return out
        except Exception:
            pass
    return []


def load_category_styles() -> dict:
    """Estilos por apartado. {cat: {icon, circle_color, circle_size, label_color,
       label_size, title_color, title_size, more_bg, more_fg}}"""
    if CAT_STYLES_FILE.exists():
        try:
            data = json.loads(CAT_STYLES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def get_cat_style(cat: str, styles: dict) -> dict:
    st_ = styles.get(cat, {}) if isinstance(styles, dict) else {}
    return {
        "icon":         str(st_.get("icon",         "")),
        "circle_color": str(st_.get("circle_color", "#2A2A9C")),
        "circle_size":  int(st_.get("circle_size",  96)),
        "label_color":  str(st_.get("label_color",  "#0F172A")),
        "label_size":   int(st_.get("label_size",   14)),
        "title_color":  str(st_.get("title_color",  "#2A2A9C")),
        "title_size":   int(st_.get("title_size",   22)),
        "more_bg":      str(st_.get("more_bg",      "#2A2A9C")),
        "more_fg":      str(st_.get("more_fg",      "#FFFFFF")),
    }


# ----- Carrito persistente en disco (fix bug: el <a href> reseteaba session_state) -----
def _load_cart_file() -> dict:
    if CART_FILE.exists():
        try:
            data = json.loads(CART_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def _save_cart_file(cart: dict) -> None:
    try:
        CART_FILE.write_text(json.dumps(cart, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    except Exception:
        pass


PRODUCTS_PER_PAGE = 12
PREVIEW_PER_CAT   = 5   # cuantas imagenes se muestran en la fila del home

# --- Paleta estilo Madison Center (azul rey + acento amarillo) ---
COLOR_PRIMARY    = "#2A2A9C"   # azul rey fuerte de la barra superior
COLOR_PRIMARY_2  = "#3838B8"   # azul intermedio
COLOR_PRIMARY_3  = "#4B4BD9"   # azul brillante para gradientes
COLOR_ACCENT     = "#F5B301"   # amarillo/dorado boton buscar
COLOR_ACCENT_2   = "#FFC933"   # amarillo mas claro (hover)
COLOR_BG_GRAY    = "#F4F5F7"   # gris muy suave de fondo pagina
COLOR_CARD       = "#FFFFFF"
COLOR_TEXT       = "#0F172A"
COLOR_MUTED      = "#64748B"
COLOR_PRICE      = "#16A34A"


# ----------------------------------------------------------
# Logo (compatibilidad total con archivos previos)
# ----------------------------------------------------------
def _load_logo() -> Image.Image:
    if LOGO_FILE.exists():
        raw = base64.b64decode(LOGO_FILE.read_text().strip())
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    img = Image.new("RGBA", (400, 120), (42, 42, 156, 255))
    return img


@st.cache_data(show_spinner=False)
def get_logo_b64() -> str:
    img = _load_logo()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def get_topbar_logo_b64() -> str:
    """Logo para la barra azul: usa site_logo.png si existe, si no el logo.b64."""
    try:
        if CUSTOM_LOGO_FILE.exists():
            img = Image.open(CUSTOM_LOGO_FILE).convert("RGBA")
        else:
            settings = load_site_settings()
            b64 = settings.get("site_logo_b64", "").strip()
            if b64:
                img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGBA")
            else:
                img = _load_logo()
    except Exception:
        img = _load_logo()

    # Recortar bounding box para que llene bien el espacio
    bbox = img.split()[-1].getbbox()
    if bbox:
        img = img.crop(bbox)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ----------------------------------------------------------
# Datos
# ----------------------------------------------------------
def load_products():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def load_categories():
    if not CATS_FILE.exists():
        return []
    try:
        return json.loads(CATS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def format_price(p) -> str:
    try:
        return f"${float(p):,.2f}"
    except Exception:
        return f"${p}"


def img_to_data_uri(rel_path: str) -> str:
    if rel_path:
        full = BASE_DIR / rel_path
        if full.exists():
            try:
                return "data:image/png;base64," + base64.b64encode(
                    full.read_bytes()
                ).decode()
            except Exception:
                pass
    return (
        "data:image/svg+xml;base64," + base64.b64encode(
            b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            b'<rect width="100" height="100" fill="#f1f5f9"/>'
            b'<text x="50" y="55" text-anchor="middle" fill="#94a3b8" '
            b'font-family="Arial" font-size="10">sin imagen</text></svg>'
        ).decode()
    )


# ----------------------------------------------------------
# Iconos de categoria (emoji autodetectado por palabra clave)
# ----------------------------------------------------------
_CATEGORY_ICON_RULES = [
    (r"aliment|comida|mercado|abarrot|grocer", "🛒"),
    (r"bebid|refresco|jugo|agua|licor|vino|cerveza", "🥤"),
    (r"farmac|medic|salud|pharma", "💊"),
    (r"perfum|fragancia|colonia", "🧴"),
    (r"maquill|cosmet|belleza|makeup", "💄"),
    (r"ropa|calzado|zapato|moda|vestir", "👕"),
    (r"cartera|reloj|acceso|bolso|joyeria|joyer", "👜"),
    (r"juguet|nino|kids|toy", "🧸"),
    (r"bisuter|aret|collar|anillo|pulser", "💍"),
    (r"charcut|carnic|jamon|queso|embuti", "🧀"),
    (r"panader|pan|reposter|dulce|torta|pastel", "🥐"),
    (r"limpie|hogar|jabon|deterg", "🧽"),
    (r"electro|tecno|celular|tv|telefono", "📱"),
    (r"mascot|perro|gato|pet", "🐾"),
    (r"libro|papeler|utiles", "📚"),
    (r"deport|gim|fitness", "🏋️"),
    (r"bebe|pañal", "🍼"),
    (r"herram|ferreter", "🔧"),
]


def icon_for_category(name: str, overrides: dict) -> str:
    key = (name or "").strip()
    if key in overrides:
        return overrides[key]
    lower = key.lower()
    for pattern, emoji in _CATEGORY_ICON_RULES:
        if re.search(pattern, lower):
            return emoji
    return "🏷️"


# ----------------------------------------------------------
# Carrito (session_state)
# ----------------------------------------------------------
def _cart():
    if "cart" not in st.session_state:
        st.session_state.cart = _load_cart_file()
    return st.session_state.cart


def _persist():
    _save_cart_file(st.session_state.get("cart", {}))


def cart_add(prod, qty=1):
    c = _cart()
    key = prod.get("nombre", "")
    if key in c:
        c[key]["qty"] += qty
    else:
        c[key] = {
            "nombre": key,
            "precio": float(prod.get("precio", 0) or 0),
            "imagen": prod.get("imagen", ""),
            "qty": qty,
        }
    if c[key]["qty"] <= 0:
        c.pop(key, None)
    _persist()


def cart_set(name, qty):
    c = _cart()
    if name in c:
        if qty <= 0:
            c.pop(name, None)
        else:
            c[name]["qty"] = qty
        _persist()


def cart_total():
    return sum(i["precio"] * i["qty"] for i in _cart().values())


def cart_count():
    return sum(i["qty"] for i in _cart().values())


# ----------------------------------------------------------
# Config
# ----------------------------------------------------------
_settings = load_site_settings()
_site_name = _settings.get("site_name", "Amazonia")
_site_market = _settings.get("site_market", "MARKET")

st.set_page_config(
    page_title=(f"{_site_name} {_site_market}".strip() or "Tienda"),
    page_icon="🛒",
    layout="wide",
)

logo_b64        = get_logo_b64()
topbar_logo_b64 = get_topbar_logo_b64()
category_icons  = load_category_icons()

# --- Personalizacion visual (barra superior + botones) ---
_tb_bg_color  = _settings.get("topbar_bg_color",  "#2A2A9C")
_tb_bg_img_b64 = _settings.get("topbar_bg_image_b64", "").strip()
try:    _tb_blur = max(0, min(20, int(float(_settings.get("topbar_bg_blur", "0")))))
except: _tb_blur = 0
try:    _tb_bri  = max(0, min(200, int(float(_settings.get("topbar_bg_brightness", "100")))))
except: _tb_bri  = 100
try:    _tb_sat  = max(0, min(200, int(float(_settings.get("topbar_bg_saturation", "100")))))
except: _tb_sat  = 100
try:    _tb_op   = max(0, min(100, int(float(_settings.get("topbar_bg_opacity",    "100")))))
except: _tb_op   = 100
_btn_menu_bg   = _settings.get("btn_menu_bg",   "rgba(255,255,255,.08)")
_btn_menu_fg   = _settings.get("btn_menu_fg",   "#FFFFFF")
_btn_search_bg = _settings.get("btn_search_bg", COLOR_ACCENT)
_btn_search_fg = _settings.get("btn_search_fg", "#0F172A")
_facebook_url  = (_settings.get("social_facebook_url",  "") or "").strip()
_instagram_url = (_settings.get("social_instagram_url", "") or "").strip()
_tiktok_url    = (_settings.get("social_tiktok_url",    "") or "").strip()
_btn_cart_bg   = _settings.get("btn_cart_bg",   "rgba(255,255,255,.08)")
_btn_cart_fg   = _settings.get("btn_cart_fg",   "#FFFFFF")
_delivery_text = _settings.get("delivery_text", "🚚  Delivery GRATIS en toda la zona de Coro")
# --- Fondo completo de la pagina web ---
_pg_type   = _settings.get("page_bg_type", "color")
_pg_color  = _settings.get("page_bg_color", "#F4F5F7")
_pg_img    = _settings.get("page_bg_image_b64", "").strip()
try:    _pg_blur = max(0, min(30,  int(float(_settings.get("page_bg_blur", "0")))))
except: _pg_blur = 0
try:    _pg_bri  = max(0, min(200, int(float(_settings.get("page_bg_brightness", "100")))))
except: _pg_bri  = 100
try:    _pg_op   = max(0, min(100, int(float(_settings.get("page_bg_opacity", "100")))))
except: _pg_op   = 100
_hide_logo = str(_settings.get("hide_logo", "0")).strip() in ("1", "true", "True", "yes")
_hide_titles = str(_settings.get("hide_titles", "0")).strip() in ("1", "true", "True", "yes")
try:    _logo_size_px = max(24, min(400, int(float(_settings.get("logo_size", "54")))))
except: _logo_size_px = 54
try:    _logo_offx_px = max(-400, min(400, int(float(_settings.get("logo_offset_x", "0")))))
except: _logo_offx_px = 0
_logo_align = _settings.get("logo_align", "left")
_titles    = load_titles()
_cat_styles= load_category_styles()
# --- Estilos por defecto de las secciones de apartado ---
_sec_title_color = _settings.get("section_title_color", "#2A2A9C")
try:    _sec_title_size = int(float(_settings.get("section_title_size", "22")))
except: _sec_title_size = 22
_sec_more_bg = _settings.get("section_more_bg", "#2A2A9C")
_sec_more_fg = _settings.get("section_more_fg", "#FFFFFF")
# --- Menu desplegable (aparece al hacer clic en el boton ☰) ---
_menu_panel_bg = _settings.get("menu_panel_bg", "#2A2A9C")
_menu_panel_fg = _settings.get("menu_panel_fg", "#FFFFFF")
# --- Estilos del carrito ---
_ct_pagebg = _settings.get("cart_page_bg",    "#EFF3FF")
_ct_name  = _settings.get("cart_name_color",  "#2A2A9C")
_ct_price = _settings.get("cart_price_color", "#0F172A")
_ct_qty   = _settings.get("cart_qty_color",   "#2A2A9C")
_ct_lbg   = _settings.get("cart_line_bg",     "#16A34A")
_ct_lfg   = _settings.get("cart_line_fg",     "#FFFFFF")
_ct_tot   = _settings.get("cart_total_color", "#16A34A")
_ct_paybg = _settings.get("cart_pay_bg",      "#16A34A")
_ct_payfg = _settings.get("cart_pay_fg",      "#FFFFFF")
_ct_addbg = _settings.get("cart_add_bg",      "#2A2A9C")
_ct_addfg = _settings.get("cart_add_fg",      "#FFFFFF")
_ct_delbg = _settings.get("cart_del_bg",      "#EF4444")
_ct_delfg = _settings.get("cart_del_fg",      "#FFFFFF")

# Altura aprox de la barra superior completa (banner + fila): usada para
# pintar el fondo azul de forma continua detras de los widgets nativos de
# Streamlit (que rompen el flujo de HTML).
_TOPBAR_BAND_PX = 152


# ==========================================================
# CSS GLOBAL - estilo Madison Center
# ==========================================================
st.markdown(
    f"""
    <style>
      /* --- Google Fonts para el nombre llamativo del sitio --- */
      @import url('https://fonts.googleapis.com/css2?family=Pacifico&family=Poppins:wght@400;600;700;800;900&family=Montserrat:wght@400;700;900&family=Playfair+Display:wght@400;700;900&family=Bebas+Neue&family=Lobster&family=Oswald:wght@400;700&family=Roboto:wght@400;700;900&family=Dancing+Script:wght@400;700&family=Great+Vibes&family=Anton&family=Merriweather:wght@400;700&family=Raleway:wght@400;700;900&display=swap');

      /* --- Fondo general limpio --- */
      .stApp {{
        {"background:" + f"url('data:image/png;base64,{_pg_img}') center/cover no-repeat fixed, {_pg_color};" if (_pg_type == "image" and _pg_img) else ("background-color:" + _pg_color + ";" if _pg_type != "none" else "")}
      }}
      .stApp::before {{
        {"content:''; position:fixed; inset:0; background:inherit; filter: blur(" + str(_pg_blur) + "px) brightness(" + str(_pg_bri) + "%); opacity:" + f"{_pg_op/100:.2f}" + "; pointer-events:none; z-index:-1;" if (_pg_type == "image" and _pg_img and (_pg_blur or _pg_bri != 100 or _pg_op != 100)) else "display:none;"}
      }}
      header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 0 !important;
      }}
      #MainMenu, footer {{ visibility: hidden; }}
      .main .block-container {{
        padding-top: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100% !important;
      }}
      /* algunas versiones nuevas de Streamlit usan otro data-testid */
      [data-testid="stMainBlockContainer"],
      [data-testid="stAppViewBlockContainer"] {{
        padding-top: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100% !important;
      }}

      /* --- Wrapper interno con ancho controlado --- */
      .am-wrap {{
        max-width: 1280px;
        margin: 0 auto;
        padding: 0 24px;
      }}

      /* ================= BARRA SUPERIOR AZUL ================= */
      /* La topbar entera se renderiza como un st.container(key="am_topbar_v2").
         Streamlit expone ese contenedor con la clase .st-key-am_topbar_v2, asi
         que TODO lo que va dentro (banner + logo + busqueda + carrito) queda
         visualmente DENTRO de la banda azul, sin importar donde lo pinte
         Streamlit. */
      .st-key-am_topbar_v2 {{
        position: relative;
        width: 100vw !important;
        margin-left: calc(50% - 50vw) !important;
        margin-right: calc(50% - 50vw) !important;
        background:
          {"url('data:image/png;base64," + _tb_bg_img_b64 + "') center/cover no-repeat, " if _tb_bg_img_b64 else ""}{_tb_bg_color} !important;
        color: #fff;
        padding: 0 24px 14px 24px !important;
        margin-top: 0 !important;
        margin-bottom: 8px !important;
        box-shadow: 0 4px 14px rgba(0,0,0,.12);
        border-radius: 0 !important;
        overflow: hidden;
      }}
      /* Filtros (blur/brillo/saturacion) solo se aplican cuando hay imagen */
      {"" if not _tb_bg_img_b64 else f".st-key-am_topbar_v2::before {{ content:''; position:absolute; inset:0; background: inherit; filter: blur({_tb_blur}px) brightness({_tb_bri}%) saturate({_tb_sat}%); opacity:{_tb_op/100:.2f}; pointer-events:none; z-index:0; }} .st-key-am_topbar_v2 > * {{ position: relative; z-index: 1; }}"}
      /* que los labels/inputs internos hereden buen contraste sobre azul */
      .st-key-am_topbar_v2 label, .st-key-am_topbar_v2 p {{ color: #fff !important; }}
      /* Banner de delivery */
      .am-delivery-banner {{
        text-align: center;
        font-weight: 700;
        font-size: 14px;
        letter-spacing: .2px;
        padding: 10px 12px 12px 12px;
        color: #fff;
        border-bottom: 1px solid rgba(255,255,255,.18);
        background: transparent;
        margin: 0 -24px 10px -24px;
      }}
      .am-brand {{
        display: flex; align-items: center; gap: 10px;
      }}
      .am-brand-name {{
        font-family: 'Pacifico', 'Brush Script MT', cursive;
        font-size: 30px; color: #fff; line-height: 1;
        text-shadow: 0 2px 6px rgba(0,0,0,.35);
      }}
      .am-brand-market {{
        font-family: 'Poppins', sans-serif;
        font-weight: 900; color: {COLOR_ACCENT};
        font-size: 16px; letter-spacing: 3px; margin-top: 2px;
      }}
      .am-brand-logo {{
        height: 54px; width: auto; display:block;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,.35));
      }}

      /* --- Botones utilitarios de la topbar (menu, cuenta, loyalty, cart) --- */
      .am-tb-item {{
        display: inline-flex; align-items: center; gap: 10px;
        background: rgba(255,255,255,.08);
        border: 1px solid rgba(255,255,255,.18);
        color: #fff !important; text-decoration: none !important;
        padding: 10px 16px; border-radius: 12px;
        font-family: 'Poppins', sans-serif; font-weight: 600; font-size: 14px;
        line-height: 1.1;
        transition: background .15s ease, transform .15s ease;
        white-space: nowrap;
      }}
      .am-tb-item:hover {{
        background: rgba(255,255,255,.18);
        transform: translateY(-1px);
      }}
      .am-tb-icon {{
        display:inline-flex; width:22px; height:22px; align-items:center; justify-content:center;
      }}
      .am-tb-sub {{
        display:block; font-size:11px; opacity:.85; font-weight:500;
      }}
      .am-tb-strong {{
        display:block; font-size:14px; font-weight:800; letter-spacing:.3px;
      }}

      /* Boton-icono del carrito (sin texto) */
      .am-cart-btn {{
        position: relative;
        display: inline-flex; align-items: center; justify-content: center;
        width: 54px; height: 54px; border-radius: 14px;
        background: {_btn_cart_bg};
        color: {_btn_cart_fg} !important;
        text-decoration: none !important;
        border: 1px solid rgba(255,255,255,.18);
        box-shadow: 0 4px 12px rgba(0,0,0,.18);
        transition: transform .15s ease, background .15s ease;
        font-size: 26px; line-height: 1;
      }}
      .am-cart-btn:hover {{
        transform: translateY(-1px);
        filter: brightness(1.08);
      }}
      .am-cart-badge {{
        position: absolute; top: -6px; right: -6px;
        background: {COLOR_ACCENT}; color: #0F172A;
        font-size: 11px; font-weight: 900;
        min-width: 22px; height: 22px; border-radius: 999px;
        display:inline-flex; align-items:center; justify-content:center;
        padding: 0 6px; box-shadow: 0 2px 6px rgba(0,0,0,.35);
        border: 2px solid #fff;
      }}
      .am-loyalty-medal {{
        width: 26px; height: 26px; border-radius: 50%;
        background: {COLOR_ACCENT};
        display:inline-flex; align-items:center; justify-content:center;
        color: #7A5A00; font-weight: 900; font-size: 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,.35);
      }}

      /* ================= FILA DE CATEGORIAS (CIRCULOS) ================= */
      .am-cats-wrap {{
        background: #fff;
        border-bottom: 1px solid #E5E7EB;
        padding: 22px 0 26px 0;
        margin-bottom: 24px;
      }}
      .am-cats-scroll {{
        max-width: 1280px; margin: 0 auto;
        display: flex; gap: 22px; padding: 0 24px;
        overflow-x: auto; overflow-y: hidden;
        scrollbar-width: thin;
      }}
      .am-cats-scroll::-webkit-scrollbar {{ height: 6px; }}
      .am-cats-scroll::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 3px; }}
      .am-cat-circle {{
        flex: 0 0 auto;
        display: flex; flex-direction: column; align-items: center;
        gap: 10px; text-decoration: none !important; color: {COLOR_TEXT} !important;
        min-width: 110px;
      }}
      .am-cat-circle .bubble {{
        width: 96px; height: 96px; border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, {COLOR_PRIMARY_3}, {COLOR_PRIMARY} 75%);
        color: #fff; display:flex; align-items:center; justify-content:center;
        font-size: 44px;
        box-shadow: 0 10px 22px rgba(42,42,156,.35),
                    inset 0 -6px 14px rgba(0,0,0,.15);
        transition: transform .15s ease, box-shadow .15s ease;
      }}
      .am-cat-circle:hover .bubble {{
        transform: translateY(-3px) scale(1.03);
        box-shadow: 0 14px 28px rgba(42,42,156,.45),
                    inset 0 -6px 14px rgba(0,0,0,.15);
      }}
      .am-cat-circle .label {{
        font-family: 'Poppins', sans-serif;
        font-weight: 700; font-size: 14px; text-align: center;
        color: {COLOR_TEXT}; max-width: 130px; line-height: 1.2;
      }}

      /* ================= SECCION DE APARTADO EN HOME ================= */
      .am-section {{
        background: #fff;
        border: 1px solid #E5E7EB;
        border-radius: 18px;
        padding: 22px 24px 18px 24px;
        margin-bottom: 26px;
        box-shadow: 0 6px 18px rgba(15,23,42,.06);
      }}
      .am-section-head {{
        display:flex; align-items:center; justify-content:space-between;
        margin-bottom: 16px; gap: 12px;
      }}
      .am-section-title-h {{
        font-family: 'Poppins', sans-serif;
        color: {COLOR_PRIMARY};
        font-size: 22px; font-weight: 800;
        display: inline-flex; align-items: center; gap: 10px;
        text-transform: capitalize;
      }}
      .am-section-title-h .dot {{
        width: 10px; height: 10px; border-radius: 50%;
        background: {COLOR_ACCENT};
      }}
      .am-section-empty {{
        color: {COLOR_MUTED}; text-align: center; padding: 24px;
        border: 1px dashed #E2E8F0; border-radius: 12px;
      }}

      /* Mini tarjeta de producto (preview del home) */
      .am-mini {{
        background: #fff;
        border: 1px solid #EEF0F4;
        border-radius: 14px;
        padding: 10px 8px 12px 8px;
        text-align: center;
        transition: transform .12s ease, box-shadow .12s ease;
      }}
      .am-mini:hover {{
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(15,23,42,.10);
      }}
      .am-mini img {{
        width: 100%; aspect-ratio: 1/1; object-fit: contain;
        border-radius: 10px; background: #F8FAFC;
        max-height: 130px;
      }}
      .am-mini .name {{
        font-size: 12px; color: {COLOR_TEXT}; font-weight: 600;
        margin: 8px 4px 4px 4px; line-height: 1.2;
        min-height: 30px;
        display: -webkit-box; -webkit-line-clamp: 2;
        -webkit-box-orient: vertical; overflow: hidden;
      }}
      .am-mini .price {{
        display:inline-block; background: {COLOR_PRICE}; color:#fff;
        font-weight: 800; font-size: 12px;
        padding: 3px 10px; border-radius: 8px;
      }}

      /* ================= TARJETAS DE PRODUCTO (vista apartado) ================= */
      .am-card {{
        background: {COLOR_CARD};
        border-radius: 16px; padding: 14px 12px 12px 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 8px 18px rgba(15,23,42,.10);
        text-align: center; margin-bottom: 6px;
      }}
      .am-card img {{
        width: 100%; aspect-ratio: 1/1; object-fit: contain;
        border-radius: 12px; background: #F8FAFC;
        max-height: 170px;
      }}
      .am-name {{
        font-weight: 600; color: {COLOR_TEXT};
        margin: 10px 4px 6px 4px; font-size: 14px;
        line-height: 1.25; min-height: 36px;
      }}
      .am-price {{
        display:inline-block; background:{COLOR_PRICE}; color:#fff !important;
        font-weight:800; font-size:16px; padding:5px 14px;
        border-radius:10px; margin: 2px 0 6px 0;
        box-shadow:0 2px 6px rgba(22,163,74,.25);
      }}
      .am-qty-badge {{
        display:inline-block; background:{COLOR_PRIMARY}; color:#fff;
        padding:2px 8px; border-radius:999px; font-size:11px;
        font-weight:700; margin-left:6px;
      }}
      .am-card-gap {{ height: 10px; }}
      .am-empty {{
        text-align:center; padding: 50px 20px; color:{COLOR_MUTED};
        background:#fff; border-radius:16px; border:1px dashed #e5e7eb;
      }}

      /* ---- Botones de Streamlit ---- */
      div[data-testid="stButton"] > button {{
        background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_PRIMARY_3} 100%);
        color: #fff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        min-height: 42px !important;
        box-shadow: 0 4px 12px rgba(42,42,156,.28) !important;
        transition: transform .15s ease, box-shadow .15s ease !important;
      }}
      div[data-testid="stButton"] > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 18px rgba(42,42,156,.35) !important;
        filter: brightness(1.05);
      }}
      /* Botones de la topbar identificados por su key de Streamlit */
      .st-key-btn_menu button, .st-key-btn_menu button:hover {{
        background: {_btn_menu_bg} !important;
        color: {_btn_menu_fg} !important;
        border: 1px solid rgba(255,255,255,.18) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,.18) !important;
      }}
      .st-key-btn_search button, .st-key-btn_search button:hover {{
        background: {_btn_search_bg} !important;
        color: {_btn_search_fg} !important;
        border-radius: 0 8px 8px 0 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,.18) !important;
      }}
      div[data-testid="stButton"] > button[kind="primary"] {{
        background: #EF4444 !important;
        box-shadow: 0 6px 14px rgba(239,68,68,.35) !important;
      }}
      div[data-testid="stButton"] > button[kind="primary"]:hover {{
        background: #DC2626 !important;
      }}
      /* Boton "Ver mas" chico y amarillo */
      div[data-testid="stButton"] > button.am-more,
      button[data-am-more="1"] {{
        background: {COLOR_ACCENT} !important;
        color: #0F172A !important;
        min-height: 36px !important;
        padding: 6px 14px !important;
        font-size: 13px !important;
      }}
      /* Los <a> "Ver más" de cada apartado usan color inline; forzamos que
         herede desde su propio span y no de la hoja de Streamlit. */
      [data-testid="stMarkdownContainer"] a > span {{
        color: inherit;
      }}
      .am-menu-panel a, .am-menu-panel a:visited, .am-menu-panel a:hover {{
        color: {_menu_panel_fg} !important;
        text-decoration: none !important;
      }}

      /* Search input estilo Madison */
      div[data-testid="stTextInput"] > div > div > input {{
        background: #fff !important;
        color: #000 !important;
        caret-color: #000 !important;
        border: none !important;
        height: 46px !important;
        border-radius: 8px 0 0 8px !important;
        font-size: 15px !important;
        padding-left: 14px !important;
      }}
      div[data-testid="stTextInput"] > div > div > input::placeholder {{
        color: #6B7280 !important;
        opacity: 1 !important;
      }}

      /* Modal cantidad */
      .am-modal-img {{
        display:block; margin: 0 auto 10px auto;
        max-height: 160px; width:auto;
        border-radius: 12px; background:#f8fafc;
        border:1px solid #E2E8F0;
      }}
      .am-modal-name {{
        text-align:center; font-weight:700; font-size:18px;
        color:{COLOR_TEXT}; margin: 4px 0 2px 0;
      }}
      .am-modal-price {{
        text-align:center; color:{COLOR_PRICE}; font-weight:800;
        font-size:20px; margin-bottom: 14px;
      }}

      /* ================= RESPONSIVE (TELEFONO / TABLET) ================= */
      /* Tablet */
      @media (max-width: 980px) {{
        .am-wrap {{ padding: 0 16px; }}
        .am-section {{ padding: 18px 16px 16px 16px; }}
        .am-section-title-h {{ font-size: 20px; }}
      }}

      /* Telefono - Layout compacto tipo Madison Center */
      @media (max-width: 780px) {{
        /* --- Topbar compacta --- */
        .st-key-am_topbar_v2 {{
          padding: 6px 10px 14px 10px !important;
          margin-bottom: 10px !important;
        }}
        .am-delivery-banner {{
          font-size: 12px; padding: 8px 10px;
          margin: 0 -10px 12px -10px;
          line-height: 1.35;
        }}

        /* Forzamos SIEMPRE fila horizontal (Streamlit apila columnas en mobile) */
        .st-key-am_topbar_v2 [data-testid="stHorizontalBlock"],
        .st-key-am_topbar_v2 [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {{
          display: flex !important;
          flex-direction: row !important;
          flex-wrap: wrap !important;
          gap: 8px !important;
          align-items: center !important;
          row-gap: 12px !important;
        }}
        .st-key-am_topbar_v2 [data-testid="stColumn"] {{
          min-width: 0 !important;
          display: flex !important;
          justify-content: center !important;
          align-items: center !important;
          flex-direction: row !important;
        }}
        /* Fila 1: Menu | Logo (centro) | Cuenta | Carrito - todos en la MISMA fila */
        .st-key-am_topbar_v2 [data-testid="stColumn"]:nth-child(1) {{ order: 1; flex: 0 0 46px !important; width: 46px !important; }}
        .st-key-am_topbar_v2 [data-testid="stColumn"]:nth-child(2) {{ order: 2; flex: 1 1 0 !important; width: auto !important; min-width: 0 !important; }}
        .st-key-am_topbar_v2 [data-testid="stColumn"]:nth-child(5) {{ order: 3; flex: 0 0 46px !important; width: 46px !important; }}
        .st-key-am_topbar_v2 [data-testid="stColumn"]:nth-child(7) {{ order: 4; flex: 0 0 46px !important; width: 46px !important; }}
        /* Fila 2: input + lupa (100% de ancho) */
        .st-key-am_topbar_v2 [data-testid="stColumn"]:nth-child(3) {{ order: 5; flex: 1 1 calc(100% - 60px) !important; width: auto !important; margin-top: 6px !important; }}
        .st-key-am_topbar_v2 [data-testid="stColumn"]:nth-child(4) {{ order: 6; flex: 0 0 52px !important; width: 52px !important; margin-top: 6px !important; }}
        /* Redes sociales ocultas en mobile */
        .st-key-am_topbar_v2 [data-testid="stColumn"]:nth-child(6) {{ display: none !important; }}

        /* Menu: solo icono */
        .st-key-btn_menu button {{
          width: 46px !important; min-width: 46px !important;
          height: 46px !important; min-height: 46px !important;
          padding: 0 !important; border-radius: 12px !important;
          font-size: 0 !important; line-height: 0 !important;
          color: transparent !important;
          position: relative; overflow: hidden;
        }}
        .st-key-btn_menu button > * {{ font-size: 0 !important; color: transparent !important; }}
        .st-key-btn_menu button::before {{
          content: "\\2630"; color: #fff; font-size: 24px; line-height: 1; font-weight: 900;
          position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        }}

        /* Logo mas grande y con aire arriba/abajo, separado del buscador */
        .am-brand {{
          justify-content: center; gap: 6px; text-align: center;
          width: 100%; padding: 8px 0 6px 0;
        }}
        .am-brand-name {{ font-size: 22px; }}
        .am-brand-market {{ font-size: 10px; letter-spacing: 2px; }}
        .am-brand-logo {{
          height: 72px !important;
          margin-left: 0 !important;
          margin-bottom: 4px !important;
          margin-top: 4px !important;
        }}

        /* Buscador */
        div[data-testid="stTextInput"] > div > div > input {{
          height: 44px !important;
          font-size: 16px !important;
          border-radius: 10px 0 0 10px !important;
          padding: 0 12px !important;
        }}
        .st-key-btn_search button {{
          width: 100% !important;
          height: 44px !important;
          min-height: 44px !important;
          border-radius: 0 10px 10px 0 !important;
          font-size: 20px !important;
          padding: 0 !important;
        }}

        /* Iconos de cuenta y carrito: silueta blanca via SVG, mismo tamano que menu */
        .am-tb-item {{
          width: 46px !important; height: 46px !important;
          display: flex !important; justify-content: center !important; align-items: center !important;
          padding: 0 !important; font-size: 0 !important; color: transparent !important;
          border-radius: 12px; position: relative; overflow: hidden;
        }}
        .am-tb-item * {{ font-size: 0 !important; color: transparent !important; display: none !important; }}
        .am-tb-item::before {{
          content: "";
          position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
          width: 26px; height: 26px;
          background-color: #fff;
          -webkit-mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M12 12a5 5 0 1 0-5-5 5 5 0 0 0 5 5zm0 2c-4 0-8 2-8 6v1h16v-1c0-4-4-6-8-6z'/></svg>") no-repeat center / contain;
                  mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M12 12a5 5 0 1 0-5-5 5 5 0 0 0 5 5zm0 2c-4 0-8 2-8 6v1h16v-1c0-4-4-6-8-6z'/></svg>") no-repeat center / contain;
        }}

        .am-cart-btn {{
          width: 46px !important; min-width: 46px !important;
          height: 46px !important; padding: 0 !important;
          border-radius: 12px !important;
          font-size: 0 !important; color: transparent !important;
          position: relative; overflow: visible;
          display: flex !important; align-items: center !important; justify-content: center !important;
        }}
        .am-cart-btn * {{ font-size: 0 !important; color: transparent !important; }}
        .am-cart-btn::before {{
          content: "";
          position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
          width: 26px; height: 26px;
          background-color: #fff;
          -webkit-mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M7 4h-2l-1 2v1h2l3 8-1 2a2 2 0 0 0 2 3h11v-2h-11l1-2h8l3-6h-14l-1-3zm2 15a2 2 0 1 0 2 2 2 2 0 0 0-2-2zm10 0a2 2 0 1 0 2 2 2 2 0 0 0-2-2z'/></svg>") no-repeat center / contain;
                  mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M7 4h-2l-1 2v1h2l3 8-1 2a2 2 0 0 0 2 3h11v-2h-11l1-2h8l3-6h-14l-1-3zm2 15a2 2 0 1 0 2 2 2 2 0 0 0-2-2zm10 0a2 2 0 1 0 2 2 2 2 0 0 0-2-2z'/></svg>") no-repeat center / contain;
        }}
        .am-cart-badge {{
          min-width: 16px; height: 16px; font-size: 10px;
          top: -4px !important; right: -4px !important;
        }}

        /* ================= HOME: PREVIEW DE APARTADOS ================= */
        /* Productos preview: 2 por fila, uno al lado del otro (como los circulos) */
        .am-section > [data-testid="stHorizontalBlock"],
        .am-section [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {{
          display: flex !important;
          flex-direction: row !important;
          flex-wrap: nowrap !important;
          overflow-x: auto !important;
          overflow-y: hidden !important;
          gap: 8px !important;
          scroll-snap-type: x mandatory !important;
          -webkit-overflow-scrolling: touch !important;
          padding-bottom: 4px !important;
        }}
        .am-section > [data-testid="stHorizontalBlock"]::-webkit-scrollbar {{ display: none; }}
        .am-section > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
        .am-section [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
          flex: 0 0 calc(25% - 6px) !important;
          min-width: calc(25% - 6px) !important;
          width: calc(25% - 6px) !important;
          scroll-snap-align: start !important;
        }}
        /* Excepcion: la cabecera (titulo + Ver mas) mantiene fila normal */
        .am-section > [data-testid="stHorizontalBlock"]:has(.am-section-title-h) {{
          flex-wrap: wrap !important;
          overflow: visible !important;
          flex-direction: row !important;
        }}
        .am-section > [data-testid="stHorizontalBlock"]:has(.am-section-title-h) > [data-testid="stColumn"] {{
          flex: 1 1 auto !important;
          min-width: 0 !important;
          width: auto !important;
        }}

        /* ================= CATEGORIAS (circulos) ================= */
        .am-cats-wrap {{ padding: 12px 0 14px 0; margin-bottom: 12px; }}
        .am-cats-scroll {{ gap: 10px; padding: 0 12px; }}
        .am-cat-circle {{ min-width: 68px; gap: 6px; }}
        .am-cat-circle .bubble {{ width: 64px; height: 64px; font-size: 28px; }}
        .am-cat-circle .label {{ font-size: 12px; max-width: 78px; font-weight: 700; }}

        /* ================= SECCIONES ================= */
        .am-wrap {{ padding: 0 12px; }}
        .am-section {{
          padding: 14px 12px 12px 12px;
          margin-bottom: 16px;
          border-radius: 14px;
        }}
        .am-section-head {{
          flex-direction: row; align-items: center;
          justify-content: space-between; gap: 8px; margin-bottom: 12px;
        }}
        .am-section-title-h {{ font-size: 17px; gap: 6px; }}

        /* Mini card en preview horizontal (4 por fila, estilo Madison) */
        .am-mini {{ padding: 5px 4px 7px 4px; }}
        .am-mini img {{ max-height: 74px; }}
        .am-mini .name {{ font-size: 10.5px; min-height: 26px; margin: 4px 1px 2px 1px; line-height: 1.15; }}
        .am-mini .price {{ font-size: 10.5px; padding: 2px 7px; }}

        /* ================= VISTA "VER MAS" (2 POR FILA, IGUAL QUE EL HOME) ================= */
        .am-plist [data-testid="stHorizontalBlock"] {{
          display: flex !important;
          flex-direction: row !important;
          flex-wrap: wrap !important;
          gap: 8px !important;
          row-gap: 10px !important;
        }}
        .am-plist [data-testid="stColumn"] {{
          flex: 0 0 calc(50% - 4px) !important;
          width: calc(50% - 4px) !important;
          min-width: 0 !important;
          display: block !important;
        }}
        /* Tarjeta vertical compacta */
        .am-plist .am-card {{
          display: block !important;
          text-align: center !important;
          padding: 8px 6px 10px 6px !important;
          margin-bottom: 4px !important;
        }}
        .am-plist .am-card img {{
          width: 100% !important;
          max-height: 100px !important;
          height: auto !important;
          margin: 0 auto 6px auto !important;
          object-fit: contain !important;
        }}
        .am-plist .am-card .am-name {{
          margin: 4px 2px 4px 2px !important;
          min-height: 32px !important;
          font-size: 12px !important;
          font-weight: 700 !important;
          line-height: 1.25 !important;
          text-align: center !important;
        }}
        .am-plist .am-card .am-price {{
          font-size: 12px !important;
          padding: 3px 8px !important;
          margin: 2px auto !important;
          display: inline-block !important;
        }}
        .am-plist .am-card-gap {{ display: none !important; }}
        .am-plist div[data-testid="stButton"] > button {{
          min-height: 36px !important;
          font-size: 12px !important;
          padding: 6px 8px !important;
          margin-top: 2px !important;
          margin-bottom: 8px !important;
        }}

        div[data-testid="stButton"] > button {{
          min-height: 42px !important;
          font-size: 13.5px !important;
        }}
      }}

      /* Telefonos angostos */
      @media (max-width: 420px) {{
        .am-wrap {{ padding: 0 10px; }}
        .am-brand-name {{ font-size: 20px; }}
        .am-brand-logo {{ height: 64px !important; }}
        .am-cat-circle .bubble {{ width: 58px; height: 58px; font-size: 26px; }}
        .am-cat-circle {{ min-width: 62px; }}
        .am-cat-circle .label {{ font-size: 11.5px; max-width: 72px; }}
        .am-section-title-h {{ font-size: 16px; }}
        .am-section > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
          flex: 0 0 calc(25% - 6px) !important; min-width: calc(25% - 6px) !important; width: calc(25% - 6px) !important;
        }}
        .am-mini img {{ max-height: 66px; }}
        .am-mini .name {{ font-size: 10px; min-height: 24px; }}
        .am-mini .price {{ font-size: 10px; padding: 2px 6px; }}
        .am-plist .am-card {{ grid-template-columns: 68px 1fr auto !important; }}
        .am-plist .am-card img {{ width: 68px !important; height: 68px !important; max-height: 68px !important; }}
      }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# ROUTER (?view=..., ?cat=..., ?q=...)
# ==========================================================
try:
    qp = st.query_params
    current_cat = qp.get("cat", None)
    view        = qp.get("view", None)
    url_q       = qp.get("q", None)
    if isinstance(current_cat, list): current_cat = current_cat[0] if current_cat else None
    if isinstance(view, list):        view        = view[0]        if view else None
    if isinstance(url_q, list):       url_q       = url_q[0]       if url_q else None
except Exception:
    qp = st.experimental_get_query_params()
    current_cat = (qp.get("cat",  [None]) or [None])[0]
    view        = (qp.get("view", [None]) or [None])[0]
    url_q       = (qp.get("q",    [None]) or [None])[0]


def _nav(view=None, cat=None, q=None):
    """Cambia la vista SIN recargar la pagina (conserva el carrito)."""
    try:
        st.query_params.clear()
        if view: st.query_params["view"] = view
        if cat:  st.query_params["cat"]  = cat
        if q:    st.query_params["q"]    = q
    except Exception:
        params = {}
        if view: params["view"] = view
        if cat:  params["cat"]  = cat
        if q:    params["q"]    = q
        st.experimental_set_query_params(**params)
    st.rerun()


products   = load_products()
categories = load_categories()
present = {p.get("categoria") for p in products if p.get("categoria")}
for c in present:
    if c and c not in categories:
        categories.append(c)


# ==========================================================
# BARRA SUPERIOR AZUL (Delivery + Topbar)
# ==========================================================
n_cart = cart_count()

# TODO EL HEADER va DENTRO de este contenedor -> queda dentro de la banda azul.
with st.container(key="am_topbar_v2"):
    # 1) Banner de delivery arriba de todo, dentro de la banda azul.
    st.markdown(
        f'<div class="am-delivery-banner">{_delivery_text}</div>',
        unsafe_allow_html=True,
    )

    # 2) Fila funcional: [Menu] [Logo/Brand] [Search input] [Search btn]
    #    [Mi cuenta] [Loyalty] [Carrito(icono)]
    c_menu, c_logo, c_search, c_btn, c_acc, c_social, c_cart = st.columns(
        [1.1, 2.3, 4.2, 0.9, 1.9, 1.7, 0.9], vertical_alignment="center"
    )

    with c_menu:
        if st.button("☰  Menú", key="btn_menu", use_container_width=True):
            st.session_state["menu_open"] = not st.session_state.get("menu_open", False)
            st.rerun()

    with c_logo:
        # Titulos configurables: si el usuario los definio, se usan; si no,
        # se cae en site_name/site_market como antes.
        if _hide_titles:
            blocks = []
        else:
            blocks = _titles if _titles else [
                {"text": _site_name,   "font": "Pacifico", "size": 30,
                 "color": "#FFFFFF",   "weight": "400"},
                {"text": _site_market, "font": "Poppins",  "size": 16,
                 "color": _settings.get("btn_search_bg", COLOR_ACCENT),
                 "weight": "900"},
            ]
        titles_html = "".join(
            f'<div style="font-family:\'{b["text"] and b["font"] or "Poppins"}\', sans-serif;'
            f'font-size:{b["size"]}px;color:{b["color"]};font-weight:{b["weight"]};'
            f'line-height:1.1;text-shadow:0 2px 6px rgba(0,0,0,.35);'
            f'letter-spacing:{"3px" if int(b["weight"] or 400) >= 800 and b["size"] < 22 else "0"};">{b["text"]}</div>'
            for b in blocks if b.get("text")
        )
        logo_html = ("" if _hide_logo else
            f'<img class="am-brand-logo" style="height:{_logo_size_px}px;margin-left:{_logo_offx_px}px;" src="data:image/png;base64,{topbar_logo_b64}" alt="logo"/>')
        st.markdown(
            f"""
            <a href="?" class="am-brand" style="text-decoration:none;">
              {logo_html}
              <div>{titles_html}</div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    with c_search:
        q_input = st.text_input(
            "Buscar",
            value=url_q or "",
            placeholder="¿Qué desearías buscar hoy?",
            label_visibility="collapsed",
            key="global_search",
        )

    with c_btn:
        if st.button("🔍", key="btn_search", use_container_width=True):
            if q_input and q_input.strip():
                _nav(view="search", q=q_input.strip())
            else:
                _nav()

    with c_acc:
        st.markdown(
            """
            <div class="am-tb-item" title="Cuenta">
              <span class="am-tb-icon">👤</span>
              <span>
                <span class="am-tb-sub">Iniciar sesión / Registrar</span>
                <span class="am-tb-strong">Mi cuenta</span>
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_social:
        # SVGs oficiales (Simple Icons, licencia CC0) para que se vean nítidos
        _svg_facebook = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            'width="22" height="22" fill="#ffffff" aria-hidden="true">'
            '<path d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 '
            '1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 '
            '1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0 '
            '-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622'
            'c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564'
            'h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12'
            '-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z"/></svg>'
        )
        _svg_instagram = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            'width="20" height="20" fill="#ffffff" aria-hidden="true">'
            '<path d="M12 2.163c3.204 0 3.584.012 4.849.07 1.366.062 2.633.336 '
            '3.608 1.311.975.975 1.249 2.242 1.311 3.608.058 1.265.069 1.645.069 '
            '4.849 0 3.205-.012 3.584-.069 4.849-.062 1.366-.336 2.633-1.311 '
            '3.608-.975.975-2.242 1.249-3.608 1.311-1.265.058-1.645.07-4.849.07'
            '-3.205 0-3.584-.012-4.849-.07-1.366-.062-2.633-.336-3.608-1.311'
            '-.975-.975-1.249-2.242-1.311-3.608C2.175 15.647 2.163 15.268 '
            '2.163 12s.012-3.584.07-4.849c.062-1.366.336-2.633 1.311-3.608'
            '.975-.975 2.242-1.249 3.608-1.311C8.416 2.175 8.796 2.163 12 2.163'
            'zm0 1.802c-3.148 0-3.523.011-4.767.068-1.006.046-1.554.213-1.918.353'
            '-.482.187-.827.41-1.188.771-.361.361-.584.706-.771 1.188-.14.364'
            '-.307.912-.353 1.918C2.976 8.477 2.965 8.852 2.965 12s.011 3.523.068 '
            '4.767c.046 1.006.213 1.554.353 1.918.187.482.41.827.771 1.188.361.361 '
            '.706.584 1.188.771.364.14.912.307 1.918.353 1.244.057 1.619.068 '
            '4.767.068s3.523-.011 4.767-.068c1.006-.046 1.554-.213 1.918-.353'
            '.482-.187.827-.41 1.188-.771.361-.361.584-.706.771-1.188.14-.364'
            '.307-.912.353-1.918.057-1.244.068-1.619.068-4.767s-.011-3.523-.068'
            '-4.767c-.046-1.006-.213-1.554-.353-1.918-.187-.482-.41-.827-.771'
            '-1.188-.361-.361-.706-.584-1.188-.771-.364-.14-.912-.307-1.918-.353'
            'C15.523 3.976 15.148 3.965 12 3.965zm0 3.063A4.972 4.972 0 1 1 12 '
            '16.972 4.972 4.972 0 0 1 12 7.028zm0 8.203A3.231 3.231 0 1 0 12 '
            '8.769a3.231 3.231 0 0 0 0 6.462zm5.171-8.406a1.163 1.163 0 1 1-2.326 '
            '0 1.163 1.163 0 0 1 2.326 0z"/></svg>'
        )
        _svg_tiktok = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            'width="20" height="20" fill="#ffffff" aria-hidden="true">'
            '<path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 '
            '2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13'
            'V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5.8 20.1a6.34 6.34 0 0 0 '
            '10.86-4.43V8.66a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1.84 '
            '-.09z"/></svg>'
        )
        _social_items = []
        _btn_base = (
            "display:inline-flex;align-items:center;justify-content:center;"
            "width:38px;height:38px;margin:0 4px;text-decoration:none;"
            "box-shadow:0 2px 6px rgba(0,0,0,.25);"
        )
        if _facebook_url:
            _social_items.append(
                f'<a href="{_facebook_url}" target="_blank" rel="noopener" '
                f'title="Facebook" aria-label="Facebook" '
                f'style="{_btn_base}border-radius:50%;background:#1877F2;">'
                f'{_svg_facebook}</a>'
            )
        if _instagram_url:
            _social_items.append(
                f'<a href="{_instagram_url}" target="_blank" rel="noopener" '
                f'title="Instagram" aria-label="Instagram" '
                f'style="{_btn_base}border-radius:10px;'
                f'background:radial-gradient(circle at 30% 110%,#FEDA75 0%,'
                f'#FA7E1E 25%,#D62976 50%,#962FBF 75%,#4F5BD5 100%);">'
                f'{_svg_instagram}</a>'
            )
        if _tiktok_url:
            _social_items.append(
                f'<a href="{_tiktok_url}" target="_blank" rel="noopener" '
                f'title="TikTok" aria-label="TikTok" '
                f'style="{_btn_base}border-radius:50%;background:#000;">'
                f'{_svg_tiktok}</a>'
            )
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:center;gap:2px;">'
            + "".join(_social_items) +
            '</div>',
            unsafe_allow_html=True,
        )

    with c_cart:
        _badge = (f"<span class='am-cart-badge'>{n_cart}</span>" if n_cart else "")
        st.markdown(
            f"""
            <div style="display:flex; justify-content:center;">
              <a class="am-cart-btn" href="?view=cart" title="Ver carrito"
                 aria-label="Ver carrito" target="_self">
                🛒{_badge}
              </a>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------- Panel desplegable del menu (al lado izquierdo) ----------
if st.session_state.get("menu_open", False):
    _items_html = "".join(
        f'<a href="?cat={c}" target="_self" '
        f'style="display:block;padding:12px 18px;border-bottom:1px solid rgba(255,255,255,.15);'
        f'font-family:Poppins,sans-serif;font-weight:600;font-size:14px;">'
        f'{c.capitalize()}</a>'
        for c in categories
    ) or (
        '<div style="padding:14px 18px;opacity:.85;font-size:13px;">'
        'Aún no hay apartados.</div>'
    )
    st.markdown(
        f'''
        <div class="am-menu-panel" style="
            position:relative;max-width:280px;margin:8px 0 12px 12px;
            background:{_menu_panel_bg};color:{_menu_panel_fg};
            border-radius:14px;box-shadow:0 10px 24px rgba(0,0,0,.22);
            overflow:hidden;">
          <div style="padding:10px 18px;font-weight:800;font-size:13px;
                      letter-spacing:1px;text-transform:uppercase;opacity:.85;
                      border-bottom:1px solid rgba(255,255,255,.2);">
            Apartados
          </div>
          {_items_html}
        </div>
        ''',
        unsafe_allow_html=True,
    )





# ==========================================================
# FILA DE CATEGORIAS (CIRCULOS) - navegacion rapida a apartados
# ==========================================================
if categories:
    circles_html = ['<div class="am-cats-wrap"><div class="am-cats-scroll">']
    for cat in categories:
        stl = get_cat_style(cat, _cat_styles)
        icon = stl["icon"] or icon_for_category(cat, category_icons)
        sz   = stl["circle_size"]
        cc   = stl["circle_color"]
        lc   = stl["label_color"]
        ls   = stl["label_size"]
        circles_html.append(
            f'<a class="am-cat-circle" href="?cat={cat}" style="min-width:{max(sz+20,80)}px;">'
            f'  <div class="bubble" style="width:{sz}px;height:{sz}px;'
            f'background: radial-gradient(circle at 30% 30%, color-mix(in srgb, {cc} 78%, white) 0%, {cc} 78%);'
            f'font-size:{int(sz*0.46)}px;">{icon}</div>'
            f'  <div class="label" style="color:{lc};font-size:{ls}px;">{cat}</div>'
            f'</a>'
        )
    circles_html.append("</div></div>")
    st.markdown("".join(circles_html), unsafe_allow_html=True)


# ==========================================================
# Dialogo (modal) para elegir cantidad
# ==========================================================
def _open_add_dialog(prod):
    st.session_state["_add_dialog_prod"] = prod
    st.session_state["_add_dialog_qty"]  = 1


def _render_add_dialog():
    prod = st.session_state.get("_add_dialog_prod")
    if not prod:
        return
    dialog_dec = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

    def _body():
        img_src = img_to_data_uri(prod.get("imagen", ""))
        name = prod.get("nombre", "")
        st.markdown(f'<img class="am-modal-img" src="{img_src}" alt="{name}"/>', unsafe_allow_html=True)
        st.markdown(f'<div class="am-modal-name">{name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="am-modal-price">{format_price(prod.get("precio",0))}</div>',
                    unsafe_allow_html=True)
        st.markdown("**Cantidad**")
        qty = st.number_input(
            "Cantidad", min_value=1, max_value=999, step=1,
            value=int(st.session_state.get("_add_dialog_qty", 1)),
            key="_add_dialog_qty_input", label_visibility="collapsed",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Cancelar", use_container_width=True, key="_add_dialog_cancel"):
                st.session_state.pop("_add_dialog_prod", None)
                st.rerun()
        with c2:
            if st.button("Agregar al carrito", type="primary",
                         use_container_width=True, key="_add_dialog_ok"):
                cart_add(prod, int(qty))
                st.session_state.pop("_add_dialog_prod", None)
                st.rerun()

    if dialog_dec:
        @dialog_dec(f"Agregar «{prod.get('nombre','')}»")
        def _dlg():
            _body()
        _dlg()
    else:
        with st.container(border=True):
            st.subheader(f"Agregar «{prod.get('nombre','')}»")
            _body()


# ==========================================================
# CONTENIDO PRINCIPAL
# ==========================================================
st.markdown('<div class="am-wrap">', unsafe_allow_html=True)


def render_product_grid(prods, key_prefix, cols_per_row=4):
    """Grid de productos completos (tarjeta grande + boton agregar)."""
    st.markdown('<div class="am-plist">', unsafe_allow_html=True)
    for i in range(0, len(prods), cols_per_row):
        row = st.columns(cols_per_row)
        for j, (col, prod) in enumerate(zip(row, prods[i:i + cols_per_row])):
            name = prod.get("nombre", "")
            key_id = f"{key_prefix}_{i}_{j}_{name}"
            in_cart = _cart().get(name, {}).get("qty", 0)
            img_src = img_to_data_uri(prod.get("imagen", ""))
            with col:
                badge = (f'<span class="am-qty-badge">En carrito: {in_cart}</span>'
                         if in_cart else "")
                st.markdown(
                    f"""
                    <div class="am-card">
                        <img src="{img_src}" alt="{name}"/>
                        <div class="am-name">{name}{badge}</div>
                        <div class="am-price">{format_price(prod.get('precio',0))}</div>
                    </div>
                    <div class="am-card-gap"></div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("🛒  Agregar al carrito", key=f"add_{key_id}",
                             use_container_width=True, type="primary"):
                    _open_add_dialog(prod)
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ================== VISTA: CARRITO ==================
if view == "cart":
    # Fondo personalizable de la pagina del carrito
    st.markdown(
        f"<style>.stApp {{ background: {_ct_pagebg} !important; }}</style>",
        unsafe_allow_html=True,
    )
    if st.button("← Seguir comprando", key="btn_back_shop"):
        _nav(cat=current_cat)
    st.markdown(
        f'<h2 style="color:{_sec_title_color};font-family:Poppins;">🛒 Tu carrito</h2>',
        unsafe_allow_html=True,
    )

    cart = _cart()
    if not cart:
        st.markdown(
            '<div class="am-empty">Tu carrito está vacío.<br>'
            'Agrega productos desde los apartados.</div>',
            unsafe_allow_html=True,
        )
    else:
        for name, it in list(cart.items()):
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([0.7, 3, 2.2, 2, 0.6])
                with c1:
                    st.markdown(
                        f'<img src="{img_to_data_uri(it["imagen"])}" '
                        f'style="width:56px;height:56px;object-fit:contain;'
                        f'border-radius:10px;background:#fff;border:1px solid #E2E8F0;padding:3px;"/>',
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f'<div style="font-weight:700;color:{_ct_name};font-size:13px;line-height:1.2;">{name}</div>'
                        f'<div style="color:{_ct_price};font-size:11px;margin-top:2px;">'
                        f'{format_price(it["precio"])} c/u</div>',
                        unsafe_allow_html=True,
                    )
                with c3:
                    b1, bq, b2 = st.columns([1, 1, 1])
                    with b1:
                        if st.button("−", key=f"cart_minus_{name}"):
                            cart_set(name, it["qty"] - 1); st.rerun()
                    with bq:
                        st.markdown(
                            f'<div style="text-align:center;font-weight:900;'
                            f'padding-top:6px;color:{_ct_qty};font-size:16px;">'
                            f'{it["qty"]}</div>',
                            unsafe_allow_html=True,
                        )
                    with b2:
                        if st.button("+", key=f"cart_plus_{name}"):
                            cart_set(name, it["qty"] + 1); st.rerun()
                with c4:
                    st.markdown(
                        f'<div style="padding-top:4px;text-align:center;">'
                        f'<span style="display:inline-block;background:{_ct_lbg};'
                        f'color:{_ct_lfg};font-weight:700;font-size:13px;padding:4px 10px;'
                        f'border-radius:8px;">{format_price(it["precio"] * it["qty"])}</span></div>',
                        unsafe_allow_html=True,
                    )
                with c5:
                    st.markdown(
                        f"<style>.st-key-cart_del_{name.replace(' ','_')} button{{background:{_ct_delbg} !important;color:{_ct_delfg} !important;}}</style>",
                        unsafe_allow_html=True,
                    )
                    if st.button("🗑️", key=f"cart_del_{name}"):
                        cart_set(name, 0); st.rerun()

        st.markdown("---")

        # Botones: "Anadir mas productos" + "Vaciar carrito"
        st.markdown(
            f"<style>"
            f".st-key-cart_add_more button{{background:{_ct_addbg} !important;color:{_ct_addfg} !important;}}"
            f".st-key-cart_pay_now button{{background:{_ct_paybg} !important;color:{_ct_payfg} !important;font-size:14px !important;min-height:42px !important;padding:6px 14px !important;font-weight:800 !important;}}"
            f"</style>",
            unsafe_allow_html=True,
        )
        addc1, addc2 = st.columns([1, 1])
        with addc1:
            if st.button("＋  Añadir más productos", key="cart_add_more", use_container_width=True):
                _nav()
        with addc2:
            if st.button("🗑  Vaciar carrito", key="cart_clear", use_container_width=True):
                st.session_state.cart = {}
                _persist()
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Total grande + boton Pagar ahora
        tt1, tt2 = st.columns([2, 1])
        with tt1:
            st.markdown(
                f'<div style="font-size:20px;font-weight:700;color:{_ct_name};margin-top:8px;">Total a pagar:</div>'
                f'<div style="font-size:42px;font-weight:900;color:{_ct_tot};'
                f'text-shadow:0 2px 6px rgba(22,163,74,.25);line-height:1.1;">'
                f'{format_price(cart_total())}</div>',
                unsafe_allow_html=True,
            )
        with tt2:
            st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
            if st.button("💳  Pagar ahora", key="cart_pay_now", use_container_width=True):
                st.success("¡Gracias por tu compra! (Aquí conectas tu pasarela de pago).")


# ================== VISTA: RESULTADOS DE BUSQUEDA GLOBAL ==================
elif view == "search":
    q = (url_q or "").strip()
    st.markdown(
        f'<h2 style="color:{COLOR_PRIMARY};font-family:Poppins;">'
        f'🔍 Resultados para: <span style="color:{COLOR_TEXT};">"{q}"</span></h2>',
        unsafe_allow_html=True,
    )
    if st.button("← Volver al inicio", key="btn_back_home_from_search"):
        _nav()
    if not q:
        st.info("Escribe algo en la barra de búsqueda.")
    else:
        ql = q.lower()
        results = [p for p in products
                   if ql in str(p.get("nombre", "")).lower()
                   or ql in str(p.get("categoria", "")).lower()]
        if not results:
            st.markdown(
                '<div class="am-empty">No se encontraron productos que coincidan.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption(f"{len(results)} resultado(s) en toda la tienda.")
            render_product_grid(results, key_prefix="search")


# ================== VISTA: HOME (LISTA DE APARTADOS con preview) ==================
elif not current_cat:
    if not categories:
        st.markdown(
            '<div class="am-empty">Aún no hay apartados.<br>'
            'Crea apartados desde la app de escritorio '
            '(botón «Agregar nuevo apartado»).</div>',
            unsafe_allow_html=True,
        )
    else:
        for idx, cat in enumerate(categories):
            cat_prods = [p for p in products if p.get("categoria") == cat]
            emoji = icon_for_category(cat, category_icons)
            total_cat = len(cat_prods)

            # Cabecera de la seccion (titulo + boton ver mas) - estilo por apartado
            stl = get_cat_style(cat, _cat_styles)
            tcolor = stl["title_color"] or _sec_title_color
            tsize  = stl["title_size"]  or _sec_title_size
            mbg    = stl["more_bg"]     or _sec_more_bg
            mfg    = stl["more_fg"]     or _sec_more_fg
            micon  = stl["icon"] or emoji
            st.markdown('<div class="am-section">', unsafe_allow_html=True)
            head_l, head_r = st.columns([6, 1.4], vertical_alignment="center")
            with head_l:
                st.markdown(
                    f'<div class="am-section-title-h" style="color:{tcolor};font-size:{tsize}px;">'
                    f'<span class="dot"></span> {micon} {cat.capitalize()}'
                    f' <span style="color:{COLOR_MUTED};font-size:13px;font-weight:600;'
                    f'margin-left:8px;">· {total_cat} producto(s)</span></div>',
                    unsafe_allow_html=True,
                )
            with head_r:
                st.markdown(
                    f'<a href="?cat={cat}" target="_self" '
                    f'style="display:block;text-align:center;text-decoration:none !important;'
                    f'background:{mbg} !important;color:{mfg} !important;font-weight:700;'
                    f'padding:10px 16px;border-radius:12px;font-family:Poppins,sans-serif;'
                    f'box-shadow:0 4px 12px rgba(0,0,0,.15);">'
                    f'<span style="color:{mfg} !important;">Ver más →</span></a>',
                    unsafe_allow_html=True,
                )

            if not cat_prods:
                st.markdown(
                    '<div class="am-section-empty">Aún no hay productos en este apartado.</div>',
                    unsafe_allow_html=True,
                )
            else:
                preview = cat_prods[:PREVIEW_PER_CAT]
                cols = st.columns(PREVIEW_PER_CAT)
                for k, prod in enumerate(preview):
                    with cols[k]:
                        img_src = img_to_data_uri(prod.get("imagen", ""))
                        name = prod.get("nombre", "")
                        # Todo el mini-card es un enlace al apartado
                        st.markdown(
                            f"""
                            <a href="?cat={cat}" style="text-decoration:none;">
                              <div class="am-mini">
                                <img src="{img_src}" alt="{name}"/>
                                <div class="name">{name}</div>
                                <div class="price">{format_price(prod.get('precio',0))}</div>
                              </div>
                            </a>
                            """,
                            unsafe_allow_html=True,
                        )
            st.markdown('</div>', unsafe_allow_html=True)


# ================== VISTA: PRODUCTOS DE UN APARTADO ==================
else:
    top1, top2 = st.columns([1, 5])
    with top1:
        if st.button("← Apartados", key="btn_back_cats"):
            _nav()
    emoji = icon_for_category(current_cat, category_icons)
    st.markdown(
        f'<h2 style="color:{COLOR_PRIMARY};font-family:Poppins;">'
        f'{emoji} {current_cat.capitalize()}</h2>',
        unsafe_allow_html=True,
    )

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        query = st.text_input(
            "Buscar producto",
            placeholder=f"Buscar en {current_cat}…",
            label_visibility="collapsed",
            key="cat_search",
        )
    with col_s2:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()

    cat_prods = [p for p in products if p.get("categoria") == current_cat]
    if query:
        q = query.lower().strip()
        cat_prods = [p for p in cat_prods if q in str(p.get("nombre", "")).lower()]

    if not cat_prods:
        st.markdown(
            '<div class="am-empty">No hay productos en este apartado todavía.<br>'
            'Agrégalos desde la app de escritorio.</div>',
            unsafe_allow_html=True,
        )
    else:
        total = len(cat_prods)
        pages = max(1, (total + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE)
        page = st.number_input("Página", min_value=1, max_value=pages,
                               value=1, step=1) if pages > 1 else 1
        start = (page - 1) * PRODUCTS_PER_PAGE
        chunk = cat_prods[start:start + PRODUCTS_PER_PAGE]

        render_product_grid(chunk, key_prefix=f"cat_{current_cat}", cols_per_row=4)
        st.caption(f"Mostrando {len(chunk)} de {total} productos.")


st.markdown("</div>", unsafe_allow_html=True)  # cierra am-wrap


# Render del dialogo si esta activo
if st.session_state.get("_add_dialog_prod"):
    _render_add_dialog()
