#!/usr/bin/env python3
"""
Ravion Studio - Lead Finder (Sri Lanka)
=======================================
Finds Sri Lankan businesses that have NO real website (or only a Facebook/Instagram page)
and are a good fit for AI agents (WhatsApp AI assistant, booking bot, website).

Sources (official / legal):
  * google  - Google Places API (New) Text Search  (needs API key, 1,000 free calls/month)
  * osm     - OpenStreetMap Overpass API           (free, no key, smaller coverage)
  * demo    - built-in fake sample data to test the tool without internet

Output: an Excel file (sorted by lead score) + CSV, with WhatsApp links and pitch ideas.

Usage examples:
  python leadfinder.py --source demo
  python leadfinder.py --source google --cities Kuliyapitiya Kurunegala --categories salon dental_clinic
  python leadfinder.py --source google --max-calls 100
  python leadfinder.py --source osm --cities Colombo Kandy
"""
import argparse, csv, datetime as dt, json, math, os, re, sys, time
from urllib.parse import urlparse, quote

try:
    import requests
except ImportError:
    requests = None

# --------------------------------------------------------------------------- config
CITIES = {  # name: (lat, lon)  - used for OSM search radius; Google uses the name
    "Colombo": (6.9271, 79.8612), "Dehiwala": (6.8511, 79.8659), "Maharagama": (6.8480, 79.9265),
    "Nugegoda": (6.8649, 79.8997), "Gampaha": (7.0917, 79.9999), "Negombo": (7.2083, 79.8358),
    "Kandy": (7.2906, 80.6337), "Galle": (6.0535, 80.2210), "Matara": (5.9549, 80.5550),
    "Kurunegala": (7.4863, 80.3647), "Kuliyapitiya": (7.4688, 80.0401), "Chilaw": (7.5758, 79.7953),
    "Puttalam": (8.0362, 79.8283), "Anuradhapura": (8.3114, 80.4037), "Jaffna": (9.6615, 80.0255),
    "Ratnapura": (6.6828, 80.3992), "Badulla": (6.9934, 81.0550), "Nuwara Eliya": (6.9497, 80.7891),
    "Kalutara": (6.5854, 79.9607), "Panadura": (6.7106, 79.9074), "Kegalle": (7.2513, 80.3464),
    "Trincomalee": (8.5874, 81.2152), "Batticaloa": (7.7310, 81.6747), "Hambantota": (6.1241, 81.1185),
}

# key: (google search words, OSM tag filters, fit weight 0-15, pitch idea in Sinhala)
CATEGORIES = {
    "salon":         ("hair salon", ['shop=hairdresser'], 15,
                      "WhatsApp AI booking assistant + online booking page (branch/stylist/time)"),
    "beauty_salon":  ("beauty salon bridal", ['shop=beauty'], 15,
                      "Bridal/beauty inquiries වලට AI auto-reply + package price list + booking"),
    "barber":        ("barber shop", ['shop=hairdresser'], 12,
                      "Queue/booking AI assistant - customer ලට waiting නැතුව slot එකක්"),
    "dental_clinic": ("dental clinic", ['amenity=dentist', 'healthcare=dentist'], 15,
                      "Appointment booking + reminder AI (no-shows අඩු කරනවා)"),
    "medical_clinic":("medical center channeling", ['amenity=clinic', 'amenity=doctors'], 13,
                      "Channeling booking AI + doctor availability WhatsApp එකෙන්"),
    "tuition":       ("tuition class", ['amenity=school', 'office=educational_institution'], 15,
                      "Class times/fees AI assistant + student registration + payment reminders"),
    "guest_house":   ("guest house", ['tourism=guest_house'], 15,
                      "Tourists ලට English 24/7 AI reply + room availability + booking site"),
    "hotel":         ("hotel", ['tourism=hotel'], 12,
                      "Booking.com commission නැතුව direct booking site + AI concierge"),
    "restaurant":    ("restaurant", ['amenity=restaurant'], 10,
                      "Menu + order/table booking WhatsApp AI"),
    "cafe":          ("cafe", ['amenity=cafe'], 8,
                      "Menu + orders + events WhatsApp AI"),
    "gym":           ("gym fitness center", ['leisure=fitness_centre'], 10,
                      "Membership inquiries/fees AI + class schedule"),
    "spa":           ("spa ayurveda", ['shop=massage', 'leisure=spa'], 13,
                      "Treatment booking AI (English + Sinhala) + package list"),
    "driving_school":("driving school", ['amenity=driving_school'], 12,
                      "Lesson booking + license process FAQ AI"),
    "photography":   ("wedding photography studio", ['craft=photographer', 'shop=photo'], 10,
                      "Package inquiries AI + portfolio site"),
    "vehicle_service":("vehicle service center", ['shop=car_repair'], 11,
                      "Service booking AI + 'vehicle ready' WhatsApp notifications"),
    "pharmacy":      ("pharmacy", ['amenity=pharmacy'], 7,
                      "Medicine availability/order WhatsApp AI"),
    "cake_shop":     ("cake shop custom cakes", ['shop=pastry', 'shop=bakery'], 13,
                      "Cake orders WhatsApp AI - design, size, price, delivery date auto ගන්නවා"),
    "veterinary":    ("veterinary clinic pet", ['amenity=veterinary'], 12,
                      "Pet appointment booking + vaccination reminders AI"),
    "optical":       ("optical shop eye test", ['shop=optician'], 10,
                      "Eye test booking + frame/lens price inquiries AI"),
    "event_planner": ("wedding planner decoration", ['shop=party', 'craft=caterer'], 12,
                      "Package inquiries 24/7 AI + date availability + quote request form"),
    "physio":        ("physiotherapy clinic", ['healthcare=physiotherapist'], 12,
                      "Session booking + follow-up reminders AI"),
}
DEFAULT_CATEGORIES = ["salon", "beauty_salon", "dental_clinic", "tuition", "guest_house", "spa"]
DEFAULT_CITIES = ["Kuliyapitiya", "Kurunegala", "Negombo", "Gampaha"]

