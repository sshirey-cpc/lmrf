"""
Build all 9 section pages with:
- Interactive map↔sidebar (click dot → sidebar scrolls, click sidebar → map zooms)
- "Read guide →" links using actual Ghost post slug lookup
- USACE mile marker coordinates
- River line overlay
- Terrain/satellite toggle
"""

import json
import os
import re

OUTPUT_DIR = "C:/Users/scott/lmrf/rivergator/book-preview"
USACE_PATH = "C:/Users/scott/lmrf/rivergator/content-markdown/usace-mile-coordinates.json"
RIVER_PATH = "C:/Users/scott/lmrf/rivergator/book-preview/river_coords_clean.txt"
SLUG_PATH = "C:/Users/scott/lmrf/rivergator/ghost-import/mile-to-slug.js"
MAPBOX = "pk.eyJ1Ijoic3NoaXJleTc2IiwiYSI6ImNtbmdmeHphNDA4aW8yd29wbWgxYTY3cWcifQ.34MAJqDY8qcKm_48AMQuNQ"
SITE = "http://35.188.103.101"

with open(USACE_PATH) as f:
    usace = json.load(f)
miss = usace.get('MISSISSIPPI-LO', {})
atch = usace.get('LO-ATCHAFALAYA, ABOVE BERWICK LOCK', {})

with open(RIVER_PATH) as f:
    all_river = json.loads(f.read())

with open(SLUG_PATH) as f:
    slug_js = f.read()

def get_coord(mile, bank, river='miss'):
    coords = miss if river == 'miss' else atch
    c = coords.get(str(int(round(mile))))
    if not c:
        closest = min(coords.keys(), key=lambda m: abs(int(m) - mile))
        c = coords[closest]
    lng, lat = c
    offset = 0.003 if bank == 'LBD' else -0.003
    return round(lng + offset, 5), round(lat, 5)

def river_section(lat_lo, lat_hi):
    return [c for c in all_river if lat_lo - 0.1 <= c[1] <= lat_hi + 0.1]

