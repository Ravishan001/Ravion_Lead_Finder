#!/usr/bin/env python3
"""
Ravion Studio - Gym Lead Finder (worldwide)
==========================================
Finds gyms / fitness studios that have NO member system yet (no website, or only a
Facebook/Instagram page, or a basic website with no booking/member software) so you can
pitch them RepFlint.

Uses the same official Google Places API (New) key as leadfinder.py. Nothing in
leadfinder.py / app.py is changed - this module only *imports* helpers from it.

What Google gives us : name, phone, website, rating, review count, opening hours, price
                       level, location.
What it does NOT give: member count, coach count. We ESTIMATE them from review count
                       (clearly marked "est.") - confirm on the first call/visit.

CLI:
  python gymfinder.py --source demo
  python gymfinder.py --country "Sri Lanka" --cities Kuliyapitiya Kurunegala --radius 8
  python gymfinder.py --country "United Kingdom" --cities Leicester --types gym crossfit --max-calls 12
"""
import argparse, concurrent.futures as cf, datetime as dt, json, math, os, random, re, sys, time
from urllib.parse import urlparse, quote

import leadfinder as lf

try:
    import requests
except ImportError:
    requests = None

HERE = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(HERE, "gym_leads.json")
GEO_CACHE = os.path.join(HERE, "geo_cache.json")

# key: (Google search words, label)
GYM_TYPES = {
    "gym":          ("gym", "Gym"),
    "fitness":      ("fitness center", "Fitness center"),
    "crossfit":     ("crossfit box functional training", "CrossFit / Functional"),
    "ladies":       ("ladies gym women only fitness", "Ladies gym"),
    "martial_arts": ("martial arts MMA boxing gym", "Martial arts / Boxing"),
    "yoga":         ("yoga studio", "Yoga studio"),
    "pilates":      ("pilates studio", "Pilates studio"),
}
DEFAULT_TYPES = ["gym", "fitness"]

# Big chains already run corporate systems - not RepFlint buyers.
CHAINS = ["anytime fitness", "gold's gym", "golds gym", "planet fitness", "snap fitness", "puregym",
          "pure gym", "f45", "orangetheory", "crunch fitness", "24 hour fitness", "la fitness",
          "equinox", "the gym group", "fitness first", "cult.fit", "cultfit", "fitness time",
          "gymnation", "jetts", "world gym", "virgin active", "basic-fit", "basic fit", "mcfit",
          "clever fit", "smart fit", "bodytech", "celebrity fitness", "power world", "powerworld",
          "club pilates", "barry's", "goodlife fitness", "energie fitness", "david lloyd",
          "nuffield health", "true fitness", "fitness 24 seven", "evolve fit", "anytime"]

# Gym management software - if a site links to one of these, they already have a system.
SYSTEM_HOSTS = {
    "mindbodyonline.com": "Mindbody", "mindbody.io": "Mindbody", "glofox.com": "Glofox",
    "gymmaster.com": "GymMaster", "clubready.com": "ClubReady", "wodify.com": "Wodify",
    "pushpress.com": "PushPress", "zenplanner.com": "Zen Planner", "teamup.com": "TeamUp",
    "gymdesk.com": "Gymdesk", "virtuagym.com": "Virtuagym", "exercise.com": "Exercise.com",
    "perfectgym.com": "PerfectGym", "trainerize.com": "Trainerize", "wellnessliving.com": "WellnessLiving",
    "momence.com": "Momence", "marianatek.com": "Mariana Tek", "bsport.io": "bsport",
    "clubworx.com": "Clubworx", "ezfacility.com": "EZFacility", "eversports": "Eversports",
    "gymcatch.com": "GymCatch", "legitfit.com": "LegitFit", "abcfitness.com": "ABC Fitness",
    "daxko.com": "Daxko", "clubautomation.com": "Club Automation", "arketa": "Arketa",
    "fitogram": "Fitogram", "sportsnow": "SportsNow", "gymflow": "Gymflow", "hapana": "Hapana",
    "fisikal": "Fisikal", "gymsync": "GymSync", "repflint": "RepFlint (yours!)",
}
SYSTEM_WORDS = ["member login", "members login", "member portal", "members area", "book a class",
                "book class", "book now", "class timetable", "join online", "sign up online",
                "download our app", "apps.apple.com", "play.google.com/store"]

