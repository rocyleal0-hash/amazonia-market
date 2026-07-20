# ==========================================================
# AMAZONIA MARKET - Tienda Virtual (Streamlit)
# ==========================================================
#     streamlit run tienda.py
# Requisitos:  pip install streamlit pillow
# ==========================================================

import base64
import io
import json
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

# --- Personalización de la página (editable desde la app de escritorio) ---
SETTINGS_FILE    = BASE_DIR / "site_settings.json"
CUSTOM_LOGO_FILE = BASE_DIR / "site_logo.png"

def load_site_settings() -> dict:
    """Lee el nombre y el logo personalizados. Si no existen, usa los valores por defecto."""
    defaults = {"site_name": "Amazonia", "site_market": "MARKET"}
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                defaults.update({k: v for k, v in data.items() if isinstance(v, str) and v.strip()})
        except Exception:
            pass
    return defaults

def get_banner_data_uri() -> str:
    # 1) banner.png / banner.jpg junto al script (si el usuario quiere reemplazarlo)
    for ext, mime in (("png", "image/png"), ("jpg", "image/jpeg"), ("jpeg", "image/jpeg")):
        f = BASE_DIR / f"banner.{ext}"
        if f.exists():
            try:
                return f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()
            except Exception:
                pass
    # 2) Fallback: banner incrustado en el propio código (no requiere archivo externo)
    try:
        from banner_embed import EMBEDDED_BANNER_B64
        return "data:image/jpeg;base64," + EMBEDDED_BANNER_B64
    except Exception:
        return ""

PRODUCTS_PER_PAGE = 12

# --- Paleta (azul brillante + gris claro) ---
COLOR_PRIMARY   = "#1D4ED8"   # azul del logo (carrito)
COLOR_PRIMARY_2 = "#2563EB"   # azul brillante
COLOR_PRIMARY_3 = "#3B82F6"   # azul claro brillante
COLOR_ACCENT    = "#F59E0B"
COLOR_BG_GRAY   = "#E5E7EB"   # gris claro brillante de fondo
COLOR_CARD      = "#FFFFFF"
COLOR_TEXT      = "#0F172A"
COLOR_MUTED     = "#64748B"

# Patrón de carritos de compras para el fondo.
# Si existe "carts_pattern.jpg" (o .png) junto al script, se usa esa imagen
# (carritos grises realistas, mismo estilo que la portada). Si no, se usa
# un fallback SVG sencillo para que la app no se rompa.
def get_carts_pattern_data_uri() -> str:
    for ext, mime in (("jpg", "image/jpeg"), ("jpeg", "image/jpeg"), ("png", "image/png")):
        f = BASE_DIR / f"carts_pattern.{ext}"
        if f.exists():
            try:
                return f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()
            except Exception:
                pass
    # Fallback: patrón SVG con carritos de compras realistas de tamaños
    # variados repartidos por todo el mosaico. Este patrón se usa como
    # textura de fondo (repeat) en la portada.
    cart = (
        '<g fill="none" stroke="#475569" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M4 8 h12 l4 6 h60 l-8 30 h-46 z"/>'
        '<path d="M22 20 h50" opacity="0.55"/>'
        '<path d="M26 30 h44" opacity="0.55"/>'
        '<path d="M32 14 v30" opacity="0.55"/>'
        '<path d="M46 14 v30" opacity="0.55"/>'
        '<path d="M60 14 v30" opacity="0.55"/>'
        '<path d="M24 44 l-4 8"/>'
        '<path d="M70 44 l4 8"/>'
        '<circle cx="30" cy="56" r="5" fill="#475569"/>'
        '<circle cx="66" cy="56" r="5" fill="#475569"/>'
        '<path d="M16 14 l-6 -6 h-6"/>'
        "</g>"
    )
    def place(x, y, s, op=0.55, rot=0):
        return (
            f'<g transform="translate({x},{y}) rotate({rot}) scale({s})" '
            f'opacity="{op}">{cart}</g>'
        )
    carts_svg = "".join([
        place(30,  50, 1.10, 0.55),
        place(230, 30, 0.75, 0.45, -6),
        place(380, 90, 1.35, 0.60),
        place(90,  230, 0.85, 0.45, 4),
        place(260, 210, 1.15, 0.55),
        place(430, 260, 0.70, 0.40, -8),
        place(40,  380, 0.95, 0.50, 6),
        place(210, 400, 1.25, 0.55),
        place(400, 420, 0.80, 0.45),
        place(150, 130, 0.60, 0.35, 10),
        place(350, 360, 0.55, 0.35, -4),
    ])
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="560" height="560" '
        'viewBox="0 0 560 560">'
        '<rect width="560" height="560" fill="#B7BDC6"/>'
        f"{carts_svg}"
        "</svg>"
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()

