"""
Split riverlog content into individual mile-marker posts — v2.
Fixes: clean titles, short slugs, proper HTML formatting.
"""

import os
import re
import json
import glob
import hashlib
from datetime import datetime, timezone

PAGES_DIR = "C:/Users/scott/lmrf/rivergator/riverlog-data/pages"
USACE_PATH = "C:/Users/scott/lmrf/rivergator/content-markdown/usace-mile-coordinates.json"
OUTPUT_DIR = "C:/Users/scott/lmrf/rivergator/ghost-import"

SECTIONS = [
    ("stlouis-to-caruthersville", "St. Louis to Caruthersville"),
    ("caruthersville-to-memphis", "Caruthersville to Memphis"),
    ("memphis-to-helena", "Memphis to Helena"),
    ("helena-to-greenville", "Helena to Greenville"),
    ("greenville-to-vicksburg", "Greenville to Vicksburg"),
    ("vicksburg-to-baton-rouge", "Vicksburg to Baton Rouge"),
    ("atchafalaya-river", "Atchafalaya River"),
    ("baton-rouge-to-venice", "Baton Rouge to Venice"),
    ("birdsfoot-delta", "Birdsfoot Delta"),
]

# Pattern: "736 LBD Memphis, Tennessee" or "736.5 RBD Some Place Name"
MILE_RE = re.compile(
    r'(?:^|\n)\s*(?:LBD\s+)?(?:Mile\s+)?(\d{1,3}(?:\.\d{1,2})?)\s+(LBD|RBD|L\.?B\.?D\.?|R\.?B\.?D\.?)\s+'
)

# Alternative: "LBD 736 Name" or "RBD Mile 736"
MILE_RE2 = re.compile(
    r'(?:^|\n)\s*(LBD|RBD)\s+(?:Mile\s+)?(\d{1,3}(?:\.\d{1,2})?)\s+'
)


def extract_landmark_name(text, start_pos):
    """Extract just the landmark name from text after the mile/bank designation.
    Stops at the first sentence boundary or after ~60 chars."""
    remaining = text[start_pos:start_pos + 200].strip()

    # Remove URLs
    remaining = re.sub(r'https?://\S+', '', remaining).strip()

    # Take up to the first period, comma-heavy break, or newline
    # But ensure we get at least a few words
    name = ""
    for i, char in enumerate(remaining):
        if char == '\n':
            break
        if char == '.' and i > 5:
            name = remaining[:i]
            break
        if i > 80:
            # Find last space before 80
            name = remaining[:80].rsplit(' ', 1)[0]
            break

    if not name:
        name = remaining.split('\n')[0][:80]

    # Clean up
    name = name.strip().rstrip(',').rstrip(':').strip()

    # Remove common prefixes that aren't part of the name
    name = re.sub(r'^(?:the|a|an)\s+', '', name, flags=re.IGNORECASE)

    # If the name is too generic (starts with lowercase), try harder
    if name and name[0].islower():
        # Try to find a capitalized phrase
        cap_match = re.search(r'([A-Z][A-Za-z\s\'.,&()-]{3,60})', remaining[:150])
        if cap_match:
            name = cap_match.group(1).strip().rstrip('.')

    # Final cleanup
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > 60:
        name = name[:60].rsplit(' ', 1)[0]

    return name if name else "River Mile"


def find_mile_markers(text):
    """Find all mile marker positions in text. Returns [(position, mile, bank, name)]."""
    markers = []

    for m in MILE_RE.finditer(text):
        mile = float(m.group(1))
        bank = m.group(2).replace('.', '').upper()
        if 0 <= mile <= 960:
            name = extract_landmark_name(text, m.end())
            markers.append((m.start(), mile, bank, name))

    for m in MILE_RE2.finditer(text):
        bank = m.group(1).replace('.', '').upper()
        mile = float(m.group(2))
        if 0 <= mile <= 960:
            # Check not duplicate
            already = any(abs(mk[1] - mile) < 0.05 and mk[2] == bank for mk in markers)
            if not already:
                name = extract_landmark_name(text, m.end())
                markers.append((m.start(), mile, bank, name))

    markers.sort(key=lambda x: x[0])

    # Deduplicate markers at same mile+bank (keep first)
    seen = set()
    unique = []
    for pos, mile, bank, name in markers:
        key = (round(mile, 1), bank)
        if key not in seen:
            seen.add(key)
            unique.append((pos, mile, bank, name))

    return unique