SOCIAL_HOSTS = ("facebook.com", "fb.com", "fb.me", "instagram.com", "linktr.ee", "wa.me",
                "whatsapp.com", "tiktok.com", "youtube.com", "business.site", "sites.google.com")

GOOGLE_FIELDS = ",".join("places." + f for f in [
    "id", "displayName", "formattedAddress", "nationalPhoneNumber", "internationalPhoneNumber",
    "websiteUri", "rating", "userRatingCount", "businessStatus", "googleMapsUri",
    "primaryTypeDisplayName", "location", "priceLevel", "regularOpeningHours"]) + ",nextPageToken"
PRICE_POINTS = {"PRICE_LEVEL_FREE": 0, "PRICE_LEVEL_INEXPENSIVE": 3, "PRICE_LEVEL_MODERATE": 8,
                "PRICE_LEVEL_EXPENSIVE": 13, "PRICE_LEVEL_VERY_EXPENSIVE": 15}
PRICE_LABEL = {"PRICE_LEVEL_FREE": "Free", "PRICE_LEVEL_INEXPENSIVE": "$", "PRICE_LEVEL_MODERATE": "$$",
               "PRICE_LEVEL_EXPENSIVE": "$$$", "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$"}
TIERS = [(70, "A · Top"), (50, "B · Established"), (30, "C · Growing"), (0, "D · Small/New")]
GOOGLE_PRICE_PER_1000 = 35.0   # Text Search Enterprise SKU (websiteUri/phone/rating), USD
GOOGLE_FREE_PER_MONTH = 1000



# --------------------------------------------------------------------------- hooks (used by the app)
_LOGGER = print
_PROGRESS = None


def log(*a):
    _LOGGER(" ".join(str(x) for x in a))


def progress(done, total, text=""):
    if _PROGRESS:
        _PROGRESS(done, total, text)

# --------------------------------------------------------------------------- helpers
def website_status(url):
    if not url:
        return "none"
    host = (urlparse(url if "://" in url else "http://" + url).hostname or "").lower()
    if any(host == h or host.endswith("." + h) for h in SOCIAL_HOSTS):
        return "social_only"
    return "has_website"


def normalize_phone(national, international=""):
    """Returns (display, is_mobile, whatsapp_link)."""
    raw = re.sub(r"\D", "", international or national or "")
    if not raw:
        return "", False, ""
    if raw.startswith("94"):
        local = "0" + raw[2:]
    elif raw.startswith("0"):
        local = raw
    else:
        local = "0" + raw
    is_mobile = bool(re.match(r"^07[0-8]\d{7}$", local))
    display = f"{local[:3]} {local[3:6]} {local[6:]}" if len(local) == 10 else local
    wa = f"https://wa.me/94{local[1:]}" if is_mobile else ""
    return display, is_mobile, wa


def score_lead(lead):
    s, why = 0, []
    if lead["website_status"] == "none":
        s += 40; why.append("website නෑ")
    elif lead["website_status"] == "social_only":
        s += 35; why.append("FB/IG විතරයි")
    reviews = lead.get("reviews") or 0
    if reviews:
        s += min(25, int(reviews ** 0.5 * 2.5))
        if reviews >= 50: why.append(f"busy ({reviews} reviews)")
    rating = lead.get("rating") or 0
    if rating >= 4.0:
        s += 10; why.append(f"rating {rating}")
    if lead["is_mobile"]:
        s += 10; why.append("WhatsApp number")
    elif lead["phone"]:
        s += 4
    s += CATEGORIES.get(lead["category"], (None, None, 8))[2]
    return min(100, s), ", ".join(why)