# ----------------------------------------------------------
# Logo
# ----------------------------------------------------------
def _load_logo() -> Image.Image:
    if LOGO_FILE.exists():
        raw = base64.b64decode(LOGO_FILE.read_text().strip())
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    img = Image.new("RGBA", (400, 120), (11, 42, 107, 255))
    return img

@st.cache_data(show_spinner=False)
def get_logo_b64() -> str:
    img = _load_logo()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

@st.cache_data(show_spinner=False)
def get_logo_watermark_b64(opacity: float = 0.10, radius: int = 3) -> str:
    """Logo blanco difuminado para patrón de fondo sobre azul."""
    img = _load_logo()
    # Convertimos el logo a blanco puro conservando alpha
    r, g, b, a = img.split()
    white = Image.new("RGBA", img.size, (255, 255, 255, 0))
    white.putalpha(a.point(lambda v: int(v * opacity)))
    white = white.filter(ImageFilter.GaussianBlur(radius=radius))
    buf = io.BytesIO()
    white.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

@st.cache_data(show_spinner=False)
def get_logo_badge_b64(size: int = 160, bg=(55, 65, 81), radius: int = 32) -> str:
    """
    Badge cuadrado con esquinas redondeadas que contiene el LOGO REAL
    de Amazonia Market (carrito azul + 'Amazonia' cursiva blanca + 'MARKET'
    azul), tal cual sale en la imagen del logo, pero pequeñito. Se le añade
    un contorno negro alrededor de todo lo visible para que las letras y el
    carrito destaquen sobre el fondo gris del badge.
    """
    from PIL import ImageDraw
    logo = _load_logo().copy()

    # 1) Quitar fondo claro (gris/blanco) del logo original -> transparente,
    #    conservando el resto de colores del logo (azul, blanco de la cursiva).
    px = logo.load()
    w, h = logo.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            # gris muy claro / casi blanco = fondo
            if r > 225 and g > 225 and b > 225:
                px[x, y] = (0, 0, 0, 0)

    # 2) Recortar al bounding box de los pixeles visibles para que el logo
    #    llene el badge (nada de márgenes vacíos).
    bbox = logo.split()[-1].getbbox()
    if bbox:
        logo = logo.crop(bbox)

    # 3) Contorno negro grueso alrededor de las letras/carrito.
    alpha = logo.split()[-1]
    outline = Image.new("RGBA", logo.size, (0, 0, 0, 0))
    for dx in (-3, -2, -1, 0, 1, 2, 3):
        for dy in (-3, -2, -1, 0, 1, 2, 3):
            if dx == 0 and dy == 0:
                continue
            shifted = Image.new("L", logo.size, 0)
            shifted.paste(alpha, (dx, dy))
            black = Image.new("RGBA", logo.size, (0, 0, 0, 255))
            black.putalpha(shifted)
            outline = Image.alpha_composite(outline, black)
    logo_outlined = Image.alpha_composite(outline, logo)

    # 4) Badge cuadrado con fondo gris fuerte y esquinas redondeadas.
    badge = Image.new("RGBA", (size, size), (*bg, 255))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=radius, fill=255)

    padding = int(size * 0.10)
    max_w = size - 2 * padding
    lw, lh = logo_outlined.size
    scale = min(max_w / lw, max_w / lh) if lw and lh else 1
    new_w, new_h = max(1, int(lw * scale)), max(1, int(lh * scale))
    logo_resized = logo_outlined.resize((new_w, new_h), Image.LANCZOS)

    x = (size - new_w) // 2
    y = (size - new_h) // 2
    badge.paste(logo_resized, (x, y), logo_resized)
    badge.putalpha(mask)

    buf = io.BytesIO()
    badge.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def get_custom_badge_b64(size: int = 160, radius: int = 32,
                         bg=(55, 65, 81), shadow_pad: int = 12,
                          logo_fingerprint: str = "") -> str:
    """
    Si existe un logo personalizado (site_logo.png) lo renderiza dentro de un
    badge cuadrado con esquinas redondeadas, fondo oscuro y sombra alrededor.
    Devuelve la imagen final en base64. Si no hay logo personalizado, cae al
    badge por defecto con el logo original de Amazonia Market.

    `logo_fingerprint` identifica el archivo actual. Esta función NO se cachea
    porque el logo lo cambia otra app (Tkinter) mientras Streamlit sigue abierto.
    """
    from PIL import ImageDraw
    if not CUSTOM_LOGO_FILE.exists():
        return get_logo_badge_b64(size=size, bg=bg, radius=radius)

    try:
        logo = Image.open(CUSTOM_LOGO_FILE).convert("RGBA")
    except Exception:
        return get_logo_badge_b64(size=size, bg=bg, radius=radius)

    # Lienzo total incluye espacio para la sombra
    total = size + shadow_pad * 2
    canvas = Image.new("RGBA", (total, total), (0, 0, 0, 0))

    # 1) Sombra: rectángulo redondeado negro difuminado
    shadow = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (shadow_pad, shadow_pad, shadow_pad + size, shadow_pad + size),
        radius=radius, fill=(0, 0, 0, 170)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_pad // 2 + 3))
    canvas = Image.alpha_composite(canvas, shadow)

    # 2) Badge con fondo oscuro
    badge = Image.new("RGBA", (size, size), (*bg, 255))

    # 3) Ajustar la imagen del usuario dentro del badge (contain, con padding)
    padding = int(size * 0.08)
    inner = size - 2 * padding
    lw, lh = logo.size
    scale = min(inner / lw, inner / lh) if lw and lh else 1
    new_w, new_h = max(1, int(lw * scale)), max(1, int(lh * scale))
    logo_resized = logo.resize((new_w, new_h), Image.LANCZOS)
    x = (size - new_w) // 2
    y = (size - new_h) // 2
    badge.paste(logo_resized, (x, y), logo_resized)

    # 4) Máscara de esquinas redondeadas
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    badge.putalpha(mask)

    # 5) Pegar el badge sobre el canvas (encima de la sombra)
    canvas.paste(badge, (shadow_pad, shadow_pad), badge)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
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
# Carrito (session_state)
# ----------------------------------------------------------
def _cart():
    if "cart" not in st.session_state:
        st.session_state.cart = {}
    return st.session_state.cart

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