def make_clean_slug(mile, bank, name):
    """Make a short, clean slug like 'mile-736-memphis-mud-island'."""
    # Clean name for slug
    slug_name = re.sub(r'[^a-z0-9\s]', '', name.lower())
    slug_name = re.sub(r'\s+', '-', slug_name).strip('-')
    # Take first 3-4 words max
    parts = slug_name.split('-')[:4]
    slug_name = '-'.join(parts)

    mile_str = str(mile).replace('.', '-')
    return f"mile-{mile_str}-{slug_name}"


def text_to_html(text):
    """Convert raw text to well-formatted HTML with paragraphs."""
    # Split on double newlines or long whitespace gaps
    text = re.sub(r'\n{2,}', '\n\n', text)

    # Also split before mile marker references within text
    text = re.sub(r'(\d{3}(?:\.\d)?\s+(?:LBD|RBD))', r'\n\n\1', text)

    paragraphs = text.split('\n\n')
    html_parts = []

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue

        # Remove URLs
        p = re.sub(r'https?://\S+', '', p).strip()

        # Detect sub-mile-marker headers within the text
        header_match = re.match(
            r'^(\d{1,3}(?:\.\d{1,2})?)\s+(LBD|RBD)\s+(.+)', p
        )
        if header_match:
            mile = header_match.group(1)
            bank = header_match.group(2)
            rest = header_match.group(3)
            # Extract name from rest (first phrase)
            name_end = rest.find('.')
            if name_end > 0 and name_end < 80:
                landmark = rest[:name_end]
                description = rest[name_end+1:].strip()
                html_parts.append(f'<h4>Mile {mile} {bank} — {landmark}</h4>')
                if description:
                    html_parts.append(f'<p>{description}</p>')
            else:
                html_parts.append(f'<h4>Mile {mile} {bank}</h4>')
                html_parts.append(f'<p>{rest}</p>')
            continue

        # Detect water level headers
        wl_match = re.match(r'^(Low Water|Medium Water|High Water|Flood Stage|Extreme Low Water|Extreme High Water)[:\s]+(.*)', p)
        if wl_match:
            html_parts.append(f'<p><strong>{wl_match.group(1)}:</strong> {wl_match.group(2)}</p>')
            continue

        # Regular paragraph — split very long paragraphs at sentence boundaries
        if len(p) > 1500:
            sentences = re.split(r'(?<=[.!?])\s+', p)
            chunk = ""
            for s in sentences:
                chunk += s + " "
                if len(chunk) > 400:
                    html_parts.append(f'<p>{chunk.strip()}</p>')
                    chunk = ""
            if chunk.strip():
                html_parts.append(f'<p>{chunk.strip()}</p>')
        else:
            html_parts.append(f'<p>{p}</p>')

    return '\n'.join(html_parts)


def make_id(text):
    return hashlib.sha256(text.encode()).hexdigest()[:24]