def parse_hours(h):
    """Google regularOpeningHours -> (days_open, latest_close_hour)."""
    if not h:
        return None, None
    days, close = set(), 0
    for p in h.get("periods", []):
        o, c = p.get("open", {}), p.get("close", {})
        if "day" in o:
            days.add(o["day"])
        if c:
            hr = c.get("hour", 0) + (24 if c.get("day") != o.get("day") else 0)
            close = max(close, hr)
        else:
            close = 24  # open 24h
    return len(days), close


def make_lead(category, city, source, pid, name, address, national, international, website,
              rating, reviews, maps_url, gtype="", status="OPERATIONAL", price_level="", hours=None):
    phone, is_mobile, wa = normalize_phone(national, international)
    days, close = parse_hours(hours)
    lead = dict(id=f"{source}:{pid}", name=name, category=category, type=gtype or category,
                city=city, address=address, phone=phone, is_mobile=is_mobile, whatsapp=wa,
                website=website or "", website_status=website_status(website),
                rating=rating, reviews=reviews, maps=maps_url, status=status, source=source,
                price_level=price_level or "", days_open=days, close_hour=close,
                pitch=CATEGORIES.get(category, ("", [], 8, ""))[3])
    lead["score"], lead["why"] = score_lead(lead)
    return lead


def _brand_key(name):
    n = name.lower()
    for c in CITIES:
        n = n.replace(c.lower(), "")
    n = re.sub(r"\b(branch|salon|saloon|the|pvt|ltd|\(.*?\))\b", "", n)
    return re.sub(r"[^a-z0-9]", "", n)


def add_reach(leads):
    """Business size / reach tier. Uses ALL found businesses (before filtering)."""
    brands = {}
    for l in leads:
        k = _brand_key(l["name"])
        if len(k) >= 4:
            brands.setdefault(k, set()).add(l["address"] or l["id"])
    for l in leads:
        s, notes = 0.0, []
        v = l.get("reviews") or 0
        s += min(50, 50 * math.log10(1 + v) / math.log10(501))           # 500 reviews = full
        if l.get("rating"):
            m, prior = 15, 4.2                                           # trust-adjusted rating
            br = (v * l["rating"] + m * prior) / (v + m)
            s += max(0, min(1, (br - 3.8) / 1.1)) * 20
        s += PRICE_POINTS.get(l.get("price_level"), 5)
        if l.get("price_level") in ("PRICE_LEVEL_EXPENSIVE", "PRICE_LEVEL_VERY_EXPENSIVE"):
            notes.append("premium prices")
        b = len(brands.get(_brand_key(l["name"]), ())) or 1
        l["branches"] = b
        if b >= 3: s += 10; notes.append(f"{b} branches")
        elif b == 2: s += 6; notes.append("2 branches")
        if l["website_status"] != "none":
            s += 5
        if l.get("days_open") == 7: s += 3
        if (l.get("close_hour") or 0) >= 20: s += 2
        if v >= 100: notes.append(f"{v} reviews")
        l["reach"] = int(min(100, round(s)))
        l["tier"] = next(t for th, t in TIERS if l["reach"] >= th)
        l["reach_why"] = ", ".join(notes)


# --------------------------------------------------------------------------- sources
def google_search(categories, cities, api_key, max_calls, pages):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": api_key,
               "X-Goog-FieldMask": GOOGLE_FIELDS}
    calls, out = 0, []
    for cat in categories:
        for city in cities:
            token = None
            for _ in range(pages):
                if calls >= max_calls:
                    log(f"  ! --max-calls {max_calls} reached, stopping.")
                    return out, calls
                body = {"textQuery": f"{CATEGORIES[cat][0]} in {city}, Sri Lanka",
                        "regionCode": "LK", "languageCode": "en", "pageSize": 20}
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
                    out.append(make_lead(
                        cat, city, "google", p.get("id"), p.get("displayName", {}).get("text", ""),
                        p.get("formattedAddress", ""), p.get("nationalPhoneNumber", ""),
                        p.get("internationalPhoneNumber", ""), p.get("websiteUri", ""),
                        p.get("rating"), p.get("userRatingCount"), p.get("googleMapsUri", ""),
                        p.get("primaryTypeDisplayName", {}).get("text", ""),
                        p.get("businessStatus", "OPERATIONAL"),
                        p.get("priceLevel", ""), p.get("regularOpeningHours")))
                log(f"  {cat:15s} {city:14s} page → {len(places)} places")
                progress(calls, min(max_calls, len(categories) * len(cities) * pages), f"{cat} · {city}")
                token = data.get("nextPageToken")
                if not token:
                    break
                time.sleep(2)  # next page token needs a moment
    return out, calls


