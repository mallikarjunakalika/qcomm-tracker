"""
Q-Commerce Cigarette SKU Availability Checker  v3.0
- Age gate handler added
- Multiple search aliases per SKU
- Looser fuzzy matching
"""
import asyncio, re, json, datetime
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

PINCODES = [
    ("700156","New Town AA II-III","Premium"),
    ("700019","Ballygunge","Premium"),
    ("700016","Park Street / Camac Street","Premium"),
    ("700106","New Town Action Area I","Premium"),
    ("700020","Gariahat / Ballygunge Phari","Premium"),
    ("700027","Alipore","Premium"),
    ("700107","Chinar Park / Rajarhat","Upper Mid"),
    ("700097","Salt Lake Sec V / Karunamoyee","Upper Mid"),
    ("700150","Rajarhat E","Upper Mid"),
    ("700075","Kasba","Upper Mid"),
    ("700033","Tollygunge","Upper Mid"),
    ("700053","New Alipore","Upper Mid"),
    ("700064","Salt Lake Sec I-III","Upper Mid"),
    ("700073","Anandapur / EM Bypass","Upper Mid"),
    ("700098","Krishnapur / NT fringe","Upper Mid"),
    ("700022","Dhakuria / Golpark","Upper Mid"),
    ("700072","Jodhpur Park","Upper Mid"),
    ("700032","Jadavpur","Upper Mid"),
    ("700021","Lansdowne / Beck Bagan","Upper Mid"),
    ("700015","Elgin Road / Bhowanipore N","Upper Mid"),
    ("700091","Salt Lake Sec IV-V","Upper Mid"),
    ("700086","Deshapriya Park","Upper Mid"),
    ("700077","Dhakuria W","Upper Mid"),
    ("700026","Southern Avenue / Lake E","Upper Mid"),
    ("700084","Garia / Narendrapur fringe","Upper Mid"),
    ("700028","Bhabanipur / Paddapukur","Upper Mid"),
    ("700025","Bhowanipore","Upper Mid"),
    ("700155","New Town Adj","Upper Mid"),
    ("700029","Lake Gardens","Upper Mid"),
]

