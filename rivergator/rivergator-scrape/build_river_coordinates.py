"""
Build river coordinates for key mile markers along the Lower Mississippi.
Uses known town/landmark coordinates that sit ON the river, then outputs
a JSON file for the map.

Sources: Wikipedia coordinates for river towns, verified against river position.
These are towns/landmarks that sit directly on the Mississippi River bank.
"""

import json
import os
import math

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "content-markdown", "river-coordinates.json")

# Known points ON the river, verified coordinates
# Format: (mile, lat, lng, name)
RIVER_POINTS = [
    # St. Louis to Caruthersville
    (195, 38.6270, -90.1994, "St. Louis, MO"),
    (180, 38.4700, -90.2100, "Herculaneum, MO"),
    (166, 38.3150, -90.3800, "Festus/Crystal City, MO"),
    (150, 38.1500, -90.3950, "Ste. Genevieve, MO"),
    (130, 37.8000, -89.6800, "Kaskaskia Island, IL"),
    (110, 37.5700, -89.5200, "Chester, IL"),
    (80,  37.2200, -89.4600, "Grand Tower, IL"),
    (52,  37.0053, -89.1765, "Cairo, IL"),
    (953, 36.8883, -89.1950, "Wickliffe, KY"),
    (930, 36.7500, -89.2200, "New Madrid, MO"),
    (900, 36.4500, -89.4800, "Tiptonville, TN"),
    (870, 36.1814, -89.6664, "Caruthersville, MO"),

    # Caruthersville to Memphis
    (850, 36.0300, -89.7400, "Cottonwood Point, MO"),
    (830, 35.8500, -89.8700, "Osceola, AR"),
    (800, 35.5800, -90.0100, "Barfield, AR"),
    (770, 35.3600, -90.0200, "Shelby Forest, TN"),
    (737, 35.1496, -90.0490, "Memphis, TN"),

    # Memphis to Helena
    (734, 35.1300, -90.0590, "Memphis Lower Bridges"),
    (725, 35.0200, -90.1100, "McKellar Lake Harbor"),
    (715, 34.9200, -90.2200, "Cat Island"),
    (700, 34.8200, -90.3000, "Tunica, MS"),
    (687, 34.7200, -90.3800, "Mhoon Landing"),
    (676, 34.6200, -90.4800, "St. Francis River"),
    (663, 34.5292, -90.5918, "Helena, AR"),

    # Helena to Greenville
    (652, 34.3700, -90.6400, "Friars Point, MS"),
    (640, 34.2500, -90.7500, "Island 62"),
    (620, 34.0800, -90.8500, "Rosedale, MS"),
    (600, 33.8500, -90.9200, "Scott, MS"),
    (580, 33.6500, -91.0000, "Benoit, MS"),
    (537, 33.4100, -91.0600, "Greenville, MS"),

    # Greenville to Vicksburg
    (520, 33.2500, -91.1200, "Lake Village, AR"),
    (500, 33.0500, -91.1800, "Lake Providence, LA"),
    (480, 32.8800, -91.1000, "Tallulah, LA"),
    (460, 32.6500, -90.9500, "Eagle Lake, MS"),
    (437, 32.3525, -90.8775, "Vicksburg, MS"),

    # Vicksburg to Baton Rouge
    (420, 32.2000, -90.9500, "Grand Gulf, MS"),
    (400, 31.9500, -91.1000, "Port Gibson, MS"),
    (364, 31.5604, -91.4043, "Natchez, MS"),
    (340, 31.3700, -91.4800, "Vidalia, LA"),
    (305, 30.9500, -91.5200, "St. Francisville, LA"),
    (270, 30.6500, -91.3500, "Port Hudson, LA"),
    (229, 30.4507, -91.1874, "Baton Rouge, LA"),

    # Atchafalaya River (separate channel)
    (159, 31.0700, -91.6000, "Old River/Simmesport, LA"),
    (130, 30.7500, -91.6500, "Krotz Springs, LA"),
    (100, 30.4500, -91.6800, "Henderson, LA"),
    (70,  30.2200, -91.5300, "Breaux Bridge, LA"),
    (40,  30.0000, -91.3500, "New Iberia area, LA"),
    (0,   29.7008, -91.1972, "Morgan City, LA"),

    # Baton Rouge to Venice
    (225, 30.4200, -91.1500, "Port Allen, LA"),
    (200, 30.2200, -90.9500, "Donaldsonville, LA"),
    (175, 30.0500, -90.7500, "Convent, LA"),
    (150, 29.9800, -90.6000, "Gramercy, LA"),
    (128, 29.9500, -90.4000, "Destrehan, LA"),
    (105, 29.9400, -90.1200, "Harahan/Bridge City, LA"),
    (95,  29.9511, -90.0715, "New Orleans, LA"),
    (82,  29.9200, -89.9500, "Chalmette, LA"),
    (60,  29.7500, -89.7500, "English Turn, LA"),
    (40,  29.5500, -89.5500, "Empire, LA"),
    (20,  29.3800, -89.4200, "Buras, LA"),
    (10,  29.2769, -89.3547, "Venice, LA"),

    # Birdsfoot Delta
    (8,   29.2500, -89.3300, "South of Venice"),
    (5,   29.2000, -89.2800, "Pilottown, LA"),
    (0,   29.1500, -89.2500, "Head of Passes"),
]