def osm_search(categories, cities, radius_m):
    url = "https://overpass-api.de/api/interpreter"
    out = []
    for city in cities:
        if city not in CITIES:
            log(f"  ! {city}: coordinates not in CITIES list, skipping for OSM"); continue
        lat, lon = CITIES[city]
        for cat in categories:
            parts = []
            for tag in CATEGORIES[cat][1]:
                k, v = tag.split("=")
                parts.append(f'nwr["{k}"="{v}"](around:{radius_m},{lat},{lon});')
            q = f"[out:json][timeout:60];({''.join(parts)});out center tags;"
            try:
                r = requests.post(url, data={"data": q}, timeout=90,
                                  headers={"User-Agent": "RavionStudio-LeadFinder/1.0"})
                r.raise_for_status()
            except Exception as e:
                log(f"  ! OSM error {city}/{cat}: {e}"); continue
            els = r.json().get("elements", [])
            for e in els:
                t = e.get("tags", {})
                if not t.get("name"):
                    continue
                c_lat = e.get("lat") or e.get("center", {}).get("lat")
                c_lon = e.get("lon") or e.get("center", {}).get("lon")
                web = t.get("website") or t.get("contact:website") or t.get("contact:facebook") or ""
                addr = ", ".join(x for x in [t.get("addr:housenumber"), t.get("addr:street"),
                                             t.get("addr:city") or city] if x)
                out.append(make_lead(
                    cat, city, "osm", f"{e['type']}/{e['id']}", t["name"], addr,
                    t.get("phone") or t.get("contact:phone") or t.get("contact:mobile") or "", "",
                    web, None, None,
                    f"https://www.google.com/maps/search/?api=1&query={c_lat},{c_lon}"))
            log(f"  {cat:15s} {city:14s} → {len(els)} places")
            progress(cities.index(city) * len(categories) + categories.index(cat) + 1,
                     len(cities) * len(categories), f"{cat} · {city}")
            time.sleep(1.5)  # be polite to the free server
    return out


def demo_data(categories, cities):
    """Fake businesses only - to test the tool. NOT real leads."""
    import random
    random.seed(7)
    words = {"salon": ["Glamour", "Style Zone", "Hair Lounge", "Classic Cuts", "Royal Look"],
             "beauty_salon": ["Bridal Bliss", "Shine Beauty", "Rose Bridal", "Pearl Beauty"],
             "dental_clinic": ["Smile Dental", "City Dental Care", "Bright Teeth"],
             "tuition": ["Success Academy", "Vidya Institute", "Pragna Classes", "Gnana Tuition"],
             "guest_house": ["Green View Inn", "Lake Side Rest", "Palm Villa"],
             "spa": ["Herbal Ayurveda Spa", "Lotus Wellness", "Serene Spa"]}
    out = []
    for cat in categories:
        for city in cities:
            for i, w in enumerate(words.get(cat, ["Sample Business A", "Sample Business B"])):
                web = random.choice(["", "", "", "https://facebook.com/demo", "https://demo-site.lk"])
                mob = random.random() < 0.75
                ph = f"07{random.randint(0,8)}{random.randint(1000000,9999999)}" if mob else \
                     f"037{random.randint(1000000,9999999)}"
                rv = random.choice([0, 3, 12, 28, 45, 80, 150, 260, 420])
                price = random.choice(["", "", "PRICE_LEVEL_INEXPENSIVE", "PRICE_LEVEL_MODERATE",
                                       "PRICE_LEVEL_EXPENSIVE"])
                close = random.choice([18, 19, 20, 21])
                hrs = {"periods": [{"open": {"day": d, "hour": 9}, "close": {"day": d, "hour": close}}
                                   for d in range(random.choice([6, 7]))]}
                out.append(make_lead(cat, city, "demo", f"{cat}-{city}-{i}", f"[DEMO] {w} {city}",
                                     f"No {i+1}, Main Street, {city}", ph, "", web,
                                     round(random.uniform(3.6, 4.9), 1) if rv else None, rv,
                                     "https://maps.google.com", price_level=price, hours=hrs))
    return out


# --------------------------------------------------------------------------- output (local files)
COLS = [("tier", "Tier", 15), ("reach", "Reach", 8), ("score", "Lead score", 10),
        ("name", "Business", 34), ("category", "Category", 15), ("city", "City", 13),
        ("phone", "Phone", 14), ("whatsapp", "WhatsApp", 12), ("website_status", "Website", 13),
        ("website", "Website URL", 26), ("rating", "Rating", 8), ("reviews", "Reviews", 9),
        ("price", "Price", 7), ("branches", "Branches", 9), ("why", "Why this lead", 40),
        ("pitch", "Pitch idea", 52), ("address", "Address", 40), ("maps", "Google Maps", 12),
        ("status_col", "My status", 14), ("notes", "Notes", 30), ("source", "Source", 9)]