SECTIONS = [
    {
        "slug": "stlouis-to-caruthersville",
        "file": "sections/stlouis-to-caruthersville.html",
        "name": "St. Louis to Caruthersville",
        "miles_label": "Mile 195–870",
        "lat_range": (36.1, 38.7),
        "center": [-89.8, 37.4], "zoom": 7,
        "prev": None,
        "next": ("Caruthersville to Memphis", "sections/caruthersville-to-memphis.html"),
        "markers": [
            (200.6, 'RBD', 'Maple Island Access Ramp', 'access_point'),
            (194.2, 'LBD', 'Chain of Rocks Canal', 'access_point'),
            (183.4, 'RBD', 'Mary Meachum Freedom Crossing', 'other'),
            (174.0, 'RBD', 'Bellerive Park', 'access_point'),
            (166.7, 'RBD', 'Cliff Cave County Park', 'camping'),
            (158.7, 'RBD', 'Kimmswick', 'town'),
            (148.5, 'RBD', 'Plattin Creek', 'confluence'),
            (109.9, 'RBD', 'Chester Bridge', 'bridge'),
            (88.4, 'LBD', "LaCour's Island", 'island'),
            (80.0, 'RBD', 'Tower Rock', 'other'),
            (66.6, 'RBD', 'Moccasin Springs Harbor', 'access_point'),
            (52.0, 'LBD', 'Cairo, Illinois', 'town'),
            (953.0, 'RBD', "Birds Point Dikes", 'camping'),
            (937.2, 'LBD', 'Columbus-Belmont State Park', 'access_point'),
            (924.6, 'RBD', 'Dorena Boat Ramp', 'access_point'),
            (878.0, 'LBD', 'Marr Towhead Secret Sandbar', 'camping'),
        ],
    },
    {
        "slug": "caruthersville-to-memphis",
        "file": "sections/caruthersville-to-memphis.html",
        "name": "Caruthersville to Memphis",
        "miles_label": "Mile 850–737",
        "lat_range": (35.1, 36.2),
        "center": [-89.8, 35.7], "zoom": 8,
        "prev": ("St. Louis to Caruthersville", "sections/stlouis-to-caruthersville.html"),
        "next": ("Memphis to Helena", "section-preview.html"),
        "markers": [
            (850.0, 'RBD', 'Caruthersville Harbor', 'access_point'),
            (830.0, 'LBD', 'Osceola, Arkansas', 'town'),
            (811.0, 'RBD', 'Barfield Landing', 'access_point'),
            (800.0, 'LBD', 'Loosahatchie Bar', 'camping'),
            (785.0, 'RBD', 'Brandywine Chute', 'island'),
            (770.0, 'LBD', 'Shelby Forest', 'camping'),
            (758.0, 'LBD', 'Densford Bar and Dikes', 'island'),
            (749.0, 'LBD', 'Hickman Bar', 'camping'),
            (742.0, 'RBD', 'Fulton, Tennessee', 'town'),
            (737.0, 'LBD', 'Memphis', 'town'),
        ],
    },
    {
        "slug": "memphis-to-helena",
        "file": "section-preview.html",
        "name": "Memphis to Helena",
        "miles_label": "Mile 737–663",
        "lat_range": (34.35, 35.2),
        "center": [-90.3, 34.85], "zoom": 8,
        "prev": ("Caruthersville to Memphis", "sections/caruthersville-to-memphis.html"),
        "next": ("Helena to Greenville", "sections/helena-to-greenville.html"),
        "markers": [
            (736, 'LBD', 'Memphis, Mud Island Harbor', 'access_point'),
            (735, 'LBD', 'Memphis Bridges', 'bridge'),
            (733, 'RBD', 'Presidents Island', 'island'),
            (727, 'RBD', 'TVA Transmission Lines', 'hazard'),
            (725, 'LBD', 'McKellar Lake Harbor', 'harbor'),
            (722, 'RBD', 'Dismal Point / Ensley Bar', 'camping'),
            (715, 'LBD', 'Cat Island No. 50', 'camping'),
            (700, 'RBD', 'Tunica / Basket Bar', 'access_point'),
            (688, 'LBD', 'Mhoon Landing', 'access_point'),
            (672, 'RBD', 'Mouth of the St. Francis River', 'confluence'),
            (663, 'RBD', 'Helena Harbor', 'access_point'),
            (662, 'LBD', 'Helena Bridge (US 49)', 'bridge'),
            (657, 'LBD', 'Yazoo Pass Entrance', 'other'),
            (655, 'LBD', 'Montezuma Landing', 'access_point'),
            (652, 'LBD', 'Friars Point', 'town'),
        ],
    },
    {
        "slug": "helena-to-greenville",
        "file": "sections/helena-to-greenville.html",
        "name": "Helena to Greenville",
        "miles_label": "Mile 663–537",
        "lat_range": (33.3, 34.55),
        "center": [-90.9, 33.9], "zoom": 8,
        "prev": ("Memphis to Helena", "section-preview.html"),
        "next": ("Greenville to Vicksburg", "sections/greenville-to-vicksburg.html"),
        "markers": [
            (663, 'RBD', 'Helena Harbor', 'access_point'),
            (652, 'LBD', 'Friars Point', 'town'),
            (641, 'LBD', 'Island 62', 'camping'),
            (637, 'LBD', 'Island 63 / Quapaw Landing', 'camping'),
            (630, 'RBD', 'Sunflower River Cutoff', 'confluence'),
            (620, 'LBD', 'Rosedale', 'town'),
            (610, 'RBD', 'Hurricane Island', 'island'),
            (601, 'LBD', 'Smith Point Sandbar', 'camping'),
            (590, 'RBD', 'Mound Landing', 'access_point'),
            (580, 'LBD', 'Winterville area', 'other'),
            (562, 'LBD', 'Arkansas City', 'town'),
            (537, 'LBD', 'Greenville, MS', 'town'),
        ],
    },
    {
        "slug": "greenville-to-vicksburg",
        "file": "sections/greenville-to-vicksburg.html",
        "name": "Greenville to Vicksburg",
        "miles_label": "Mile 537–437",
        "lat_range": (32.3, 33.5),
        "center": [-91.0, 32.9], "zoom": 8,
        "prev": ("Helena to Greenville", "sections/helena-to-greenville.html"),
        "next": ("Vicksburg to Baton Rouge", "sections/vicksburg-to-baton-rouge.html"),
        "markers": [
            (537, 'LBD', 'Greenville, MS', 'town'),
            (520, 'RBD', 'Lake Village, AR', 'town'),
            (500, 'RBD', 'Opossum Chute', 'island'),
            (487, 'LBD', 'Lake Providence', 'town'),
            (475, 'RBD', 'Baxter Bend', 'camping'),
            (462, 'LBD', 'Omega Bend', 'other'),
            (458, 'LBD', 'Eagle Lake Pass', 'confluence'),
            (445, 'RBD', 'Yazoo River Diversion Canal', 'confluence'),
            (437, 'LBD', 'Vicksburg, MS', 'town'),
        ],
    },
    {
        "slug": "vicksburg-to-baton-rouge",
        "file": "sections/vicksburg-to-baton-rouge.html",
        "name": "Vicksburg to Baton Rouge",
        "miles_label": "Mile 437–225",
        "lat_range": (30.4, 32.4),
        "center": [-91.3, 31.4], "zoom": 7,
        "prev": ("Greenville to Vicksburg", "sections/greenville-to-vicksburg.html"),
        "next": ("Atchafalaya River", "sections/atchafalaya-river.html"),
        "markers": [
            (437, 'LBD', 'Vicksburg, MS', 'town'),
            (425, 'RBD', 'Grand Gulf', 'access_point'),
            (400, 'RBD', 'Rodney Landing', 'access_point'),
            (380, 'RBD', 'Cole Creek', 'camping'),
            (365, 'RBD', 'Old River / Atchafalaya Split', 'confluence'),
            (364, 'LBD', 'Natchez, MS', 'town'),
            (340, 'RBD', 'Vidalia, LA', 'town'),
            (310, 'LBD', 'Wilkinson Creek', 'confluence'),
            (305, 'LBD', 'St. Francisville, LA', 'town'),
            (270, 'LBD', 'Port Hudson', 'other'),
            (250, 'RBD', 'Refinery Row', 'hazard'),
            (233, 'LBD', 'Baton Rouge Bridge', 'bridge'),
            (228, 'LBD', 'Baton Rouge, LA', 'town'),
        ],
    },
    {
        "slug": "atchafalaya-river",
        "file": "sections/atchafalaya-river.html",
        "name": "Atchafalaya River",
        "miles_label": "Mile 0–310",
        "lat_range": (29.5, 31.1),
        "center": [-91.5, 30.3], "zoom": 8,
        "prev": ("Vicksburg to Baton Rouge", "sections/vicksburg-to-baton-rouge.html"),
        "next": ("Baton Rouge to Venice", "sections/baton-rouge-to-venice.html"),
        "markers": [
            (310, 'RBD', 'Old River Lock', 'access_point'),
            (280, 'LBD', 'Simmesport', 'town'),
            (250, 'RBD', 'Melville', 'town'),
            (220, 'LBD', 'Krotz Springs', 'town'),
            (190, 'RBD', 'Butte La Rose', 'access_point'),
            (160, 'LBD', 'Henderson Levee', 'access_point'),
            (130, 'LBD', 'Breaux Bridge area', 'town'),
            (100, 'RBD', 'Bayou Benoit', 'confluence'),
            (70, 'LBD', 'Bayou Teche', 'confluence'),
            (40, 'RBD', 'Jeanerette area', 'town'),
            (10, 'LBD', 'Morgan City', 'town'),
        ],
        "river": "atch",
    },
    {
        "slug": "baton-rouge-to-venice",
        "file": "sections/baton-rouge-to-venice.html",
        "name": "Baton Rouge to Venice",
        "miles_label": "Mile 229–10",
        "lat_range": (29.2, 30.5),
        "center": [-90.3, 29.9], "zoom": 8,
        "prev": ("Atchafalaya River", "sections/atchafalaya-river.html"),
        "next": ("Birdsfoot Delta", "sections/birdsfoot-delta.html"),
        "markers": [
            (228, 'LBD', 'Baton Rouge', 'town'),
            (206, 'RBD', 'Donaldsonville', 'town'),
            (178, 'LBD', 'Convent / Calumet', 'other'),
            (150, 'LBD', 'Gramercy', 'town'),
            (132, 'LBD', 'Bonnet Carre Spillway', 'other'),
            (115, 'RBD', 'Destrehan', 'town'),
            (105, 'LBD', 'Bridge City', 'town'),
            (95, 'LBD', 'New Orleans', 'town'),
            (82, 'LBD', 'Chalmette', 'town'),
            (60, 'RBD', 'English Turn', 'other'),
            (40, 'LBD', 'Empire', 'town'),
            (20, 'LBD', 'Buras', 'town'),
            (10, 'LBD', 'Venice', 'town'),
        ],
    },
    {
        "slug": "birdsfoot-delta",
        "file": "sections/birdsfoot-delta.html",
        "name": "Birdsfoot Delta",
        "miles_label": "Mile 10–0",
        "lat_range": (28.9, 29.35),
        "center": [-89.35, 29.15], "zoom": 10,
        "prev": ("Baton Rouge to Venice", "sections/baton-rouge-to-venice.html"),
        "next": None,
        "markers": [
            (10, 'LBD', 'Venice, LA', 'town'),
            (8, 'RBD', 'Baptiste Collette Bayou', 'confluence'),
            (5.5, 'RBD', 'Southeast Pass', 'confluence'),
            (5, 'RBD', 'Pilottown', 'town'),
            (3.4, 'LBD', 'Camping Spot', 'camping'),
            (1.5, 'RBD', 'Lower Shallow Island', 'island'),
            (0.5, 'RBD', 'Head of Passes', 'other'),
        ],
    },
]

