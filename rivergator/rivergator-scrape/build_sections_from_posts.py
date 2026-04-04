"""
Build section pages using ONLY mile markers that have actual Ghost posts.
No more 404s — every dot on the map links to a real page.
"""

import json, os, re, subprocess

USACE_PATH = "C:/Users/scott/lmrf/rivergator/content-markdown/usace-mile-coordinates.json"
RIVER_PATH = "C:/Users/scott/lmrf/rivergator/book-preview/river_coords_clean.txt"
SLUG_JS_PATH = "C:/Users/scott/lmrf/rivergator/ghost-import/mile-to-slug.js"
OUTPUT_DIR = "C:/Users/scott/lmrf/rivergator/book-preview"
MAPBOX = "pk.eyJ1Ijoic3NoaXJleTc2IiwiYSI6ImNtbmdmeHphNDA4aW8yd29wbWgxYTY3cWcifQ.34MAJqDY8qcKm_48AMQuNQ"
SITE = "http://35.188.103.101"
CONTENT_KEY = "e7387ee5394ff913c8b7d38c51"

with open(USACE_PATH) as f:
    usace = json.load(f)
miss = usace.get('MISSISSIPPI-LO', {})

with open(RIVER_PATH) as f:
    all_river = json.loads(f.read())

with open(SLUG_JS_PATH) as f:
    slug_js = f.read()

# Fetch all posts from Ghost
print("Fetching posts from Ghost...")
all_posts = []
for page in range(1, 20):
    result = subprocess.run(['curl', '-s',
        f'{SITE}/ghost/api/content/posts/?key={CONTENT_KEY}&fields=slug,title&limit=100&page={page}&include=tags'],
        capture_output=True)
    data = json.loads(result.stdout)
    posts = data.get('posts', [])
    if not posts: break
    all_posts.extend(posts)
print(f"Total posts: {len(all_posts)}")

# Parse mile markers and group by section, deduplicate
section_markers = {}
seen_per_section = {}

for p in all_posts:
    section = ''
    for t in p.get('tags', []):
        if t['slug'] in ['stlouis-to-caruthersville','caruthersville-to-memphis','memphis-to-helena',
                        'helena-to-greenville','greenville-to-vicksburg','vicksburg-to-baton-rouge',
                        'atchafalaya-river','baton-rouge-to-venice','birdsfoot-delta']:
            section = t['slug']

    m = re.match(r'Mile (\d+(?:\.\d+)?)\s*(LBD|RBD)?\s*', p['title'])
    if m and section:
        mile = float(m.group(1))
        bank = m.group(2) or ''
        name_match = re.search(r'[—–-]\s*(.+)', p['title'])
        name = name_match.group(1).strip()[:50] if name_match else 'River Feature'

        # Skip bad names
        if name in ['River Feature', 'St'] or len(name) < 3:
            continue

        # Deduplicate: keep first occurrence per mile per section
        key = f"{section}-{round(mile, 1)}"
        if section not in seen_per_section:
            seen_per_section[section] = set()
        if key in seen_per_section[section]:
            continue
        seen_per_section[section].add(key)

        if section not in section_markers:
            section_markers[section] = []

        section_markers[section].append({
            'mile': mile,
            'bank': bank,
            'name': name,
            'slug': p['slug']
        })

for section, markers in sorted(section_markers.items()):
    print(f"  {section}: {len(markers)} unique markers")

# Feature type detection from name
def detect_type(name):
    nl = name.lower()
    if any(w in nl for w in ['ramp', 'landing', 'access', 'harbor', 'lock']): return 'access_point'
    if any(w in nl for w in ['camp', 'sandbar', 'bar', 'island', 'towhead', 'dune']): return 'camping'
    if any(w in nl for w in ['bridge']): return 'bridge'
    if any(w in nl for w in ['town', 'city', 'village', 'welcome']) or name[0].isupper() and ',' in name: return 'town'
    if any(w in nl for w in ['creek', 'bayou', 'river', 'mouth', 'pass', 'confluence']): return 'confluence'
    if any(w in nl for w in ['danger', 'hazard', 'avoid', 'refinery', 'chemical']): return 'hazard'
    return 'other'