WEB_LABEL = {"none": "No website", "social_only": "FB/IG only", "has_website": "Has website"}


def full_why(l):
    return ", ".join(x for x in [l.get("why"), l.get("reach_why")] if x)


def cell_value(l, k):
    if k == "website_status": return WEB_LABEL.get(l[k], l[k])
    if k == "price": return PRICE_LABEL.get(l.get("price_level"), "")
    if k == "why": return full_why(l)
    if k == "status_col": return "New"
    if k == "notes": return ""
    v = l.get(k, "")
    return "" if v is None else v


def write_outputs(leads, outdir, stamp):
    os.makedirs(outdir, exist_ok=True)
    csv_path = os.path.join(outdir, f"leads_{stamp}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([c[1] for c in COLS])
        for l in leads:
            w.writerow([cell_value(l, k) for k, _, _ in COLS])
    xlsx_path = os.path.join(outdir, f"leads_{stamp}.xlsx")
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.formatting.rule import ColorScaleRule
        from openpyxl.worksheet.datavalidation import DataValidation
    except ImportError:
        log("  (openpyxl not installed - only CSV written. pip install openpyxl)")
        return csv_path, None
    wb = Workbook(); ws = wb.active; ws.title = "Leads"
    ws.append([c[1] for c in COLS])
    for i, (_, _, wdt) in enumerate(COLS, 1):
        ws.cell(1, i).font = Font(bold=True, color="FFFFFF")
        ws.cell(1, i).fill = PatternFill("solid", fgColor="1F2937")
        ws.column_dimensions[ws.cell(1, i).column_letter].width = wdt
    tier_fill = {"A": "C6EFCE", "B": "DDEBF7", "C": "FFF2CC", "D": "EDEDED"}
    for r, l in enumerate(leads, 2):
        for c, (k, _, _) in enumerate(COLS, 1):
            v = cell_value(l, k)
            cell = ws.cell(r, c, v)
            if k in ("whatsapp", "maps") and v:
                cell.value = "Open"; cell.hyperlink = v; cell.font = Font(color="0563C1", underline="single")
            if k == "tier":
                cell.fill = PatternFill("solid", fgColor=tier_fill[v[0]]); cell.font = Font(bold=True)
            if k in ("pitch", "why", "address"):
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    n = len(leads) + 1
    ws.freeze_panes = "E2"
    ws.auto_filter.ref = f"A1:{ws.cell(1, len(COLS)).column_letter}{n}"
    if n > 1:
        for col in ("B", "C"):
            ws.conditional_formatting.add(f"{col}2:{col}{n}", ColorScaleRule(
                start_type="num", start_value=30, start_color="F8D7DA", mid_type="num", mid_value=60,
                mid_color="FFF3CD", end_type="num", end_value=90, end_color="C6EFCE"))
        dv = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"')
        ws.add_data_validation(dv)
        sc = [i for i, c in enumerate(COLS, 1) if c[0] == "status_col"][0]
        dv.add(f"{ws.cell(1, sc).column_letter}2:{ws.cell(1, sc).column_letter}{n}")
    wb.save(xlsx_path)
    return csv_path, xlsx_path


# --------------------------------------------------------------------------- Google Sheet sync
STATUSES = ["New", "Messaged", "Replied", "Meeting", "Won", "Not interested"]
# (header, lead-key or None, kind)  kind: auto = tool updates it, user = you edit it, keep = set once
SHEET_COLS = [
    ("Tier", "tier", "auto"), ("Business", "name", "auto"),
    ("Status", None, "user"), ("Contacted on", None, "user"), ("Next follow-up", None, "user"),
    ("Notes", None, "user"),
    ("Reach", "reach", "auto"), ("Lead score", "score", "auto"), ("Category", "category", "auto"),
    ("City", "city", "auto"), ("Phone", "phone", "auto"), ("WhatsApp", "whatsapp", "auto"),
    ("Website", "website_status", "auto"), ("Website URL", "website", "auto"),
    ("Rating", "rating", "auto"), ("Reviews", "reviews", "auto"), ("Price", "price", "auto"),
    ("Branches", "branches", "auto"), ("Why", "why", "auto"), ("Pitch idea", "pitch", "auto"),
    ("Address", "address", "auto"), ("Google Maps", "maps", "auto"),
    ("First found", None, "keep"), ("Last updated", None, "auto"), ("Source", "source", "auto"),
    ("ID", "id", "auto"),
]
HEAD = [c[0] for c in SHEET_COLS]
LAST = chr(ord("A") + len(HEAD) - 1)          # 26 columns -> "Z"
COL = {h: i for i, h in enumerate(HEAD)}
TIER_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}


