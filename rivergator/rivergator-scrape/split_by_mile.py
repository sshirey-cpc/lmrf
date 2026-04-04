"""
Split riverlog content into individual mile-marker posts.
Each post covers one mile marker (or a tight cluster of markers at the same mile).

Reads the 655 original riverlog pages, detects mile marker boundaries,
and outputs individual posts ready for Ghost import.
"""

import os
import re
import json
import glob
import hashlib
from datetime import datetime

PAGES_DIR = "C:/Users/scott/lmrf/rivergator/riverlog-data/pages"
USACE_PATH = "C:/Users/scott/lmrf/rivergator/content-markdown/usace-mile-coordinates.json"
OUTPUT_DIR = "C:/Users/scott/lmrf/rivergator/ghost-import"

SECTIONS = [
    ("stlouis-to-caruthersville", "St. Louis to Caruthersville", "Mile 953–870"),
    ("caruthersville-to-memphis", "Caruthersville to Memphis", "Mile 850–737"),
    ("memphis-to-helena", "Memphis to Helena", "Mile 737–663"),
    ("helena-to-greenville", "Helena to Greenville", "Mile 663–537"),
    ("greenville-to-vicksburg", "Greenville to Vicksburg", "Mile 537–437"),
    ("vicksburg-to-baton-rouge", "Vicksburg to Baton Rouge", "Mile 437–225"),
    ("atchafalaya-river", "Atchafalaya River", "Mile 159–0"),
    ("baton-rouge-to-venice", "Baton Rouge to Venice", "Mile 229–10"),
    ("birdsfoot-delta", "Birdsfoot Delta", "Mile 10–0"),
]

# Mile marker detection pattern
MILE_PATTERN = re.compile(
    r'(?:^|\s)(\d{1,3}(?:\.\d{1,2})?)\s+(LBD|RBD|L\.?B\.?D\.?|R\.?B\.?D\.?)\s+(.+?)(?:\s{2,}|\n|$)'
)

# Alternative: "LBD Mile XXX" or just "XXX.X Name" at start
MILE_PATTERN2 = re.compile(
    r'(?:^|\s)(LBD|RBD)\s+(?:Mile\s+)?(\d{1,3}(?:\.\d{1,2})?)\s+(.+?)(?:\s{2,}|\n|$)'
)

MILE_PATTERN3 = re.compile(
    r'^(\d{1,3}(?:\.\d{1,2})?)\s+([A-Z][A-Za-z\s\'.,&()-]{3,60})'
)


def detect_mile_markers(text):
    """Find all mile marker positions in text, return list of (char_position, mile, bank, name)."""
    markers = []

    for m in MILE_PATTERN.finditer(text):
        mile = float(m.group(1))
        bank = m.group(2).replace('.', '').upper()
        name = m.group(3).strip()[:80]
        if 0 <= mile <= 960:
            markers.append((m.start(), mile, bank, name))

    for m in MILE_PATTERN2.finditer(text):
        bank = m.group(1).replace('.', '').upper()
        mile = float(m.group(2))
        name = m.group(3).strip()[:80]
        if 0 <= mile <= 960:
            already = any(abs(mk[1] - mile) < 0.1 for mk in markers)
            if not already:
                markers.append((m.start(), mile, bank, name))

    # Sort by position in text
    markers.sort(key=lambda x: x[0])
    return markers


def split_text_by_markers(text, markers):
    """Split text into sections based on mile marker positions."""
    if not markers:
        return [{"mile": None, "bank": "", "name": "Content", "text": text}]

    sections = []
    for i, (pos, mile, bank, name) in enumerate(markers):
        # Text from this marker to the next (or end)
        start = pos
        if i + 1 < len(markers):
            end = markers[i + 1][0]
        else:
            end = len(text)

        section_text = text[start:end].strip()
        if len(section_text) > 50:  # Skip tiny fragments
            sections.append({
                "mile": mile,
                "bank": bank,
                "name": name.split('.')[0].strip(),  # First sentence of name
                "text": section_text
            })

    # Include any preamble text before the first marker
    if markers and markers[0][0] > 100:
        preamble = text[:markers[0][0]].strip()
        if len(preamble) > 100:
            sections.insert(0, {
                "mile": None,
                "bank": "",
                "name": "Introduction",
                "text": preamble
            })

    return sections


