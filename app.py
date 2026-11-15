"""
Ravion Lead Finder - App
Run:  python -m streamlit run app.py      (or double-click Start_App.bat)
"""
import json, os, time
import pandas as pd
import streamlit as st
import leadfinder as lf

HERE = os.path.dirname(os.path.abspath(__file__))
SETTINGS = os.path.join(HERE, "settings.json")

st.set_page_config(page_title="Ravion Lead Finder", page_icon="🔎", layout="wide")
import gym_common as _gc
_gc.password_gate(st)   # only when APP_PASSWORD is set (cloud)

# --------------------------------------------------------------------------- data
GROUPS = {
    "💇 Beauty & Wellness": ["salon", "beauty_salon", "barber", "spa", "gym"],
    "🩺 Health & Care": ["dental_clinic", "medical_clinic", "physio", "optical", "veterinary", "pharmacy"],
    "🎓 Education": ["tuition", "driving_school"],
    "🏨 Tourism & Food": ["guest_house", "hotel", "restaurant", "cafe", "cake_shop"],
    "🎉 Events & Services": ["event_planner", "photography", "vehicle_service"],
}
LABELS = {
    "salon": "Hair salon", "beauty_salon": "Beauty / Bridal salon", "barber": "Barber shop",
    "spa": "Spa / Ayurveda", "gym": "Gym / Fitness", "dental_clinic": "Dental clinic",
    "medical_clinic": "Medical center / Channeling", "physio": "Physiotherapy", "optical": "Optical shop",
    "veterinary": "Vet / Pet clinic", "pharmacy": "Pharmacy", "tuition": "Tuition class",
    "driving_school": "Driving school", "guest_house": "Guest house", "hotel": "Hotel",
    "restaurant": "Restaurant", "cafe": "Cafe", "cake_shop": "Cake shop",
    "event_planner": "Wedding / Event planner", "photography": "Wedding photography",
    "vehicle_service": "Vehicle service center",
}
SRI_LANKA = {
    "Western": {
        "Colombo": ["Colombo", "Dehiwala", "Nugegoda", "Maharagama", "Moratuwa", "Battaramulla",
                    "Malabe", "Homagama", "Kottawa"],
        "Gampaha": ["Gampaha", "Negombo", "Ja-Ela", "Wattala", "Kadawatha", "Kiribathgoda",
                    "Minuwangoda", "Nittambuwa", "Veyangoda"],
        "Kalutara": ["Kalutara", "Panadura", "Horana", "Beruwala", "Matugama"],
    },
    "Central": {
        "Kandy": ["Kandy", "Peradeniya", "Katugastota", "Gampola", "Nawalapitiya", "Digana"],
        "Matale": ["Matale", "Dambulla", "Galewela"],
        "Nuwara Eliya": ["Nuwara Eliya", "Hatton", "Talawakele"],
    },
    "Southern": {
        "Galle": ["Galle", "Hikkaduwa", "Ambalangoda", "Elpitiya"],
        "Matara": ["Matara", "Weligama", "Akuressa", "Dikwella"],
        "Hambantota": ["Hambantota", "Tangalle", "Tissamaharama", "Ambalantota"],
    },
    "North Western": {
        "Kurunegala": ["Kurunegala", "Kuliyapitiya", "Narammala", "Wariyapola", "Pannala",
                       "Nikaweratiya", "Polgahawela"],
        "Puttalam": ["Chilaw", "Puttalam", "Wennappuwa", "Marawila", "Nattandiya", "Dankotuwa"],
    },
    "North Central": {
        "Anuradhapura": ["Anuradhapura", "Kekirawa", "Medawachchiya"],
        "Polonnaruwa": ["Polonnaruwa", "Kaduruwela", "Hingurakgoda"],
    },
    "Sabaragamuwa": {
        "Ratnapura": ["Ratnapura", "Embilipitiya", "Balangoda", "Pelmadulla"],
        "Kegalle": ["Kegalle", "Mawanella", "Warakapola", "Ruwanwella"],
    },
    "Uva": {
        "Badulla": ["Badulla", "Bandarawela", "Welimada", "Ella", "Haputale"],
        "Monaragala": ["Monaragala", "Wellawaya", "Buttala"],
    },
    "Eastern": {
        "Trincomalee": ["Trincomalee", "Kinniya"],
        "Batticaloa": ["Batticaloa", "Kattankudy"],
        "Ampara": ["Ampara", "Kalmunai", "Akkaraipattu"],
    },
    "Northern": {
        "Jaffna": ["Jaffna", "Chavakachcheri", "Point Pedro"],
        "Vavuniya": ["Vavuniya"], "Kilinochchi": ["Kilinochchi"],
        "Mannar": ["Mannar"], "Mullaitivu": ["Mullaitivu"],
    },
}


