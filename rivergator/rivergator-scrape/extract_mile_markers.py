"""
Extract mile markers from all riverlog pages into structured JSON.
Parses patterns like "663 LBD", "734.7 RBD", "Mile 195" etc.
Also identifies features: access points, camping, hazards, towns, bridges, islands.
"""

import os
import re
import json
import glob

PAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "riverlog-data", "pages")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "content-markdown")

SECTIONS = [
    ("stlouis-to-caruthersville", "St. Louis to Caruthersville", 195, 850),
    ("caruthersville-to-memphis", "Caruthersville to Memphis", 850, 737),
    ("memphis-to-helena", "Memphis to Helena", 737, 663),
    ("helena-to-greenville", "Helena to Greenville", 663, 537),
    ("greenville-to-vicksburg", "Greenville to Vicksburg", 537, 437),
    ("vicksburg-to-baton-rouge", "Vicksburg to Baton Rouge", 437, 225),
    ("atchafalaya-river", "Atchafalaya River", 159, 0),
    ("baton-rouge-to-venice", "Baton Rouge to Venice", 229, 10),
    ("birdsfoot-delta", "Birdsfoot Delta", 10, 0),
]

# Feature detection keywords
FEATURE_PATTERNS = {
    "access_point": [
        r'\b(?:boat ramp|boat launch|ramp|landing|put[- ]?in|take[- ]?out|access point|public access)\b',
    ],
    "camping": [
        r'\b(?:camp(?:ing|site|ground)?|tent|bivouac|overnight|sleep here)\b',
    ],
    "hazard": [
        r'\b(?:danger(?:ous)?|hazard|avoid|warning|caution|deadly|do not|unsafe|whirlpool|strainer)\b',
    ],
    "town": [
        r'\b(?:town of|city of|village of|community of|population)\b',
    ],
    "bridge": [
        r'\b(?:bridge|overpass|crossing)\b',
    ],
    "island": [
        r'\b(?:island|towhead|bar|sandbar|sand bar)\b',
    ],
    "confluence": [
        r'\b(?:confluence|mouth of|joins|enters|creek|bayou|river enters|tributary)\b',
    ],
    "lock_dam": [
        r'\b(?:lock|dam|lock and dam)\b',
    ],
    "dike": [
        r'\b(?:dike|dikes|wing dam|chevron|revetment|rip[- ]?rap)\b',
    ],
    "harbor": [
        r'\b(?:harbor|harbour|port|marina|dock|wharf)\b',
    ],
    "supply": [
        r'\b(?:grocery|store|gas station|resupply|supplies|water source|potable)\b',
    ],
}


def detect_features(text):
    """Detect feature types from surrounding text."""
    text_lower = text.lower()
    features = []
    for feature_type, patterns in FEATURE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                features.append(feature_type)
                break
    return features


def extract_markers_from_text(text, section_slug):
    """Extract all mile markers from a page of text."""
    markers = []

    # Split into lines for context
    lines = text.split('\n')

    for i, line in enumerate(lines):
        # Pattern 1: "XXX.X LBD/RBD Name..." (most common)
        for m in re.finditer(r'(?:^|\s)(\d{1,3}(?:\.\d{1,2})?)\s+(LBD|RBD|L\.?B\.?D\.?|R\.?B\.?D\.?)\s+(.+?)(?:\.|$)', line):
            mile = float(m.group(1))
            bank = m.group(2).replace('.', '').upper()
            name = m.group(3).strip()
            # Clean up name - take first sentence or up to 100 chars
            name = re.split(r'[.!?]', name)[0].strip()
            if len(name) > 120:
                name = name[:120].rsplit(' ', 1)[0] + '...'

            # Get context (surrounding 500 chars for feature detection)
            start = max(0, m.start() - 200)
            end = min(len(line), m.end() + 300)
            context = line[start:end]

            # Also include next line for context
            if i + 1 < len(lines):
                context += ' ' + lines[i + 1]

            features = detect_features(context)

            markers.append({
                'mile': mile,
                'bank': bank,
                'name': name,
                'section': section_slug,
                'features': features,
                'context_preview': context[:200].strip(),
            })

        # Pattern 2: "LBD/RBD Mile XXX" or "LBD XXX.X"
        for m in re.finditer(r'(LBD|RBD|L\.?B\.?D\.?|R\.?B\.?D\.?)\s+(?:Mile\s+)?(\d{1,3}(?:\.\d{1,2})?)\s+(.+?)(?:\.|$)', line):
            bank = m.group(1).replace('.', '').upper()
            mile = float(m.group(2))
            name = m.group(3).strip()
            name = re.split(r'[.!?]', name)[0].strip()
            if len(name) > 120:
                name = name[:120].rsplit(' ', 1)[0] + '...'

            start = max(0, m.start() - 200)
            end = min(len(line), m.end() + 300)
            context = line[start:end]
            if i + 1 < len(lines):
                context += ' ' + lines[i + 1]

            features = detect_features(context)

            # Avoid duplicates
            already = any(
                abs(mk['mile'] - mile) < 0.01 and mk['bank'] == bank and mk['name'] == name
                for mk in markers
            )
            if not already:
                markers.append({
                    'mile': mile,
                    'bank': bank,
                    'name': name,
                    'section': section_slug,
                    'features': features,
                    'context_preview': context[:200].strip(),
                })

        # Pattern 3: Standalone "XXX.X Name" at line start (common in appendices)
        m = re.match(r'^(\d{1,3}(?:\.\d{1,2})?)\s+([A-Z][a-zA-Z\s\',&-]{3,80})', line)
        if m:
            mile = float(m.group(1))
            name = m.group(2).strip()
            # Only if it looks like a real mile marker (reasonable range)
            if 0 <= mile <= 1000:
                context = line[:300]
                if i + 1 < len(lines):
                    context += ' ' + lines[i + 1]
                features = detect_features(context)

                already = any(
                    abs(mk['mile'] - mile) < 0.05 and mk['name'][:20] == name[:20]
                    for mk in markers
                )
                if not already:
                    markers.append({
                        'mile': mile,
                        'bank': '',
                        'name': name,
                        'section': section_slug,
                        'features': features,
                        'context_preview': context[:200].strip(),
                    })

    return markers


