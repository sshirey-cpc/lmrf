"""
Build section pages for all 9 river sections using USACE mile marker coordinates.
Each page gets: map with river line + mile markers, chapter list with Ghost links.
"""

import json
import os

OUTPUT_DIR = "C:/Users/scott/lmrf/rivergator/book-preview/sections"
USACE_PATH = "C:/Users/scott/lmrf/rivergator/content-markdown/usace-mile-coordinates.json"
RIVER_COORDS_PATH = "C:/Users/scott/lmrf/rivergator/book-preview/river_coords_clean.txt"
MAPBOX_TOKEN = "pk.eyJ1Ijoic3NoaXJleTc2IiwiYSI6ImNtbmdmeHphNDA4aW8yd29wbWgxYTY3cWcifQ.34MAJqDY8qcKm_48AMQuNQ"
SITE_URL = "http://35.188.103.101"

# Load USACE data
with open(USACE_PATH) as f:
    usace = json.load(f)
miss = usace['MISSISSIPPI-LO']

# Load river line
with open(RIVER_COORDS_PATH) as f:
    all_river_coords = json.loads(f.read())

SECTIONS = [
    # ---- 1. St. Louis to Caruthersville ----
    {
        "slug": "stlouis-to-caruthersville",
        "name": "St. Louis to Caruthersville",
        "miles_label": "Mile 195–850",
        "mile_range": (195, 850),
        "lat_range": (38.65, 36.05),
        "map_center": [-89.70, 37.35],
        "map_zoom": 7,
        "prev": None,
        "next": {"name": "Caruthersville to Memphis", "url": f"{SITE_URL}/sections/caruthersville-to-memphis.html"},
        "chapters": [
            {"type": "intro", "title": "Introduction", "slug": "stlouis-to-caruthersville-stl-car-preamble",
             "meta": "Overview", "desc": "Preamble to the St. Louis to Caruthersville section — the beginning of the Lower Mississippi River Water Trail."},
            {"type": "chapter", "title": "St. Louis to Chain of Rocks", "slug": "mile-194-2-chain-of-rocks-canal",
             "meta": "Mile 195–180 · Upper St. Louis", "desc": "Maple Island, Mary Meachum Freedom Crossing, Chain of Rocks Canal, and the start below St. Louis."},
            {"type": "chapter", "title": "Cliff Cave to Kimmswick", "slug": "mile-166-7-cliff-cave-county-park",
             "meta": "Mile 167–159 · South St. Louis County", "desc": "Cliff Cave County Park, Bellerive Park, and the historic river town of Kimmswick."},
            {"type": "chapter", "title": "Tower Rock to Moccasin Springs", "slug": "mile-80-0-tower-rock",
             "meta": "Mile 80–67 · Perry County", "desc": "Tower Rock — the legendary midstream monolith — and Moccasin Springs Harbor."},
            {"type": "chapter", "title": "Cape Girardeau to Trail of Tears", "slug": "mile-52-2-lbd-cape-girardeau-flood-wall-classy-entranc",
             "meta": "Mile 52–35 · Cape Girardeau", "desc": "Cape Girardeau flood wall, Trail of Tears State Park, and Devil's Island."},
            {"type": "chapter", "title": "Fort Defiance to Wickliffe", "slug": "mile-0-8-lbd-fort-defiance-the-mississippi-and-ohio-r",
             "meta": "Mile 1–951 · Ohio Confluence", "desc": "Fort Defiance at the Ohio River confluence, Wickliffe, Columbus-Belmont State Park, and the Kentucky bluffs."},
            {"type": "chapter", "title": "Dorena to Caruthersville", "slug": "mile-924-6-dorena-boat-ramp",
             "meta": "Mile 925–850 · New Madrid Bend", "desc": "Dorena boat ramp, New Madrid seismic zone, and arrival at Caruthersville Harbor."},
            {"type": "appendix", "title": "Appendix", "slug": "stlouis-to-caruthersville-stl-car-appendix",
             "meta": "Resources · Journals", "desc": "Supplementary materials, expedition journals, and reference information for the upper section."},
        ],
        "markers": [
            (195, 'RBD', 'Chain of Rocks Canal', 'access_point'),
            (183, 'RBD', 'Mary Meachum Freedom Crossing', 'other'),
            (174, 'RBD', 'Bellerive Park', 'access_point'),
            (167, 'RBD', 'Cliff Cave County Park', 'camping'),
            (159, 'RBD', 'Kimmswick', 'town'),
            (134, 'LBD', 'Ste. Genevieve', 'town'),
            (110, 'RBD', 'Chester, IL', 'town'),
            (88, 'LBD', "LaCour's Island", 'island'),
            (80, 'RBD', 'Tower Rock', 'other'),
            (67, 'RBD', 'Moccasin Springs Harbor', 'access_point'),
            (52, 'LBD', 'Cape Girardeau', 'town'),
            (35, 'LBD', 'Santa Fe Chute', 'other'),
            (951, 'LBD', 'Wickliffe, KY', 'town'),
            (937, 'LBD', 'Columbus-Belmont State Park', 'camping'),
            (878, 'LBD', 'Marr Towhead', 'camping'),
            (850, 'RBD', 'Caruthersville Harbor', 'access_point'),
        ],
    },
    # ---- 2. Caruthersville to Memphis ----
    {
        "slug": "caruthersville-to-memphis",
        "name": "Caruthersville to Memphis",
        "miles_label": "Mile 850–737",
        "mile_range": (850, 737),
        "lat_range": (36.20, 35.05),
        "map_center": [-89.85, 35.60],
        "map_zoom": 8,
        "prev": {"name": "St. Louis to Caruthersville", "url": f"{SITE_URL}/sections/stlouis-to-caruthersville.html"},
        "next": {"name": "Helena to Greenville", "url": f"{SITE_URL}/sections/helena-to-greenville.html"},
        "chapters": [
            {"type": "intro", "title": "Introduction", "slug": "caruthersville-to-memphis-introduction-2",
             "meta": "Overview", "desc": "Introduction to the Caruthersville to Memphis section, including Chickasaw Bluffs and the approach to Memphis."},
            {"type": "chapter", "title": "Caruthersville to Osceola", "slug": "mile-849-0-mouth-of-the-caruthersville",
             "meta": "Mile 849–785 · Upper section", "desc": "Caruthersville Harbor, Lady Luck Casino, Nebraska Landing, and arrival at Osceola, Arkansas."},
            {"type": "chapter", "title": "Osceola to Shelby Forest", "slug": "mile-785-0-rbd-osceola-arkansas-if-you-stay-main-channe",
             "meta": "Mile 785–753 · Chickasaw Bluffs", "desc": "Forked Deer River, Hatchie River, Randolph Landing, and Shelby Forest boat ramp."},
            {"type": "chapter", "title": "Shelby Forest to Memphis", "slug": "mile-752-7-lbd-shelby-forest-boat-ramp-concrete-revetme",
             "meta": "Mile 753–737 · Memphis approach", "desc": "Wolf River, Loosahatchie River, Hickman bars, and the 4th Chickasaw Bluff at Memphis."},
        ],
        "markers": [
            (850, 'RBD', 'Caruthersville Harbor', 'access_point'),
            (846, 'RBD', 'Isle of Capri Casino', 'other'),
            (814, 'LBD', 'Nebraska Landing', 'access_point'),
            (797, 'LBD', 'Forked Deer River', 'confluence'),
            (785, 'RBD', 'Osceola, AR', 'town'),
            (773, 'LBD', 'Hatchie River Mouth', 'confluence'),
            (771, 'LBD', 'Randolph Landing', 'access_point'),
            (769, 'LBD', "Richardson's Landing", 'other'),
            (767, 'RBD', 'Island 35 Boat Ramp', 'access_point'),
            (757, 'RBD', 'Angelo Towhead area', 'island'),
            (753, 'LBD', 'Shelby Forest Boat Ramp', 'access_point'),
            (746, 'LBD', 'Upper Hickman', 'camping'),
            (741, 'LBD', 'Loosahatchie River', 'confluence'),
            (737, 'LBD', '4th Chickasaw Bluff / Memphis', 'town'),
        ],
    },
    # ---- 3. Helena to Greenville (existing) ----
    {
        "slug": "helena-to-greenville",
        "name": "Helena to Greenville",
        "miles_label": "Mile 663–537",
        "mile_range": (663, 537),
        "lat_range": (34.55, 33.30),
        "map_center": [-90.90, 33.90],
        "map_zoom": 8,
        "prev": {"name": "Caruthersville to Memphis", "url": f"{SITE_URL}/sections/caruthersville-to-memphis.html"},
        "next": {"name": "Greenville to Vicksburg", "url": f"{SITE_URL}/sections/greenville-to-vicksburg.html"},
        "chapters": [
            {"type": "intro", "title": "St. Francis to Helena", "slug": "river-log-helena-to-greenville-st-francis-to-helena",
             "meta": "6 pages", "desc": "Upper section introduction, the St. Francis River route, and approach to Helena."},
            {"type": "chapter", "title": "Helena to Island 63", "slug": "river-log-helena-to-greenville-helena-to-island-63",
             "meta": "Mile 663–637 · 11 pages", "desc": "Friars Point, Kangaroo Point, Island 62, and the legendary Island 63 — home of Quapaw Canoe Company's river camp."},
            {"type": "chapter", "title": "Island 63 to Hurricane", "slug": "river-log-helena-to-greenville-island-63-to-hurricane",
             "meta": "Mile 637–610 · 11 pages", "desc": "Sunflower River cutoff, deep delta wilderness, Hurricane Island and its sandbars."},
            {"type": "chapter", "title": "Hurricane to Rosedale", "slug": "river-log-helena-to-greenville-hurricane-to-rosedale",
             "meta": "Mile 610–580 · 10 pages", "desc": "Rosedale landing, Mound Landing, and the heart of the Mississippi Delta."},
            {"type": "chapter", "title": "Rosedale to Arkansas City", "slug": "river-log-helena-to-greenville-rosedale-to-arkansas-city",
             "meta": "Mile 580–537 · 11 pages", "desc": "Winterville, Arkansas City, Tarpley Cutoff, and approach to Greenville."},
        ],
        "markers": [
            (663, 'RBD', 'Helena Harbor', 'access_point'),
            (660, 'LBD', 'Helena Bridge area', 'bridge'),
            (652, 'LBD', 'Friars Point', 'town'),
            (649, 'RBD', 'Kangaroo Point', 'other'),
            (641, 'LBD', 'Island 62', 'camping'),
            (637, 'LBD', 'Island 63 / Quapaw Landing', 'camping'),
            (630, 'RBD', 'Sunflower River Cutoff', 'confluence'),
            (620, 'LBD', 'Rosedale', 'town'),
            (610, 'RBD', 'Hurricane Island', 'island'),
            (600, 'LBD', 'Scott, MS', 'other'),
            (590, 'RBD', 'Mound Landing', 'access_point'),
            (580, 'LBD', 'Winterville area', 'other'),
            (562, 'LBD', 'Arkansas City', 'town'),
            (550, 'RBD', 'Tarpley Cutoff', 'other'),
            (537, 'LBD', 'Greenville, MS', 'town'),
        ],
    },
    # ---- 4. Greenville to Vicksburg ----
    {
        "slug": "greenville-to-vicksburg",
        "name": "Greenville to Vicksburg",
        "miles_label": "Mile 537–437",
        "mile_range": (537, 437),
        "lat_range": (33.40, 32.30),
        "map_center": [-90.95, 32.85],
        "map_zoom": 8,
        "prev": {"name": "Helena to Greenville", "url": f"{SITE_URL}/sections/helena-to-greenville.html"},
        "next": {"name": "Vicksburg to Baton Rouge", "url": f"{SITE_URL}/sections/vicksburg-to-baton-rouge.html"},
        "chapters": [
            {"type": "intro", "title": "Introduction", "slug": "greenville-to-vicksburg-introductiongtov",
             "meta": "Overview", "desc": "Introduction to the Greenville to Vicksburg section — deep Delta country, cutoffs, and oxbow lakes."},
            {"type": "chapter", "title": "Greenville to Mayersville", "slug": "mile-537-0-lbd-warfield-point-park-ideally-situated-alo",
             "meta": "Mile 537–496 · Upper section", "desc": "Warfield Point Park, Sunnyside Landing, American Cutoff, Lake Lee, and arrival at Mayersville."},
            {"type": "chapter", "title": "Mayersville to Lake Providence", "slug": "mile-496-0-lbd-tennis-court-landing-paddlers-will-find",
             "meta": "Mile 496–458 · Middle section", "desc": "Bunch's Cutoff, Chotard Lake, Eagle Lake, Tara Landing, and the Tallulah tornado corridor."},
            {"type": "chapter", "title": "Lake Providence to Vicksburg", "slug": "greenville-to-vicksburg-lake-providence-to-vicksburg",
             "meta": "Mile 458–437 · Lower section", "desc": "Paw Paw Chute, King's Point, Lake Centennial, and arrival at Vicksburg via the Yazoo River."},
        ],
        "markers": [
            (537, 'LBD', 'Warfield Point / Greenville', 'access_point'),
            (532, 'RBD', 'Sunnyside Landing', 'access_point'),
            (525, 'LBD', 'American Cutoff / Lake Lee', 'other'),
            (513, 'RBD', 'Old Matthews Bend', 'other'),
            (504, 'RBD', "Bunch's Cutoff", 'other'),
            (496, 'LBD', 'Mayersville / Tennis Court Landing', 'access_point'),
            (491, 'LBD', 'Lake Washington area', 'other'),
            (461, 'LBD', 'Chotard Lake / Terrapin Neck', 'other'),
            (459, 'LBD', 'Tallulah Tornado Cut', 'other'),
            (458, 'LBD', 'Eagle Lake / Tara Landing', 'camping'),
            (457, 'RBD', 'Madison Parish Boat Launch', 'access_point'),
            (447, 'LBD', 'Paw Paw Chute', 'other'),
            (442, 'RBD', 'Last Island above Vicksburg', 'island'),
            (438, 'RBD', "King's Point / Lake Centennial", 'access_point'),
            (437, 'LBD', 'Vicksburg / Yazoo River', 'town'),
        ],
    },
    # ---- 5. Vicksburg to Baton Rouge (existing) ----
    {
        "slug": "vicksburg-to-baton-rouge",
        "name": "Vicksburg to Baton Rouge",
        "miles_label": "Mile 437–225",
        "mile_range": (437, 225),
        "lat_range": (32.40, 30.40),
        "map_center": [-91.30, 31.40],
        "map_zoom": 7,
        "prev": {"name": "Greenville to Vicksburg", "url": f"{SITE_URL}/sections/greenville-to-vicksburg.html"},
        "next": {"name": "Baton Rouge to Venice", "url": f"{SITE_URL}/sections/baton-rouge-to-venice.html"},
        "chapters": [
            {"type": "intro", "title": "Introduction", "slug": "river-log-vicksburg-to-baton-rouge-introv-b",
             "meta": "7 pages", "desc": "Overview of the Loess Bluffs section, gage references, and navigation guidance."},
            {"type": "chapter", "title": "Vicksburg to Natchez", "slug": "river-log-vicksburg-to-baton-rouge-vicksburg-to-natchez",
             "meta": "Mile 437–364 · 21 pages", "desc": "Grand Gulf, Port Gibson, the spectacular Loess Bluffs, and arrival at historic Natchez."},
            {"type": "chapter", "title": "Natchez to St. Francisville", "slug": "river-log-vicksburg-to-baton-rouge-natchez-to-stfrancisville",
             "meta": "Mile 364–305 · 22 pages", "desc": "Vidalia, the Angola bend, Tunica Hills, and the bluffs of St. Francisville."},
            {"type": "chapter", "title": "St. Francisville to Baton Rouge", "slug": "river-log-vicksburg-to-baton-rouge-stfrancisville-to-baton-rouge",
             "meta": "Mile 305–225 · 18 pages", "desc": "Port Hudson, the chemical corridor begins, and arrival at Baton Rouge."},
            {"type": "appendix", "title": "Appendix", "slug": "river-log-vicksburg-to-baton-rouge-appendixv-b",
             "meta": "28 pages · Journals · Resources", "desc": "Expedition journals, historical references, flora and fauna, and supplementary materials."},
        ],
        "markers": [
            (437, 'LBD', 'Vicksburg, MS', 'town'),
            (425, 'RBD', 'Grand Gulf', 'access_point'),
            (410, 'LBD', 'Port Gibson area', 'other'),
            (400, 'RBD', 'Rodney Landing', 'access_point'),
            (390, 'LBD', 'St. Catherine Creek', 'confluence'),
            (380, 'RBD', 'Cole Creek', 'other'),
            (364, 'LBD', 'Natchez, MS', 'town'),
            (350, 'RBD', 'Vidalia, LA', 'town'),
            (335, 'LBD', 'Angola / Louisiana State Penitentiary', 'other'),
            (320, 'RBD', 'Tunica Hills', 'camping'),
            (305, 'LBD', 'St. Francisville, LA', 'town'),
            (290, 'RBD', 'Bayou Sara', 'confluence'),
            (270, 'LBD', 'Port Hudson', 'other'),
            (250, 'RBD', 'Baton Rouge Refinery Row', 'hazard'),
            (233, 'LBD', 'Baton Rouge Bridge', 'bridge'),
            (228, 'LBD', 'Baton Rouge, LA', 'town'),
        ],
    },
    # ---- 6. Atchafalaya River ----
    {
        "slug": "atchafalaya-river",
        "name": "Atchafalaya River",
        "miles_label": "Mile 0–310",
        "mile_range": (0, 310),
        "lat_range": (29.70, 30.95),
        "map_center": [-91.50, 30.30],
        "map_zoom": 8,
        "usace_key": "LO-ATCHAFALAYA, ABOVE BERWICK LOCK",
        "prev": {"name": "Vicksburg to Baton Rouge", "url": f"{SITE_URL}/sections/vicksburg-to-baton-rouge.html"},
        "next": {"name": "Baton Rouge to Venice", "url": f"{SITE_URL}/sections/baton-rouge-to-venice.html"},
        "chapters": [
            {"type": "intro", "title": "Introduction", "slug": "atchafalaya-river-introduction",
             "meta": "Overview", "desc": "Introduction to the Atchafalaya River — America's largest river swamp and the Mississippi's primary distributary."},
            {"type": "chapter", "title": "Three Rivers to Melville", "slug": "mile-0-1-lbd-three-rivers-landing-a-nice-sandbar-emer",
             "meta": "Mile 0–30 · Upper Atchafalaya", "desc": "Three Rivers Landing, Bunge Dock, Turner's Bayou, Cypress Point, and approach to Melville."},
            {"type": "chapter", "title": "Melville to Krotz Springs", "slug": "mile-29-7-rbd-melville-boat-ramp-primitive-a-broad-gra",
             "meta": "Mile 30–43 · Middle section", "desc": "Melville boat ramp, Broad Bay, Frank Diesl Point, and Port of Krotz Springs."},
            {"type": "chapter", "title": "Krotz Springs to Blue Heron Point", "slug": "mile-42-5-rbd-port-of-krotz-springs-the-port-of-krotz",
             "meta": "Mile 43–69 · Swamp corridor", "desc": "Cell towers for navigation, Jake's Bayou, Blue Heron Point, and the deep Atchafalaya basin."},
            {"type": "chapter", "title": "Blue Heron Point to Bailey's Basin", "slug": "mile-68-5-blue-heron-point",
             "meta": "Mile 69–120 · Lower Atchafalaya", "desc": "Lake Mongoulois, Blue Hole, and Bailey's Basin — the lower reaches of the swamp river."},
            {"type": "chapter", "title": "God's Island to Wilkinson Creek", "slug": "mile-144-3-gods-island-the-atchafalaya",
             "meta": "Mile 144–310 · Delta country", "desc": "God's Island, the Atchafalaya Delta, and Wilkinson Creek at the Gulf approach."},
            {"type": "appendix", "title": "Appendix", "slug": "atchafalaya-river-appendixar",
             "meta": "Resources · Journals", "desc": "Supplementary materials, expedition journals, and references for the Atchafalaya route."},
        ],
        "markers": [
            (0, 'LBD', 'Three Rivers Landing', 'access_point'),
            (6, 'RBD', 'Bunge Dock', 'other'),
            (15, 'RBD', "Turner's Bayou", 'other'),
            (30, 'RBD', 'Melville Boat Ramp', 'access_point'),
            (32, 'LBD', 'Broad Bay', 'other'),
            (43, 'RBD', 'Port of Krotz Springs', 'town'),
            (45, 'RBD', 'Frank Diesl Point', 'camping'),
            (60, 'LBD', 'Cell Tower', 'other'),
            (69, 'LBD', 'Blue Heron Point', 'camping'),
            (76, 'LBD', 'Lake Mongoulois Point', 'camping'),
            (95, 'LBD', 'Blue Hole', 'other'),
            (120, 'LBD', "Bailey's Basin", 'access_point'),
            (144, 'LBD', "God's Island", 'island'),
            (310, 'LBD', 'Wilkinson Creek', 'confluence'),
        ],
    },
    # ---- 7. Baton Rouge to Venice ----
    {
        "slug": "baton-rouge-to-venice",
        "name": "Baton Rouge to Venice",
        "miles_label": "Mile 225–10",
        "mile_range": (225, 10),
        "lat_range": (30.50, 29.25),
        "map_center": [-90.10, 29.90],
        "map_zoom": 8,
        "prev": {"name": "Atchafalaya River", "url": f"{SITE_URL}/sections/atchafalaya-river.html"},
        "next": {"name": "Birdsfoot Delta", "url": f"{SITE_URL}/sections/birdsfoot-delta.html"},
        "chapters": [
            {"type": "intro", "title": "Introduction", "slug": "baton-rouge-to-venice-introduction",
             "meta": "Overview", "desc": "Introduction to the Baton Rouge to Venice section — the industrial corridor, New Orleans, and the run to the Gulf."},
            {"type": "chapter", "title": "Baton Rouge to Donaldsonville", "slug": "mile-173-0-bringier-point-possible-allweather",
             "meta": "Mile 225–175 · Chemical corridor", "desc": "Shell Chemical, Marathon Garyville Refinery, Bringier Point, and the dense industrial corridor."},
            {"type": "chapter", "title": "Donaldsonville to Norco", "slug": "mile-148-1-grandview-beach-paddlers-will",
             "meta": "Mile 175–127 · River Parishes", "desc": "Grandview Beach, Kinder Morgan, Belmont Crossing, and Shell Norco."},
            {"type": "chapter", "title": "Norco to New Orleans", "slug": "mile-118-8-international-matex-st",
             "meta": "Mile 127–92 · Approach to the city", "desc": "Elmwood Marine Services, Pan American, and arrival at Jackson Barracks and the French Quarter."},
            {"type": "chapter", "title": "New Orleans", "slug": "mile-94-4-mandeville-street-wharf-942",
             "meta": "Mile 95–81 · The Crescent City", "desc": "Mandeville Street Wharf, Julia Street Cruise Terminal, Gretna Ferry, and Caernarvon Diversion."},
            {"type": "chapter", "title": "New Orleans to Venice", "slug": "mile-81-4-caernarvon-fresh-water-diversion",
             "meta": "Mile 81–10 · Plaquemines Parish", "desc": "Poydras, Happy Jack, Bohemia Beach, Bass Enterprises, and the road to Venice."},
        ],
        "markers": [
            (225, 'LBD', 'Baton Rouge', 'town'),
            (207, 'RBD', 'Plaquemine Lock', 'other'),
            (175, 'RBD', 'Bayou Lafourche', 'confluence'),
            (156, 'RBD', 'Belmont Crossing', 'other'),
            (149, 'LBD', 'Grandview Beach', 'camping'),
            (141, 'LBD', 'Marathon Garyville Refinery', 'hazard'),
            (127, 'LBD', 'Shell Norco', 'hazard'),
            (112, 'LBD', 'Small Sand Dune', 'camping'),
            (104, 'RBD', 'Nine-Mile Point', 'hazard'),
            (95, 'LBD', 'New Orleans / French Quarter', 'town'),
            (81, 'LBD', 'Caernarvon Diversion', 'other'),
            (44, 'LBD', 'Bohemia Beach', 'camping'),
            (35, 'LBD', 'Bass Enterprises', 'other'),
            (25, 'RBD', "Motto's Basin", 'access_point'),
            (13, 'LBD', 'Hunting Lodge Pass', 'other'),
        ],
    },
    # ---- 8. Birdsfoot Delta ----
    {
        "slug": "birdsfoot-delta",
        "name": "Birdsfoot Delta",
        "miles_label": "Mile 10–0",
        "mile_range": (10, 0),
        "lat_range": (29.35, 29.00),
        "map_center": [-89.30, 29.15],
        "map_zoom": 10,
        "prev": {"name": "Baton Rouge to Venice", "url": f"{SITE_URL}/sections/baton-rouge-to-venice.html"},
        "next": None,
        "chapters": [
            {"type": "intro", "title": "Introduction", "slug": "birdsfoot-delta-introduction",
             "meta": "Overview", "desc": "Introduction to the Birdsfoot Delta — the end of the river, Head of Passes, and the Gulf of Mexico."},
            {"type": "chapter", "title": "Grand Pass Island", "slug": "mile-10-2-grand-pass-island-the",
             "meta": "Mile 10 · Delta entrance", "desc": "Grand Pass Island — the highest ground in the delta and gateway to the passes."},
            {"type": "chapter", "title": "Pilottown", "slug": "mile-2-4-shell-pipeline-co-pilottown",
             "meta": "Mile 2 · End of the road", "desc": "Shell Pipeline, Pilottown Wharf — the last outpost before the Gulf of Mexico."},
            {"type": "appendix", "title": "Appendix", "slug": "birdsfoot-delta-appendix",
             "meta": "Resources", "desc": "Supplementary materials and references for the Birdsfoot Delta."},
        ],
        "markers": [
            (10, 'RBD', 'Grand Pass Island', 'island'),
            (8, 'LBD', 'South Pass junction', 'confluence'),
            (6, 'RBD', 'Southwest Pass junction', 'confluence'),
            (4, 'LBD', 'Pass a Loutre', 'confluence'),
            (3, 'RBD', 'Head of Passes', 'other'),
            (2, 'LBD', 'Pilottown Wharf', 'access_point'),
            (1, 'RBD', 'Shell Pipeline dock', 'other'),
            (0, 'LBD', 'Mile Zero / Gulf of Mexico', 'other'),
        ],
    },
]


