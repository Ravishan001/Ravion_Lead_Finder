# Ravion Lead Finder – Sri Lanka (v3 · App)

## 🚀 App එක පාවිච්චි කරන හැටි (ලේසිම විදිහ)

1. මේ folder එකේ address bar එකේ `cmd` type කරලා මේක run කරන්න (එක පාරක් විතරයි):
   ```
   pip install -r requirements.txt
   ```
2. **Start_App.bat** එක double-click කරන්න. තත්පර 5කින් විතර browser එකේ app එක open වෙනවා.
   - කළු පාට window එක **close කරන්න එපා**. App එක run වෙන්නේ ඒකෙන්.
   - App එක නවත්තන්න ඕන නම් ඒ කළු window එක close කරන්න.
   - Browser එක ඉබේම open වුණේ නැත්නම් browser එකේ `http://localhost:8501` කියලා type කරන්න.
3. පළවෙනි පාරට විතරක්: වම් පැත්තේ **Settings** එකේ **Google Maps API key**, **Sheet ID**, **Service account file** path එක දාලා **Save settings** කරන්න.
   - ඔයා කලින් `setx` වලින් API key එකයි Sheet ID එකයි දාලා තියෙනවා නම් ඒවා දැනටමත් load වෙලා තියෙනවා.
4. Search එක set කරලා Start කරන්න:
   - **1 · Business types**: checkboxes වලින් ඕන types තෝරන්න. ★★★ තියෙන ඒවා AI agent එකකට හොඳටම ගැලපෙනවා.
   - **2 · ප්‍රදේශය**: පළාත → දිස්ත්‍රික්කය → නගර තෝරන්න. List එකේ නැති නගරයක් ඕන නම් "තව නගර" box එකේ type කරන්න.
   - **3 · Filters**: Tier (A Top / B Est. / C Growing / D Small), අවම Lead score, search depth, max calls.
   - යටින් තියෙන **🚀 Start** button එක click කරන්න.
5. Results table එක app එකේම පේනවා: WhatsApp 💬 Chat link, Maps 📍 link, Excel download. Results ඔයාගේ Google Sheet එකටත් ඉබේම save වෙනවා.

> Start button එකට උඩින් තියෙන box එකේ Google calls කීයක් යනවද කියලා පෙන්නනවා. Calls 30ට වඩා යනවා නම් warning එකක් එනවා.
> Test කරන්න ඕන නම් වම් පැත්තේ **Data source → Demo** තෝරන්න. එතකොට fake data එක්ක run වෙනවා, calls යන්නේ නෑ.

පහළින් තියෙන්නේ command line එකෙන් පාවිච්චි කරන හැටියි, setup එකේ විස්තරයි.

---

Website නැති (නැත්නම් FB/IG page එකක් විතරක් තියෙන) ලංකාවේ businesses හොයලා මේ දේවල් කරනවා:
- ඒ business එක කොච්චර ලොකුද කියලා බලලා **Tier එකක් (A/B/C/D)** දෙනවා.
- Results ඔක්කොම **ඔයාගේ Google Sheet එකට** auto save කරනවා.
- Contact කරපු අයව **වෙනම tab එකක** පෙන්නනවා.

---

## Tier (Reach) එක හදන හැටි

Google එකේ ලොකු salon එකක්ද පොඩි එකක්ද කියලා කෙලින්ම පෙන්නන්නේ නෑ. ඒ නිසා tool එක මේ signals 0–100 **Reach score** එකකට එකතු කරනවා:

| Signal | Points | ඇයි |
|---|---|---|
| Google reviews ගණන | 50 දක්වා | Customers ගොඩක් එනවා = reviews ගොඩක්. Reach එකට හොඳම signal එක මේක |
| Trust-adjusted rating | 20 දක්වා | Reviews 2ක් තියෙන 5.0 එකකට වඩා reviews 300ක් තියෙන 4.6 එකක් වටිනවා |
| Price level ($ – $$$$) | 15 දක්වා | $$$ නම් premium salon එකක්, budget එකත් තියෙනවා |
| Branches | 10 දක්වා | එකම නමින් තැන් කිහිපයක් තියෙනවා නම් chain එකක් |
| Online presence | 5 | FB/IG page එකක් තියෙනවා = marketing ගැන හිතනවා |
| Open වෙලාවල් | 5 දක්වා | සතියේ දවස් 7ම open, රෑ 8න් පස්සේ වහනවා = busy |