SYS_LABEL = {
    "none": "No website", "social_only": "FB/IG only", "site_no_system": "Website, no system",
    "site_unchecked": "Website (not checked)", "site_maybe_system": "Website, maybe system",
    "has_system": "Has system", "chain": "Chain",
}
SYS_POINTS = {"none": 35, "social_only": 33, "site_no_system": 22, "site_unchecked": 14,
              "site_maybe_system": 6, "has_system": 0, "chain": 0}
DEFAULT_TARGETS = ["none", "social_only", "site_no_system", "site_unchecked"]
STATUSES = lf.STATUSES  # New, Messaged, Replied, Meeting, Won, Not interested

PITCH = {
    "en": ("Hi {name} team 👋 I'm Ravishan from Ravion Studio. I noticed {reason}. "
           "We built RepFlint - a simple gym app: your members get their own app (workout plans, progress) "
           "and you get one dashboard for memberships, payments, attendance and coaches. "
           "Can I send you a 2-minute demo?"),
    "si": ("ආයුබෝවන් {name} team 👋 මම Ravishan, Ravion Studio එකෙන්. {reason_si}. "
           "අපි RepFlint කියලා gym app එකක් හැදුවා - members ලට workout plans, progress බලන්න app එකක්, "
           "ඔයාලට memberships, payments, attendance, coaches ඔක්කොම manage කරන්න එක dashboard එකක්. "
           "විනාඩි 2ක demo එකක් එවන්නද?"),
}
REASON = {
    "none": ("{name} doesn't have a website or member app yet", "ඔයාලගේ gym එකට තවම website එකක් හරි member app එකක් හරි නෑ කියලා දැක්කා"),
    "social_only": ("{name} runs mainly on Facebook/Instagram", "ඔයාලා වැඩිපුරම Facebook/Instagram එකෙන් වැඩ කරන්නේ කියලා දැක්කා"),
    "site_no_system": ("{name} has a website but no member app or online system", "ඔයාලට website එකක් තිබුණට member app එකක්/online system එකක් නෑ වගේ"),
}

_LOGGER = print
_PROGRESS = None


def log(*a):
    _LOGGER(" ".join(str(x) for x in a))


def progress(d, t, txt=""):
    if _PROGRESS:
        _PROGRESS(d, t, txt)


