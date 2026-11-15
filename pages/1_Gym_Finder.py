"""Ravion Gym Finder - find gyms with no member system (worldwide) to pitch RepFlint."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import altair as alt
import pandas as pd
import streamlit as st
import gymfinder as gf
import gym_common as gc

st.set_page_config(page_title="Gym Finder · Ravion", page_icon="🏋️", layout="wide")
gc.password_gate(st)
cfg = gc.load_cfg()
gc.header(st, "🏋️", "Gym Finder", "System එකක් නැති gyms හොයලා RepFlint pitch කරන්න · Sri Lanka + ලෝකෙම")

# --------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("⚙️ Gym Finder")
    sa_ok = os.path.exists(cfg.get("service_account", ""))
    st.markdown(
        f'<span class="chip {"ok" if cfg.get("api_key") else "no"}">Maps API key</span>'
        f'<span class="chip {"ok" if cfg.get("sheet_id") else "no"}">Sheet ID</span>'
        f'<span class="chip {"ok" if sa_ok else "no"}">service_account.json</span>', unsafe_allow_html=True)
    st.caption("Keys වෙනස් කරන්න ඕන නම් main page (app) එකේ Settings එකෙන්.")
    source = st.radio("Data source", ["google", "demo"], horizontal=True,
                      format_func={"google": "Google", "demo": "Demo (free test)"}.get)
    gc.link(st, "pages/2_Gym_Dashboard.py", "📊 Gym Dashboard එකට යන්න")

# --------------------------------------------------------------------------- 1 types
gc.step(st, 1, "Gym වර්ග", "මොන වගේ fitness businesses ද")
types = st.pills("Types", list(gf.GYM_TYPES), selection_mode="multi", default=gf.DEFAULT_TYPES,
                 format_func=lambda k: gf.GYM_TYPES[k][1], label_visibility="collapsed") or []

# --------------------------------------------------------------------------- 2 location
gc.step(st, 2, "ප්‍රදේශය", "රට → නගර → km radius")
c1, c2 = st.columns([1, 2])
country = c1.selectbox("රට (Country)", list(gc.COUNTRIES), index=0)
region, lang_default, starter = gc.COUNTRIES[country]
if country.startswith("Other"):
    o1, o2 = c2.columns([2, 1])
    country = o1.text_input("Country name", placeholder="eg: Italy") or ""
    region = o2.text_input("Region code (2 letters)", placeholder="IT", max_chars=2).upper()
    cities = []
elif country == "Sri Lanka":
    a1, a2 = c2.columns(2)
    provinces = a1.multiselect("පළාත", list(gc.SRI_LANKA), default=["North Western"])
    dopts = [d for p in provinces for d in gc.SRI_LANKA[p]]
    districts = a2.multiselect("දිස්ත්‍රික්කය", dopts, default=[d for d in ["Kurunegala"] if d in dopts])
    topts = [t for p in provinces for d, ts in gc.SRI_LANKA[p].items() if d in districts for t in ts]
    cities = st.multiselect("නගර", topts, default=topts[:2])
else:
    cities = c2.multiselect("Cities", starter, default=starter[:1])
e1, e2 = st.columns([3, 1.3])
extra = e1.text_input("තව නගර (comma වලින්)", placeholder="උදා: Giriulla, Alawwa  /  Leicester, Bolton")
cities = list(dict.fromkeys(cities + [t.strip() for t in extra.split(",") if t.strip()]))
radius = e2.slider("Radius (km)", 2, 50, 10, help="නගරයේ මැද ඉඳන් මේ km ගාණට වඩා දුර gyms අයින් කරනවා")

# --------------------------------------------------------------------------- 3 targets
gc.step(st, 3, "කවුද target", "RepFlint විකුණන්න ලේසිම gyms")
t1, t2, t3 = st.columns([1.5, 1, 1])
with t1:
    targets = st.pills("System status", list(gf.SYS_LABEL)[:-1], selection_mode="multi",
                       default=gf.DEFAULT_TARGETS, format_func=gf.SYS_LABEL.get,
                       help="'Website (not checked)' = website check එක off කළොත්/site එක open වුණේ නැත්නම්") or []
    chains = st.toggle("Big chains අයින් කරන්න (Anytime, Gold's, Power World…)", value=True)
    check = st.toggle("Gym websites open කරලා member system එකක් තියෙනවද බලන්න", value=True,
                      help="Mindbody, Glofox වගේ software / 'member login' තියෙනවද කියලා homepage එක බලනවා. "
                           "Google calls යන්නේ නෑ.")
with t2:
    min_score = st.slider("අවම Score", 0, 100, 50, 5)
    min_reviews = st.number_input("අවම reviews", 0, 1000, 0, 5,
                                  help="Reviews වැඩි = members වැඩි = budget තියෙනවා")
with t3:
    pages = st.select_slider("Search depth", [1, 2, 3], value=2, format_func=lambda p: f"{p * 20} places")
    max_calls = st.number_input("Max Google calls", 1, 500, 30)
    sync = st.toggle("'Gym Leads' sheet tab එකටත් copy කරන්න", value=False, disabled=not cfg.get("sheet_id"))

# --------------------------------------------------------------------------- 4 message
gc.step(st, 4, "WhatsApp message", "Results වල 💬 click කළාම මේ message එක ready වෙලා open වෙනවා")
lang = st.radio("භාෂාව", ["si", "en"], horizontal=True, index=0 if lang_default == "si" else 1,
                format_func={"si": "සිංහල", "en": "English"}.get)
key = f"gym_pitch_{lang}"
with st.expander("✏️ Message එක edit කරන්න  ({name}, {city}, {reason}" + (", {reason_si}" if lang == "si" else "") + ")"):
    tpl = st.text_area("Template", value=cfg.get(key) or gf.PITCH[lang], height=140, label_visibility="collapsed")
    b1, b2 = st.columns(2)
    if b1.button("💾 Save message"):
        gc.save_cfg_keys(**{key: tpl}); st.success("Saved")
    if b2.button("↺ Default එකට"):
        gc.save_cfg_keys(**{key: ""}); st.rerun()

# --------------------------------------------------------------------------- summary
st.markdown("<br>", unsafe_allow_html=True)
cache = gf._load_json(gf.GEO_CACHE, {})
geo = sum(1 for c in cities if f"{c}|{country}".lower() not in cache
          and not (country == "Sri Lanka" and c in gf.lf.CITIES))
planned = len(types) * len(cities) * pages + geo
use = min(planned, max_calls) if source == "google" else 0
s = st.columns([1, 1, 1, 1.7])
gc.kpi(s[0], "Gym types", len(types))
gc.kpi(s[1], "Cities", len(cities), country or "—")
gc.kpi(s[2], "Google calls", use if source == "google" else "—", f"incl. {geo} city lookups" if geo else "")
with s[3]:
    if source != "google":
        st.info("Demo mode - fake gyms, Google calls යන්නේ නෑ")
    elif planned > max_calls:
        st.warning(f"Calls {planned}ක් ඕන, limit එක {max_calls}. සමහර searches කැපෙනවා.")
    elif use > 30:
        st.warning("Daily quota එක 30 නම් මේක වැඩියි.")
    else:
        st.info(f"Places ~{len(types) * len(cities) * pages * 20}ක් විතර check කරනවා · "
                f"මාසෙට free calls 1,000 ඇතුළේ ✓")

ready = bool(types and cities and targets and country) and (source != "google" or cfg.get("api_key"))
if source == "google" and not cfg.get("api_key"):
    st.error("Main page එකේ Settings වල Google Maps API key එක දාලා Save කරන්න.")
start = st.button("🏋️  Start - Gyms හොයන්න", type="primary", use_container_width=True, disabled=not ready)

# --------------------------------------------------------------------------- run
if start:
    bar = st.progress(0.0, text="පටන් ගන්නවා…")
    logs = []
    with st.status("Searching gyms…", expanded=True) as status:
        box = st.empty()

        def _log(line):
            logs.append(line); box.code("\n".join(logs[-14:]), language=None)

        gf._LOGGER = _log
        gf._PROGRESS = lambda d, t, txt: bar.progress(min(d / max(t, 1), 1.0), text=f"{txt}  ({d}/{t})")
        try:
            res = gf.run_gym_search(types, cities, country, region, source, cfg.get("api_key", ""),
                                    int(max_calls), pages, radius, targets, chains, int(min_reviews),
                                    min_score, check, lang, {lang: tpl},
                                    sheet_id=cfg.get("sheet_id", ""),
                                    service_account=cfg.get("service_account", ""), sync=sync)
            st.session_state["gym_res"] = res
            bar.progress(1.0, text="ඉවරයි ✓")
            status.update(label=f"ඉවරයි - gym leads {len(res['kept'])}ක්", state="complete", expanded=False)
        except Exception as e:
            status.update(label="Error", state="error"); st.error(str(e))
        finally:
            gf._LOGGER, gf._PROGRESS = print, None

# --------------------------------------------------------------------------- results
res = st.session_state.get("gym_res")
if res:
    gc.step(st, "✓", "Results", f"Dashboard එකට save වුණා: +{res['added']} අලුත්, {res['updated']} update")
    kept = res["kept"]
    hot = sum(1 for g in kept if g["priority"].startswith("🔥"))
    members = sum(((g["members_low"] or 0) + (g["members_high"] or 0)) // 2 for g in kept)
    k = st.columns(5)
    gc.kpi(k[0], "Places found", res["found"], f"{res['far']} දුර නිසා අයින් කළා")
    gc.kpi(k[1], "Gym leads", len(kept))
    gc.kpi(k[2], "🔥 Hot", hot, "score 75+")
    gc.kpi(k[3], "Est. members", f"{members:,}", "leads ඔක්කොගෙම (est.)")
    gc.kpi(k[4], "Google calls", res["calls"])
    if res["sheet"] == "ok":
        st.success("'Gym Leads' tab එකට copy කළා ✓")
    elif res["sheet"].startswith("error"):
        st.error(f"Sheet sync වුණේ නෑ: {res['sheet'][7:]}")

    sc = pd.DataFrame([{"System": gf.SYS_LABEL[s], "Gyms": n} for s, n in res["sys_counts"].items()])
    if not sc.empty:
        st.altair_chart(alt.Chart(sc).mark_bar(cornerRadiusEnd=6, color="#f97316").encode(
            x=alt.X("Gyms:Q"), y=alt.Y("System:N", sort="-x", title=None), tooltip=["System", "Gyms"])
            .properties(height=36 * len(sc) + 20, title="හම්බුණු gyms ඔක්කොම - system status අනුව"),
            use_container_width=True)

    if kept:
        df = pd.DataFrame([{
            "Priority": g["priority"], "Score": g["score"], "Gym": g["name"], "City": g["city"],
            "Km": g["dist_km"], "Est. members": g["members_est"], "Est. coaches": g["coaches"],
            "Size": g["size"], "System": gf.SYS_LABEL[g["system"]], "Rating": g["rating"],
            "Reviews": g["reviews"], "Phone": g["phone"], "WhatsApp": g["whatsapp"] or None,
            "Website": g["website"] or None, "Why": g["why"], "Maps": g["maps"] or None} for g in kept])
        st.dataframe(df, use_container_width=True, hide_index=True, height=520, column_config={
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
            "WhatsApp": st.column_config.LinkColumn("WhatsApp", display_text="💬 Send pitch"),
            "Website": st.column_config.LinkColumn("Website", display_text="🔗 Open"),
            "Maps": st.column_config.LinkColumn("Maps", display_text="📍 Open"),
            "Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
            "Why": st.column_config.TextColumn(width="large")})
        st.markdown('<div class="note">Members/coaches ගණන් <b>estimate</b> එකක් (Google reviews ගණනෙන්). '
                    'Google එකේ members ගණන නෑ. ඇත්ත ගණන call එකේදී අහන්න: "දැන් members කීයක් විතර ඉන්නවද? '
                    'Payments record කරන්නේ කොහොමද?"</div>', unsafe_allow_html=True)
        d1, d2, d3 = st.columns(3)
        if res.get("xlsx") and os.path.exists(res["xlsx"]):
            with open(res["xlsx"], "rb") as f:
                d1.download_button("⬇️ Excel", f.read(), os.path.basename(res["xlsx"]), use_container_width=True)
        with open(res["csv"], "rb") as f:
            d2.download_button("⬇️ CSV", f.read(), os.path.basename(res["csv"]), use_container_width=True)
        with d3:
            gc.link(st, "pages/2_Gym_Dashboard.py", "📊 Dashboard එක open කරන්න", use_container_width=True)
    else:
        st.info("මේ filters වලට gyms නෑ. Score එක අඩු කරලා, radius එක වැඩි කරලා, හරි targets වැඩි කරලා try කරන්න.")