# Each SKU has multiple search aliases — tries each until a match is found
# (market_sku, brand, display_name, segment, [search_aliases])
SKUS = [
    ("AMCLUBCLOVEMINT10",  "American Club",  "American Club Clove Mint 10",          "KSFT",
     ["American Club Clove", "American Club Mint", "American Club 10"]),

    ("AMCNYCOOLSLKFTK20",  "American Club",  "American Club NY Cool 20",             "Super KSFT",
     ["American Club NY Cool", "American Club 20", "American Club"]),

    ("B&HFTKGB20",         "Benson & Hedges","Benson & Hedges Blue Gold 20",         "KSFT",
     ["Benson Hedges Blue", "B&H Blue Gold", "Benson Hedges 20", "Benson Hedges"]),

    ("B&HFTKSPL20",        "Benson & Hedges","Benson & Hedges Special 20",           "KSFT",
     ["Benson Hedges Special", "B&H Special", "Benson Hedges 20"]),

    ("CLALPHATECFK20",     "Classic",        "Classic Alphatec 20",                  "KSFT",
     ["Classic Alphatec", "Classic Alpha Tec", "ITC Classic Alphatec"]),

    ("CLFLKBT10",          "Classic",        "Classic Balanced Taste 10",            "KSFT",
     ["Classic Balanced Taste", "Classic Milds 10", "Classic Milds", "ITC Classic 10"]),

    ("CLFTKBT20",          "Classic",        "Classic Balanced Taste 20",            "KSFT",
     ["Classic Balanced Taste 20", "Classic Milds 20", "ITC Classic 20"]),

    ("CLCLOVEFTK12",       "Classic",        "Classic Clove 12",                     "Super KSFT",
     ["Classic Clove", "ITC Classic Clove", "Classic Clove 12"]),

    ("CLASSICCONNECTFK20", "Classic",        "Classic Connect 20",                   "KSFT",
     ["Classic Connect", "ITC Classic Connect"]),

    ("CLDOUBLEBURST10",    "Classic",        "Classic Double Burst 10",              "KSFT",
     ["Classic Double Burst", "ITC Classic Double Burst"]),

    ("CLDOUBLEBURST20",    "Classic",        "Classic Double Burst 20",              "KSFT",
     ["Classic Double Burst 20"]),

    ("CLFINTASTLOWSMEL20", "Classic",        "Classic Fine Taste 20",                "KSFT",
     ["Classic Fine Taste", "Classic Fine", "ITC Classic Fine"]),

    ("CLASSICICEBURST10",  "Classic",        "Classic Ice Burst 10",                 "KSFT",
     ["Classic Ice Burst", "Classic Ice 10", "ITC Classic Ice"]),

    ("CLASSICICEBURST20",  "Classic",        "Classic Ice Burst 20",                 "KSFT",
     ["Classic Ice Burst 20", "Classic Ice 20"]),

    ("CLFTKREFT10",        "Classic",        "Classic Refined Taste 10",             "KSFT",
     ["Classic Refined Taste", "Classic Ultra Mild", "Classic Refined 10", "ITC Classic Refined"]),

    ("CLFTLREFT20",        "Classic",        "Classic Refined Taste 20",             "KSFT",
     ["Classic Refined Taste 20", "Classic Ultra Mild 20"]),

    ("CLFTKRT10",          "Classic",        "Classic Rich Taste 10",                "KSFT",
     ["Classic Rich Taste", "Classic Regular 10", "Classic Rich 10", "ITC Classic Regular"]),

    ("CLFTKRT20",          "Classic",        "Classic Rich Taste 20",                "KSFT",
     ["Classic Rich Taste 20", "Classic Regular 20", "ITC Classic 20"]),

    ("CLFTKVR16CP",        "Classic",        "Classic Verve 16",                     "KSFT",
     ["Classic Verve", "ITC Classic Verve"]),

    ("CLFTKVRBT16CP",      "Classic",        "Classic Verve Balance Taste 16",       "KSFT",
     ["Classic Verve Balance", "Classic Verve Balanced"]),

    ("FLSPLDSFT10",        "Flake",          "Flake Special 10",                     "DSFT",
     ["Flake Special", "ITC Flake", "Flake Cigarette"]),

    ("GFFTKBLUE10",        "Gold Flake",     "Gold Flake Blue 10",                   "KSFT",
     ["Gold Flake Blue 10", "Gold Flake Kings Blue 10", "GF Blue 10"]),

    ("GFFTKBLUE20",        "Gold Flake",     "Gold Flake Blue 20",                   "KSFT",
     ["Gold Flake Blue 20", "Gold Flake Kings Blue 20"]),

    ("GFINDIEMINTFT10",    "Gold Flake",     "Gold Flake Indie Mint 10",             "RSFT",
     ["Gold Flake Indie Mint", "Gold Flake Indie", "GF Indie Mint"]),

    ("GFKMIXPOD10",        "Gold Flake",     "Gold Flake Mixpod 10",                 "KSFT",
     ["Gold Flake Mixpod", "GF Mixpod 10", "Gold Flake Mix Pod"]),

    ("GFKMIXPOD20",        "Gold Flake",     "Gold Flake Mixpod 20",                 "KSFT",
     ["Gold Flake Mixpod 20", "GF Mixpod 20"]),

    ("GFPRFT10",           "Gold Flake",     "Gold Flake Premium Filter 10",         "RSFT",
     ["Gold Flake Premium Filter", "Gold Flake Premium 10", "GF Premium Filter"]),

    ("GFFTK10",            "Gold Flake",     "Gold Flake Kings 10",                  "KSFT",
     ["Gold Flake Kings 10", "Gold Flake 10", "GF Kings 10"]),

    ("GFFTK20",            "Gold Flake",     "Gold Flake Kings 20",                  "KSFT",
     ["Gold Flake Kings 20", "Gold Flake 20", "GF Kings 20"]),

    ("GFSLFTK16CP",        "Gold Flake",     "Gold Flake SLK 16",                    "KSFT",
     ["Gold Flake SLK", "Gold Flake Silk", "GF SLK 16"]),

    ("GFSPSTRDSFT10-VAR2", "Gold Flake",     "Gold Flake Super Star 10",             "DSFT",
     ["Gold Flake Super Star", "GF Super Star", "Gold Flake Superstar"]),

    ("GFTKTWINPOD10",      "Gold Flake",     "Gold Flake Twinpod 10",                "KSFT",
     ["Gold Flake Twinpod", "GF Twinpod 10", "Gold Flake Twin Pod"]),

    ("GFTKTWINPOD20",      "Gold Flake",     "Gold Flake Twinpod 20",                "KSFT",
     ["Gold Flake Twinpod 20", "GF Twinpod 20"]),

    ("IKFTKWHITEGOLD20",   "India Kings",    "India Kings White Gold 20",            "KSFT",
     ["India Kings White Gold", "India Kings 20", "ITC India Kings"]),

    ("NC10",               "Navy Cut",       "Navy Cut 10",                          "Longs",
     ["Navy Cut 10", "ITC Navy Cut", "Navy Cut Filter 10", "Navy Cut Cigarette"]),

    ("SCBLUEDSFT10",       "SilkCut",        "Silkcut Blue 10",                      "DSFT",
     ["Silk Cut Blue", "Silkcut Blue", "ITC Silk Cut Blue"]),

    ("SCDSFT10",           "SilkCut",        "Silkcut Special 10",                   "DSFT",
     ["Silk Cut Special", "Silkcut Special", "ITC Silk Cut", "Silk Cut 10"]),
]

