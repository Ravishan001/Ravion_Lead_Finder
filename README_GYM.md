# 🏋️ Gym Finder + 📊 Dashboard (RepFlint sales tool)

පරණ Lead Finder එක (app.py / leadfinder.py) **කිසිම වෙනසක් නෑ**. මේක අලුතින් එකතු කරපු pages දෙකක්.

## Install කරන හැටි
1. මේ zip එකේ තියෙන මේ files ටික ඔයාගේ **leadfinder folder එකට** copy කරන්න:
   - `gymfinder.py`, `gym_common.py`, `README_GYM.md`, `requirements.txt`
   - `pages` folder එක මුළුමනින්ම (ඇතුළේ `1_Gym_Finder.py`, `2_Gym_Dashboard.py`)
2. Folder එකේ `cmd` එකේ එක පාරක් run කරන්න: `pip install -r requirements.txt`
3. සුපුරුදු විදිහටම **Start_App.bat** double-click කරන්න.
4. වම් පැත්තේ menu එකේ දැන් **app / Gym Finder / Gym Dashboard** කියලා pages 3ක් පේනවා.

API key, Sheet ID ඔක්කොම පරණ app එකේම settings. ආයෙත් දාන්න ඕන නෑ.

## Gym Finder
1. **Gym වර්ග** – Gym, Fitness center, CrossFit, Ladies gym, Martial arts, Yoga, Pilates
2. **ප්‍රදේශය** – ලංකාව (පළාත → දිස්ත්‍රික්කය → නගර) හරි ලෝකේ වෙන රටක් + නගර. **Radius (km)** එකට වඩා දුර gyms ඉබේම අයින් වෙනවා.
3. **Target** – System status අනුව:
   | Status | තේරුම | Score |
   |---|---|---|
   | No website | කිසි online එකක් නෑ | ⭐ හොඳම |
   | FB/IG only | Facebook/Instagram විතරයි | ⭐ හොඳම |
   | Website, no system | Website තියෙනවා, member login/booking software නෑ | හොඳයි |
   | Website, maybe system | "Member login", "Book a class", app links වගේ දේවල් තියෙනවා | අඩුයි |
   | Has system | Mindbody, Glofox, GymMaster වගේ software එකක් පාවිච්චි කරනවා | ❌ |
   - Anytime Fitness, Gold's Gym, Power World වගේ **big chains** default එකෙන් අයින් කරනවා.
   - "Websites check" on නම් gym එකේ homepage එක එක පාරක් open කරලා software එකක් තියෙනවද බලනවා (Google calls යන්නේ නෑ).
4. **WhatsApp message** – සිංහල/English. Results එකේ **💬 Send pitch** click කළාම ඒ gym එකේ නමත් එක්ක message එක ready වෙලා WhatsApp open වෙනවා. Message එක edit කරලා save කරගන්න පුළුවන්.

## Members / coaches ගණන ගැන (වැදගත්)
Google එකේ members ගණනක් හරි coaches ගණනක් හරි **නෑ**. ඒ නිසා tool එක **Google reviews ගණනෙන් estimate** එකක් දෙනවා:
- Active members ≈ 3 × reviews^0.8 (range එකක් විදිහට). උදා: reviews 40 ≈ members 35–85, reviews 400 ≈ 220–540
- Coaches ≈ members 40–60කට 1යි
- Size: Small / Medium / Large / Very large

මේවා **"est."** – ඇත්ත ගණන call එකේදී අහන්න. ඒක Notes එකේ ලියාගන්න.

## Dashboard
- KPIs: gyms, Hot leads, est. members, contacted, meetings, won
- Charts: sales pipeline, city අනුව, system status, reviews vs score
- 🗺️ Map එකේ gyms (තැඹිලි = Hot)
- Table එකේම **Status / Contacted on / Next follow-up / Notes** edit කරලා **Save** කරන්න
  - Status එක "Messaged" කළාම follow-up date එක දවස් 3කින් ඉබේම වැටෙනවා
- **Google Sheet එකට push** – ඔයාගේ sheet එකේ **"Gym Leads"** කියලා වෙනම tab එකකට copy කරනවා (All Leads tab එකට අත ගහන්නේ නෑ). Edit කරන්න ඕන app dashboard එකේ; sheet එක phone එකෙන් බලන්න copy එකක්.
- Data save වෙන්නේ folder එකේ `gym_leads.json` file එකේ.

## Command line (optional)
```
python gymfinder.py --source demo
python gymfinder.py --country "Sri Lanka" --cities Kuliyapitiya Kurunegala --radius 8 --lang si
python gymfinder.py --country "United Kingdom" --cities Leicester --types gym crossfit --max-calls 12
```

## Calls / cost
Calls = types × cities × depth + අලුත් නගරයක location එක හොයන්න 1 (ඊට පස්සේ `geo_cache.json` එකේ save වෙනවා, ලංකාවේ ප්‍රධාන නගර free).
උදා: types 2 × cities 3 × depth 2 = calls 12.

## හොඳට පාවිච්චි කරන්න
- එක gym එකකට එක personal message එකක්. "එපා" කිව්වොත් Status = Not interested.
- Google terms අනුව data දවස් 30කට වඩා තියාගන්න එපා – Dashboard එක කියනකොට ආයෙත් run කරලා refresh කරන්න.