| Tier | Reach | තේරුම |
|---|---|---|
| **A · Top** | 70+ | ලොකු / ප්‍රසිද්ධ / premium. Budget තියෙනවා, AI එකකින් ලොකු වාසියක් ගන්න පුළුවන් |
| **B · Established** | 50–69 | හොඳට යන, customers ලා දිගටම එන business |
| **C · Growing** | 30–49 | හැදි හැදී එන business |
| **D · Small/New** | 30ට අඩු | පොඩි / අලුත්. Budget අඩු වෙන්න පුළුවන් |

**Lead score** එක වෙනම තියෙනවා. ඒකෙන් පෙන්නන්නේ ඔයාගේ service එකට කොච්චර ගැලපෙනවද කියන එක (website නෑ, WhatsApp number එකක් තියෙනවා වගේ දේවල්).
- හොඳම target එක: **A/B tier + Lead score වැඩි** අය.
- Branches ගණන් කරන්නේ නමෙන් විතරයි. Common නමක් තියෙන salons දෙකක් වෙන වෙනම අයිතිකරුවන්ගේ වෙන්න පුළුවන් නිසා Maps එකේ check කරලා බලන්න.

---

## Setup

### 1. Python + libraries
1. python.org එකෙන් Python install කරන්න. Install කරනකොට **"Add python.exe to PATH"** tick කරන්න.
2. leadfinder folder එකේ address bar එකේ `cmd` type කරලා Enter කරන්න.
3. මේක run කරන්න:
   ```
   pip install -r requirements.txt
   ```
4. Test කරන්න:
   ```
   python leadfinder.py --source demo --no-sheet
   ```

### 2. Google Places API key (දැනටමත් කරලා ඉවරයි නම් skip කරන්න)
- Places API (New) enable කරන්න, API key එකක් හදලා Places API (New) එකට විතරක් restrict කරන්න.
- ඊට පස්සේ මේක run කරන්න:
  ```
  setx GOOGLE_MAPS_API_KEY "AIza..."
  ```
- ⚠️ $1 budget alert එකකුයි, daily quota එක 30ට අඩු කරන එකයි අනිවාර්යයෙන් කරන්න.

### 3. Google Sheet එක connect කරන්න (එක පාරක් විතරයි, විනාඩි 10ක් විතර යනවා)

**a) Google Sheets API enable කරන්න**
console.cloud.google.com එකේ **එකම project එකේ** → APIs & Services → Library → **Google Sheets API** → **Enable**.

**b) Service account එකක් හදන්න** (මේක tool එකට ඔයාගේ sheet එකේ ලියන්න දෙන "robot account" එකක්)
1. **IAM & Admin → Service Accounts → + Create service account**
2. Name එකට `lead-finder` දාලා **Create and continue** click කරන්න. Roles මුකුත් දාන්න ඕන නෑ, **Done** click කරන්න.
3. හදපු service account එක click කරලා **Keys** tab එකට යන්න → **Add key → Create new key → JSON** → **Create**.
4. එතකොට `.json` file එකක් download වෙනවා. ඒක **`service_account.json`** කියලා rename කරලා **leadfinder folder එකට** දාන්න.
   - ⚠️ මේ file එක password එකක් වගේ. කාටවත් දෙන්න එපා, GitHub එකට දාන්නත් එපා.

**c) Google Sheet එක හදලා share කරන්න**
1. sheets.google.com එකේ අලුත් sheet එකක් හදලා ඒකට **Ravion Leads** කියලා නම දෙන්න.
2. `service_account.json` file එක Notepad එකෙන් open කරලා ඒකේ `"client_email"` එක copy කරන්න. ඒක `lead-finder@....iam.gserviceaccount.com` වගේ එකක්.
3. Sheet එකේ **Share** click කරලා ඒ email එක paste කරන්න. **Editor** තෝරලා, "Notify people" untick කරලා **Share** කරන්න.

**d) Sheet ID එක set කරන්න**
- Sheet URL එක මේ වගේ: `https://docs.google.com/spreadsheets/d/`**`1AbC...xyz`**`/edit`
- මැද තියෙන bold කොටස තමයි ID එක. ඒක copy කරලා මේක run කරන්න:
  ```
  setx GOOGLE_SHEET_ID "1AbC...xyz"
  ```
- ඊට පස්සේ CMD එක **close කරලා ආයෙත් open කරන්න**.

දැන් tool එක run කරන හැම පාරකම results ඉබේම sheet එකට යනවා.

---