def merge_rows(existing_values, leads, today):
    """existing_values: 2D list from the sheet (header first). Returns new 2D body (no header).
    Keeps your Status/Contacted on/Next follow-up/Notes and First found; refreshes the rest."""
    rows, order, extra = {}, [], []
    if existing_values:
        old_head = existing_values[0]
        idx = {h: i for i, h in enumerate(old_head)}
        for r in existing_values[1:]:
            if not any(str(x).strip() for x in r):
                continue
            d = {h: (r[idx[h]] if h in idx and idx[h] < len(r) else "") for h in HEAD}
            if d["ID"]:
                rows[d["ID"]] = d; order.append(d["ID"])
            else:
                extra.append(d)                       # rows you typed in yourself
    added = updated = 0
    for l in leads:
        d = rows.get(l["id"])
        if d is None:
            d = {h: "" for h in HEAD}; d["Status"] = "New"; d["First found"] = today
            rows[l["id"]] = d; order.append(l["id"]); added += 1
        else:
            updated += 1
        for h, key, kind in SHEET_COLS:
            if kind == "auto" and key:
                d[h] = cell_value(l, key)
        d["Last updated"] = today
    body = [rows[i] for i in order] + extra

    def sort_key(d):
        t = str(d.get("Tier") or "D")[:1]
        try: reach = float(d.get("Reach") or 0)
        except ValueError: reach = 0
        return (TIER_ORDER.get(t, 4), -reach)
    body.sort(key=sort_key)
    return [[d[h] for h in HEAD] for d in body], added, updated


def sync_sheet(leads, sheet_id, sa_file):
    try:
        import gspread
        from gspread.utils import ValueRenderOption, ValueInputOption, DateTimeOption
    except ImportError:
        log("  ! gspread install කරලා නෑ:  pip install gspread"); return
    if not os.path.exists(sa_file):
        log(f"  ! Service account file එක නෑ: {sa_file}  (README → Google Sheet setup)"); return
    gc = gspread.service_account(filename=sa_file)
    sh = gc.open_by_key(sheet_id)
    titles = [w.title for w in sh.worksheets()]
    fresh = "All Leads" not in titles
    ws = sh.worksheet("All Leads") if not fresh else sh.add_worksheet("All Leads", rows=200, cols=len(HEAD))
    existing = [] if fresh else ws.get_values(value_render_option=ValueRenderOption.formula,
                                              date_time_render_option=DateTimeOption.formatted_string)
    today = dt.date.today().isoformat()
    body, added, updated = merge_rows(existing, leads, today)
    need = len(body) + 50
    if ws.row_count < need or ws.col_count < len(HEAD):
        ws.resize(rows=max(need, ws.row_count), cols=max(len(HEAD), ws.col_count))
    ws.batch_clear([f"A2:{LAST}{max(ws.row_count, need)}"])
    ws.update([HEAD] + body, "A1", value_input_option=ValueInputOption.user_entered)
    if fresh:
        _format_sheet(sh, ws)
        if "Sheet1" in titles and len(titles) == 1:
            try: sh.del_worksheet(sh.worksheet("Sheet1"))
            except Exception: pass
    _ensure_views(sh, titles)
    log(f"  Google Sheet: +{added} new, {updated} updated, total {len(body)} rows")
    log(f"  https://docs.google.com/spreadsheets/d/{sheet_id}")