TEMPLATE = '''<!DOCTYPE html>
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
.chapter-card{{display:block;padding:12px 16px;border-bottom:1px solid #eee;text-decoration:none;color:inherit;cursor:pointer;transition:background 0.15s}}
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
<header class="site-header"><h1><a href="{site}">The Rivergator</a></h1></header>
<nav class="site-nav"><a href="{site}" class="active">River Log</a><a href="#">Paddler's Guide</a><a href="#">Resources</a><a href="#">About</a></nav>
<div class="breadcrumb"><a href="{site}">River Log</a> &rsaquo; {name}</div>
<div class="section-hero">
<h1>{name}</h1>
<div class="mile-range">{miles_label}</div>
<div class="section-stats">
<div class="section-stat"><div class="num">{num_markers}</div><div class="label">Markers</div></div>
</div>
</div>
<div class="section-layout">
<div>
<div class="section-map"><div id="map"></div>
<div class="map-style-toggle"><button class="active" id="btn-terrain">Terrain</button><button id="btn-satellite">Satellite</button></div>
</div>
<div class="map-legend">
<div class="legend-item"><div class="legend-dot" style="background:#2ecc71"></div> Access Point</div>
<div class="legend-item"><div class="legend-dot" style="background:#e67e22"></div> Camping</div>
<div class="legend-item"><div class="legend-dot" style="background:#e74c3c"></div> Hazard</div>
<div class="legend-item"><div class="legend-dot" style="background:#3498db"></div> Bridge</div>
<div class="legend-item"><div class="legend-dot" style="background:#9b59b6"></div> Town</div>
</div>
</div>
<div class="chapter-list"><div class="chapter-list-header">Mile Markers</div><div id="marker-list" style="max-height:400px;overflow-y:auto;"></div></div>
</div>
<div class="section-nav">{prev_html}{next_html}</div>
<footer class="site-footer"><p>The Rivergator &copy; <a href="https://lowermsfoundation.org">Lower Mississippi River Foundation</a></p><p style="margin-top:4px">Written by John Ruskey</p></footer>
<script>
mapboxgl.accessToken = '{mapbox}';
const markers = {markers_js};
const typeColors = {{access_point:'#2ecc71',camping:'#e67e22',hazard:'#e74c3c',bridge:'#3498db',town:'#9b59b6',harbor:'#2ecc71',island:'#e67e22',confluence:'#3498db',other:'#7f8c8d'}};
const riverCoords = {river_js};
{slug_lookup_js}
const map = new mapboxgl.Map({{container:'map',style:'mapbox://styles/mapbox/outdoors-v12',center:{center_js},zoom:{zoom}}});
map.addControl(new mapboxgl.NavigationControl(),'top-right');
function addRiverLine(){{if(map.getSource('river'))return;map.addSource('river',{{type:'geojson',data:{{type:'Feature',geometry:{{type:'LineString',coordinates:riverCoords}}}}}});map.addLayer({{id:'river-glow',type:'line',source:'river',paint:{{'line-color':'#1B4965','line-width':6,'line-opacity':0.3,'line-blur':2}}}});map.addLayer({{id:'river-line',type:'line',source:'river',paint:{{'line-color':'#1B4965','line-width':3,'line-opacity':0.8}}}})}}
const markerEls={{}},mapMarkers={{}};
function highlightMarker(mile){{document.querySelectorAll('.chapter-card.highlighted').forEach(el=>el.classList.remove('highlighted'));const card=document.getElementById('card-'+mile);if(card){{card.classList.add('highlighted');const list=document.getElementById('marker-list');const cardTop=card.offsetTop-list.offsetTop;list.scrollTo({{top:cardTop-list.clientHeight/3,behavior:'smooth'}})}}Object.keys(markerEls).forEach(k=>{{const el=markerEls[k];if(k==mile){{el.style.width='18px';el.style.height='18px';el.style.border='3px solid #1B4965'}}else{{el.style.width='12px';el.style.height='12px';el.style.border='2px solid white'}}}})}}
function addMarkers(){{const list=document.getElementById('marker-list');list.innerHTML='';markers.forEach(m=>{{const color=typeColors[m.type]||'#7f8c8d';const el=document.createElement('div');el.style.cssText='background:'+color+';width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3);cursor:pointer;transition:all 0.2s;';markerEls[m.mile]=el;const mileNum=m.mile%1===0?m.mile.toFixed(1):String(m.mile);const mileStr=mileNum.replace('.','-');const slugName=m.name.toLowerCase().replace(/[^a-z0-9\\s]/g,'').split(/\\s+/).slice(0,4).join('-');const generatedSlug='mile-'+mileStr+'-'+slugName;const postSlug=mileToSlug[mileNum]||generatedSlug;const popup=new mapboxgl.Popup({{offset:10}}).setHTML('<div class="popup-title">Mile '+m.mile+' '+m.bank+'</div><div class="popup-detail">'+m.name+'</div><a class="popup-link" href="{site}/'+postSlug+'/">Read guide &rarr;</a>');const marker=new mapboxgl.Marker(el).setLngLat([m.lng,m.lat]).setPopup(popup).addTo(map);mapMarkers[m.mile]=marker;el.addEventListener('click',()=>highlightMarker(m.mile));const card=document.createElement('div');card.className='chapter-card';card.id='card-'+m.mile;card.style.cursor='pointer';card.innerHTML='<div class="chapter-type" style="background:'+color+'22;color:'+color+';border:1px solid '+color+'44;">Mile '+m.mile+' '+m.bank+'</div><h3>'+m.name+'</h3>';card.addEventListener('click',()=>{{map.flyTo({{center:[m.lng,m.lat],zoom:14,duration:1200}});Object.values(mapMarkers).forEach(mk=>{{if(mk.getPopup().isOpen())mk.togglePopup()}});marker.togglePopup();highlightMarker(m.mile)}});list.appendChild(card)}})}}
map.on('load',()=>{{addRiverLine();addMarkers()}});
function setMapStyle(s){{const styles={{'outdoors':'mapbox://styles/mapbox/outdoors-v12','satellite-streets':'mapbox://styles/mapbox/satellite-streets-v12'}};map.setStyle(styles[s]);document.getElementById('btn-terrain').classList.toggle('active',s==='outdoors');document.getElementById('btn-satellite').classList.toggle('active',s==='satellite-streets');map.once('style.load',()=>{{addRiverLine();addMarkers()}})}}
document.getElementById('btn-terrain').onclick=()=>setMapStyle('outdoors');
document.getElementById('btn-satellite').onclick=()=>setMapStyle('satellite-streets');
</script>
</body>
</html>'''