atch = usace.get('LO-ATCHAFALAYA, ABOVE BERWICK LOCK', {})


def get_usace_coord(mile, bank, usace_key=None):
    """Get USACE coordinate with LBD/RBD offset."""
    source = atch if usace_key and 'ATCHAFALAYA' in usace_key else miss
    coord = source.get(str(mile))
    if not coord:
        # Find closest
        closest = min(source.keys(), key=lambda m: abs(int(m) - mile))
        coord = source[closest]
    lng, lat = coord
    offset = 0.003 if bank == 'LBD' else -0.003
    return lng + offset, lat


def get_section_river_coords(lat_range, usace_key=None):
    """Filter river coordinates to a section's latitude range."""
    if usace_key and 'ATCHAFALAYA' in usace_key:
        # Build river line from USACE Atchafalaya coordinates, sorted by mile
        coords = []
        for mile_str in sorted(atch.keys(), key=lambda m: int(m)):
            coords.append(atch[mile_str])
        return coords
    lo, hi = min(lat_range), max(lat_range)
    return [c for c in all_river_coords if lo - 0.1 <= c[1] <= hi + 0.1]


def build_section_html(section):
    """Build a complete section HTML page."""
    s = section

    # Build markers JS
    usace_key = s.get("usace_key")
    markers_js = "const markers = [\n"
    for mile, bank, name, mtype in s["markers"]:
        lng, lat = get_usace_coord(mile, bank, usace_key)
        markers_js += f'    {{ mile:{mile}, bank:"{bank}", name:"{name}", lng:{lng:.5f}, lat:{lat:.5f}, type:"{mtype}" }},\n'
    markers_js += "];"

    # Get section river coords
    section_river = get_section_river_coords(s["lat_range"], usace_key)
    river_js = json.dumps(section_river, separators=(',', ':'))

    # Build chapters HTML
    chapters_html = ""
    for ch in s["chapters"]:
        type_class = f"type-{ch['type']}"
        type_label = ch["type"].capitalize()
        if ch["type"] == "chapter":
            type_label = "River Log"
        chapters_html += f'''
        <a class="chapter-card" href="{SITE_URL}/{ch['slug']}/">
            <div class="chapter-type {type_class}">{type_label}</div>
            <h3>{ch["title"]}</h3>
            <div class="chapter-meta">{ch["meta"]}</div>
            <div class="chapter-desc">{ch["desc"]}</div>
        </a>'''

    # Section stats
    total_miles = abs(s["mile_range"][0] - s["mile_range"][1])

    prev_html = f'<a href="{s["prev"]["url"]}">&larr; {s["prev"]["name"]}</a>' if s.get("prev") else '<span></span>'
    next_html = f'<a href="{s["next"]["url"]}">{s["next"]["name"]} &rarr;</a>' if s.get("next") else '<span></span>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{s["name"]} — The Rivergator</title>
    <link href="https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.css" rel="stylesheet">
    <script src="https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Georgia', serif; background: #f8f6f2; color: #1a1a1a; }}
        .site-header {{ background: #1B4965; color: white; padding: 16px 20px; }}
        .site-header h1 {{ font-size: 22px; }}
        .site-header h1 a {{ color: white; text-decoration: none; }}
        .site-nav {{ background: #15374d; display: flex; justify-content: center; flex-wrap: wrap; }}
        .site-nav a {{ color: #a8cce0; text-decoration: none; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 1.5px; padding: 12px 20px; transition: color 0.2s, background 0.2s; }}
        .site-nav a:hover, .site-nav a.active {{ color: white; background: rgba(255,255,255,0.1); }}
        .breadcrumb {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13px; color: #888; padding: 12px 20px; max-width: 1100px; margin: 0 auto; }}
        .breadcrumb a {{ color: #1B4965; text-decoration: none; }}
        .section-hero {{ max-width: 1100px; margin: 0 auto; padding: 0 20px 24px; }}
        .section-hero h1 {{ font-size: 32px; color: #1B4965; margin-bottom: 4px; }}
        .section-hero .mile-range {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 15px; color: #888; font-style: italic; }}
        .section-stats {{ display: flex; gap: 24px; padding: 16px 0; border-top: 1px solid #e0ddd6; border-bottom: 1px solid #e0ddd6; margin-bottom: 20px; }}
        .section-stat {{ text-align: center; }}
        .section-stat .num {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 22px; font-weight: 700; color: #1B4965; }}
        .section-stat .label {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }}
        .section-layout {{ max-width: 1100px; margin: 0 auto; padding: 0 20px 40px; display: grid; grid-template-columns: 1fr 340px; gap: 24px; }}
        .section-map {{ height: 450px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.1); position: relative; }}
        #map {{ width: 100%; height: 100%; }}
        .map-style-toggle {{ position: absolute; top: 12px; left: 12px; z-index: 10; display: flex; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.3); overflow: hidden; }}
        .map-style-toggle button {{ border: none; background: white; color: #333; padding: 12px 20px; font-size: 14px; font-weight: 700; cursor: pointer; }}
        .map-style-toggle button.active {{ background: #1B4965; color: white; }}
        .map-style-toggle button:hover:not(.active) {{ background: #e0eef5; }}
        .map-style-toggle button:not(:last-child) {{ border-right: 1px solid #ddd; }}
        .map-legend {{ display: flex; gap: 16px; padding: 10px 0; flex-wrap: wrap; }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 12px; color: #666; }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
        .chapter-list {{ background: white; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }}
        .chapter-list-header {{ background: #1B4965; color: white; padding: 14px 18px; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}
        .chapter-card {{ display: block; padding: 14px 18px; border-bottom: 1px solid #eee; text-decoration: none; color: inherit; transition: background 0.2s; }}
        .chapter-card:hover {{ background: #f0f5f8; }}
        .chapter-card h3 {{ font-size: 16px; color: #1B4965; margin-bottom: 4px; }}
        .chapter-card .chapter-meta {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 12px; color: #999; }}
        .chapter-card .chapter-desc {{ font-size: 13px; color: #666; margin-top: 6px; line-height: 1.5; }}
        .chapter-type {{ display: inline-block; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 2px 8px; border-radius: 10px; margin-bottom: 6px; }}
        .type-intro {{ background: #e8f4e8; color: #2d7a2d; }}
        .type-chapter {{ background: #e0eef5; color: #1B4965; }}
        .type-appendix {{ background: #f5e8d0; color: #8a6d3b; }}
        .section-nav {{ max-width: 1100px; margin: 0 auto; padding: 0 20px 40px; display: flex; justify-content: space-between; }}
        .section-nav a {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 14px; color: #1B4965; text-decoration: none; padding: 10px 16px; border: 1px solid #d0d0d0; border-radius: 6px; }}
        .section-nav a:hover {{ background: #e0eef5; }}
        .site-footer {{ text-align: center; padding: 24px 20px; color: #999; font-size: 13px; border-top: 1px solid #e0ddd6; }}
        .site-footer a {{ color: #1B4965; text-decoration: none; }}
        .mapboxgl-popup-content {{ padding: 10px 14px; border-radius: 6px; max-width: 220px; }}
        .popup-title {{ font-weight: 700; color: #1B4965; font-size: 13px; }}
        .popup-detail {{ font-size: 11px; color: #666; margin-top: 2px; }}
        @media (max-width: 768px) {{
            .section-layout {{ grid-template-columns: 1fr; }}
            .section-map {{ height: 300px; }}
            .section-hero h1 {{ font-size: 24px; }}
        }}
    </style>
</head>
<body>
<header class="site-header"><h1><a href="{SITE_URL}">The Rivergator</a></h1></header>
<nav class="site-nav">
    <a href="{SITE_URL}" class="active">River Log</a>
    <a href="#">Paddler's Guide</a>
    <a href="#">Resources</a>
    <a href="#">River Media</a>
    <a href="#">About</a>
</nav>
<div class="breadcrumb"><a href="{SITE_URL}">River Log</a> &rsaquo; {s["name"]}</div>
<div class="section-hero">
    <h1>{s["name"]}</h1>
    <div class="mile-range">{s["miles_label"]} &middot; {total_miles} river miles</div>
    <div class="section-stats">
        <div class="section-stat"><div class="num">{total_miles}</div><div class="label">Miles</div></div>
        <div class="section-stat"><div class="num">{len(s["markers"])}</div><div class="label">Markers</div></div>
        <div class="section-stat"><div class="num">{len(s["chapters"])}</div><div class="label">Chapters</div></div>
    </div>
</div>
<div class="section-layout">
    <div>
        <div class="section-map">
            <div id="map"></div>
            <div class="map-style-toggle">
                <button class="active" id="btn-terrain">Terrain</button>
                <button id="btn-satellite">Satellite</button>
            </div>
        </div>
        <div class="map-legend">
            <div class="legend-item"><div class="legend-dot" style="background:#2ecc71"></div> Access Point</div>
            <div class="legend-item"><div class="legend-dot" style="background:#e67e22"></div> Camping</div>
            <div class="legend-item"><div class="legend-dot" style="background:#e74c3c"></div> Hazard</div>
            <div class="legend-item"><div class="legend-dot" style="background:#3498db"></div> Bridge</div>
            <div class="legend-item"><div class="legend-dot" style="background:#9b59b6"></div> Town</div>
        </div>
    </div>
    <div class="chapter-list">
        <div class="chapter-list-header">Chapters</div>
        {chapters_html}
    </div>
</div>
<div class="section-nav">{prev_html}{next_html}</div>
<footer class="site-footer">
    <p>The Rivergator &copy; <a href="https://lowermsfoundation.org">Lower Mississippi River Foundation</a></p>
    <p style="margin-top: 4px;">Written by John Ruskey</p>
</footer>
<script>
mapboxgl.accessToken = '{MAPBOX_TOKEN}';
{markers_js}
const typeColors = {{ access_point:'#2ecc71', camping:'#e67e22', hazard:'#e74c3c', bridge:'#3498db', town:'#9b59b6', harbor:'#2ecc71', island:'#e67e22', confluence:'#3498db', other:'#7f8c8d' }};
const sectionRiverCoords = {river_js};
const map = new mapboxgl.Map({{ container:'map', style:'mapbox://styles/mapbox/outdoors-v12', center:{json.dumps(s["map_center"])}, zoom:{s["map_zoom"]} }});
map.addControl(new mapboxgl.NavigationControl(), 'top-right');
function addRiverLine() {{
    if (map.getSource('river')) return;
    map.addSource('river', {{ type:'geojson', data:{{ type:'Feature', geometry:{{ type:'LineString', coordinates:sectionRiverCoords }} }} }});
    map.addLayer({{ id:'river-glow', type:'line', source:'river', paint:{{ 'line-color':'#1B4965', 'line-width':6, 'line-opacity':0.3, 'line-blur':2 }} }});
    map.addLayer({{ id:'river-line', type:'line', source:'river', paint:{{ 'line-color':'#1B4965', 'line-width':3, 'line-opacity':0.8 }} }});
}}
function addMarkers() {{
    markers.forEach(m => {{
        const color = typeColors[m.type] || '#7f8c8d';
        const el = document.createElement('div');
        el.style.cssText = 'background:'+color+';width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3);cursor:pointer;';
        const popup = new mapboxgl.Popup({{ offset:10 }}).setHTML('<div class="popup-title">Mile '+m.mile+' '+m.bank+'</div><div class="popup-detail">'+m.name+'</div>');
        new mapboxgl.Marker(el).setLngLat([m.lng, m.lat]).setPopup(popup).addTo(map);
    }});
}}
map.on('load', () => {{ addRiverLine(); addMarkers(); }});
function setMapStyle(style) {{
    const styles = {{ 'outdoors':'mapbox://styles/mapbox/outdoors-v12', 'satellite-streets':'mapbox://styles/mapbox/satellite-streets-v12' }};
    map.setStyle(styles[style]);
    document.getElementById('btn-terrain').classList.toggle('active', style==='outdoors');
    document.getElementById('btn-satellite').classList.toggle('active', style==='satellite-streets');
    map.once('style.load', () => {{ addRiverLine(); addMarkers(); }});
}}
document.getElementById('btn-terrain').onclick = () => setMapStyle('outdoors');
document.getElementById('btn-satellite').onclick = () => setMapStyle('satellite-streets');
</script>
</body>
</html>'''


# Build pages
os.makedirs(OUTPUT_DIR, exist_ok=True)

for section in SECTIONS:
    html = build_section_html(section)
    path = os.path.join(OUTPUT_DIR, f"{section['slug']}.html")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Built: {section['slug']}.html ({len(html):,} bytes)")

print(f"\nDone! Files in: {OUTPUT_DIR}")