# --------------------------------------------------------------------------- helpers
def haversine(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180
    h = (math.sin((la2 - la1) * p / 2) ** 2 +
         math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(h))


def _load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def is_chain(name):
    n = name.lower()
    return any(c in n for c in CHAINS)


def phone_info(national, international, region):
    """(display, is_mobile True/False/None, whatsapp digits)."""
    if region == "LK":
        disp, mob, wa = lf.normalize_phone(national, international)
        return disp, mob, (wa.rsplit("/", 1)[-1] if wa else "")
    digits = re.sub(r"\D", "", international or "")
    disp = international or national or ""
    return disp, None, (digits if len(digits) >= 8 else "")


def site_status(url):
    st = lf.website_status(url)
    if st == "none":
        return "none", ""
    host = (urlparse(url if "://" in url else "http://" + url).hostname or "").lower()
    for h, nm in SYSTEM_HOSTS.items():
        if h in host:
            return "has_system", nm
    return ("social_only", "") if st == "social_only" else ("site_unchecked", "")


def deep_check(url):
    """Opens the gym's own homepage once and looks for gym software / member login."""
    try:
        r = requests.get(url, timeout=7, headers={"User-Agent": "Mozilla/5.0 (RavionLeadFinder)"},
                         stream=True)
        html = r.raw.read(400_000, decode_content=True).decode("utf-8", "ignore").lower()
    except Exception:
        return "site_unchecked", ""
    for h, nm in SYSTEM_HOSTS.items():
        if h in html:
            return "has_system", nm
    if any(w in html for w in SYSTEM_WORDS):
        return "site_maybe_system", ""
    return "site_no_system", ""


def open_hours(h):
    days, close = lf.parse_hours(h)
    early = None
    if h:
        hrs = [p.get("open", {}).get("hour") for p in h.get("periods", []) if "hour" in p.get("open", {})]
        early = min(hrs) if hrs else None
    return days, close, early


def estimate_size(reviews):
    """Rough, honest estimate - Google has no member count. Reviews pile up over the years
    (old members too), so the curve is sub-linear: active members ≈ 3 × reviews^0.8, shown as
    a range (0.6× – 1.5×). 400 reviews ≈ 220–540 members, 40 reviews ≈ 35–85."""
    r = reviews or 0
    if not r:
        return None, None, "Unknown", ""
    mid = 3 * r ** 0.8
    lo, hi = max(10, round(mid * .6)), max(30, round(mid * 1.5))
    size = ("Small" if mid < 60 else "Medium" if mid < 180 else "Large" if mid < 400 else "Very large")
    c_lo = max(1, round(lo / 60))          # ~1 coach per 40-60 active members
    c_hi = max(c_lo + 1, round(hi / 40))
    return lo, hi, size, f"{c_lo}–{c_hi}"


def score_gym(g):
    s, why = SYS_POINTS.get(g["system"], 0), []
    why.append(SYS_LABEL[g["system"]] + (f" ({g['system_name']})" if g.get("system_name") else ""))
    r = g.get("reviews") or 0
    if r:
        s += min(25, int(math.sqrt(r) * 2.2))
        if r >= 50:
            why.append(f"busy ({r} reviews)")
    rt = g.get("rating") or 0
    if rt >= 4.2:
        s += 8; why.append(f"rating {rt}")
    elif rt >= 4.0:
        s += 5
    if g["is_mobile"]:
        s += 10; why.append("WhatsApp number")
    elif g["is_mobile"] is None and g["phone"]:
        s += 7
    elif g["phone"]:
        s += 4
    if g.get("days_open") == 7:
        s += 4; why.append("open 7 days")
    if (g.get("close_hour") or 0) >= 21:
        s += 3
    if g.get("open_early") is not None and g["open_early"] <= 6:
        s += 3; why.append("opens early")
    if g["size"] in ("Medium", "Large", "Very large"):
        s += 4
    s = min(100, s)
    pri = "🔥 Hot" if s >= 75 else ("Warm" if s >= 55 else "Cold")
    return s, pri, ", ".join(why)


def pitch_for(g, lang="en", templates=None):
    t = (templates or {}).get(lang) or PITCH[lang]
    key = g["system"] if g["system"] in REASON else "site_no_system"
    en, si = REASON[key]
    return t.format(name=g["name"], city=g["city"], reason=en.format(name=g["name"]), reason_si=si)


def make_gym(gtype, city, country, region, center, source, pid, name, address, national, international,
             website, rating, reviews, maps_url, status="OPERATIONAL", price_level="", hours=None,
             lat=None, lon=None):
    phone, mob, wa = phone_info(national, international, region)
    system, sysname = site_status(website)
    if is_chain(name):
        system = "chain"
    days, close, early = open_hours(hours)
    lo, hi, size, coaches = estimate_size(reviews)
    g = dict(id=f"{source}:{pid}", name=name, gym_type=gtype, type_label=GYM_TYPES.get(gtype, ("", gtype))[1],
             city=city, country=country, region=region, address=address, phone=phone, is_mobile=mob,
             wa_digits=wa, website=website or "", system=system, system_name=sysname,
             website_status=lf.website_status(website), rating=rating, reviews=reviews or 0,
             price_level=price_level or "", days_open=days, close_hour=close, open_early=early,
             lat=lat, lon=lon, maps=maps_url, status=status, source=source,
             members_low=lo, members_high=hi, size=size, coaches=coaches)
    g["dist_km"] = round(haversine(center, (lat, lon)), 1) if (center and lat is not None) else None
    return g


def finalize(g, lang, templates):
    g["score"], g["priority"], g["why"] = score_gym(g)
    g["pitch"] = pitch_for(g, lang, templates)
    g["whatsapp"] = f"https://wa.me/{g['wa_digits']}?text={quote(g['pitch'])}" if g["wa_digits"] else ""
    g["members_est"] = f"{g['members_low']}–{g['members_high']}" if g["members_low"] else "?"
    return g


# --------------------------------------------------------------------------- Google
def geocode(city, country, api_key, cache):
    key = f"{city}|{country}".lower()
    if key in cache:
        return tuple(cache[key]), 0
    if country == "Sri Lanka" and city in lf.CITIES:
        return lf.CITIES[city], 0
    r = requests.post("https://places.googleapis.com/v1/places:searchText",
                      headers={"Content-Type": "application/json", "X-Goog-Api-Key": api_key,
                               "X-Goog-FieldMask": "places.location,places.formattedAddress"},
                      json={"textQuery": f"{city}, {country}", "pageSize": 1}, timeout=30)
    if r.status_code != 200:
        if r.status_code in (400, 401, 403):
            raise RuntimeError(f"Google API error {r.status_code}: {r.text[:300]}")
        return None, 1
    p = (r.json().get("places") or [{}])[0].get("location")
    if not p:
        return None, 1
    cache[key] = [p["latitude"], p["longitude"]]
    _save_json(GEO_CACHE, cache)
    return (p["latitude"], p["longitude"]), 1


def google_gyms(types, cities, country, region, api_key, max_calls, pages, radius_km):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": api_key,
               "X-Goog-FieldMask": lf.GOOGLE_FIELDS}
    cache = _load_json(GEO_CACHE, {})
    calls, out, total = 0, [], len(types) * len(cities) * pages
    for city in cities:
        center, c = geocode(city, country, api_key, cache)
        calls += c
        if not center:
            log(f"  ! {city}: location not found, skipping"); continue
        for t in types:
            token = None
            for _ in range(pages):
                if calls >= max_calls:
                    log(f"  ! max calls {max_calls} reached, stopping.")
                    return out, calls
                body = {"textQuery": f"{GYM_TYPES[t][0]} in {city}, {country}", "languageCode": "en",
                        "pageSize": 20, "locationBias": {"circle": {
                            "center": {"latitude": center[0], "longitude": center[1]},
                            "radius": float(min(50000, radius_km * 1000))}}}
                if region:
                    body["regionCode"] = region
                if token:
                    body["pageToken"] = token
                r = requests.post(url, headers=headers, json=body, timeout=30)
                calls += 1
                if r.status_code != 200:
                    log(f"  ! Google error {r.status_code}: {r.text[:300]}")
                    if r.status_code in (400, 401, 403):
                        raise RuntimeError(f"Google API error {r.status_code}: {r.text[:300]}")
                    break
                data = r.json()
                places = data.get("places", [])
                for p in places:
                    loc = p.get("location") or {}
                    out.append(make_gym(
                        t, city, country, region, center, "google", p.get("id"),
                        p.get("displayName", {}).get("text", ""), p.get("formattedAddress", ""),
                        p.get("nationalPhoneNumber", ""), p.get("internationalPhoneNumber", ""),
                        p.get("websiteUri", ""), p.get("rating"), p.get("userRatingCount"),
                        p.get("googleMapsUri", ""), p.get("businessStatus", "OPERATIONAL"),
                        p.get("priceLevel", ""), p.get("regularOpeningHours"),
                        loc.get("latitude"), loc.get("longitude")))
                log(f"  {t:13s} {city:16s} → {len(places)} places")
                progress(calls, total, f"{t} · {city}")
                token = data.get("nextPageToken")
                if not token:
                    break
                time.sleep(2)
    return out, calls