def get_coord(mile, bank):
    c = miss.get(str(int(round(mile))))
    if not c:
        closest = min(miss.keys(), key=lambda m: abs(int(m) - mile))
        c = miss[closest]
    lng, lat = c
    offset = 0.003 if bank == 'LBD' else (-0.003 if bank == 'RBD' else 0)
    return round(lng + offset, 5), round(lat, 5)

def river_section(lat_lo, lat_hi):
    return [c for c in all_river if lat_lo - 0.1 <= c[1] <= lat_hi + 0.1]

# Chart sheet PDFs hosted on our server (extracted from original Rivergator)
# These are the USACE navigation chart pages Ruskey referenced
NAV_CHART_SHEETS = {
    "stlouis-to-caruthersville": ["sheet077.pdf", "sheet078.pdf", "sheet078a.pdf"],
    "caruthersville-to-memphis": ["sheet075.pdf", "sheet076.pdf", "sheet076a.pdf", "sheet077.pdf"],
    "memphis-to-helena": ["sheet073.pdf", "sheet074.pdf", "sheet075.pdf"],
    "helena-to-greenville": ["sheet070.pdf", "sheet071.pdf", "sheet072.pdf", "sheet073.pdf"],
    "greenville-to-vicksburg": ["sheet068.pdf", "sheet069.pdf", "sheet070.pdf"],
    "vicksburg-to-baton-rouge": ["sheet065.pdf", "sheet066.pdf", "sheet067.pdf", "sheet068.pdf"],
    "atchafalaya-river": [],
    "baton-rouge-to-venice": ["sheet064.pdf", "sheet065.pdf"],
    "birdsfoot-delta": ["sheet064.pdf"],
}

SECTION_CONFIG = [
    ("stlouis-to-caruthersville", "St. Louis to Caruthersville", "Mile 195–870", (36.1, 38.7), [-89.8, 37.4], 7, None, ("Caruthersville to Memphis", "sections/caruthersville-to-memphis.html")),
    ("caruthersville-to-memphis", "Caruthersville to Memphis", "Mile 850–737", (35.1, 36.2), [-89.8, 35.7], 8, ("St. Louis to Caruthersville", "sections/stlouis-to-caruthersville.html"), ("Memphis to Helena", "section-preview.html")),
    ("memphis-to-helena", "Memphis to Helena", "Mile 737–663", (34.35, 35.2), [-90.3, 34.85], 8, ("Caruthersville to Memphis", "sections/caruthersville-to-memphis.html"), ("Helena to Greenville", "sections/helena-to-greenville.html")),
    ("helena-to-greenville", "Helena to Greenville", "Mile 663–537", (33.3, 34.55), [-90.9, 33.9], 8, ("Memphis to Helena", "section-preview.html"), ("Greenville to Vicksburg", "sections/greenville-to-vicksburg.html")),
    ("greenville-to-vicksburg", "Greenville to Vicksburg", "Mile 537–437", (32.3, 33.5), [-91.0, 32.9], 8, ("Helena to Greenville", "sections/helena-to-greenville.html"), ("Vicksburg to Baton Rouge", "sections/vicksburg-to-baton-rouge.html")),
    ("vicksburg-to-baton-rouge", "Vicksburg to Baton Rouge", "Mile 437–225", (30.4, 32.4), [-91.3, 31.4], 7, ("Greenville to Vicksburg", "sections/greenville-to-vicksburg.html"), ("Atchafalaya River", "sections/atchafalaya-river.html")),
    ("atchafalaya-river", "Atchafalaya River", "Mile 0–310", (29.5, 31.1), [-91.5, 30.3], 8, ("Vicksburg to Baton Rouge", "sections/vicksburg-to-baton-rouge.html"), ("Baton Rouge to Venice", "sections/baton-rouge-to-venice.html")),
    ("baton-rouge-to-venice", "Baton Rouge to Venice", "Mile 229–10", (29.2, 30.5), [-90.3, 29.9], 8, ("Atchafalaya River", "sections/atchafalaya-river.html"), ("Birdsfoot Delta", "sections/birdsfoot-delta.html")),
    ("birdsfoot-delta", "Birdsfoot Delta", "Mile 10–0", (28.9, 29.35), [-89.35, 29.15], 10, ("Baton Rouge to Venice", "sections/baton-rouge-to-venice.html"), None),
]

# Read template from build_all_sections.py output format
# (reusing the same template structure)