def main():
    with open(USACE_PATH) as f:
        usace = json.load(f)
    miss_coords = usace.get('MISSISSIPPI-LO', {})

    all_posts = []

    for section_slug, section_name in SECTIONS:
        print(f"\n=== {section_name} ===")

        pattern = os.path.join(PAGES_DIR, f"{section_slug}-*.txt")
        files = sorted(glob.glob(pattern))

        # Group by chapter
        chapters = {}
        for filepath in files:
            basename = os.path.basename(filepath).replace('.txt', '')
            remainder = basename[len(section_slug) + 1:]
            m = re.match(r'(.+)-(\d+)$', remainder)
            if m:
                chapter_slug = m.group(1)
                page_num = int(m.group(2))
                if chapter_slug not in chapters:
                    chapters[chapter_slug] = []
                chapters[chapter_slug].append((page_num, filepath))

        for chapter_slug, pages in sorted(chapters.items()):
            pages.sort(key=lambda x: x[0])

            full_text = ""
            for page_num, filepath in pages:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                lines = content.split('\n')
                body_start = 0
                for i, line in enumerate(lines):
                    if line.startswith('=' * 20):
                        body_start = i + 1
                        break
                body = '\n'.join(lines[body_start:]).strip()
                full_text += body + "\n\n"

            is_intro = 'intro' in chapter_slug.lower() or 'preamble' in chapter_slug.lower()
            is_appendix = 'appendix' in chapter_slug.lower() or 'addendum' in chapter_slug.lower()

            if is_intro or is_appendix:
                post_type = "introduction" if is_intro else "appendix"
                nice_name = "Introduction" if is_intro else "Appendix"
                title = f"{section_name} — {nice_name}"
                slug = f"{section_slug}-{nice_name.lower()}"

                all_posts.append({
                    "title": title,
                    "slug": slug,
                    "html": text_to_html(full_text[:20000]),
                    "section": section_slug,
                    "section_name": section_name,
                    "mile": None,
                    "bank": "",
                    "post_type": post_type,
                    "excerpt": f"{section_name} — {nice_name}",
                })
                continue

            # Find mile markers
            markers = find_mile_markers(full_text)

            if not markers:
                title = f"{section_name} — {chapter_slug.replace('-', ' ').title()}"
                slug = f"{section_slug}-{chapter_slug}"
                all_posts.append({
                    "title": title,
                    "slug": slug,
                    "html": text_to_html(full_text[:15000]),
                    "section": section_slug,
                    "section_name": section_name,
                    "mile": None,
                    "bank": "",
                    "post_type": "chapter",
                    "excerpt": f"{section_name}",
                })
                continue

            # Split by markers
            for i, (pos, mile, bank, name) in enumerate(markers):
                start = pos
                end = markers[i + 1][0] if i + 1 < len(markers) else len(full_text)
                section_text = full_text[start:end].strip()

                if len(section_text) < 50:
                    continue

                title = f"Mile {mile} {bank} — {name}"
                slug = make_clean_slug(mile, bank, name)

                coord = miss_coords.get(str(int(round(mile))))

                post = {
                    "title": title,
                    "slug": slug,
                    "html": text_to_html(section_text),
                    "section": section_slug,
                    "section_name": section_name,
                    "mile": mile,
                    "bank": bank,
                    "post_type": "mile-marker",
                    "excerpt": f"{section_name} — Mile {mile} {bank}",
                }
                if coord:
                    post["lng"] = coord[0]
                    post["lat"] = coord[1]

                all_posts.append(post)

            print(f"  {chapter_slug}: {len(markers)} mile markers")

    # Also add preamble content before first marker in each chapter
    # (already handled by intro detection above)

    mile_posts = [p for p in all_posts if p["post_type"] == "mile-marker"]
    print(f"\n{'='*60}")
    print(f"TOTAL: {len(all_posts)} posts")
    print(f"  Mile markers: {len(mile_posts)}")
    print(f"  Intros: {len([p for p in all_posts if p['post_type'] == 'introduction'])}")
    print(f"  Appendices: {len([p for p in all_posts if p['post_type'] == 'appendix'])}")

    # Show sample titles
    print(f"\nSample titles:")
    for p in mile_posts[:20]:
        print(f"  {p['title'][:70]}")
        print(f"    slug: {p['slug']}")

    # Save for Ghost API creation
    output_path = os.path.join(OUTPUT_DIR, "ghost-import-v2.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_posts, f)

    print(f"\nSaved: {output_path} ({len(all_posts)} posts)")


if __name__ == '__main__':
    main()
