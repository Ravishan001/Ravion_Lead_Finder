"""Ravion Gym Dashboard - your RepFlint sales pipeline (all gym leads ever found)."""
import datetime as dt, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import altair as alt
import pandas as pd
import streamlit as st
import gymfinder as gf
import gym_common as gc

st.set_page_config(page_title="Gym Dashboard · Ravion", page_icon="📊", layout="wide")
gc.password_gate(st)
cfg = gc.load_cfg()
gc.header(st, "📊", "Gym Dashboard", "RepFlint sales pipeline · හොයාගත්ත gyms ඔක්කොම එක තැනක")

db = gf.load_db()
leads = list(db["leads"].values())
if not leads:
    st.info("තවම gyms නෑ. **Gym Finder** page එකෙන් search එකක් run කරන්න (Demo එකෙනුත් බලන්න පුළුවන්).")
    gc.link(st, "pages/1_Gym_Finder.py", "🏋️ Gym Finder")
    st.stop()

df = pd.DataFrame(leads)
for c, d in [("status", "New"), ("notes", ""), ("contacted_on", ""), ("next_follow", ""), ("lat", None),
             ("lon", None), ("members_low", 0), ("members_high", 0), ("country", ""), ("size", "Unknown")]:
    if c not in df:
        df[c] = d
df["System"] = df["system"].map(gf.SYS_LABEL).fillna(df["system"])
df["members_mid"] = ((df["members_low"].fillna(0) + df["members_high"].fillna(0)) / 2).round()
df["status"] = df["status"].replace("", "New").fillna("New")

# --------------------------------------------------------------------------- filters
with st.sidebar:
    st.header("🔎 Filters")
    f_country = st.multiselect("Country", sorted(df["country"].dropna().unique()))
    f_city = st.multiselect("City", sorted(df[df["country"].isin(f_country) | (not f_country)]["city"].unique()))
    f_pri = st.multiselect("Priority", ["🔥 Hot", "Warm", "Cold"])
    f_status = st.multiselect("Status", gf.STATUSES)
    f_size = st.multiselect("Size (est.)", ["Very large", "Large", "Medium", "Small", "Unknown"])
    f_q = st.text_input("Search", placeholder="gym name / notes")
    hide_demo = st.toggle("[DEMO] rows හංගන්න", value=False)
    st.divider()
    gc.link(st, "pages/1_Gym_Finder.py", "🏋️ Gym Finder එකට")

v = df.copy()
if f_country: v = v[v["country"].isin(f_country)]
if f_city: v = v[v["city"].isin(f_city)]
if f_pri: v = v[v["priority"].isin(f_pri)]
if f_status: v = v[v["status"].isin(f_status)]
if f_size: v = v[v["size"].isin(f_size)]
if hide_demo: v = v[~v["name"].str.startswith("[DEMO]")]
if f_q:
    q = f_q.lower()
    v = v[v["name"].str.lower().str.contains(q, regex=False) | v["notes"].str.lower().str.contains(q, regex=False)]

# --------------------------------------------------------------------------- KPIs
today = dt.date.today().isoformat()
contacted = v[v["status"] != "New"]
won = (v["status"] == "Won").sum()
k = st.columns(6)
gc.kpi(k[0], "Gyms", len(v), f"{len(df)} total")
gc.kpi(k[1], "🔥 Hot leads", int((v["priority"] == "🔥 Hot").sum()), "score 75+")
gc.kpi(k[2], "Est. members", f"{int(v['members_mid'].sum()):,}", "RepFlint users වෙන්න පුළුවන්")
gc.kpi(k[3], "Contacted", len(contacted), f"{len(contacted) / max(len(v), 1):.0%} of leads")
gc.kpi(k[4], "Meetings", int((v["status"] == "Meeting").sum()))
gc.kpi(k[5], "Won 🏆", int(won), f"{won / max(len(contacted), 1):.0%} close rate")

due = v[(v["next_follow"].astype(str) != "") & (v["next_follow"].astype(str) <= today)
        & ~v["status"].isin(["Won", "Not interested"])]
if len(due):
    st.warning(f"⏰ අද follow-up කරන්න ඕන gyms {len(due)}ක්: " + ", ".join(due["name"].head(8)))
stale = (df["last_updated"].astype(str) < (dt.date.today() - dt.timedelta(days=30)).isoformat()).sum()
if stale:
    st.caption(f"ℹ️ Gyms {stale}ක data දවස් 30කට වඩා පරණයි - Google terms අනුව Gym Finder එකෙන් ආයෙත් run කරලා refresh කරන්න.")

# --------------------------------------------------------------------------- charts
st.markdown("<br>", unsafe_allow_html=True)
ORANGE, PALETTE = "#f97316", ["#f97316", "#a855f7", "#38bdf8", "#22c55e", "#facc15", "#f43f5e", "#94a3b8"]
c1, c2 = st.columns(2)
with c1:
    p = v["status"].value_counts().reindex(gf.STATUSES, fill_value=0).reset_index()
    p.columns = ["Status", "Gyms"]
    st.altair_chart(alt.Chart(p).mark_bar(cornerRadiusEnd=6, color=ORANGE).encode(
        x="Gyms:Q", y=alt.Y("Status:N", sort=gf.STATUSES, title=None), tooltip=["Status", "Gyms"])
        .properties(title="Sales pipeline", height=230), use_container_width=True)