UNIQUE_BRANDS = sorted(set(s[1] for s in SKUS))
PLATFORMS = ["Blinkit", "Zepto", "Swiggy Instamart"]


# ── AGE GATE HANDLER ──────────────────────────────────────────
async def handle_age_gate(page):
    """Click through any age verification popup."""
    age_gate_selectors = [
        "text=I am 18",
        "text=Yes, I am 18",
        "text=I'm 18",
        "text=Yes, I'm above 18",
        "text=Confirm Age",
        "text=I am above 18",
        "text=Yes, I am above 18",
        "text=Proceed",
        "text=Continue",
        "button[class*='age']",
        "[data-testid*='age']",
        "[class*='age-gate']",
        "[class*='ageGate']",
    ]
    for sel in age_gate_selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1500):
                await btn.click(timeout=2000)
                await page.wait_for_timeout(1000)
                print("    ✅ Age gate cleared")
                return True
        except Exception:
            pass
    return False


# ── FUZZY MATCH ───────────────────────────────────────────────
def loose_match(alias, page_text):
    """Match if majority of meaningful words from alias appear in page text."""
    page_lower = page_text.lower()
    alias_lower = alias.lower()
    # Remove pack sizes
    core = re.sub(r'\b(\d+s?|pack|of)\b', '', alias_lower).strip()
    words = [w for w in core.split() if len(w) > 2]
    if not words:
        return False
    matches = sum(1 for w in words if w in page_lower)
    # Need at least 60% of words to match
    return matches >= max(1, len(words) * 0.6)


# ── LOCATION SETTER ───────────────────────────────────────────
async def set_location(page, pincode, platform):
    urls = {
        "Blinkit":          "https://blinkit.com",
        "Zepto":            "https://www.zeptonow.com",
        "Swiggy Instamart": "https://www.swiggy.com/instamart",
    }
    try:
        await page.goto(urls[platform], timeout=35000)
        await page.wait_for_timeout(3000)

        # Handle age gate immediately on page load
        await handle_age_gate(page)

        for sel in ["[data-testid='location-bar']", "text=Detect Location",
                    "[class*='location']", "text=Enter Location", "text=Enter manually"]:
            try:
                await page.click(sel, timeout=2500)
                await page.wait_for_timeout(1000)
                break
            except Exception:
                pass

        for sel in ["input[placeholder*='pincode']","input[placeholder*='Pincode']",
                    "input[placeholder*='Enter']","input[placeholder*='area']",
                    "input[placeholder*='Search']","input[type='text']"]:
            try:
                inp = page.locator(sel).first
                await inp.fill(pincode, timeout=4000)
                await page.wait_for_timeout(1500)
                for sug in ["[data-testid*='suggestion']","[data-testid*='location']",
                            "[class*='suggestion']","[class*='location-item']",
                            "[role='option']","li"]:
                    try:
                        await page.locator(sug).first.click(timeout=2500)
                        await page.wait_for_timeout(2000)
                        return True
                    except Exception:
                        pass
            except Exception:
                pass
        return False
    except Exception:
        return False