for slug, name, miles_label, lat_range, center, zoom, prev, nexts in SECTION_CONFIG:
    markers = section_markers.get(slug, [])
    markers.sort(key=lambda x: -x['mile'])

    # Limit to top 30 markers per section for performance (can increase later)
    if len(markers) > 40:
        # Keep evenly spaced markers
        step = len(markers) // 35
        markers = markers[::step]

    # Build markers JS with USACE coords and actual slugs
    markers_js_items = []
    for m in markers:
        lng, lat = get_coord(m['mile'], m['bank'])
        mtype = detect_type(m['name'])
        markers_js_items.append(
            f'{{mile:{m["mile"]},bank:"{m["bank"]}",name:"{m["name"]}",lng:{lng},lat:{lat},type:"{mtype}",slug:"{m["slug"]}"}}'
        )
    markers_js = "[" + ",".join(markers_js_items) + "]"

    lat_lo, lat_hi = lat_range
    rv = river_section(lat_lo, lat_hi)
    river_js = json.dumps(rv, separators=(',', ':'))

    prev_html = f'<a href="{SITE}/{prev[1]}">&larr; {prev[0]}</a>' if prev else '<span></span>'
    next_html = f'<a href="{SITE}/{nexts[1]}">{nexts[0]} &rarr;</a>' if nexts else '<span></span>'

    # Nav chart sheet PDFs for this section
    chart_sheets = NAV_CHART_SHEETS.get(slug, [])
    nav_chart_codes_js = json.dumps(chart_sheets)

    # Use slug directly from marker data instead of generating it
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} — The Rivergator</title>
<link href="https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.css" rel="stylesheet">
<script src="https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Georgia',serif;background:#f8f6f2;color:#1a1a1a}}
.site-header{{background:#1B4965;color:white;padding:16px 20px}}
.site-header h1{{font-size:22px}}.site-header h1 a{{color:white;text-decoration:none}}
.site-nav{{background:#15374d;display:flex;justify-content:center;flex-wrap:wrap}}
.site-nav a{{color:#a8cce0;text-decoration:none;font-family:'Helvetica Neue',Arial,sans-serif;font-size:13px;font-weight:500;text-transform:uppercase;letter-spacing:1.5px;padding:12px 20px}}
.site-nav a:hover,.site-nav a.active{{color:white;background:rgba(255,255,255,0.1)}}
.breadcrumb{{font-family:'Helvetica Neue',Arial,sans-serif;font-size:13px;color:#888;padding:12px 20px;max-width:1100px;margin:0 auto}}
.breadcrumb a{{color:#1B4965;text-decoration:none}}
.section-hero{{max-width:1100px;margin:0 auto;padding:0 20px 24px}}
.section-hero h1{{font-size:32px;color:#1B4965;margin-bottom:4px}}
.section-hero .mile-range{{font-family:'Helvetica Neue',Arial,sans-serif;font-size:15px;color:#888;font-style:italic}}
.section-stats{{display:flex;gap:24px;padding:16px 0;border-top:1px solid #e0ddd6;border-bottom:1px solid #e0ddd6;margin-bottom:20px}}
.section-stat{{text-align:center}}.section-stat .num{{font-family:'Helvetica Neue',Arial,sans-serif;font-size:22px;font-weight:700;color:#1B4965}}.section-stat .label{{font-family:'Helvetica Neue',Arial,sans-serif;font-size:11px;color:#999;text-transform:uppercase;letter-spacing:0.5px}}
.section-layout{{max-width:1100px;margin:0 auto;padding:0 20px 40px;display:grid;grid-template-columns:1fr 340px;gap:24px}}
.section-map{{height:450px;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.1);position:relative}}
#map{{width:100%;height:100%}}
.map-style-toggle{{position:absolute;top:12px;left:12px;z-index:10;display:flex;background:white;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.3);overflow:hidden}}
.map-style-toggle button{{border:none;background:white;color:#333;padding:12px 20px;font-size:14px;font-weight:700;cursor:pointer}}
.map-style-toggle button.active{{background:#1B4965;color:white}}
.map-style-toggle button:hover:not(.active){{background:#e0eef5}}
.map-style-toggle button:not(:last-child){{border-right:1px solid #ddd}}
.map-legend{{display:flex;gap:16px;padding:10px 0;flex-wrap:wrap}}
.legend-item{{display:flex;align-items:center;gap:6px;font-family:'Helvetica Neue',Arial,sans-serif;font-size:12px;color:#666}}
.legend-dot{{width:10px;height:10px;border-radius:50%}}
.chapter-list{{background:white;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.08);overflow:hidden}}
.chapter-list-header{{background:#1B4965;color:white;padding:14px 18px;font-family:'Helvetica Neue',Arial,sans-serif;font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:1px}}
.chapter-card{{display:block;padding:12px 16px;border-bottom:1px solid #eee;cursor:pointer;transition:background 0.15s}}
.chapter-card:hover{{background:#f0f5f8}}
.chapter-card.highlighted{{background:#dceef8;border-left:4px solid #1B4965}}
.chapter-card h3{{font-size:15px;color:#1B4965;margin:0 0 2px}}.chapter-card .chapter-meta{{font-family:'Helvetica Neue',Arial,sans-serif;font-size:11px;color:#999}}
.chapter-type{{display:inline-block;font-family:'Helvetica Neue',Arial,sans-serif;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;padding:2px 8px;border-radius:10px;margin-bottom:4px}}
.section-nav{{max-width:1100px;margin:0 auto;padding:0 20px 40px;display:flex;justify-content:space-between}}
.section-nav a{{font-family:'Helvetica Neue',Arial,sans-serif;font-size:14px;color:#1B4965;text-decoration:none;padding:10px 16px;border:1px solid #d0d0d0;border-radius:6px}}.section-nav a:hover{{background:#e0eef5}}
.site-footer{{text-align:center;padding:24px 20px;color:#999;font-size:13px;border-top:1px solid #e0ddd6}}.site-footer a{{color:#1B4965;text-decoration:none}}
.mapboxgl-popup-content{{padding:10px 14px;border-radius:6px;max-width:240px}}.popup-title{{font-weight:700;color:#1B4965;font-size:13px}}.popup-detail{{font-size:11px;color:#666;margin-top:2px}}.popup-link{{display:block;margin-top:6px;font-size:12px;color:#1B4965;font-weight:600;text-decoration:none}}
@media(max-width:768px){{.section-layout{{grid-template-columns:1fr}}.section-map{{height:300px}}.section-hero h1{{font-size:24px}}}}
</style>
</head>
<body>
<header class="site-header"><h1><a href="{SITE}">The Rivergator</a></h1></header>
<nav class="site-nav"><a href="{SITE}" class="active">River Log</a><a href="#">Paddler's Guide</a><a href="#">Resources</a><a href="#">About</a></nav>
<div class="breadcrumb"><a href="{SITE}">River Log</a> &rsaquo; {name}</div>
<div class="section-hero">
<h1>{name}</h1>
<div class="mile-range">{miles_label}</div>
<div class="section-stats">
<div class="section-stat"><div class="num">{len(markers)}</div><div class="label">Markers</div></div>
</div>
</div>
<div class="section-layout">
<div>
<div class="section-map"><div id="map"></div>
<div class="map-style-toggle"><button class="active" id="btn-terrain">Terrain</button><button id="btn-satellite">Satellite</button></div>
</div>
<div class="map-legend">
<div class="legend-item"><div class="legend-dot" style="background:#2ecc71"></div> Access</div>
<div class="legend-item"><div class="legend-dot" style="background:#e67e22"></div> Camping</div>
<div class="legend-item"><div class="legend-dot" style="background:#e74c3c"></div> Hazard</div>
<div class="legend-item"><div class="legend-dot" style="background:#3498db"></div> Bridge/Creek</div>
<div class="legend-item"><div class="legend-dot" style="background:#9b59b6"></div> Town</div>
</div>
</div>
<div class="chapter-list"><div class="chapter-list-header">Mile Markers</div><div id="marker-list" style="max-height:400px;overflow-y:auto;"></div></div>
</div>
<div class="section-nav">{prev_html}{next_html}</div>
<footer class="site-footer"><p>The Rivergator &copy; <a href="https://lowermsfoundation.org">Lower Mississippi River Foundation</a></p><p style="margin-top:4px">Written by John Ruskey</p></footer>
<script>
mapboxgl.accessToken='{MAPBOX}';
const markers={markers_js};
const typeColors={{access_point:'#2ecc71',camping:'#e67e22',hazard:'#e74c3c',bridge:'#3498db',town:'#9b59b6',confluence:'#3498db',other:'#7f8c8d'}};
const riverCoords={river_js};
const map=new mapboxgl.Map({{container:'map',style:'mapbox://styles/mapbox/outdoors-v12',center:{json.dumps(center)},zoom:{zoom}}});
map.addControl(new mapboxgl.NavigationControl(),'top-right');
function addRiverLine(){{if(map.getSource('river'))return;map.addSource('river',{{type:'geojson',data:{{type:'Feature',geometry:{{type:'LineString',coordinates:riverCoords}}}}}});map.addLayer({{id:'river-glow',type:'line',source:'river',paint:{{'line-color':'#1B4965','line-width':6,'line-opacity':0.3,'line-blur':2}}}});map.addLayer({{id:'river-line',type:'line',source:'river',paint:{{'line-color':'#1B4965','line-width':3,'line-opacity':0.8}}}})}}
const markerEls={{}},mapMarkers={{}};
function highlightMarker(mile){{document.querySelectorAll('.chapter-card.highlighted').forEach(el=>el.classList.remove('highlighted'));const card=document.getElementById('card-'+mile);if(card){{card.classList.add('highlighted');const list=document.getElementById('marker-list');const cardTop=card.offsetTop-list.offsetTop;list.scrollTo({{top:cardTop-list.clientHeight/3,behavior:'smooth'}})}}Object.keys(markerEls).forEach(k=>{{const el=markerEls[k];if(k==mile){{el.style.width='18px';el.style.height='18px';el.style.border='3px solid #1B4965'}}else{{el.style.width='12px';el.style.height='12px';el.style.border='2px solid white'}}}})}}
function addMarkers(){{const list=document.getElementById('marker-list');list.innerHTML='';markers.forEach(m=>{{const color=typeColors[m.type]||'#7f8c8d';const el=document.createElement('div');el.style.cssText='background:'+color+';width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3);cursor:pointer;transition:all 0.2s;';markerEls[m.mile]=el;const popup=new mapboxgl.Popup({{offset:10}}).setHTML('<div class="popup-title">Mile '+m.mile+' '+m.bank+'</div><div class="popup-detail">'+m.name+'</div><a class="popup-link" href="{SITE}/'+m.slug+'/">Read guide &rarr;</a>');const marker=new mapboxgl.Marker(el).setLngLat([m.lng,m.lat]).setPopup(popup).addTo(map);mapMarkers[m.mile]=marker;el.addEventListener('click',()=>highlightMarker(m.mile));const card=document.createElement('div');card.className='chapter-card';card.id='card-'+m.mile;card.style.cursor='pointer';card.innerHTML='<div class="chapter-type" style="background:'+color+'22;color:'+color+';border:1px solid '+color+'44;">Mile '+m.mile+' '+m.bank+'</div><h3>'+m.name+'</h3><a href="{SITE}/'+m.slug+'/" style="font-size:12px;color:#1B4965;font-weight:600;text-decoration:none;" onclick="event.stopPropagation()">Read guide &rarr;</a>';card.addEventListener('click',()=>{{map.flyTo({{center:[m.lng,m.lat],zoom:12,duration:1200}});Object.values(mapMarkers).forEach(mk=>{{if(mk.getPopup().isOpen())mk.togglePopup()}});marker.togglePopup();highlightMarker(m.mile)}});list.appendChild(card)}})}}
map.on('load',()=>{{addRiverLine();addMarkers()}});
document.getElementById('btn-terrain').onclick=()=>{{map.setStyle('mapbox://styles/mapbox/outdoors-v12');setActive('btn-terrain');map.once('style.load',()=>{{addRiverLine();addMarkers()}})}};
document.getElementById('btn-satellite').onclick=()=>{{map.setStyle('mapbox://styles/mapbox/satellite-streets-v12');setActive('btn-satellite');map.once('style.load',()=>{{addRiverLine();addMarkers()}})}};
function setActive(id){{document.querySelectorAll('.map-style-toggle button').forEach(b=>b.classList.remove('active'));document.getElementById(id).classList.add('active')}}
</script>
</body>
</html>'''

    file_map = {
        'memphis-to-helena': 'section-preview.html',
    }
    filename = file_map.get(slug, f'sections/{slug}.html')
    path = os.path.join(OUTPUT_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Built: {filename} ({len(markers)} markers, all with real posts)")

print("\nDone! All 9 sections rebuilt with verified slugs.")