with c2:
    cc = v.groupby("city").agg(Gyms=("id", "count"), Hot=("priority", lambda s: (s == "🔥 Hot").sum())) \
          .reset_index().sort_values("Gyms", ascending=False).head(12)
    m = cc.melt("city", ["Gyms", "Hot"], "Kind", "n")
    st.altair_chart(alt.Chart(m).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X("n:Q", title=None), y=alt.Y("city:N", sort="-x", title=None),
        color=alt.Color("Kind:N", scale=alt.Scale(range=["#a855f7", ORANGE]), legend=alt.Legend(orient="bottom")),
        yOffset="Kind:N", tooltip=["city", "Kind", "n"]).properties(title="City අනුව", height=230),
        use_container_width=True)
c3, c4 = st.columns(2)
with c3:
    s = v["System"].value_counts().reset_index(); s.columns = ["System", "Gyms"]
    st.altair_chart(alt.Chart(s).mark_arc(innerRadius=60, cornerRadius=4).encode(
        theta="Gyms:Q", color=alt.Color("System:N", scale=alt.Scale(range=PALETTE)),
        tooltip=["System", "Gyms"]).properties(title="ඔන්ලයින් තත්වය (system status)", height=250),
        use_container_width=True)
with c4:
    st.altair_chart(alt.Chart(v).mark_circle(size=90, opacity=.8).encode(
        x=alt.X("reviews:Q", title="Google reviews", scale=alt.Scale(type="symlog")),
        y=alt.Y("score:Q", title="Lead score"),
        color=alt.Color("priority:N", scale=alt.Scale(domain=["🔥 Hot", "Warm", "Cold"],
                                                       range=[ORANGE, "#a855f7", "#64748b"])),
        tooltip=["name", "city", "reviews", "score", "members_est", "System"])
        .properties(title="ලොකු + ලේසි gyms = දකුණු උඩ කොන", height=250), use_container_width=True)

mv = v.dropna(subset=["lat", "lon"])
if len(mv):
    mv = mv.assign(color=mv["priority"].map({"🔥 Hot": "#f97316", "Warm": "#a855f7"}).fillna("#64748b"),
                   size=(mv["members_mid"].fillna(20).clip(20, 600) * 4))
    st.markdown("**🗺️ Map** · තැඹිලි = Hot · දම් = Warm · ලොකු කව = members වැඩි")
    st.map(mv, latitude="lat", longitude="lon", color="color", size="size", height=380)

# --------------------------------------------------------------------------- pipeline table (editable)
gc.step(st, "✎", "Gyms list", "Status / dates / notes මෙතනම edit කරලා Save කරන්න")


def to_date(x):
    try:
        return dt.date.fromisoformat(str(x)[:10])
    except Exception:
        return None


t = v.sort_values(["score"], ascending=False)
edit = pd.DataFrame({
    "id": t["id"], "Priority": t["priority"], "Gym": t["name"], "Status": t["status"],
    "Contacted on": t["contacted_on"].map(to_date), "Next follow-up": t["next_follow"].map(to_date),
    "Notes": t["notes"].fillna(""), "Score": t["score"], "Est. members": t["members_est"],
    "Coaches": t["coaches"], "System": t["System"], "City": t["city"], "Reviews": t["reviews"],
    "Phone": t["phone"], "WhatsApp": t["whatsapp"].replace("", None), "Maps": t["maps"].replace("", None)})
out = st.data_editor(edit, hide_index=True, use_container_width=True, height=520, key="gym_editor",
                     disabled=[c for c in edit.columns if c not in ("Status", "Contacted on", "Next follow-up", "Notes")],
                     column_config={
                         "id": None,
                         "Status": st.column_config.SelectboxColumn("Status", options=gf.STATUSES, required=True),
                         "Contacted on": st.column_config.DateColumn(format="YYYY-MM-DD"),
                         "Next follow-up": st.column_config.DateColumn(format="YYYY-MM-DD"),
                         "Notes": st.column_config.TextColumn(width="large"),
                         "Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
                         "WhatsApp": st.column_config.LinkColumn(display_text="💬 Pitch"),
                         "Maps": st.column_config.LinkColumn(display_text="📍")})

b1, b2, b3, b4 = st.columns(4)
if b1.button("💾 Save changes", type="primary", use_container_width=True):
    n = 0
    for _, r in out.iterrows():
        rec = db["leads"].get(r["id"])
        if not rec:
            continue
        st_new = r["Status"] or "New"
        co = r["Contacted on"].isoformat() if pd.notna(r["Contacted on"]) and r["Contacted on"] else ""
        nf = r["Next follow-up"].isoformat() if pd.notna(r["Next follow-up"]) and r["Next follow-up"] else ""
        if st_new != "New" and not co:            # auto date like the Sheet Apps Script
            co = today
        if st_new == "Messaged" and not nf:
            nf = (dt.date.today() + dt.timedelta(days=3)).isoformat()
        new = dict(status=st_new, contacted_on=co, next_follow=nf, notes=r["Notes"] or "")
        if any(rec.get(k2, "") != v2 for k2, v2 in new.items()):
            rec.update(new); n += 1
    gf.save_db(db)
    st.success(f"Saved ✓ ({n} changed)")
    st.rerun()
if b2.button("📊 Google Sheet එකට push", use_container_width=True, disabled=not cfg.get("sheet_id")):
    try:
        n = gf.push_sheet(cfg["sheet_id"], cfg.get("service_account", ""))
        st.success(f"'Gym Leads' tab එකට gyms {n}ක් ලිව්වා ✓")
    except Exception as e:
        st.error(f"Sheet error: {e}")
b3.download_button("⬇️ CSV", t.drop(columns=["System"]).to_csv(index=False).encode("utf-8-sig"),
                   f"gym_leads_{today}.csv", use_container_width=True)
if b4.button("🧹 [DEMO] rows delete කරන්න", use_container_width=True):
    db["leads"] = {i: g for i, g in db["leads"].items() if not g["name"].startswith("[DEMO]")}
    gf.save_db(db); st.rerun()