# ── SEARCH WITH ALIASES ───────────────────────────────────────
async def search_sku(page, sku, platform):
    """
    Try each alias until a match is found.
    Returns (found: bool, price: str|None)
    """
    msku, brand, name, seg, aliases = sku

    card_sels = {
        "Blinkit":          ".product-card, [data-testid='product-item'], [class*='ProductCard']",
        "Zepto":            "[class*='ProductCard'], [class*='product-card']",
        "Swiggy Instamart": "[class*='ItemCard'], [class*='item-card']",
    }

    for alias in aliases:
        try:
            # Handle any age gate that appeared
            await handle_age_gate(page)

            search_inp = page.locator(
                "input[placeholder*='Search'], input[type='search']"
            ).first
            await search_inp.click(timeout=4000)
            await search_inp.fill("", timeout=2000)
            await search_inp.type(alias, delay=70)
            await page.wait_for_timeout(2500)

            # Handle age gate after search
            await handle_age_gate(page)

            page_text = await page.inner_text("body")

            # Check if any results visible
            if "no result" in page_text.lower() or "not found" in page_text.lower():
                continue

            if not loose_match(alias, page_text):
                continue

            # Try to get price from matching card
            price = None
            try:
                cards = page.locator(card_sels.get(platform, "[class*='card']"))
                count = await cards.count()
                for i in range(min(count, 20)):
                    ct = await cards.nth(i).inner_text(timeout=800)
                    if loose_match(alias, ct):
                        m = re.search(r'₹\s*(\d+)', ct)
                        if m:
                            price = f"₹{m.group(1)}"
                        break
            except Exception:
                pass

            return True, price

        except Exception:
            continue

    return False, None