def main():
    all_markers = []

    # Process all riverlog page text files
    txt_files = sorted(glob.glob(os.path.join(PAGES_DIR, "*.txt")))
    print(f"Processing {len(txt_files)} riverlog page files...")

    for filepath in txt_files:
        basename = os.path.basename(filepath).replace('.txt', '')

        # Determine section from filename
        section_slug = None
        for slug, _, _, _ in SECTIONS:
            if basename.startswith(slug):
                section_slug = slug
                break

        if not section_slug:
            continue

        # Skip appendix/intro pages for mile markers (they reference miles but aren't the primary source)
        # Actually, let's include them — appendices have valuable data too

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip header
        lines = content.split('\n')
        body_start = 0
        for i, line in enumerate(lines):
            if line.startswith('=' * 20):
                body_start = i + 1
                break
        body = '\n'.join(lines[body_start:])

        markers = extract_markers_from_text(body, section_slug)

        # Tag markers with their chapter
        chapter_slug = basename.replace(section_slug + '-', '').rsplit('-', 1)[0]
        for mk in markers:
            mk['chapter'] = chapter_slug
            mk['source_file'] = basename

        all_markers.extend(markers)

    # Deduplicate - same mile + same name within a section
    seen = set()
    unique_markers = []
    for mk in all_markers:
        key = (mk['section'], round(mk['mile'], 1), mk['name'][:30])
        if key not in seen:
            seen.add(key)
            unique_markers.append(mk)

    # Sort by section order then mile (descending, since river flows south)
    section_order = {slug: i for i, (slug, _, _, _) in enumerate(SECTIONS)}
    unique_markers.sort(key=lambda mk: (section_order.get(mk['section'], 99), -mk['mile']))

    # Stats
    print(f"\nTotal markers extracted: {len(all_markers)}")
    print(f"After dedup: {len(unique_markers)}")

    # By section
    print("\nMarkers by section:")
    for slug, name, _, _ in SECTIONS:
        count = sum(1 for mk in unique_markers if mk['section'] == slug)
        print(f"  {name}: {count}")

    # By feature type
    print("\nMarkers by feature:")
    feature_counts = {}
    for mk in unique_markers:
        for f in mk['features']:
            feature_counts[f] = feature_counts.get(f, 0) + 1
    for feat, count in sorted(feature_counts.items(), key=lambda x: -x[1]):
        print(f"  {feat}: {count}")

    # Sample markers
    print("\nSample markers (first 20):")
    for mk in unique_markers[:20]:
        bank = f" {mk['bank']}" if mk['bank'] else ""
        feats = ', '.join(mk['features']) if mk['features'] else 'none'
        print(f"  Mile {mk['mile']}{bank} — {mk['name'][:60]} [{feats}]")

    # Save full dataset
    output_path = os.path.join(OUTPUT_DIR, 'mile-markers.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_markers': len(unique_markers),
            'generated': '2026-04-01',
            'sections': [
                {'slug': slug, 'name': name, 'mile_start': ms, 'mile_end': me}
                for slug, name, ms, me in SECTIONS
            ],
            'markers': unique_markers,
        }, f, indent=2)

    print(f"\nSaved to: {output_path}")

    # Also save a simplified CSV-like version for quick reference
    csv_path = os.path.join(OUTPUT_DIR, 'mile-markers.csv')
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write('mile,bank,name,section,features\n')
        for mk in unique_markers:
            feats = '|'.join(mk['features'])
            name = mk['name'].replace('"', "'")
            f.write(f'{mk["mile"]},{mk["bank"]},"{name}",{mk["section"]},{feats}\n')

    print(f"CSV saved to: {csv_path}")


if __name__ == '__main__':
    main()