## Run කරන හැටි
```
# Kuliyapitiya salons (calls 3)
python leadfinder.py --cities Kuliyapitiya --categories salon beauty_salon --max-calls 6

# Top level (A/B tier) salons විතරක්
python leadfinder.py --cities Negombo Kurunegala Gampaha --categories salon beauty_salon --tiers A B

# Lead score එකෙන් sort කරන්න (default: tier/reach)
python leadfinder.py --sort score
```
`run_leadfinder.bat` එක double-click කරලාත් run කරන්න පුළුවන්.

**Calls ගණන් හදන හැටි:** categories × cities × 3. උදාහරණයක් විදිහට categories 2ක් × cities 3ක් = calls 18යි. Daily limit එක 30 නම් දවසකට combinations 10ක් විතර run කරන්න පුළුවන්.

---

## Google Sheet එකේ tabs

| Tab | මොකක්ද |
|---|---|
| **All Leads** | Leads ඔක්කොම. ඔයා edit කරන්නේ මේ එක විතරයි |
| **Top Tier** | A සහ B tier විතරක් (auto) |
| **Contacted** | Status එක "New" නැති හැම එකක්ම, ඒ කියන්නේ message/call කරපු අය (auto) |
| **Follow-up** | "Next follow-up" date එක අද හෝ හෙට තියෙන අය (auto) |
| **Summary** | Tier, status, city අනුව ගණන් (auto) |

**All Leads එකේ ඔයා edit කරන columns:** **Status** (dropdown එක), **Contacted on**, **Next follow-up**, **Notes**.
- Tool එක ආයෙත් run කරනකොට මේ columns **කවදාවත් overwrite වෙන්නේ නෑ**. Reviews, rating, tier වගේ ඒවා විතරයි update වෙන්නේ.
- එකම business එක ආයෙත් හම්බුණොත් අලුත් row එකක් හැදෙන්නේ නෑ, තියෙන row එකම update වෙනවා.
- ඔයා තනියම type කරලා දාන rows ත් එහෙමම තියෙනවා.
- Status: New → Messaged → Replied → Meeting → Won / Not interested

### (Optional) Status එක මාරු කළාම date එක auto වැටෙන්න
Sheet එකේ **Extensions → Apps Script** එකට ගිහින් තියෙන code එක delete කරලා මේක paste කරන්න. ඊට පස්සේ **Save** කරන්න.
```javascript
function onEdit(e) {
  const sh = e.range.getSheet();
  if (sh.getName() !== 'All Leads' || e.range.getColumn() !== 3 || e.range.getRow() < 2) return;
  const row = e.range.getRow();
  const contacted = sh.getRange(row, 4), follow = sh.getRange(row, 5);
  if (e.value && e.value !== 'New' && !contacted.getValue()) contacted.setValue(new Date());
  if (e.value === 'Messaged' && !follow.getValue()) {
    const d = new Date(); d.setDate(d.getDate() + 3); follow.setValue(d);   // දවස් 3කින් follow-up
  }
}
```
දැන් Status එක **Messaged** කළාම "Contacted on" එකට අද date එකත්, "Next follow-up" එකට දවස් 3කට පස්සේ date එකත් ඉබේම වැටෙනවා.

---

## Errors ආවොත්
| Error එක | විසඳුම |
|---|---|
| `Service account file එක නෑ` | `service_account.json` එක leadfinder folder එකේ තියෙනවද, නම හරියටම ඒකද කියලා බලන්න (`.json.json` වෙලා නැද්ද) |
| `PERMISSION_DENIED` / `403` (sheet) | Sheet එක service account email එකට **Editor** විදිහට share කළාද බලන්න |
| `SpreadsheetNotFound` / `404` | Sheet ID එක හරියට copy කළාද බලන්න |
| `Google Sheets API has not been used` | 3(a) පියවර කරලා විනාඩි කිහිපයක් ඉඳලා ආයෙත් try කරන්න |
| Key create කරන්න බෑ කියනවා | Personal Gmail account එකකින් project එක හදලා ආයෙත් try කරන්න |

## හොඳට පාවිච්චි කරන්න
- Spam කරන්න එපා. හොඳම leads ටික තෝරලා, ඒ business එකටම හදපු demo එකක් එක්ක personal message එකක් යවන්න. කවුරුහරි "එපා" කිව්වොත් Status එක "Not interested" කරලා ආයෙත් message කරන්න එපා.
- Google ගේ terms වලට අනුව Places data දිගු කාලයක් store කරලා තියාගන්න හරි, විකුණන්න හරි බෑ. මේ sheet එක ඔයාගේ working list එකක් විතරයි. පරණ data අයින් කරලා tool එක ආයෙත් run කරලා fresh data ගන්න.