def fit_stars(key):
    w = lf.CATEGORIES[key][2]
    return "★★★" if w >= 13 else ("★★" if w >= 10 else "★")


# --------------------------------------------------------------------------- settings
def load_cfg():
    cfg = lf.load_settings(HERE)
    try:
        with open(SETTINGS, encoding="utf-8") as f:
            cfg.update({k: v for k, v in json.load(f).items() if v})
    except Exception:
        pass
    return cfg


def save_cfg(cfg):
    with open(SETTINGS, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


cfg = load_cfg()

# --------------------------------------------------------------------------- style
st.markdown("""
<style>
.block-container{padding-top:1.6rem;max-width:1250px}
.hero{display:flex;align-items:center;gap:16px;margin-bottom:6px}
.hero h1{font-size:2.1rem;margin:0}
.hero p{margin:2px 0 0;color:#94a3b8}
.step{display:flex;align-items:center;gap:12px;margin:26px 0 8px}
.step b{width:34px;height:34px;border-radius:50%;background:#f97316;color:#fff;display:flex;
        align-items:center;justify-content:center;font-size:1.05rem}
.step span{font-size:1.25rem;font-weight:700}
.step small{color:#94a3b8;font-weight:400;font-size:.9rem;margin-left:6px}
.sumcard{background:#111a2e;border:1px solid #1e293b;border-radius:16px;padding:16px 20px}
.sumcard .n{font-size:1.9rem;font-weight:800;color:#fdba74}
.chip{display:inline-block;padding:3px 10px;border-radius:999px;font-size:.8rem;margin-right:6px}
.ok{background:#14532d;color:#bbf7d0}.no{background:#3f1d1d;color:#fecaca}
button[data-testid="stBaseButton-primary"]{min-height:3.6rem;border-radius:14px}
button[data-testid="stBaseButton-primary"] p{font-size:1.25rem!important;font-weight:800}
.fit{color:#fb923c;font-size:.8rem;letter-spacing:1px}
</style>""", unsafe_allow_html=True)

st.markdown("""<div class="hero"><div style="font-size:2.6rem">🔎</div><div>
<h1>Ravion Lead Finder</h1><p>Website නැති, AI agent එකක් ඕන busy businesses හොයන්න · Sri Lanka</p>
</div></div>""", unsafe_allow_html=True)

# --------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    sa_ok = os.path.exists(cfg.get("service_account", ""))
    st.markdown(
        f'<span class="chip {"ok" if cfg.get("api_key") else "no"}">Maps API key</span>'
        f'<span class="chip {"ok" if cfg.get("sheet_id") else "no"}">Sheet ID</span>'
        f'<span class="chip {"ok" if sa_ok else "no"}">service_account.json</span>',
        unsafe_allow_html=True)
    with st.expander("Keys / Google Sheet", expanded=not cfg.get("api_key")):
        k = st.text_input("Google Maps API key", value=cfg.get("api_key", ""), type="password")
        s = st.text_input("Google Sheet ID", value=cfg.get("sheet_id", ""),
                          help="Sheet URL එකේ /d/ සහ /edit අතර කොටස")
        sa = st.text_input("Service account file", value=cfg.get("service_account", ""))
        if st.button("💾 Save settings", use_container_width=True):
            cfg.update(api_key=k.strip(), sheet_id=s.strip(), service_account=sa.strip())
            save_cfg(cfg)
            st.success("Saved!")
            time.sleep(0.6)
            st.rerun()
    if cfg.get("sheet_id"):
        st.link_button("📊 Google Sheet එක open කරන්න",
                       f"https://docs.google.com/spreadsheets/d/{cfg['sheet_id']}", use_container_width=True)
    st.divider()
    source = st.radio("Data source", ["google", "demo", "osm"], horizontal=True,
                      format_func={"google": "Google", "demo": "Demo", "osm": "OSM (free)"}.get,
                      help="Demo = fake data, test කරන්න. OSM = free නමුත් data අඩුයි.")
    st.caption("Ravion Studio · ravionstudio.com")

# --------------------------------------------------------------------------- step 1: categories
st.markdown('<div class="step"><b>1</b><span>Business types<small>AI agent එකක් ඕන වෙන, '
            'messages ගොඩක් එන businesses</small></span></div>', unsafe_allow_html=True)


def set_cats(keys):
    for c in lf.CATEGORIES:
        st.session_state[f"cat_{c}"] = c in keys


for c in lf.CATEGORIES:
    st.session_state.setdefault(f"cat_{c}", c in ("salon", "beauty_salon"))

b1, b2, b3, _ = st.columns([1.3, 1, 1, 4])
b1.button("★★★ Best fit", on_click=set_cats,
          args=([c for c in lf.CATEGORIES if lf.CATEGORIES[c][2] >= 13],), use_container_width=True)
b2.button("All", on_click=set_cats, args=(list(lf.CATEGORIES),), use_container_width=True)
b3.button("Clear", on_click=set_cats, args=([],), use_container_width=True)

gcols = st.columns(len(GROUPS))
for col, (gname, keys) in zip(gcols, GROUPS.items()):
    with col:
        with st.container(border=True):
            st.markdown(f"**{gname}**")
            for c in keys:
                st.checkbox(f"{LABELS[c]} {fit_stars(c)}", key=f"cat_{c}", help=lf.CATEGORIES[c][3])
categories = [c for c in lf.CATEGORIES if st.session_state.get(f"cat_{c}")]
st.caption("★★★ = AI agent එකකට හොඳටම ගැලපෙනවා (bookings/inquiries ගොඩක්) · ★ = පොඩ්ඩක් ගැලපෙනවා")

# --------------------------------------------------------------------------- step 2: area
st.markdown('<div class="step"><b>2</b><span>ප්‍රදේශය<small>පළාත → දිස්ත්‍රික්කය → නගර</small>'
            '</span></div>', unsafe_allow_html=True)
a1, a2 = st.columns(2)
provinces = a1.multiselect("පළාත (Province)", list(SRI_LANKA), default=["North Western"])
dist_opts = [d for p in provinces for d in SRI_LANKA[p]]
districts = a2.multiselect("දිස්ත්‍රික්කය (District)", dist_opts,
                           default=[d for d in ["Kurunegala"] if d in dist_opts])
town_opts = [t for p in provinces for d, ts in SRI_LANKA[p].items() if d in districts for t in ts]
t1, t2 = st.columns([3, 1.4])
pick_all = t2.toggle("දිස්ත්‍රික්කයේ හැම නගරයම", value=False)
towns = t1.multiselect("නගර (Towns)", town_opts,
                       default=town_opts if pick_all else town_opts[:2], disabled=pick_all)
if pick_all:
    towns = town_opts
extra = st.text_input("තව නගර (comma වලින් වෙන් කරන්න)", placeholder="උදා: Giriulla, Alawwa")
towns = list(dict.fromkeys(towns + [t.strip() for t in extra.split(",") if t.strip()]))
if source == "osm":
    missing = [t for t in towns if t not in lf.CITIES]
    if missing:
        st.warning(f"OSM source එකට coordinates නැති නගර skip වෙනවා: {', '.join(missing)}")

# --------------------------------------------------------------------------- step 3: options
st.markdown('<div class="step"><b>3</b><span>Filters<small>මොන වගේ leads ද ඕන</small></span></div>',
            unsafe_allow_html=True)
o1, o2, o3 = st.columns([1.25, 1, 1])
with o1:
    tier_labels = {"A": "A Top", "B": "B Est.", "C": "C Growing", "D": "D Small"}
    tiers = st.pills("Business level (Tier)", list(tier_labels), selection_mode="multi",
                     default=["A", "B", "C"], format_func=tier_labels.get,
                     help="Reviews, rating, price level, branches අනුව ලොකු කම") or []
    sort = st.radio("Sort", ["reach", "score"], horizontal=True,
                    format_func={"reach": "ලොකුම business උඩට", "score": "හොඳම lead fit උඩට"}.get)
with o2:
    min_score = st.slider("අවම Lead score", 0, 100, 50, 5,
                          help="Website නෑ + WhatsApp number + busy = වැඩි score")
    website_mode = st.radio("Website", ["no", "all"], horizontal=True,
                            format_func={"no": "Website නැති අය විතරක්", "all": "ඔක්කොම"}.get)
with o3:
    pages = st.select_slider("Search depth (එක search එකකට)", options=[1, 2, 3], value=3,
                             format_func=lambda p: f"{p * 20} places")
    max_calls = st.number_input("Max Google calls (cost guard)", 1, 500, 30)
    sync = st.toggle("Google Sheet එකට save කරන්න", value=bool(cfg.get("sheet_id")),
                     disabled=not cfg.get("sheet_id"))

# --------------------------------------------------------------------------- summary + start
st.markdown("<br>", unsafe_allow_html=True)
planned = len(categories) * len(towns) * pages
use_calls = min(planned, max_calls) if source == "google" else 0
s1, s2, s3, s4 = st.columns([1, 1, 1, 1.6])
for col, n, lab in [(s1, len(categories), "Business types"), (s2, len(towns), "Towns"),
                    (s3, use_calls if source == "google" else "—", "Google calls")]:
    col.markdown(f'<div class="sumcard"><div class="n">{n}</div>{lab}</div>', unsafe_allow_html=True)
with s4:
    if source == "google":
        if planned > max_calls:
            st.warning(f"Calls {planned}ක් ඕන, ඒත් limit එක {max_calls}. සමහර searches කැපෙනවා.")
        elif use_calls > 30:
            st.warning("ඔයාගේ daily quota එක 30 නම් මේක ඒකට වඩා වැඩියි.")
        else:
            st.info(f"Businesses ~{use_calls * 20}ක් විතර check කරනවා · free limit ඇතුළේ ✓")
    else:
        st.info("Demo/OSM - Google calls යන්නේ නෑ")

ready = bool(categories and towns and tiers) and (source != "google" or cfg.get("api_key"))
if source == "google" and not cfg.get("api_key"):
    st.error("Sidebar එකේ Google Maps API key එක දාලා Save කරන්න.")
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
start = st.button("🚀  Start - Leads හොයන්න", type="primary", use_container_width=True, disabled=not ready)

# --------------------------------------------------------------------------- run
if start:
    bar = st.progress(0.0, text="පටන් ගන්නවා…")
    logs = []
    with st.status("Searching…", expanded=True) as status:
        box = st.empty()

        def _log(line):
            logs.append(line)
            box.code("\n".join(logs[-14:]), language=None)

        lf._LOGGER = _log
        lf._PROGRESS = lambda d, t, txt: bar.progress(min(d / max(t, 1), 1.0), text=f"{txt}  ({d}/{t})")
        try:
            res = lf.run_search(
                categories, towns, source, cfg.get("api_key", ""), int(max_calls), pages, 8000,
                min_score, tiers, website_mode == "all", sort, os.path.join(HERE, "output"),
                cfg.get("sheet_id", ""), cfg.get("service_account", ""), sync)
            st.session_state["res"] = res
            bar.progress(1.0, text="ඉවරයි ✓")
            status.update(label=f"ඉවරයි - leads {len(res['kept'])}ක්", state="complete", expanded=False)
        except Exception as e:
            status.update(label="Error", state="error")
            st.error(str(e))
        finally:
            lf._LOGGER, lf._PROGRESS = print, None

# --------------------------------------------------------------------------- results
res = st.session_state.get("res")
if res:
    st.markdown('<div class="step"><b>✓</b><span>Results</span></div>', unsafe_allow_html=True)
    m = st.columns(6)
    m[0].metric("Businesses found", res["found"])
    m[1].metric("Leads", len(res["kept"]))
    for i, t in enumerate("ABCD"):
        m[2 + i].metric(f"Tier {t}", res["counts"][t])
    if res["sheet"] == "ok":
        st.success("Google Sheet එකට save කළා ✓")
    elif res["sheet"].startswith("error"):
        st.error(f"Google Sheet sync වුණේ නෑ: {res['sheet'][7:]}")

    rows = [{
        "Tier": l["tier"], "Reach": l["reach"], "Lead score": l["score"], "Business": l["name"],
        "Type": LABELS.get(l["category"], l["category"]), "City": l["city"], "Phone": l["phone"],
        "WhatsApp": l["whatsapp"] or None, "Rating": l["rating"], "Reviews": l["reviews"],
        "Website": lf.WEB_LABEL.get(l["website_status"]), "Why": lf.full_why(l),
        "Pitch idea": l["pitch"], "Maps": l["maps"] or None,
    } for l in res["kept"]]
    df = pd.DataFrame(rows)
    if not df.empty:
        f1, f2 = st.columns([1, 3])
        tf = f1.pills("Tier filter", sorted(df["Tier"].unique()), selection_mode="multi",
                      default=sorted(df["Tier"].unique()), format_func=lambda t: t.split(" · ")[0]) or []
        q = f2.text_input("Search", placeholder="නම / city / type")
        view = df[df["Tier"].isin(tf)]
        if q:
            mask = view[["Business", "City", "Type"]].apply(
                lambda r: q.lower() in " ".join(map(str, r)).lower(), axis=1)
            view = view[mask]
        st.dataframe(
            view, use_container_width=True, hide_index=True, height=520,
            column_config={
                "Reach": st.column_config.ProgressColumn("Reach", min_value=0, max_value=100, format="%d"),
                "Lead score": st.column_config.ProgressColumn("Lead score", min_value=0, max_value=100, format="%d"),
                "WhatsApp": st.column_config.LinkColumn("WhatsApp", display_text="💬 Chat"),
                "Maps": st.column_config.LinkColumn("Maps", display_text="📍 Open"),
                "Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
                "Why": st.column_config.TextColumn(width="medium"),
                "Pitch idea": st.column_config.TextColumn(width="large"),
            })
        d1, d2, d3 = st.columns(3)
        if res.get("xlsx") and os.path.exists(res["xlsx"]):
            with open(res["xlsx"], "rb") as f:
                d1.download_button("⬇️ Excel download", f.read(), os.path.basename(res["xlsx"]),
                                   use_container_width=True)
        with open(res["csv"], "rb") as f:
            d2.download_button("⬇️ CSV download", f.read(), os.path.basename(res["csv"]),
                               use_container_width=True)
        if cfg.get("sheet_id"):
            d3.link_button("📊 Google Sheet", f"https://docs.google.com/spreadsheets/d/{cfg['sheet_id']}",
                           use_container_width=True)
    else:
        st.info("මේ filters වලට leads නෑ. Lead score එක අඩු කරලා හරි, Tier වැඩි කරලා හරි ආයෙත් try කරන්න.")