# ── HTML BUILDER ──────────────────────────────────────────────
def build_html(rows, run_dt):
    data_str = json.dumps(rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Q-Commerce Availability · ECAL Branch</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{{--bg:#080d1a;--surface:#0e1628;--border:#1e2d4a;--gold:#c9a84c;--gold2:#e8c97a;--text:#dce8ff;--muted:#6b82a8;--green:#22c55e}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh}}
  header{{border-bottom:1px solid var(--border);padding:20px 32px;display:flex;align-items:center;justify-content:space-between;background:linear-gradient(90deg,#080d1a 60%,#0f1c35)}}
  .logo{{display:flex;align-items:center;gap:14px}}
  .logo-mark{{width:38px;height:38px;border-radius:8px;background:linear-gradient(135deg,#c9a84c,#7a5a1a);display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:800;color:#fff}}
  h1{{font-size:1.15rem;font-weight:700;letter-spacing:.5px}}
  .subtitle{{font-size:.75rem;color:var(--muted);margin-top:2px;font-family:'DM Mono',monospace}}
  .run-time{{font-size:.7rem;color:var(--muted);font-family:'DM Mono',monospace;text-align:right}}
  .run-time span{{color:var(--gold);font-weight:600}}
  .stats{{display:flex;gap:1px;border-bottom:1px solid var(--border);background:var(--border)}}
  .stat{{flex:1;background:var(--surface);padding:14px 20px;display:flex;flex-direction:column;gap:2px}}
  .stat-val{{font-size:1.6rem;font-weight:800;color:var(--gold);line-height:1}}
  .stat-lbl{{font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px}}
  .filters{{padding:16px 32px;border-bottom:1px solid var(--border);display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start;background:var(--surface)}}
  .filter-group{{display:flex;flex-direction:column;gap:6px}}
  .filter-label{{font-size:.6rem;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted)}}
  .pills{{display:flex;flex-wrap:wrap;gap:5px}}
  .pill{{padding:4px 11px;border-radius:20px;font-size:.72rem;font-weight:600;cursor:pointer;border:1px solid var(--border);background:#12213a;color:var(--muted);transition:all .15s;user-select:none}}
  .pill.active{{background:var(--gold);color:#080d1a;border-color:var(--gold)}}
  .pill:hover:not(.active){{border-color:var(--gold);color:var(--text)}}
  .search-wrap{{display:flex;align-items:flex-end;gap:8px;margin-left:auto}}
  #search{{background:var(--bg);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:8px;font-family:'Syne',sans-serif;font-size:.8rem;width:200px;outline:none}}
  #search:focus{{border-color:var(--gold)}}
  #count-badge{{font-size:.7rem;color:var(--muted);font-family:'DM Mono',monospace;white-space:nowrap;padding-bottom:8px}}
  .table-wrap{{overflow-x:auto;padding:0 0 40px}}
  table{{width:100%;border-collapse:collapse;font-size:.78rem}}
  thead th{{position:sticky;top:0;z-index:10;background:#0b1223;border-bottom:2px solid var(--gold);padding:10px 14px;text-align:left;font-size:.6rem;text-transform:uppercase;letter-spacing:1.2px;color:var(--gold);white-space:nowrap;cursor:pointer}}
  thead th:hover{{color:var(--gold2)}}
  .sort-icon{{opacity:.4;margin-left:4px}}
  thead th.sorted .sort-icon{{opacity:1}}
  tbody tr{{border-bottom:1px solid var(--border);transition:background .1s}}
  tbody tr:hover{{background:#0f1e38}}
  td{{padding:8px 14px;white-space:nowrap}}
  td.sku-name{{white-space:normal;max-width:240px;color:var(--text);font-weight:500}}
  td.brand{{color:var(--gold2);font-weight:600}}
  td.segment{{font-family:'DM Mono',monospace;font-size:.68rem;color:var(--muted)}}
  td.tier-premium{{color:#a78bfa}}
  td.tier-uppermid{{color:#60a5fa}}
  .avail-yes{{display:inline-flex;align-items:center;gap:4px;color:var(--green);font-weight:700;font-size:.75rem}}
  .avail-no{{display:inline-flex;align-items:center;gap:4px;color:#374151;font-size:.75rem}}
  .dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0}}
  .dot-yes{{background:var(--green);box-shadow:0 0 6px var(--green)}}
  .dot-no{{background:#374151}}
  .price-tag{{font-family:'DM Mono',monospace;font-size:.7rem;color:#94a3b8;background:#12213a;padding:1px 6px;border-radius:4px}}
  .platform-tag{{font-size:.62rem;font-weight:700;letter-spacing:.5px;padding:2px 8px;border-radius:4px;text-transform:uppercase}}
  .plat-blinkit{{background:#1a2e0a;color:#86efac}}
  .plat-zepto{{background:#2a1040;color:#c4b5fd}}
  .plat-swiggy{{background:#2a1010;color:#fca5a5}}
  #empty{{text-align:center;padding:60px 20px;color:var(--muted);font-size:.9rem;display:none}}
</style>
</head>
<body>
<header>
  <div class="logo">
    <div class="logo-mark">Q</div>
    <div><h1>Q-Commerce Availability Tracker</h1><div class="subtitle">ECAL Branch · Premium + Upper Mid Zones</div></div>
  </div>
  <div class="run-time">Updated<br><span>{run_dt}</span></div>
</header>
<div class="stats">
  <div class="stat"><div class="stat-val" id="s-total">—</div><div class="stat-lbl">Total Checks</div></div>
  <div class="stat"><div class="stat-val" id="s-avail">—</div><div class="stat-lbl">Available</div></div>
  <div class="stat"><div class="stat-val" id="s-pct">—</div><div class="stat-lbl">Availability %</div></div>
  <div class="stat"><div class="stat-val" id="s-pins">—</div><div class="stat-lbl">Pincodes</div></div>
  <div class="stat"><div class="stat-val" id="s-skus">—</div><div class="stat-lbl">SKUs Tracked</div></div>
</div>
<div class="filters">
  <div class="filter-group"><div class="filter-label">Platform</div><div class="pills" id="f-platform"></div></div>
  <div class="filter-group"><div class="filter-label">Tier</div><div class="pills" id="f-tier"></div></div>
  <div class="filter-group"><div class="filter-label">Area / Pincode</div><div class="pills" id="f-area"></div></div>
  <div class="filter-group"><div class="filter-label">Brand</div><div class="pills" id="f-brand"></div></div>
  <div class="filter-group"><div class="filter-label">Segment</div><div class="pills" id="f-segment"></div></div>
  <div class="filter-group"><div class="filter-label">Availability</div><div class="pills" id="f-avail"></div></div>
  <div class="search-wrap">
    <div><div class="filter-label">Search SKU</div><input id="search" type="text" placeholder="type to filter…"></div>
    <div id="count-badge">— rows</div>
  </div>
</div>
<div class="table-wrap">
  <table>
    <thead><tr>
      <th data-col="platform">Platform <span class="sort-icon">↕</span></th>
      <th data-col="pincode">Pincode <span class="sort-icon">↕</span></th>
      <th data-col="area">Area <span class="sort-icon">↕</span></th>
      <th data-col="tier">Tier <span class="sort-icon">↕</span></th>
      <th data-col="brand">Brand <span class="sort-icon">↕</span></th>
      <th data-col="sku_name">SKU Name <span class="sort-icon">↕</span></th>
      <th data-col="segment">Segment <span class="sort-icon">↕</span></th>
      <th data-col="available">Available <span class="sort-icon">↕</span></th>
      <th data-col="price">Price <span class="sort-icon">↕</span></th>
    </tr></thead>
    <tbody id="tbody"></tbody>
  </table>
  <div id="empty">No results match your filters</div>
</div>
<script>
const RAW={data_str};
const state={{platform:new Set(['ALL']),tier:new Set(['ALL']),area:new Set(['ALL']),brand:new Set(['ALL']),segment:new Set(['ALL']),avail:new Set(['ALL']),search:''}};
let sortCol=null,sortDir=1;
const uniq=k=>[...new Set(RAW.map(r=>r[k]).filter(Boolean))].sort();
function buildPills(id,key,vals){{
  const w=document.getElementById(id);
  ['ALL',...vals].forEach(v=>{{
    const p=document.createElement('span');
    p.className='pill'+(v==='ALL'?' active':'');p.textContent=v==='ALL'?'All':v;p.dataset.val=v;
    p.addEventListener('click',()=>toggle(key,v,w));w.appendChild(p);
  }});
}}
function toggle(key,val,wrap){{
  const s=state[key];
  if(val==='ALL'){{s.clear();s.add('ALL');}}else{{s.delete('ALL');s.has(val)?s.delete(val):s.add(val);if(!s.size)s.add('ALL');}}
  wrap.querySelectorAll('.pill').forEach(p=>p.classList.toggle('active',s.has(p.dataset.val)));render();
}}
function filtered(){{
  return RAW.filter(r=>{{
    if(!state.platform.has('ALL')&&!state.platform.has(r.platform))return false;
    if(!state.tier.has('ALL')&&!state.tier.has(r.tier))return false;
    if(!state.area.has('ALL')&&!state.area.has(r.area))return false;
    if(!state.brand.has('ALL')&&!state.brand.has(r.brand))return false;
    if(!state.segment.has('ALL')&&!state.segment.has(r.segment))return false;
    if(!state.avail.has('ALL')){{if(state.avail.has('Available')&&r.available!==100)return false;if(state.avail.has('Unavailable')&&r.available===100)return false;}}
    if(state.search){{const q=state.search.toLowerCase();if(!(r.sku_name||'').toLowerCase().includes(q)&&!(r.brand||'').toLowerCase().includes(q)&&!(r.area||'').toLowerCase().includes(q))return false;}}
    return true;
  }}).sort((a,b)=>{{if(!sortCol)return 0;const va=a[sortCol]??'',vb=b[sortCol]??'';return va<vb?-sortDir:va>vb?sortDir:0;}});
}}
function pc(p){{return p==='Blinkit'?'plat-blinkit':p==='Zepto'?'plat-zepto':'plat-swiggy';}}
function render(){{
  const rows=filtered();
  document.getElementById('count-badge').textContent=rows.length+' rows';
  const av=rows.filter(r=>r.available===100);
  document.getElementById('s-total').textContent=rows.length.toLocaleString();
  document.getElementById('s-avail').textContent=av.length.toLocaleString();
  document.getElementById('s-pct').textContent=rows.length?Math.round(av.length/rows.length*100)+'%':'—';
  document.getElementById('s-pins').textContent=new Set(rows.map(r=>r.pincode)).size;
  document.getElementById('s-skus').textContent=new Set(rows.map(r=>r.market_sku)).size;
  document.getElementById('empty').style.display=rows.length?'none':'block';
  document.getElementById('tbody').innerHTML=rows.map(r=>`<tr>
    <td><span class="platform-tag ${{pc(r.platform)}}">${{r.platform}}</span></td>
    <td style="font-family:'DM Mono',monospace;font-size:.72rem;color:#94a3b8">${{r.pincode}}</td>
    <td>${{r.area}}</td>
    <td class="tier-${{(r.tier||'').toLowerCase().replace(' ','')}}">${{r.tier}}</td>
    <td class="brand">${{r.brand}}</td>
    <td class="sku-name">${{r.sku_name}}</td>
    <td class="segment">${{r.segment}}</td>
    <td>${{r.available===100?'<span class="avail-yes"><span class="dot dot-yes"></span>Yes</span>':'<span class="avail-no"><span class="dot dot-no"></span>No</span>'}}</td>
    <td>${{r.price?`<span class="price-tag">${{r.price}}</span>`:''}}</td>
  </tr>`).join('');
}}
document.querySelectorAll('thead th').forEach(th=>{{
  th.addEventListener('click',()=>{{
    const col=th.dataset.col;sortCol===col?sortDir*=-1:(sortCol=col,sortDir=1);
    document.querySelectorAll('thead th').forEach(t=>t.classList.remove('sorted'));
    th.classList.add('sorted');th.querySelector('.sort-icon').textContent=sortDir===1?'↓':'↑';render();
  }});
}});
document.getElementById('search').addEventListener('input',e=>{{state.search=e.target.value.trim();render();}});
buildPills('f-platform','platform',uniq('platform'));
buildPills('f-tier','tier',uniq('tier'));
buildPills('f-area','area',uniq('area'));
buildPills('f-brand','brand',uniq('brand'));
buildPills('f-segment','segment',uniq('segment'));
const aw=document.getElementById('f-avail');
['ALL','Available','Unavailable'].forEach(v=>{{
  const p=document.createElement('span');p.className='pill'+(v==='ALL'?' active':'');
  p.textContent=v==='ALL'?'All':v;p.dataset.val=v;
  p.addEventListener('click',()=>toggle('avail',v,aw));aw.appendChild(p);
}});
render();
</script>
</body></html>"""


# ── MAIN ──────────────────────────────────────────────────────
async def run():
    all_rows = []
    run_dt = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    ).strftime("%d %b %Y, %I:%M %p IST")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage",
                  "--disable-blink-features=AutomationControlled"]
        )

        total = len(PINCODES) * len(PLATFORMS)
        done = 0

        for (pincode, area, tier) in PINCODES:
            print(f"\n📍 {pincode} {area} [{tier}]")

            for platform in PLATFORMS:
                done += 1
                print(f"  🏪 {platform} ({done}/{total})")

                page = await browser.new_page()
                await page.add_init_script(
                    "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
                )

                loc_ok = await set_location(page, pincode, platform)

                if not loc_ok:
                    print(f"    ⚠️  Location failed")
                    for s in SKUS:
                        all_rows.append({
                            "platform":platform,"pincode":pincode,"area":area,"tier":tier,
                            "brand":s[1],"market_sku":s[0],"sku_name":s[2],"segment":s[3],
                            "available":0,"price":None,"notes":"location_failed",
                        })
                    await page.close()
                    continue

                for sku in SKUS:
                    found, price = await search_sku(page, sku, platform)
                    icon = f"✅ {price}" if found else "❌"
                    print(f"    {icon:<12} {sku[2][:45]}")
                    all_rows.append({
                        "platform":platform,"pincode":pincode,"area":area,"tier":tier,
                        "brand":sku[1],"market_sku":sku[0],"sku_name":sku[2],"segment":sku[3],
                        "available":100 if found else 0,"price":price,"notes":"",
                        "checked_at":run_dt,
                    })
                    await asyncio.sleep(0.6)

                await page.close()

        await browser.close()

    html = build_html(all_rows, run_dt)
    with open("index.html","w",encoding="utf-8") as f:
        f.write(html)
    with open("last_run.txt","w") as f:
        f.write(run_dt)

    print(f"\n✅ Done — {len(all_rows)} rows. index.html updated.")


if __name__ == "__main__":
    asyncio.run(run())