def cart_set(name, qty):
    c = _cart()
    if name in c:
        if qty <= 0:
            c.pop(name, None)
        else:
            c[name]["qty"] = qty

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
st.set_page_config(page_title=f"{_site_name} {_site_market}", page_icon="🛒", layout="wide")

logo_b64      = get_logo_b64()
logo_wm_b64   = get_logo_watermark_b64()
carts_bg_uri  = get_carts_pattern_data_uri()

# ---- CSS global ----
st.markdown(
    f"""
    <style>
      /* Fondo gris claro con patrón de carritos de compras REALES */
      .stApp {{
        background-color: {COLOR_BG_GRAY};
        background-image: url("{carts_bg_uri}");
        background-repeat: repeat;
        background-size: 520px 520px;
      }}
      .main .block-container {{
        position: relative; z-index: 1;
        padding-top: 1rem; max-width: 1200px;
      }}

      /* Ocultar la barra blanca superior de Streamlit para que la portada
         llegue hasta arriba, sin franja blanca. */
      header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 0 !important;
      }}
      #MainMenu, footer {{ visibility: hidden; }}
      .main .block-container {{ padding-top: 0 !important; }}

      /* ---------- HERO estilo Gerald's ---------- */
      .am-hero {{
        position: relative;
        width: 100vw;
        margin-left: calc(50% - 50vw);
        margin-right: calc(50% - 50vw);
        margin-top: 0;
        margin-bottom: 20px;
        min-height: 210px;
        overflow: hidden;
        /* Gris más oscuro que el resto de la app para que sobresalga */
        background-color: #7F8794;
        background-image: url("{carts_bg_uri}");
        background-repeat: repeat;
        background-size: 320px 320px;
        background-blend-mode: multiply;
        display: flex;
        align-items: center;
        padding: 30px 48px;
      }}
      .am-hero-inner {{
        position: relative; z-index: 1;
        display: flex; align-items: center; gap: 22px;
      }}
      .am-hero-badge {{
        width: 104px; height: 104px; border-radius: 24px;
        box-shadow: 0 12px 28px rgba(0,0,0,.35);
        display: block;
      }}
      .am-hero-info {{ display: flex; flex-direction: column; gap: 10px; }}
      .am-hero-title {{
        margin: 0;
        font-family: "Brush Script MT", "Lucida Handwriting", cursive;
        color: #fff;
        font-weight: 700;
        font-size: 34px;
        line-height: 1;
        -webkit-text-stroke: 1.5px #000;
        text-shadow: 0 2px 6px rgba(0,0,0,.5);
      }}
      .am-hero-title .market {{
        font-family: "Arial Black", "Helvetica", sans-serif;
        color: {COLOR_PRIMARY};
        font-size: 22px;
        letter-spacing: 2px;
        margin-left: 8px;
        -webkit-text-stroke: 1.2px #000;
      }}
      .am-hero-status {{
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(0,0,0,.45);
        color: #fff; font-weight: 600; font-size: 14px;
        padding: 6px 14px; border-radius: 999px;
        width: fit-content;
        backdrop-filter: blur(4px);
      }}
      .am-hero-dot {{
        width: 10px; height: 10px; border-radius: 50%;
        background: #22C55E; box-shadow: 0 0 8px #22C55E;
      }}


      /* Barra superior del carrito */
      .am-topbar {{
        display:flex; align-items:center; justify-content:flex-end;
        gap:10px; margin: 0 0 8px 0;
      }}

      /* Apartados */
      .am-cat {{
        display:flex; align-items:center; justify-content:space-between;
        background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_PRIMARY_3} 100%);
        color: #fff !important; text-decoration: none !important;
        padding: 28px 28px; border-radius: 18px;
        margin-bottom: 16px; font-size: 22px; font-weight: 800;
        box-shadow: 0 10px 24px rgba(29,78,216,.35);
        transition: transform .15s ease, box-shadow .15s ease;
      }}
      .am-cat:hover {{ transform: translateY(-2px);
        box-shadow: 0 14px 30px rgba(29,78,216,.45); }}
      .am-cat .count {{
        background: rgba(255,255,255,.22); padding: 4px 12px;
        border-radius: 999px; font-size: 13px; font-weight: 600;
      }}
      .am-section-title {{
        color: {COLOR_PRIMARY}; font-weight: 900; font-size: 24px;
        margin: 6px 0 14px 0;
        text-shadow: 0 1px 2px rgba(255,255,255,.6);
      }}

      /* --------- Botones de Streamlit en AZUL BRILLANTE y anchos --------- */
      /* Botones normales (apartados, carrito, etc.) */
      div[data-testid="stButton"] > button {{
        background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_PRIMARY_3} 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 22px 26px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        min-height: 68px !important;
        box-shadow: 0 8px 20px rgba(29,78,216,.35) !important;
        transition: transform .15s ease, box-shadow .15s ease !important;
      }}
      div[data-testid="stButton"] > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 26px rgba(29,78,216,.45) !important;
        filter: brightness(1.05);
      }}


      /* Tarjetas de producto (compactas y redonditas) */
      .am-card {{
        background: {COLOR_CARD};
        border-radius: 18px; padding: 14px 12px 12px 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 10px 22px rgba(0,0,0,.18);
        text-align: center;
        margin-bottom: 6px;
      }}
      .am-card img {{
        width: 100%; aspect-ratio: 1/1; object-fit: contain;
        border-radius: 12px; background: #f8fafc;
        max-height: 170px;
      }}
      .am-name {{
        font-weight: 600; color: {COLOR_TEXT};
        margin: 10px 4px 6px 4px; font-size: 14px;
        line-height: 1.25; min-height: 36px;
      }}
      .am-price {{
        display:inline-block; background:#16A34A; color:#fff !important;
        font-weight:800; font-size:16px; padding:5px 14px;
        border-radius:10px; margin: 2px 0 6px 0;
        box-shadow:0 2px 6px rgba(22,163,74,.25);
      }}
      .am-qty-badge {{
        display:inline-block; background:{COLOR_PRIMARY}; color:#fff;
        padding:2px 8px; border-radius:999px; font-size:11px;
        font-weight:700; margin-left:6px;
      }}
      /* Espaciador entre la tarjeta y el botón "Agregar al carrito" */
      .am-card-gap {{ height: 10px; }}
      .am-empty {{
        text-align:center; padding: 50px 20px; color:{COLOR_MUTED};
        background:#fff; border-radius:16px; border:1px dashed #e5e7eb;
      }}
      .stButton>button {{
        border-radius: 12px; font-weight: 600;
      }}
      /* Botón "Agregar al carrito" — rojo/coral, con aire */
      div[data-testid="stButton"] > button[kind="primary"] {{
        background: #EF4444; border-color: #EF4444; color:#fff;
        padding: 10px 14px;
        box-shadow: 0 6px 14px rgba(239,68,68,.35);
      }}
      div[data-testid="stButton"] > button[kind="primary"]:hover {{
        background: #DC2626; border-color: #DC2626;
        transform: translateY(-1px);
        box-shadow: 0 8px 18px rgba(220,38,38,.4);
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
        text-align:center; color:#16A34A; font-weight:800;
        font-size:20px; margin-bottom: 14px;
      }}
      footer {{ visibility:hidden; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- HERO ----
if CUSTOM_LOGO_FILE.exists():
    _logo_stat = CUSTOM_LOGO_FILE.stat()
    _logo_fingerprint = f"{_logo_stat.st_mtime_ns}-{_logo_stat.st_size}"
else:
    _logo_fingerprint = "sin-logo-personalizado"
logo_badge_b64 = get_custom_badge_b64(logo_fingerprint=_logo_fingerprint)
st.markdown(
    f"""
    <div class="am-hero">
      <div class="am-hero-inner">
        <img class="am-hero-badge"
             src="data:image/png;base64,{logo_badge_b64}"
             alt="Amazonia Market"/>
        <div class="am-hero-info">
          <div class="am-hero-title">{_site_name}<span class="market">{_site_market}</span></div>
          <div class="am-hero-status">
            <span class="am-hero-dot"></span> Activo hasta las 9 p.m
          </div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---- Router ----
try:
    qp = st.query_params
    current_cat = qp.get("cat", None)
    view = qp.get("view", None)
    if isinstance(current_cat, list):
        current_cat = current_cat[0] if current_cat else None
    if isinstance(view, list):
        view = view[0] if view else None
except Exception:
    qp = st.experimental_get_query_params()
    current_cat = (qp.get("cat", [None]) or [None])[0]
    view = (qp.get("view", [None]) or [None])[0]

products   = load_products()
categories = load_categories()
present = {p.get("categoria") for p in products if p.get("categoria")}
for c in present:
    if c not in categories:
        categories.append(c)

def _nav(view=None, cat=None):
    """Cambia la vista SIN recargar la página (conserva el carrito)."""
    try:
        st.query_params.clear()
        if view: st.query_params["view"] = view
        if cat:  st.query_params["cat"]  = cat
    except Exception:
        params = {}
        if view: params["view"] = view
        if cat:  params["cat"]  = cat
        st.experimental_set_query_params(**params)
    st.rerun()

# ---- Topbar carrito ----
top_l, top_r = st.columns([6, 2])
with top_r:
    n = cart_count()
    label = f"🛒 Ver carrito ({n})" if n else "🛒 Carrito"
    if st.button(label, use_container_width=True, key="btn_open_cart"):
        _nav(view="cart", cat=current_cat)

# ----------------------------------------------------------
# Diálogo (modal) para elegir cantidad
# ----------------------------------------------------------
def _open_add_dialog(prod):
    st.session_state["_add_dialog_prod"] = prod
    st.session_state["_add_dialog_qty"]  = 1

def _render_add_dialog():
    prod = st.session_state.get("_add_dialog_prod")
    if not prod:
        return
    # Compat: @st.dialog (>=1.32) o experimental_dialog
    dialog_dec = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

    def _body():
        img_src = img_to_data_uri(prod.get("imagen", ""))
        name = prod.get("nombre", "")
        st.markdown(
            f'<img class="am-modal-img" src="{img_src}" alt="{name}"/>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="am-modal-name">{name}</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="am-modal-price">{format_price(prod.get("precio",0))}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**Cantidad**")
        qty = st.number_input(
            "Cantidad",
            min_value=1, max_value=999, step=1,
            value=int(st.session_state.get("_add_dialog_qty", 1)),
            key="_add_dialog_qty_input",
            label_visibility="collapsed",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Cancelar", use_container_width=True,
                         key="_add_dialog_cancel"):
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
        # Fallback si la versión de Streamlit no tiene dialog
        with st.container(border=True):
            st.subheader(f"Agregar «{prod.get('nombre','')}»")
            _body()

# ================== VISTA: CARRITO ==================
if view == "cart":
    if st.button("← Seguir comprando", key="btn_back_shop"):
        _nav(cat=current_cat)
    st.markdown('<div class="am-section-title">🛒 Tu carrito</div>',
                unsafe_allow_html=True)

    cart = _cart()
    if not cart:
        st.markdown(
            '<div class="am-empty">Tu carrito está vacío.<br>'
            'Agrega productos desde los apartados.</div>',
            unsafe_allow_html=True,
        )
    else:
        for name, it in list(cart.items()):
            c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 1])
            with c1:
                st.markdown(
                    f'<img src="{img_to_data_uri(it["imagen"])}" '
                    f'style="width:64px;height:64px;object-fit:cover;'
                    f'border-radius:10px;border:1px solid #E2E8F0;background:#fff;"/>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(f"**{name}**")
                st.caption(f"{format_price(it['precio'])} c/u")
            with c3:
                b1, bq, b2 = st.columns([1, 1, 1])
                with b1:
                    if st.button("−", key=f"cart_minus_{name}"):
                        cart_set(name, it["qty"] - 1); st.rerun()
                with bq:
                    st.markdown(
                        f'<div style="text-align:center;font-weight:700;'
                        f'padding-top:6px;color:{COLOR_PRIMARY};">{it["qty"]}</div>',
                        unsafe_allow_html=True,
                    )
                with b2:
                    if st.button("+", key=f"cart_plus_{name}"):
                        cart_set(name, it["qty"] + 1); st.rerun()
            with c4:
                st.markdown(
                    f'<div style="padding-top:8px;font-weight:700;'
                    f'color:#4ADE80;">{format_price(it["precio"]*it["qty"])}</div>',
                    unsafe_allow_html=True,
                )
            with c5:
                if st.button("🗑", key=f"cart_del_{name}"):
                    cart_set(name, 0); st.rerun()

        st.markdown("---")
        tt1, tt2 = st.columns([3, 1])
        with tt1:
            st.markdown(
                f'<div style="font-size:22px;font-weight:800;color:{COLOR_PRIMARY};">'
                f'Total: <span style="color:#16A34A;">{format_price(cart_total())}'
                f'</span></div>',
                unsafe_allow_html=True,
            )
        with tt2:
            if st.button("Vaciar carrito", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

# ================== VISTA: LISTA DE APARTADOS ==================
elif not current_cat:
    st.markdown('<div class="am-section-title">Elige un apartado</div>',
                unsafe_allow_html=True)
    if not categories:
        st.markdown(
            '<div class="am-empty">Aún no hay apartados.<br>'
            'Crea apartados desde la app de escritorio '
            '(botón «Agregar nuevo apartado»).</div>',
            unsafe_allow_html=True,
        )
    else:
        counts = {}
        for p in products:
            c = p.get("categoria", "")
            counts[c] = counts.get(c, 0) + 1
        for idx, cat in enumerate(categories):
            n = counts.get(cat, 0)
            if st.button(
                f"📁   {cat}    ·    {n} producto(s)",
                key=f"cat_btn_{idx}_{cat}",
                use_container_width=True,
            ):
                _nav(cat=cat)

# ================== VISTA: PRODUCTOS DE UN APARTADO ==================
else:
    if st.button("← Volver a apartados", key="btn_back_cats"):
        _nav()
    st.markdown(f'<div class="am-section-title">📁 {current_cat}</div>',
                unsafe_allow_html=True)

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        query = st.text_input(
            "Buscar producto",
            placeholder=f"Buscar en {current_cat}…",
            label_visibility="collapsed",
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

        cols_per_row = 4
        for i in range(0, len(chunk), cols_per_row):
            row = st.columns(cols_per_row)
            for j, (col, prod) in enumerate(zip(row, chunk[i:i + cols_per_row])):
                name = prod.get("nombre", "")
                key_id = f"{i}_{j}_{name}"
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

        st.caption(f"Mostrando {len(chunk)} de {total} productos.")

# Render del diálogo si está activo
if st.session_state.get("_add_dialog_prod"):
    _render_add_dialog()