def _ensure_views(sh, titles):
    src = "'All Leads'"
    views = {
        "Top Tier": f'=IFERROR(FILTER({src}!A2:{LAST}, REGEXMATCH({src}!A2:A, "^(A|B)")), "A/B tier leads තවම නෑ")',
        "Contacted": f'=IFERROR(FILTER({src}!A2:{LAST}, {src}!C2:C<>"New", {src}!C2:C<>""), "තවම කාටවත් contact කරලා නෑ")',
        "Follow-up": f'=IFERROR(SORT(FILTER({src}!A2:{LAST}, {src}!E2:E<>"", {src}!E2:E<=TODAY()+1, {src}!C2:C<>"Won", {src}!C2:C<>"Not interested"), 5, TRUE), "අද/හෙට follow-up නෑ")',
    }
    for name, formula in views.items():
        if name in titles:
            continue
        w = sh.add_worksheet(name, rows=500, cols=len(HEAD))
        w.update([[f"={src}!A1:{LAST}1"], [formula]], "A1", value_input_option="USER_ENTERED")
        w.format(f"A1:{LAST}1", {"textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                                "backgroundColor": {"red": .12, "green": .16, "blue": .22}})
        w.freeze(rows=1, cols=2)
    if "Summary" not in titles:
        w = sh.add_worksheet("Summary", rows=60, cols=8)
        w.update([["Tier එක අනුව"], [f"=QUERY({src}!A1:B, \"select A, count(B) where A is not null group by A label count(B) 'Leads'\", 1)"]],
                 "A1", value_input_option="USER_ENTERED")
        w.update([["Status එක අනුව"], [f"=QUERY({src}!B1:C, \"select C, count(B) where C is not null group by C label count(B) 'Leads'\", 1)"]],
                 "D1", value_input_option="USER_ENTERED")
        w.update([["City එක අනුව"], [f"=QUERY({src}!B1:J, \"select J, count(B) where J is not null group by J order by count(B) desc label count(B) 'Leads'\", 1)"]],
                 "G1", value_input_option="USER_ENTERED")
        w.format("A1:H1", {"textFormat": {"bold": True}})


def _format_sheet(sh, ws):
    sid = ws.id
    def rng(c0, c1, r0=1):
        return {"sheetId": sid, "startRowIndex": r0, "startColumnIndex": c0, "endColumnIndex": c1}
    def rgb(h):
        return {"red": int(h[0:2], 16) / 255, "green": int(h[2:4], 16) / 255, "blue": int(h[4:6], 16) / 255}
    def cf(col, text, color, typ="TEXT_STARTS_WITH"):
        return {"addConditionalFormatRule": {"index": 0, "rule": {
            "ranges": [rng(col, col + 1)],
            "booleanRule": {"condition": {"type": typ, "values": [{"userEnteredValue": text}]},
                            "format": {"backgroundColor": rgb(color), "textFormat": {"bold": True}}}}}}
    reqs = [
        {"repeatCell": {"range": {**rng(0, len(HEAD), 0), "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"backgroundColor": rgb("1F2937"),
                                 "textFormat": {"bold": True, "foregroundColor": rgb("FFFFFF")}}},
                        "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"setDataValidation": {"range": rng(COL["Status"], COL["Status"] + 1), "rule": {
            "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": s} for s in STATUSES]},
            "showCustomUi": True, "strict": False}}},
        {"setDataValidation": {"range": rng(COL["Contacted on"], COL["Next follow-up"] + 1), "rule": {
            "condition": {"type": "DATE_IS_VALID"}, "strict": False}}},
        {"repeatCell": {"range": rng(COL["Contacted on"], COL["Next follow-up"] + 1),
                        "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}}},
                        "fields": "userEnteredFormat.numberFormat"}},
        cf(0, "A", "B7E1CD"), cf(0, "B", "C9DAF8"), cf(0, "C", "FFF2CC"), cf(0, "D", "EEEEEE"),
        cf(COL["Status"], "Won", "B7E1CD", "TEXT_EQ"), cf(COL["Status"], "Meeting", "FCE5CD", "TEXT_EQ"),
        cf(COL["Status"], "Replied", "FFF2CC", "TEXT_EQ"), cf(COL["Status"], "Messaged", "C9DAF8", "TEXT_EQ"),
        cf(COL["Status"], "Not interested", "E0E0E0", "TEXT_EQ"),
    ]
    widths = {"Business": 240, "Notes": 220, "Why": 280, "Pitch idea": 340, "Address": 260,
              "WhatsApp": 200, "Google Maps": 200, "Tier": 130}
    for h, px in widths.items():
        reqs.append({"updateDimensionProperties": {
            "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": COL[h], "endIndex": COL[h] + 1},
            "properties": {"pixelSize": px}, "fields": "pixelSize"}})
    sh.batch_update({"requests": reqs})
    ws.freeze(rows=1, cols=2)



# --------------------------------------------------------------------------- run (shared by CLI and app)
def run_search(categories, cities, source="google", api_key="", max_calls=150, pages=3, radius=8000,
               min_score=50, tiers=("A", "B", "C", "D"), include_with_website=False, sort="reach",
               out="output", sheet_id="", service_account="service_account.json", sync=True):
    bad = [c for c in categories if c not in CATEGORIES]
    if bad:
        raise ValueError(f"Unknown categories: {bad}")
    tiers = {t.upper()[:1] for t in tiers}
    calls = 0
    if source == "google":
        if requests is None:
            raise RuntimeError("pip install -r requirements.txt")
        if not api_key:
            raise RuntimeError("Google API key නෑ (Settings / GOOGLE_MAPS_API_KEY)")
        planned = len(categories) * len(cities) * pages
        log(f"Max planned calls: {min(planned, max_calls)} "
            f"(free: {GOOGLE_FREE_PER_MONTH}/month, then ~${GOOGLE_PRICE_PER_1000}/1000)")
        leads, calls = google_search(categories, cities, api_key, max_calls, min(pages, 3))
    elif source == "osm":
        leads = osm_search(categories, cities, radius)
    else:
        leads = demo_data(categories, cities)

    uniq = {}
    for l in leads:
        if l["id"] not in uniq or l["score"] > uniq[l["id"]]["score"]:
            uniq[l["id"]] = l
    everything = list(uniq.values())
    add_reach(everything)            # branches are counted across ALL found businesses
    kept = [l for l in everything
            if l["status"] == "OPERATIONAL"
            and (include_with_website or l["website_status"] != "has_website")
            and l["phone"] and l["score"] >= min_score and l["tier"][0] in tiers]
    if sort == "reach":
        kept.sort(key=lambda l: (TIER_ORDER[l["tier"][0]], -l["reach"], -l["score"]))
    else:
        kept.sort(key=lambda l: (-l["score"], -l["reach"]))

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path, xlsx_path = write_outputs(kept, out, stamp)
    counts = {t[1][0]: 0 for t in TIERS}
    for l in kept:
        counts[l["tier"][0]] += 1
    log(f"Found {len(everything)} businesses → {len(kept)} leads  "
        f"(A:{counts['A']}  B:{counts['B']}  C:{counts['C']}  D:{counts['D']})")
    sheet_status = "off"
    if sync and sheet_id and kept:
        log("Syncing to Google Sheet…")
        try:
            sync_sheet(kept, sheet_id, service_account)
            sheet_status = "ok"
        except Exception as e:
            sheet_status = f"error: {e}"
            log(f"  ! Google Sheet sync failed: {e}")
    return dict(kept=kept, found=len(everything), counts=counts, calls=calls,
                csv=csv_path, xlsx=xlsx_path, sheet=sheet_status)