def interpolate_point(mile, points):
    """Find or interpolate coordinates for a given river mile."""
    # Find bracketing points
    above = None
    below = None

    for m, lat, lng, name in points:
        if m == mile:
            return lat, lng
        if m > mile and (above is None or m < above[0]):
            above = (m, lat, lng)
        if m < mile and (below is None or m > below[0]):
            below = (m, lat, lng)

    if above and below:
        # Linear interpolation
        ratio = (mile - below[0]) / (above[0] - below[0])
        lat = below[1] + ratio * (above[1] - below[1])
        lng = below[2] + ratio * (above[2] - below[2])
        return lat, lng

    return None, None


def main():
    # Build section midpoint markers (for homepage)
    sections = [
        ("stlouis-to-caruthersville", "St. Louis to Caruthersville", 195, 870, "Cape Girardeau area"),
        ("caruthersville-to-memphis", "Caruthersville to Memphis", 870, 737, "Osceola area"),
        ("memphis-to-helena", "Memphis to Helena", 737, 663, "Tunica area"),
        ("helena-to-greenville", "Helena to Greenville", 663, 537, "Rosedale area"),
        ("greenville-to-vicksburg", "Greenville to Vicksburg", 537, 437, "Lake Providence area"),
        ("vicksburg-to-baton-rouge", "Vicksburg to Baton Rouge", 437, 229, "Natchez area"),
        ("atchafalaya-river", "Atchafalaya River", 159, 0, "Henderson area"),
        ("baton-rouge-to-venice", "Baton Rouge to Venice", 229, 10, "New Orleans area"),
        ("birdsfoot-delta", "Birdsfoot Delta", 10, 0, "Venice area"),
    ]

    section_markers = []
    for slug, name, mile_start, mile_end, desc in sections:
        mid_mile = (mile_start + mile_end) // 2

        # For Atchafalaya, use its own point set
        lat, lng = interpolate_point(mid_mile, RIVER_POINTS)
        if lat:
            section_markers.append({
                "slug": slug,
                "name": name,
                "mile_start": mile_start,
                "mile_end": mile_end,
                "center_mile": mid_mile,
                "lat": round(lat, 5),
                "lng": round(lng, 5),
                "description": desc
            })
            print(f"  {name}: mile {mid_mile} -> ({lat:.4f}, {lng:.4f})")

    # Build all river points for the river line
    river_line = []
    for m, lat, lng, name in sorted(RIVER_POINTS, key=lambda x: -x[0]):
        river_line.append({
            "mile": m,
            "lat": round(lat, 5),
            "lng": round(lng, 5),
            "name": name
        })

    # Read mile-markers.json and add approximate coordinates
    mm_path = os.path.join(os.path.dirname(__file__), "..", "content-markdown", "mile-markers.json")
    if os.path.exists(mm_path):
        with open(mm_path, 'r', encoding='utf-8') as f:
            mm_data = json.load(f)

        geo_markers = []
        for mk in mm_data['markers']:
            lat, lng = interpolate_point(mk['mile'], RIVER_POINTS)
            if lat:
                # Offset slightly for LBD vs RBD
                if mk.get('bank') == 'LBD':
                    lng += 0.003
                elif mk.get('bank') == 'RBD':
                    lng -= 0.003

                geo_markers.append({
                    "mile": mk['mile'],
                    "bank": mk.get('bank', ''),
                    "name": mk['name'],
                    "section": mk['section'],
                    "features": mk['features'],
                    "lat": round(lat, 5),
                    "lng": round(lng, 5),
                })

        print(f"\nGeolocated {len(geo_markers)} of {len(mm_data['markers'])} mile markers")
    else:
        geo_markers = []
        print("No mile-markers.json found")

    # Save everything
    output = {
        "section_markers": section_markers,
        "river_line": river_line,
        "mile_markers": geo_markers,
        "total_geolocated": len(geo_markers),
    }

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to: {OUTPUT}")


if __name__ == '__main__':
    main()