def demo_gyms(types, cities, country, region):
    """FAKE gyms for testing the screens. Not real leads."""
    rnd = random.Random(11)
    names = ["Iron Temple", "Muscle Factory", "Beast Mode Gym", "Fit Zone", "Power House", "Body Shape",
             "Titan Fitness", "Alpha Gym", "Flex Lab", "Pulse Fitness", "Core Strength", "Spartan Gym"]
    out = []
    for city in cities:
        center = lf.CITIES.get(city) or (7 + rnd.random(), 80 + rnd.random())
        for t in types:
            for i, n in enumerate(rnd.sample(names, 5)):
                web = rnd.choice(["", "", "https://facebook.com/demo", "https://instagram.com/demo",
                                  "https://demo-gym.com", "https://demo.glofox.com/x"])
                rv = rnd.choice([0, 4, 15, 38, 70, 120, 240, 410])
                mob = rnd.random() < .75
                ph = f"07{rnd.randint(0, 8)}{rnd.randint(1000000, 9999999)}" if mob else f"037{rnd.randint(1000000, 9999999)}"
                intl = "+94 " + ph[1:] if region == "LK" else f"+{rnd.randint(30, 99)} {rnd.randint(10**8, 10**9)}"
                op, cl = rnd.choice([5, 6, 7]), rnd.choice([20, 21, 22])
                hrs = {"periods": [{"open": {"day": d, "hour": op}, "close": {"day": d, "hour": cl}}
                                   for d in range(rnd.choice([6, 7]))]}
                lat = center[0] + rnd.uniform(-.06, .06); lon = center[1] + rnd.uniform(-.06, .06)
                out.append(make_gym(t, city, country, region, center, "demo", f"{t}-{city}-{i}",
                                    f"[DEMO] {n} {city}", f"No {i + 3}, Main Road, {city}", ph, intl, web,
                                    round(rnd.uniform(3.7, 4.9), 1) if rv else None, rv,
                                    "https://maps.google.com", price_level="", hours=hrs, lat=lat, lon=lon))
    return out