# --------------------------------------------------------------------------- main
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    here = os.path.dirname(os.path.abspath(__file__))
    cfg = load_settings(here)
    ap = argparse.ArgumentParser(description="Ravion Studio Lead Finder - Sri Lanka")
    ap.add_argument("--source", choices=["google", "osm", "demo"], default="google")
    ap.add_argument("--categories", nargs="+", default=DEFAULT_CATEGORIES,
                    help="keys: " + ", ".join(CATEGORIES))
    ap.add_argument("--cities", nargs="+", default=DEFAULT_CITIES)
    ap.add_argument("--max-calls", type=int, default=150, help="Google API call limit (cost guard)")
    ap.add_argument("--pages", type=int, default=3, help="Google pages per search (20 places each, max 3)")
    ap.add_argument("--radius", type=int, default=8000, help="OSM search radius in metres")
    ap.add_argument("--min-score", type=int, default=50)
    ap.add_argument("--tiers", nargs="+", default=["A", "B", "C", "D"], help="keep only these tiers, eg: A B")
    ap.add_argument("--sort", choices=["reach", "score"], default="reach")
    ap.add_argument("--include-with-website", action="store_true")
    ap.add_argument("--out", default=os.path.join(here, "output"))
    ap.add_argument("--api-key", default=cfg["api_key"])
    ap.add_argument("--sheet-id", default=cfg["sheet_id"])
    ap.add_argument("--service-account", default=cfg["service_account"])
    ap.add_argument("--no-sheet", action="store_true", help="don't sync to Google Sheet this run")
    a = ap.parse_args()
    print(f"\nRavion Lead Finder · source={a.source}")
    print(f"Categories: {', '.join(a.categories)}\nCities: {', '.join(a.cities)}\n")
    try:
        res = run_search(a.categories, a.cities, a.source, a.api_key, a.max_calls, a.pages, a.radius,
                         a.min_score, a.tiers, a.include_with_website, a.sort, a.out,
                         a.sheet_id, a.service_account, not a.no_sheet)
    except (RuntimeError, ValueError) as e:
        sys.exit(str(e))
    if a.source == "google":
        print(f"Google calls used this run: {res['calls']}")
    print(f"Saved: {res['xlsx'] or ''}\n       {res['csv']}")
    for l in res["kept"][:12]:
        print(f"  {l['tier']:16s} {l['reach']:3d}  {l['name'][:34]:34s} {l['city']:13s} {l['phone']:13s} "
              f"{(l.get('reviews') or 0):>4} reviews")
    if not a.sheet_id:
        print("\n(Google Sheet sync off - Sheet ID set කරලා නෑ. README බලන්න)")


def load_settings(here):
    """settings.json (saved by the app) overrides nothing set in the environment."""
    cfg = {}
    try:
        with open(os.path.join(here, "settings.json"), encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        pass
    sa_env = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")     # cloud hosting: key comes from secrets
    if sa_json and not sa_env:
        import tempfile
        sa_env = os.path.join(tempfile.gettempdir(), "ravion_service_account.json")
        with open(sa_env, "w", encoding="utf-8") as f:
            f.write(sa_json)
    return dict(
        api_key=os.environ.get("GOOGLE_MAPS_API_KEY") or cfg.get("api_key", ""),
        sheet_id=os.environ.get("GOOGLE_SHEET_ID") or cfg.get("sheet_id", ""),
        service_account=sa_env or cfg.get("service_account")
        or os.path.join(here, "service_account.json"))


if __name__ == "__main__":
    main()
