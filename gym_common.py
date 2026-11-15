"""Shared helpers for the Gym Finder + Gym Dashboard pages (does not touch app.py)."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SETTINGS = os.path.join(HERE, "settings.json")

# country: (regionCode, language for pitch, starter cities)
COUNTRIES = {
    "Sri Lanka": ("LK", "si", []),  # Sri Lanka uses the province/district picker below
    "India": ("IN", "en", ["Chennai", "Bengaluru", "Hyderabad", "Mumbai", "Pune", "Delhi", "Kochi",
                           "Coimbatore", "Madurai", "Trivandrum"]),
    "Maldives": ("MV", "en", ["Male", "Hulhumale", "Addu City"]),
    "United Arab Emirates": ("AE", "en", ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Al Ain"]),
    "Qatar": ("QA", "en", ["Doha", "Al Wakrah", "Al Rayyan"]),
    "Saudi Arabia": ("SA", "en", ["Riyadh", "Jeddah", "Dammam", "Khobar", "Mecca"]),
    "Oman": ("OM", "en", ["Muscat", "Salalah", "Sohar"]),
    "Kuwait": ("KW", "en", ["Kuwait City", "Hawalli", "Salmiya"]),
    "Bangladesh": ("BD", "en", ["Dhaka", "Chittagong", "Sylhet", "Khulna"]),
    "Pakistan": ("PK", "en", ["Karachi", "Lahore", "Islamabad", "Faisalabad"]),
    "Nepal": ("NP", "en", ["Kathmandu", "Pokhara", "Lalitpur"]),
    "Malaysia": ("MY", "en", ["Kuala Lumpur", "Penang", "Johor Bahru", "Ipoh", "Kota Kinabalu"]),
    "Singapore": ("SG", "en", ["Singapore"]),
    "Philippines": ("PH", "en", ["Manila", "Cebu City", "Davao City", "Quezon City"]),
    "Indonesia": ("ID", "en", ["Jakarta", "Bali Denpasar", "Surabaya", "Bandung"]),
    "Thailand": ("TH", "en", ["Bangkok", "Chiang Mai", "Phuket", "Pattaya"]),
    "Vietnam": ("VN", "en", ["Ho Chi Minh City", "Hanoi", "Da Nang"]),
    "Australia": ("AU", "en", ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast"]),
    "New Zealand": ("NZ", "en", ["Auckland", "Wellington", "Christchurch", "Hamilton"]),
    "United Kingdom": ("GB", "en", ["London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Leicester"]),
    "Ireland": ("IE", "en", ["Dublin", "Cork", "Galway"]),
    "United States": ("US", "en", ["Houston", "Dallas", "Phoenix", "Atlanta", "Miami", "Chicago",
                                   "Los Angeles", "New York"]),
    "Canada": ("CA", "en", ["Toronto", "Mississauga", "Brampton", "Vancouver", "Calgary", "Montreal"]),
    "Italy": ("IT", "en", ["Rome", "Milan", "Naples", "Turin", "Palermo"]),
    "Spain": ("ES", "en", ["Madrid", "Barcelona", "Valencia", "Seville"]),
    "Germany": ("DE", "en", ["Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt"]),
    "France": ("FR", "en", ["Paris", "Marseille", "Lyon", "Toulouse"]),
    "Nigeria": ("NG", "en", ["Lagos", "Abuja", "Ibadan", "Port Harcourt"]),
    "Kenya": ("KE", "en", ["Nairobi", "Mombasa", "Kisumu"]),
    "South Africa": ("ZA", "en", ["Johannesburg", "Cape Town", "Durban", "Pretoria"]),
    "Other (type below)": ("", "en", []),
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


def load_cfg():
    """Same settings the main app uses (settings.json + environment variables)."""
    import leadfinder as lf
    cfg = lf.load_settings(HERE)
    try:
        with open(SETTINGS, encoding="utf-8") as f:
            cfg.update({k: v for k, v in json.load(f).items() if v})
    except Exception:
        pass
    return cfg


def save_cfg_keys(**kw):
    cur = {}
    try:
        with open(SETTINGS, encoding="utf-8") as f:
            cur = json.load(f)
    except Exception:
        pass
    cur.update(kw)
    with open(SETTINGS, "w", encoding="utf-8") as f:
        json.dump(cur, f, indent=2)


CSS = """
<style>
.block-container{padding-top:1.4rem;max-width:1320px}
.gh{display:flex;align-items:center;gap:18px;padding:22px 26px;border-radius:22px;margin-bottom:8px;
    background:linear-gradient(120deg,#0f172a 0%,#1e1b4b 55%,#3b0764 100%);border:1px solid #312e81}
.gh .ic{font-size:2.6rem;background:#f9731622;border-radius:18px;width:68px;height:68px;display:flex;
        align-items:center;justify-content:center}
.gh h1{font-size:2rem;margin:0;color:#fff;line-height:1.15}
.gh p{margin:4px 0 0;color:#c7d2fe}
.step{display:flex;align-items:center;gap:12px;margin:26px 0 8px}
.step b{width:34px;height:34px;border-radius:50%;background:#f97316;color:#fff;display:flex;
        align-items:center;justify-content:center;font-size:1.05rem}
.step span{font-size:1.25rem;font-weight:700}
.step small{color:#94a3b8;font-weight:400;font-size:.9rem;margin-left:6px}
.kpi{background:linear-gradient(160deg,#111a2e,#0b1222);border:1px solid #1e293b;border-radius:18px;
     padding:16px 18px;height:100%}
.kpi .l{color:#94a3b8;font-size:.82rem;text-transform:uppercase;letter-spacing:.06em}
.kpi .n{font-size:2rem;font-weight:800;color:#fdba74;line-height:1.2;margin-top:4px}
.kpi .s{color:#64748b;font-size:.8rem}
.chip{display:inline-block;padding:3px 10px;border-radius:999px;font-size:.8rem;margin:0 6px 4px 0}
.ok{background:#14532d;color:#bbf7d0}.no{background:#3f1d1d;color:#fecaca}
.note{background:#1e293b;border-left:4px solid #f97316;padding:10px 14px;border-radius:8px;color:#cbd5e1;
      font-size:.88rem}
button[data-testid="stBaseButton-primary"]{min-height:3.4rem;border-radius:14px}
button[data-testid="stBaseButton-primary"] p{font-size:1.2rem!important;font-weight:800}
</style>"""


def header(st, icon, title, sub):
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f'<div class="gh"><div class="ic">{icon}</div><div><h1>{title}</h1><p>{sub}</p></div></div>',
                unsafe_allow_html=True)


def kpi(col, label, value, sub=""):
    col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="n">{value}</div>'
                 f'<div class="s">{sub}</div></div>', unsafe_allow_html=True)


def step(st, n, title, sub=""):
    st.markdown(f'<div class="step"><b>{n}</b><span>{title}<small>{sub}</small></span></div>',
                unsafe_allow_html=True)


def link(st, page, label, **kw):
    """st.page_link that never crashes (eg. when a page is opened on its own)."""
    try:
        st.page_link(page, label=label, **kw)
    except Exception:
        pass


def password_gate(st):
    """Only active when APP_PASSWORD is set (cloud hosting). Locally nothing changes."""
    pw = os.environ.get("APP_PASSWORD", "")
    if not pw or st.session_state.get("_ok_pw"):
        return
    st.markdown("### 🔒 Ravion Lead Finder")
    x = st.text_input("Password", type="password")
    if x and x == pw:
        st.session_state["_ok_pw"] = True
        st.rerun()
    elif x:
        st.error("Password වැරදියි")
    st.stop()