def text_to_html(text):
    """Convert plain text to simple HTML."""
    # Split into paragraphs
    paragraphs = text.split('\n\n')
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Detect mile marker headers
        m = re.match(r'^(\d{1,3}(?:\.\d{1,2})?)\s+(LBD|RBD)\s+(.+)', p)
        if m:
            html_parts.append(f'<h3>Mile {m.group(1)} {m.group(2)} — {m.group(3)[:60]}</h3>')
            rest = p[m.end():].strip()
            if rest:
                html_parts.append(f'<p>{rest}</p>')
        else:
            html_parts.append(f'<p>{p}</p>')
    return '\n'.join(html_parts)


def make_id(text):
    """Generate a deterministic ID from text."""
    return hashlib.sha256(text.encode()).hexdigest()[:24]


def main():
    # Load USACE coordinates
    with open(USACE_PATH) as f:
        usace = json.load(f)
    miss_coords = usace.get('MISSISSIPPI-LO', {})

    all_posts = []
    all_tags = {}

    # Process each section
    for section_slug, section_name, mile_label in SECTIONS:
        print(f"\n=== {section_name} ===")

        # Find all pages for this section
        pattern = os.path.join(PAGES_DIR, f"{section_slug}-*.txt")
        files = sorted(glob.glob(pattern))

        # Group by chapter
        chapters = {}
        for filepath in files:
            basename = os.path.basename(filepath).replace('.txt', '')
            # Extract chapter slug: section-slug-chapter-slug-pagenum
            remainder = basename[len(section_slug) + 1:]
            m = re.match(r'(.+)-(\d+)$', remainder)
            if m:
                chapter_slug = m.group(1)
                page_num = int(m.group(2))
                if chapter_slug not in chapters:
                    chapters[chapter_slug] = []
                chapters[chapter_slug].append((page_num, filepath))

        section_posts = 0

        for chapter_slug, pages in sorted(chapters.items()):
            # Sort pages by number and concatenate
            pages.sort(key=lambda x: x[0])

            full_text = ""
            for page_num, filepath in pages:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Skip header
                lines = content.split('\n')
                body_start = 0
                for i, line in enumerate(lines):
                    if line.startswith('=' * 20):
                        body_start = i + 1
                        break
                body = '\n'.join(lines[body_start:]).strip()
                full_text += body + "\n\n"

            # Detect mile markers
            markers = detect_mile_markers(full_text)

            # Is this an intro/appendix chapter?
            is_intro = 'intro' in chapter_slug.lower() or 'preamble' in chapter_slug.lower()
            is_appendix = 'appendix' in chapter_slug.lower() or 'addendum' in chapter_slug.lower()

            if is_intro or is_appendix:
                # Keep intro/appendix as single posts
                post_type = "introduction" if is_intro else "appendix"
                title = f"{section_name}: {'Introduction' if is_intro else 'Appendix'}"
                slug = f"{section_slug}-{chapter_slug}"

                all_posts.append({
                    "title": title,
                    "slug": slug,
                    "html": text_to_html(full_text[:20000]),  # Trim very long appendices
                    "section": section_slug,
                    "section_name": section_name,
                    "chapter": chapter_slug,
                    "mile": None,
                    "bank": "",
                    "post_type": post_type,
                    "word_count": len(full_text.split()),
                })
                section_posts += 1
                continue

            # Split by mile markers
            sections = split_text_by_markers(full_text, markers)

            if not sections:
                # No markers found, keep as single post
                title = f"{section_name}: {chapter_slug.replace('-', ' ').title()}"
                slug = f"{section_slug}-{chapter_slug}"
                all_posts.append({
                    "title": title,
                    "slug": slug,
                    "html": text_to_html(full_text[:15000]),
                    "section": section_slug,
                    "section_name": section_name,
                    "chapter": chapter_slug,
                    "mile": None,
                    "bank": "",
                    "post_type": "chapter",
                    "word_count": len(full_text.split()),
                })
                section_posts += 1
                continue

            # Create individual posts for each mile marker
            for sec in sections:
                mile = sec["mile"]
                bank = sec["bank"]
                name = sec["name"]

                if mile is not None:
                    title = f"Mile {mile} {bank} — {name}"
                    slug = f"mile-{str(mile).replace('.', '-')}-{bank.lower()}-{re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:40]}"
                else:
                    title = f"{section_name}: {name}"
                    slug = f"{section_slug}-{re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:40]}"

                # Get USACE coordinate if available
                coord = None
                if mile is not None:
                    mile_key = str(int(round(mile)))
                    coord = miss_coords.get(mile_key)

                post = {
                    "title": title,
                    "slug": slug,
                    "html": text_to_html(sec["text"]),
                    "section": section_slug,
                    "section_name": section_name,
                    "chapter": chapter_slug,
                    "mile": mile,
                    "bank": bank,
                    "post_type": "mile-marker",
                    "word_count": len(sec["text"].split()),
                }
                if coord:
                    post["lng"] = coord[0]
                    post["lat"] = coord[1]

                all_posts.append(post)
                section_posts += 1

            print(f"  {chapter_slug}: {len(markers)} markers -> {len(sections)} posts")

        print(f"  Section total: {section_posts} posts")

    # Stats
    mile_posts = [p for p in all_posts if p["post_type"] == "mile-marker"]
    intro_posts = [p for p in all_posts if p["post_type"] == "introduction"]
    appendix_posts = [p for p in all_posts if p["post_type"] == "appendix"]
    chapter_posts = [p for p in all_posts if p["post_type"] == "chapter"]

    print(f"\n{'='*60}")
    print(f"TOTAL POSTS: {len(all_posts)}")
    print(f"  Mile marker posts: {len(mile_posts)}")
    print(f"  Introduction posts: {len(intro_posts)}")
    print(f"  Appendix posts: {len(appendix_posts)}")
    print(f"  Chapter posts (no markers found): {len(chapter_posts)}")
    print(f"  Total words: {sum(p['word_count'] for p in all_posts):,}")

    # Build Ghost import JSON
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

    ghost_tags = [
        {"id": make_id("river-log"), "name": "#river-log", "slug": "hash-river-log", "visibility": "internal"},
        {"id": make_id("mile-marker"), "name": "#mile-marker", "slug": "hash-mile-marker", "visibility": "internal"},
    ]

    # Section tags
    for slug, name, _ in SECTIONS:
        ghost_tags.append({
            "id": make_id(f"section-{slug}"),
            "name": name,
            "slug": slug,
            "visibility": "public",
        })

    # Feature tags
    for feat in ["access-point", "camping", "hazard", "bridge", "town", "island", "confluence"]:
        ghost_tags.append({
            "id": make_id(f"feat-{feat}"),
            "name": feat.replace("-", " ").title(),
            "slug": feat,
            "visibility": "public",
        })

    ghost_posts = []
    ghost_posts_tags = []

    for i, post in enumerate(all_posts):
        post_id = make_id(f"post-{post['slug']}-{i}")

        ghost_post = {
            "id": post_id,
            "title": post["title"],
            "slug": post["slug"],
            "html": post["html"],
            "status": "published",
            "created_at": now,
            "updated_at": now,
            "published_at": now,
            "custom_excerpt": f"{post['section_name']} — {post.get('mile', '')} {post.get('bank', '')}".strip(),
            "type": "post",
            "featured": 0,
        }
        ghost_posts.append(ghost_post)

        # Tag: river-log
        ghost_posts_tags.append({"post_id": post_id, "tag_id": make_id("river-log")})

        # Tag: section
        ghost_posts_tags.append({"post_id": post_id, "tag_id": make_id(f"section-{post['section']}")})

        # Tag: mile-marker (if applicable)
        if post["post_type"] == "mile-marker":
            ghost_posts_tags.append({"post_id": post_id, "tag_id": make_id("mile-marker")})

    ghost_import = {
        "db": [{
            "meta": {"exported_on": int(datetime.utcnow().timestamp() * 1000), "version": "5.0.0"},
            "data": {
                "posts": ghost_posts,
                "tags": ghost_tags,
                "posts_tags": ghost_posts_tags,
                "users": [{
                    "id": "1",
                    "name": "John Ruskey",
                    "slug": "john-ruskey",
                    "email": "driftwoodjohnnie@icloud.com",
                    "roles": [{"name": "Author"}]
                }],
            }
        }]
    }

    # Save
    output_path = os.path.join(OUTPUT_DIR, "ghost-import-by-mile.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ghost_import, f)

    print(f"\nGhost import saved: {output_path}")
    print(f"File size: {os.path.getsize(output_path) / (1024*1024):.1f} MB")

    # Also save a mile-marker index for the section pages
    index = []
    for post in all_posts:
        if post["mile"] is not None:
            entry = {
                "mile": post["mile"],
                "bank": post["bank"],
                "name": post["title"],
                "slug": post["slug"],
                "section": post["section"],
                "words": post["word_count"],
            }
            if "lat" in post:
                entry["lat"] = post["lat"]
                entry["lng"] = post["lng"]
            index.append(entry)

    index.sort(key=lambda x: -x["mile"])
    index_path = os.path.join(OUTPUT_DIR, "mile-marker-index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)

    print(f"Mile marker index: {index_path} ({len(index)} entries)")


if __name__ == '__main__':
    main()
