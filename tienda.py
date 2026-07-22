# ==========================================================
# AMAZONIA MARKET - Tienda Virtual (Streamlit) - Estilo Madison Center
# ==========================================================
#     streamlit run tienda.py
# Requisitos:  pip install streamlit pillow
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
CAT_ICONS_FILE   = BASE_DIR / "category_icons.json"
CAT_STYLES_FILE  = BASE_DIR / "category_styles.json"
TITLES_FILE      = BASE_DIR / "titles_settings.json"
CART_FILE        = BASE_DIR / "cart.json"
ANUNCIOS_FILE    = BASE_DIR / "anuncios.json"


def load_site_settings() -> dict:
    defaults = {
        "site_name": "Amazonia",
        "site_market": "MARKET",
        "site_logo_b64": "",
        "topbar_bg_color":  "#2A2A9C",
        "topbar_bg_image_b64": "",
        "topbar_bg_blur":       "0",
        "topbar_bg_brightness": "100",
        "topbar_bg_saturation": "100",
        "topbar_bg_opacity":    "100",
        "btn_menu_bg":   "rgba(255,255,255,.08)",
        "btn_menu_fg":   "#FFFFFF",
        "btn_search_bg": "#F5B301",
        "btn_search_fg": "#0F172A",
        "btn_cart_bg":   "rgba(255,255,255,.08)",
        "btn_cart_fg":   "#FFFFFF",
        "delivery_text": "🚚  Delivery GRATIS en toda la zona de Coro",
        "page_bg_type":       "color",
        "page_bg_color":      "#F4F5F7",
        "page_bg_image_b64":  "",
        "page_bg_blur":       "0",
        "page_bg_brightness": "100",
        "page_bg_opacity":    "100",
        "hide_logo":          "0",
        "section_title_color": "#2A2A9C",
        "section_title_size":  "22",
        "section_more_bg":     "#2A2A9C",
        "section_more_fg":     "#FFFFFF",
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
        CART_FILE.write_text(json.dumps(cart, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_anuncios() -> dict:
    defaults = {
        "banner_img_b64": "",
        "banner_brightness": 100,
        "banner_blur": 0,
        "banner_overlay": 0,
        "banner_height": 460,
        "cards": [
            {"title": "", "img_b64": "", "url": ""},
            {"title": "", "img_b64": "", "url": ""},
            {"title": "", "img_b64": "", "url": ""},
            {"title": "", "img_b64": "", "url": ""},
        ],
    }
    if not ANUNCIOS_FILE.exists():
        return defaults
    try:
        data = json.loads(ANUNCIOS_FILE.read_text(encoding="utf-8"))
        for k, v in defaults.items():
            data.setdefault(k, v)
        cards = list(data.get("cards", []))
        while len(cards) < 4:
            cards.append({"title": "", "img_b64": "", "url": ""})
        data["cards"] = cards[:4]
        return data
    except Exception:
        return defaults


PRODUCTS_PER_PAGE = 12
PREVIEW_PER_CAT   = 5

COLOR_PRIMARY    = "#2A2A9C"
COLOR_PRIMARY_2  = "#3838B8"
COLOR_PRIMARY_3  = "#4B4BD9"
COLOR_ACCENT     = "#F5B301"
COLOR_ACCENT_2   = "#FFC933"
COLOR_BG_GRAY    = "#F4F5F7"
COLOR_CARD       = "#FFFFFF"
COLOR_TEXT       = "#0F172A"
COLOR_MUTED      = "#64748B"
COLOR_PRICE      = "#16A34A"


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

    bbox = img.split()[-1].getbbox()
    if bbox:
        img = img.crop(bbox)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


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
                return "data:image/png;base64," + base64.b64encode(full.read_bytes()).decode()
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


_settings = load_site_settings()
_site_name = _settings.get("site_name", "Amazonia")
_site_market = _settings.get("site_market", "MARKET")

st.set_page_config(
    page_title=(f"{_site_name} {_site_market}".strip() or "Tienda"),
    page_icon="🛒",
    layout="wide",
)

st.markdown(
    """
    <base target="_top">
    <script>
    (function(){
      function fixLinks(){
        document.querySelectorAll('a[href]').forEach(function(a){
          var href = a.getAttribute('href') || '';
          if (href.startsWith('http') && !href.includes(location.host)) return;
          a.setAttribute('target','_top');
        });
      }
      fixLinks();
      new MutationObserver(fixLinks).observe(document.body, {childList:true, subtree:true});
    })();
    </script>
    """,
    unsafe_allow_html=True,
)

logo_b64        = get_logo_b64()
topbar_logo_b64 = get_topbar_logo_b64()
category_icons  = load_category_icons()

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

_sec_title_color = _settings.get("section_title_color", "#2A2A9C")
try:    _sec_title_size = int(float(_settings.get("section_title_size", "22")))
except: _sec_title_size = 22
_sec_more_bg = _settings.get("section_more_bg", "#2A2A9C")
_sec_more_fg = _settings.get("section_more_fg", "#FFFFFF")

_menu_panel_bg = _settings.get("menu_panel_bg", "#2A2A9C")
_menu_panel_fg = _settings.get("menu_panel_fg", "#FFFFFF")

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

_TOPBAR_BAND_PX = 152

st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Pacifico&family=Poppins:wght@400;600;700;800;900&family=Montserrat:wght@400;700;900&family=Playfair+Display:wght@400;700;900&family=Bebas+Neue&family=Lobster&family=Oswald:wght@400;700&family=Roboto:wght@400;700;900&family=Dancing+Script:wght@400;700&family=Great+Vibes&family=Anton&family=Merriweather:wght@400;700&family=Raleway:wght@400;700;900&display=swap');

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
      [data-testid="stMainBlockContainer"],
      [data-testid="stAppViewBlockContainer"] {{
        padding-top: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100% !important;
      }}

      .am-wrap {{
        max-width: 1280px;
        margin: 0 auto;
        padding: 0 24px;
      }}

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
      {"" if not _tb_bg_img_b64 else f".st-key-am_topbar_v2::before {{ content:''; position:absolute; inset:0; background: inherit; filter: blur({_tb_blur}px) brightness({_tb_bri}%) saturate({_tb_sat}%); opacity:{_tb_op/100:.2f}; pointer-events:none; z-index:0; }} .st-key-am_topbar_v2 > * {{ position: relative; z-index: 1; }}"}
      .st-key-am_topbar_v2 label, .st-key-am_topbar_v2 p {{ color: #fff !important; }}
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

      .am-cats-wrap {{
        background: #fff;
        border-bottom: 1px solid #E5E7EB;
        padding: 6px 0 8px 0;
        margin-bottom: 6px;
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

      .am-tiles-row {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px;
        margin: 12px 0 20px 0;
      }}
      .am-tile {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 14px 14px 12px 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
        display: flex;
        flex-direction: column;
        min-width: 0;
      }}
      .am-tile-empty {{
        background: transparent;
        border: none;
        box-shadow: none;
        padding: 0;
      }}
      .am-tile-title {{
        font-family: Poppins, sans-serif;
        font-weight: 800;
        font-size: 16px;
        line-height: 1.2;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
      }}
      .am-tile-count {{
        color: #6b7280;
        font-size: 11px;
        font-weight: 600;
        margin-left: 4px;
      }}
      .am-tile .am-quad-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        grid-template-rows: 1fr 1fr;
        gap: 8px;
        flex: 1;
      }}
      .am-tile-more {{
        display: block;
        text-align: center;
        text-decoration: none !important;
        font-family: Poppins, sans-serif;
        font-weight: 700;
        font-size: 13px;
        padding: 8px 12px;
        border-radius: 10px;
        margin-top: 12px;
        box-shadow: 0 3px 10px rgba(0,0,0,.12);
      }}
      .am-tile-more:hover {{ filter: brightness(0.95); }}
      @media (max-width: 900px) {{
        .am-tiles-row {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      }}
      @media (max-width: 520px) {{
        .am-tiles-row {{ grid-template-columns: 1fr; gap: 12px; }}
        .am-tile-title {{ font-size: 15px; }}
      }}

      .am-quad-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        grid-template-rows: 1fr 1fr;
        gap: 10px;
      }}
      .am-quad-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        background: #fafafa;
        border-radius: 10px;
        padding: 8px 6px;
      }}
      .am-quad-empty {{ background: transparent; }}
      .am-quad-imgwrap {{
        width: 100%;
        height: 90px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
      }}
      .am-quad-imgwrap img {{
        max-width: 100%;
        max-height: 90px;
        object-fit: contain;
      }}
      .am-quad-name {{
        margin-top: 6px;
        font-family: Poppins, sans-serif;
        font-size: 12px;
        font-weight: 600;
        color: #111827;
        text-align: center;
        line-height: 1.15;
        min-height: 28px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }}

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
    </style>
    """,
    unsafe_allow_html=True,
)


# --- ROUTER ---
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


# --- HEADER & TOPBAR ---
n_cart = cart_count()

with st.container(key="am_topbar_v2"):
    st.markdown(
        f'<div class="am-delivery-banner">{_delivery_text}</div>',
        unsafe_allow_html=True,
    )

    c_menu, c_logo, c_search, c_btn, c_acc, c_social, c_cart = st.columns(
        [1.1, 2.3, 4.2, 0.9, 1.9, 1.7, 0.9], vertical_alignment="center"
    )

    with c_menu:
        if st.button("☰  Menú", key="btn_menu", use_container_width=True):
            st.session_state["menu_open"] = not st.session_state.get("menu_open", False)
            st.rerun()

    with c_logo:
        if _hide_titles:
            blocks = []
        else:
            blocks = _titles if _titles else [
                {"text": _site_name,   "font": "Pacifico", "size": 30, "color": "#FFFFFF", "weight": "400"},
                {"text": _site_market, "font": "Poppins",  "size": 16, "color": _settings.get("btn_search_bg", COLOR_ACCENT), "weight": "900"},
            ]
        titles_html = "".join(
            f'<div style="font-family:\'{b["text"] and b["font"] or "Poppins"}\', sans-serif;'
            f'font-size:{b["size"]}px;color:{b["color"]};font-weight:{b["weight"]};'
            f'line-height:1.1;text-shadow:0 2px 6px rgba(0,0,0,.35);">{b["text"]}</div>'
            for b in blocks if b.get("text")
        )
        logo_html = ("" if _hide_logo else
            f'<img class="am-brand-logo" style="height:{_logo_size_px}px;margin-left:{_logo_offx_px}px;" src="data:image/png;base64,{topbar_logo_b64}" alt="logo"/>')
        st.markdown(
            f"""
            <a href="?" class="am-brand" target="_top" style="text-decoration:none;">
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
        _svg_facebook = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="#ffffff"><path d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0 -.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z"/></svg>'
        _svg_instagram = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="#ffffff"><path d="M12 2.163c3.204 0 3.584.012 4.849.07 1.366.062 2.633.336 3.608 1.311.975.975 1.249 2.242 1.311 3.608.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.062 1.366-.336 2.633-1.311 3.608-.975.975-2.242 1.249-3.608 1.311-1.265.058-1.645.07-4.849.07-3.205 0-3.584-.012-4.849-.07-1.366-.062-2.633-.336-3.608-1.311-.975-.975-1.249-2.242-1.311-3.608C2.175 15.647 2.163 15.268 2.163 12s.012-3.584.07-4.849c.062-1.366.336-2.633 1.311-3.608.975-.975 2.242-1.249 3.608-1.311C8.416 2.175 8.796 2.163 12 2.163zm0 1.802c-3.148 0-3.523.011-4.767.068-1.006.046-1.554.213-1.918.353-.482.187-.827.41-1.188.771-.361.361-.584.706-.771 1.188-.14.364-.307.912-.353 1.918C2.976 8.477 2.965 8.852 2.965 12s.011 3.523.068 4.767c.046 1.006.213 1.554.353 1.918.187.482.41.827.771 1.188.361.361.706.584 1.188.771.364.14.912.307 1.918.353 1.244.057 1.619.068 4.767.068s3.523-.011 4.767-.068c1.006-.046 1.554-.213 1.918-.353.482-.187.827-.41 1.188-.771.361-.361.584-.706.771-1.188.14-.364.307-.912.353-1.918.057-1.244.068-1.619.068-4.767s-.011-3.523-.068-4.767c-.046-1.006-.213-1.554-.353-1.918-.187-.482-.41-.827-.771-1.188-.361-.361-.706-.584-1.188-.771-.364-.14-.912-.307-1.918-.353C15.523 3.976 15.148 3.965 12 3.965zm0 3.063A4.972 4.972 0 1 1 12 16.972 4.972 4.972 0 0 1 12 7.028zm0 8.203A3.231 3.231 0 1 0 12 8.769a3.231 3.231 0 0 0 0 6.462zm5.171-8.406a1.163 1.163 0 1 1-2.326 0 1.163 1.163 0 0 1 2.326 0z"/></svg>'
        _svg_tiktok = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="#ffffff"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5.8 20.1a6.34 6.34 0 0 0 10.86-4.43V8.66a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1.84 -.09z"/></svg>'
        _social_items = []
        _btn_base = "display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;margin:0 4px;text-decoration:none;box-shadow:0 2px 6px rgba(0,0,0,.25);"
        if _facebook_url:
            _social_items.append(f'<a href="{_facebook_url}" target="_blank" rel="noopener" title="Facebook" style="{_btn_base}border-radius:50%;background:#1877F2;">{_svg_facebook}</a>')
        if _instagram_url:
            _social_items.append(f'<a href="{_instagram_url}" target="_blank" rel="noopener" title="Instagram" style="{_btn_base}border-radius:10px;background:radial-gradient(circle at 30% 110%,#FEDA75 0%,#FA7E1E 25%,#D62976 50%,#962FBF 75%,#4F5BD5 100%);">{_svg_instagram}</a>')
        if _tiktok_url:
            _social_items.append(f'<a href="{_tiktok_url}" target="_blank" rel="noopener" title="TikTok" style="{_btn_base}border-radius:50%;background:#000;">{_svg_tiktok}</a>')
        st.markdown('<div style="display:flex;align-items:center;justify-content:center;gap:2px;">' + "".join(_social_items) + '</div>', unsafe_allow_html=True)

    with c_cart:
        _badge = f"<span class='am-cart-badge'>{n_cart}</span>" if n_cart else ""
        st.markdown(
            f"""
            <div style="display:flex; justify-content:center;">
              <a class="am-cart-btn" href="?view=cart" target="_top" aria-label="Ver carrito">
                🛒{_badge}
              </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Panel desplegable Menu
if st.session_state.get("menu_open", False):
    _items_html = "".join(
        f'<a href="?cat={c}" target="_top" style="display:block;padding:12px 18px;border-bottom:1px solid rgba(255,255,255,.15);font-family:Poppins,sans-serif;font-weight:600;font-size:14px;">{c.capitalize()}</a>'
        for c in categories
    ) or '<div style="padding:14px 18px;opacity:.85;font-size:13px;">Aún no hay apartados.</div>'
    
    st.markdown(
        f'''
        <div class="am-menu-panel" style="position:relative;max-width:280px;margin:8px 0 12px 12px;background:{_menu_panel_bg};color:{_menu_panel_fg};border-radius:14px;box-shadow:0 10px 24px rgba(0,0,0,.22);overflow:hidden;">
          <div style="padding:10px 18px;font-weight:800;font-size:13px;letter-spacing:1px;text-transform:uppercase;opacity:.85;border-bottom:1px solid rgba(255,255,255,.2);">
            Apartados
          </div>
          {_items_html}
        </div>
        ''',
        unsafe_allow_html=True,
    )

# --- CIRCULOS CATEGORIAS ---
if categories:
    circles_html = ['<div class="am-cats-wrap"><div class="am-cats-scroll">']
    for cat in categories:
        stl = get_cat_style(cat, _cat_styles)
        icon = stl["icon"] or icon_for_category(cat, category_icons)
        sz, cc, lc, ls = stl["circle_size"], stl["circle_color"], stl["label_color"], stl["label_size"]
        circles_html.append(
            f'<a class="am-cat-circle" href="?cat={cat}" target="_top" style="min-width:{max(sz+20,80)}px;">'
            f'  <div class="bubble" style="width:{sz}px;height:{sz}px;background: radial-gradient(circle at 30% 30%, color-mix(in srgb, {cc} 78%, white) 0%, {cc} 78%);font-size:{int(sz*0.46)}px;">{icon}</div>'
            f'  <div class="label" style="color:{lc};font-size:{ls}px;">{cat}</div>'
            f'</a>'
        )
    circles_html.append("</div></div>")
    st.markdown("".join(circles_html), unsafe_allow_html=True)


# --- BANNER DE ANUNCIOS ---
def render_anuncios_banner():
    _anuncios = load_anuncios()
    _cards = _anuncios.get("cards", [])
    _has_cards = any((c.get("img_b64") or c.get("title")) for c in _cards)

    _slides_raw = _anuncios.get("banner_slides", [])
    _slides = []
    for s in _slides_raw:
        b64 = (s.get("img_b64") or "").strip()
        if b64:
            _slides.append({"b64": b64, "url": (s.get("url") or "").strip()})

    if not _slides:
        legacy = (_anuncios.get("banner_img_b64") or "").strip()
        if legacy:
            _slides.append({"b64": legacy, "url": ""})

    if not _slides and not _has_cards:
        return

    _bh   = int(_anuncios.get("banner_height", 320) or 320)
    _brt  = int(_anuncios.get("banner_brightness", 100) or 100)
    _blur = int(_anuncios.get("banner_blur", 0) or 0)
    _ovr  = int(_anuncios.get("banner_overlay", 0) or 0)

    n = len(_slides)
    per = 1.5
    total = per * max(n, 1)

    def _kf(i):
        start = (i * per) / total * 100
        end   = ((i + 1) * per) / total * 100
        fade  = min(8.0, (end - start) * 0.15)
        return (
            f"@keyframes amSlide{i} {{"
            f"  0%, {max(0.0, start-0.01):.3f}% {{ opacity:0; pointer-events:none; }}"
            f"  {min(100.0, start+fade):.3f}%, {max(start+fade, end-fade):.3f}% {{ opacity:1; pointer-events:auto; }}"
            f"  {end:.3f}%, 100% {{ opacity:0; pointer-events:none; }}"
            f"}}"
        )

    keyframes_css = "".join(_kf(i) for i in range(n)) if n > 1 else "@keyframes amSlide0 { 0%,100% { opacity:1; pointer-events:auto; } }"

    slides_html = []
    for i, s in enumerate(_slides):
        url = s["url"] or "#"
        target_attr = 'target="_blank" rel="noopener"' if s["url"] else ""
        anim = f"animation: amSlide{i} {total}s linear infinite;" if n > 1 else ""
        slides_html.append(
            f'<a class="am-slide" href="{url}" {target_attr} style="{anim}">'
            f'<img src="data:image/png;base64,{s["b64"]}"/>'
            f'</a>'
        )

    st.markdown(f"""
    <style>
      .am-ads-wrap {{ max-width: 1400px; margin: 4px auto 6px auto; padding: 0 8px; }}
      .am-ads-hero {{ position: relative; width: 100%; height: {_bh}px; border-radius: 14px; overflow: hidden; background: #ffffff; box-shadow: 0 10px 30px rgba(0,0,0,.18); }}
      .am-ads-hero .am-slide {{ position:absolute; inset:0; display:block; opacity:0; pointer-events:none; text-decoration:none; }}
      .am-ads-hero .am-slide img {{ width:100%; height:100%; object-fit: contain; object-position: center center; filter: brightness({_brt}%) blur({_blur}px); display:block; }}
      .am-ads-hero .ovr {{ position:absolute; inset:0; z-index:2; pointer-events:none; background: rgba(0,0,0,{_ovr/100:.2f}); }}
      {keyframes_css}
      .am-ads-cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: -70px; position: relative; z-index: 3; padding: 0 22px; }}
      .am-ads-card {{ background: #fff; border-radius: 10px; padding: 16px 16px 14px 16px; box-shadow: 0 6px 18px rgba(0,0,0,.10); display: flex; flex-direction: column; text-decoration: none !important; color: #111 !important; transition: transform .18s ease, box-shadow .18s ease; }}
      .am-ads-card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 26px rgba(0,0,0,.16); }}
      .am-ads-card .t {{ font-family: Poppins, sans-serif; font-weight: 800; font-size: 18px; color: #0F1111; margin-bottom: 10px; line-height: 1.15; }}
      .am-ads-card .imgbox {{ width: 100%; aspect-ratio: 1/1; overflow: hidden; border-radius: 6px; background: #f2f2f2; display:flex; align-items:center; justify-content:center; }}
      .am-ads-card .imgbox img {{ width: 100%; height: 100%; object-fit: cover; }}
      .am-ads-card .lnk {{ margin-top: 10px; font-size: 13px; color: #007185; font-weight: 700; }}
      @media (max-width: 900px) {{
        .am-ads-cards {{ grid-template-columns: repeat(2, 1fr); margin-top: -40px; }}
        .am-ads-hero {{ height: {max(180, _bh-120)}px; }}
      }}
    </style>
    """, unsafe_allow_html=True)

    ovr_html = '<div class="ovr"></div>' if _ovr > 0 else ""
    html = ['<div class="am-ads-wrap">']
    html.append(f'<div class="am-ads-hero">{"".join(slides_html)}{ovr_html}</div>')
    if _has_cards:
        html.append('<div class="am-ads-cards">')
        for c in _cards:
            title = (c.get("title") or "").strip()
            url   = (c.get("url") or "").strip() or "#"
            b64   = (c.get("img_b64") or "").strip()
            img_html = f'<img src="data:image/png;base64,{b64}"/>' if b64 else '<div style="color:#aaa;font-size:12px;">Sin imagen</div>'
            html.append(
                f'<a class="am-ads-card" href="{url}" target="_top">'
                f'<div class="t">{title or "&nbsp;"}</div>'
                f'<div class="imgbox">{img_html}</div>'
                f'<div class="lnk">Ver más &rsaquo;</div>'
                f'</a>'
            )
        html.append('</div>')
    html.append('</div>')
    st.markdown("".join(html), unsafe_allow_html=True)


render_anuncios_banner()


# --- DIALOGO DE CANTIDAD ---
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
        st.markdown(f'<div class="am-modal-price">{format_price(prod.get("precio",0))}</div>', unsafe_allow_html=True)
        st.markdown("**Cantidad**")
        qty = st.number_input("Cantidad", min_value=1, max_value=999, step=1, value=int(st.session_state.get("_add_dialog_qty", 1)), key="_add_dialog_qty_input", label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Cancelar", use_container_width=True, key="_add_dialog_cancel"):
                st.session_state.pop("_add_dialog_prod", None)
                st.rerun()
        with c2:
            if st.button("Agregar al carrito", type="primary", use_container_width=True, key="_add_dialog_ok"):
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


_render_add_dialog()


# ==========================================================
# CONTENIDO PRINCIPAL
# ==========================================================
st.markdown('<div class="am-wrap">', unsafe_allow_html=True)


def render_product_grid(prods, key_prefix, cols_per_row=4):
    """Grid de productos completos con botón agregar."""
    st.markdown('<div class="am-plist">', unsafe_allow_html=True)
    for i in range(0, len(prods), cols_per_row):
        row = st.columns(cols_per_row)
        for j, (col, prod) in enumerate(zip(row, prods[i:i + cols_per_row])):
            name = prod.get("nombre", "")
            key_id = f"{key_prefix}_{i}_{j}_{name}"
            in_cart = _cart().get(name, {}).get("qty", 0)
            img_src = img_to_data_uri(prod.get("imagen", ""))
            with col:
                badge = f'<span class="am-qty-badge">En carrito: {in_cart}</span>' if in_cart else ""
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
                if st.button("🛒  Agregar al carrito", key=f"add_{key_id}", use_container_width=True, type="primary"):
                    _open_add_dialog(prod)
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ================== VISTA: CARRITO ==================
if view == "cart":
    st.markdown(f"<style>.stApp {{ background: {_ct_pagebg} !important; }}</style>", unsafe_allow_html=True)
    if st.button("← Seguir comprando", key="btn_back_shop"):
        _nav(cat=current_cat)
    st.markdown(f'<h2 style="color:{_sec_title_color};font-family:Poppins;">🛒 Tu carrito</h2>', unsafe_allow_html=True)

    cart = _cart()
    if not cart:
        st.markdown('<div class="am-empty">Tu carrito está vacío.<br>Agrega productos desde los apartados.</div>', unsafe_allow_html=True)
    else:
        for name, it in list(cart.items()):
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([0.7, 3, 2.2, 2, 0.6])
                with c1:
                    st.markdown(f'<img src="{img_to_data_uri(it["imagen"])}" style="width:56px;height:56px;object-fit:contain;border-radius:10px;background:#fff;border:1px solid #E2E8F0;padding:3px;"/>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div style="font-weight:700;color:{_ct_name};font-size:13px;line-height:1.2;">{name}</div><div style="color:{_ct_price};font-size:11px;margin-top:2px;">{format_price(it["precio"])} c/u</div>', unsafe_allow_html=True)
                with c3:
                    b1, bq, b2 = st.columns([1, 1, 1])
                    with b1:
                        if st.button("−", key=f"cart_minus_{name}"):
                            cart_set(name, it["qty"] - 1); st.rerun()
                    with bq:
                        st.markdown(f'<div style="text-align:center;font-weight:900;padding-top:6px;color:{_ct_qty};font-size:16px;">{it["qty"]}</div>', unsafe_allow_html=True)
                    with b2:
                        if st.button("+", key=f"cart_plus_{name}"):
                            cart_set(name, it["qty"] + 1); st.rerun()
                with c4:
                    st.markdown(f'<div style="padding-top:4px;text-align:center;"><span style="display:inline-block;background:{_ct_lbg};color:{_ct_lfg};font-weight:700;font-size:13px;padding:4px 10px;border-radius:8px;">{format_price(it["precio"] * it["qty"])}</span></div>', unsafe_allow_html=True)
                with c5:
                    if st.button("🗑️", key=f"cart_del_{name}"):
                        cart_set(name, 0); st.rerun()

        st.markdown("---")
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
        tt1, tt2 = st.columns([2, 1])
        with tt1:
            st.markdown(f'<div style="font-size:20px;font-weight:700;color:{_ct_name};margin-top:8px;">Total a pagar:</div><div style="font-size:42px;font-weight:900;color:{_ct_tot};text-shadow:0 2px 6px rgba(22,163,74,.25);line-height:1.1;">{format_price(cart_total())}</div>', unsafe_allow_html=True)
        with tt2:
            st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
            if st.button("💳  Pagar ahora", key="cart_pay_now", use_container_width=True):
                st.success("¡Gracias por tu compra! (Aquí conectas tu pasarela de pago).")


# ================== VISTA: RESULTADOS BÚSQUEDA GLOBAL ==================
elif view == "search":
    q = (url_q or "").strip()
    st.markdown(f'<h2 style="color:{COLOR_PRIMARY};font-family:Poppins;">🔍 Resultados para: <span style="color:{COLOR_TEXT};">"{q}"</span></h2>', unsafe_allow_html=True)
    if st.button("← Volver al inicio", key="btn_back_home_from_search"):
        _nav()
    if not q:
        st.info("Escribe algo en la barra de búsqueda.")
    else:
        ql = q.lower()
        results = [p for p in products if ql in str(p.get("nombre", "")).lower() or ql in str(p.get("categoria", "")).lower()]
        if not results:
            st.markdown('<div class="am-empty">No se encontraron productos que coincidan.</div>', unsafe_allow_html=True)
        else:
            st.caption(f"{len(results)} resultado(s) en toda la tienda.")
            render_product_grid(results, key_prefix="search")


# ================== VISTA: HOME (MUESTRA APARTADOS Y TARJETAS 2x2) ==================
elif not current_cat:
    if not categories:
        st.markdown('<div class="am-empty">Aún no hay apartados.<br>Crea apartados desde la app de escritorio (botón «Agregar nuevo apartado»).</div>', unsafe_allow_html=True)
    else:
        def _build_card_html(cat: str) -> str:
            cat_prods = [pp for pp in products if pp.get("categoria") == cat]
            emoji = icon_for_category(cat, category_icons)
            total_cat = len(cat_prods)
            stl = get_cat_style(cat, _cat_styles)
            tcolor = stl["title_color"] or _sec_title_color
            mbg    = stl["more_bg"]     or _sec_more_bg
            mfg    = stl["more_fg"]     or _sec_more_fg
            micon  = stl["icon"] or emoji

            preview = cat_prods[:4]
            items_html = ""
            for prod in preview:
                img_src = img_to_data_uri(prod.get("imagen", ""))
                name = prod.get("nombre", "")
                items_html += (
                    f'<div class="am-quad-item">'
                    f'<div class="am-quad-imgwrap"><img src="{img_src}" alt="{name}"/></div>'
                    f'<div class="am-quad-name">{name}</div>'
                    f'</div>'
                )
            for _ in range(4 - len(preview)):
                items_html += '<div class="am-quad-item am-quad-empty"></div>'

            if not preview:
                grid_html = ('<div class="am-quad-grid am-quad-grid-empty">'
                             '<div class="am-section-empty" style="grid-column:1/-1;">Aún no hay productos.</div></div>')
            else:
                grid_html = f'<div class="am-quad-grid">{items_html}</div>'

            return (
                f'<div class="am-tile">'
                f'  <div class="am-tile-title" style="color:{tcolor};">'
                f'    {micon} {cat.capitalize()}'
                f'    <span class="am-tile-count">· {total_cat} producto(s)</span>'
                f'  </div>'
                f'  {grid_html}'
                f'  <a class="am-tile-more" href="?cat={cat}" target="_top" style="background:{mbg};color:{mfg};">Ver más →</a>'
                f'</div>'
            )

        PER_ROW = 4
        for row_start in range(0, len(categories), PER_ROW):
            row_cats = categories[row_start:row_start + PER_ROW]
            cards_html = "".join(_build_card_html(c) for c in row_cats)
            for _ in range(PER_ROW - len(row_cats)):
                cards_html += '<div class="am-tile am-tile-empty"></div>'
            st.markdown(f'<div class="am-tiles-row">{cards_html}</div>', unsafe_allow_html=True)


# ================== VISTA: APARTADO INDIVIDUAL (VER MÁS / CATEGORÍA) ==================
else:
    if st.button("← Volver al inicio", key="btn_back_home"):
        _nav()

    cat_prods = [p for p in products if p.get("categoria") == current_cat]
    stl = get_cat_style(current_cat, _cat_styles)
    icon = stl["icon"] or icon_for_category(current_cat, category_icons)

    st.markdown(
        f'<h2 style="color:{stl["title_color"] or COLOR_PRIMARY};font-family:Poppins;margin-top:10px;">'
        f'{icon} {current_cat.capitalize()} <span style="font-size:16px;color:#6b7280;font-weight:400;">({len(cat_prods)} productos)</span></h2>',
        unsafe_allow_html=True,
    )

    if not cat_prods:
        st.markdown('<div class="am-empty">Este apartado aún no tiene productos registrados.</div>', unsafe_allow_html=True)
    else:
        # Paginación
        total_pages = max(1, (len(cat_prods) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE)
        page = st.session_state.get(f"page_{current_cat}", 1)
        if page > total_pages: page = 1

        start_idx = (page - 1) * PRODUCTS_PER_PAGE
        page_prods = cat_prods[start_idx:start_idx + PRODUCTS_PER_PAGE]

        render_product_grid(page_prods, key_prefix=f"cat_{current_cat}_p{page}")

        if total_pages > 1:
            st.markdown("<br>", unsafe_allow_html=True)
            p_cols = st.columns([1, 2, 1])
            with p_cols[0]:
                if page > 1 and st.button("← Anterior", key=f"prev_{current_cat}"):
                    st.session_state[f"page_{current_cat}"] = page - 1
                    st.rerun()
            with p_cols[1]:
                st.markdown(f'<div style="text-align:center;font-weight:700;padding-top:8px;">Página {page} de {total_pages}</div>', unsafe_allow_html=True)
            with p_cols[2]:
                if page < total_pages and st.button("Siguiente →", key=f"next_{current_cat}"):
                    st.session_state[f"page_{current_cat}"] = page + 1
                    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)