# --------------------------------------------------------------------------- local database (dashboard)
USER_FIELDS = ("status", "contacted_on", "next_follow", "notes", "first_found")


def load_db():
    return _load_json(DB_FILE, {"leads": {}})


def save_db(db):
    db["updated"] = dt.datetime.now().isoformat(timespec="seconds")
    _save_json(DB_FILE, db)


def merge_db(leads):
    db = load_db()
    today = dt.date.today().isoformat()
    added = updated = 0
    for g in leads:
        old = db["leads"].get(g["id"])
        rec = dict(g)
        if old:
            for k in USER_FIELDS:
                rec[k] = old.get(k, "")
            updated += 1
        else:
            rec.update(status="New", contacted_on="", next_follow="", notes="", first_found=today)
            added += 1
        rec["last_updated"] = today
        db["leads"][g["id"]] = rec
    save_db(db)
    return added, updated


# --------------------------------------------------------------------------- Google Sheet ("Gym Leads" tab)
SHEET_COLS = [("Priority", "priority"), ("Gym", "name"), ("Status", "status"),
              ("Contacted on", "contacted_on"), ("Next follow-up", "next_follow"), ("Notes", "notes"),
              ("Score", "score"), ("Tier", "tier"), ("Est. members", "members_est"),
              ("Est. coaches", "coaches"), ("Size", "size"), ("System", "system_label"),
              ("Type", "type_label"), ("City", "city"), ("Country", "country"), ("Km from city", "dist_km"),
              ("Phone", "phone"), ("WhatsApp", "whatsapp"), ("Website", "website"), ("Rating", "rating"),
              ("Reviews", "reviews"), ("Why", "why"), ("Address", "address"), ("Google Maps", "maps"),
              ("First found", "first_found"), ("Last updated", "last_updated"), ("ID", "id")]