for s in SECTIONS:
    river_type = s.get("river", "miss")
    markers_js = "["
    for mile, bank, name, mtype in s["markers"]:
        lng, lat = get_coord(mile, bank, river_type)
        markers_js += f'{{mile:{mile},bank:"{bank}",name:"{name}",lng:{lng},lat:{lat},type:"{mtype}"}},'
    markers_js += "]"

    lat_lo, lat_hi = s["lat_range"]
    rv = river_section(lat_lo, lat_hi)
    river_js = json.dumps(rv, separators=(',', ':'))

    prev_html = f'<a href="{SITE}/{s["prev"][1]}">&larr; {s["prev"][0]}</a>' if s["prev"] else '<span></span>'
    next_html = f'<a href="{SITE}/{s["next"][1]}">{s["next"][0]} &rarr;</a>' if s["next"] else '<span></span>'

    html = TEMPLATE.format(
        name=s["name"],
        miles_label=s["miles_label"],
        num_markers=len(s["markers"]),
        markers_js=markers_js,
        river_js=river_js,
        center_js=json.dumps(s["center"]),
        zoom=s["zoom"],
        mapbox=MAPBOX,
        site=SITE,
        slug_lookup_js=slug_js,
        prev_html=prev_html,
        next_html=next_html,
    )

    path = os.path.join(OUTPUT_DIR, s["file"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Built: {s['file']} ({len(s['markers'])} markers)")

print(f"\nAll 9 sections built!")