def push_sheet(sheet_id, sa_file, tab="Gym Leads"):
    """Writes the whole local gym database to one tab. The app dashboard is the place you edit
    Status/Notes; this tab is a copy you can open on your phone."""
    import gspread
    from gspread.utils import ValueInputOption
    if not os.path.exists(sa_file):
        raise RuntimeError(f"Service account file එක නෑ: {sa_file}")
    leads = sorted(load_db()["leads"].values(), key=lambda g: -(g.get("score") or 0))
    sh = gspread.service_account(filename=sa_file).open_by_key(sheet_id)
    titles = [w.title for w in sh.worksheets()]
    fresh = tab not in titles
    ws = sh.add_worksheet(tab, rows=max(200, len(leads) + 20), cols=len(SHEET_COLS)) if fresh else sh.worksheet(tab)
    rows = [[h for h, _ in SHEET_COLS]]
    for g in leads:
        g = dict(g, system_label=SYS_LABEL.get(g.get("system"), g.get("system")))
        rows.append(["" if g.get(k) is None else g.get(k) for _, k in SHEET_COLS])
    if ws.row_count < len(rows) + 10:
        ws.resize(rows=len(rows) + 50)
    ws.clear()
    ws.update(rows, "A1", value_input_option=ValueInputOption.raw)
    if fresh:
        ws.format("A1:AA1", {"textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                             "backgroundColor": {"red": .23, "green": .03, "blue": .39}})
        ws.freeze(rows=1, cols=2)
    log(f"  Google Sheet '{tab}': {len(leads)} gyms written")
    return len(leads)


# --------------------------------------------------------------------------- run
def run_gym_search(types, cities, country="Sri Lanka", region="LK", source="google", api_key="",
                   max_calls=30, pages=2, radius_km=10, targets=DEFAULT_TARGETS, exclude_chains=True,
                   min_reviews=0, min_score=50, check_websites=True, lang="en", templates=None,
                   out=os.path.join(HERE, "output"), sheet_id="", service_account="", sync=False):
    bad = [t for t in types if t not in GYM_TYPES]
    if bad:
        raise ValueError(f"Unknown gym types: {bad}")
    calls = 0
    if source == "google":
        if requests is None:
            raise RuntimeError("pip install -r requirements.txt")
        if not api_key:
            raise RuntimeError("Google API key නෑ (Settings / GOOGLE_MAPS_API_KEY)")
        raw, calls = google_gyms(types, cities, country, region, api_key, max_calls, min(pages, 3), radius_km)
    else:
        raw = demo_gyms(types, cities, country, region)

    uniq = {}
    for g in raw:
        uniq.setdefault(g["id"], g)
    found = list(uniq.values())
    far = [g for g in found if g["dist_km"] is not None and g["dist_km"] > radius_km]
    near = [g for g in found if not (g["dist_km"] is not None and g["dist_km"] > radius_km)]
    log(f"Found {len(found)} places · {len(far)} dropped (more than {radius_km} km away)")

    if check_websites and source == "google":
        todo = [g for g in near if g["system"] == "site_unchecked"]
        if todo:
            log(f"Checking {len(todo)} gym websites for member systems…")
            with cf.ThreadPoolExecutor(8) as ex:
                for g, (s, nm) in zip(todo, ex.map(lambda x: deep_check(x["website"]), todo)):
                    g["system"], g["system_name"] = s, nm
    elif check_websites:  # demo: pretend
        for g in near:
            if g["system"] == "site_unchecked":
                g["system"] = random.Random(g["id"]).choice(["site_no_system", "site_maybe_system"])

    lf.add_reach(near)
    for g in near:
        finalize(g, lang, templates)
    keep_sys = set(targets) | ({"chain"} if not exclude_chains else set())
    kept = [g for g in near if g["status"] == "OPERATIONAL" and g["system"] in keep_sys
            and (g["phone"] or g["system"] == "social_only")
            and g["reviews"] >= min_reviews and g["score"] >= min_score]
    kept.sort(key=lambda g: (-g["score"], -(g["reviews"] or 0)))

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(out, exist_ok=True)
    csv_path = os.path.join(out, f"gyms_{stamp}.csv")
    xlsx_path = os.path.join(out, f"gyms_{stamp}.xlsx")
    cols = [(h, k) for h, k in SHEET_COLS if k not in USER_FIELDS and k != "last_updated"]
    rows = []
    for g in kept:
        x = dict(g, system_label=SYS_LABEL[g["system"]])
        rows.append({h: ("" if x.get(k) is None else x.get(k)) for h, k in cols})
    import csv
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[h for h, _ in cols])
        w.writeheader(); w.writerows(rows)
    try:
        import pandas as pd
        pd.DataFrame(rows).to_excel(xlsx_path, index=False)
    except Exception:
        xlsx_path = None

    added, updated = merge_db(kept)
    log(f"Kept {len(kept)} gym leads → dashboard: +{added} new, {updated} updated")
    sheet = "off"
    if sync and sheet_id and kept:
        try:
            push_sheet(sheet_id, service_account)
            sheet = "ok"
        except Exception as e:
            sheet = f"error: {e}"
            log(f"  ! Google Sheet sync failed: {e}")
    sys_counts = {}
    for g in near:
        sys_counts[g["system"]] = sys_counts.get(g["system"], 0) + 1
    return dict(kept=kept, found=len(found), far=len(far), near=len(near), calls=calls, csv=csv_path,
                xlsx=xlsx_path, added=added, updated=updated, sheet=sheet, sys_counts=sys_counts)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    cfg = lf.load_settings(HERE)
    ap = argparse.ArgumentParser(description="Ravion Gym Lead Finder")
    ap.add_argument("--source", choices=["google", "demo"], default="google")
    ap.add_argument("--country", default="Sri Lanka")
    ap.add_argument("--region", default="", help="2-letter code, eg LK, IN, GB (auto for known countries)")
    ap.add_argument("--cities", nargs="+", default=["Kuliyapitiya", "Kurunegala"])
    ap.add_argument("--types", nargs="+", default=DEFAULT_TYPES, help="keys: " + ", ".join(GYM_TYPES))
    ap.add_argument("--radius", type=float, default=10, help="km around each city")
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--max-calls", type=int, default=30)
    ap.add_argument("--min-score", type=int, default=50)
    ap.add_argument("--lang", choices=["en", "si"], default="en")
    ap.add_argument("--no-check", action="store_true", help="don't open gym websites")
    ap.add_argument("--sheet", action="store_true", help="also write the 'Gym Leads' tab")
    a = ap.parse_args()
    try:
        from gym_common import COUNTRIES
        region = a.region or COUNTRIES.get(a.country, ("",))[0]
    except Exception:
        region = a.region
    res = run_gym_search(a.types, a.cities, a.country, region, a.source, cfg["api_key"], a.max_calls,
                         a.pages, a.radius, min_score=a.min_score, check_websites=not a.no_check, lang=a.lang,
                         sheet_id=cfg["sheet_id"], service_account=cfg["service_account"], sync=a.sheet)
    print(f"\nGoogle calls: {res['calls']}  ·  saved {res['csv']}")
    for g in res["kept"][:15]:
        print(f"  {g['priority']:7s} {g['score']:3d}  {g['name'][:32]:32s} {g['city']:14s} "
              f"{g['members_est']:>9s} members  {SYS_LABEL[g['system']]}")


if __name__ == "__main__":
    main()
