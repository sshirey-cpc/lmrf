"""
Extract all riverlog custom post types from the WordPress database dump.
This captures the 655 riverlog-page entries, 27 chapters, 9 sections, and associated images.
"""

import re
import json
import os

SQL_PATH = os.path.join(os.path.dirname(__file__), "..", "wpress-extracted", "database.sql")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "riverlog-data")


def parse_sql_string(s, start=0):
    """Parse a SQL quoted string with escape handling."""
    if s[start] != "'":
        raise ValueError(f"Expected quote at {start}")
    result = []
    i = start + 1
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            next_char = s[i + 1]
            if next_char == "'":
                result.append("'")
            elif next_char == '"':
                result.append('"')
            elif next_char == '\\':
                result.append('\\')
            elif next_char == 'n':
                result.append('\n')
            elif next_char == 'r':
                result.append('\r')
            elif next_char == 't':
                result.append('\t')
            elif next_char == '0':
                result.append('\0')
            else:
                result.append(next_char)
            i += 2
        elif s[i] == "'":
            return ''.join(result), i + 1
        else:
            result.append(s[i])
            i += 1
    return ''.join(result), i


def parse_insert_row(line):
    """Parse INSERT INTO wp_posts VALUES (...) line."""
    idx = line.find('VALUES (')
    if idx == -1:
        return None

    s = line[idx + 8:]
    fields = []
    i = 0

    try:
        while i < len(s) and len(fields) < 23:
            while i < len(s) and s[i] in ' \t':
                i += 1
            if i >= len(s):
                break
            if s[i] == "'":
                val, i = parse_sql_string(s, i)
                fields.append(val)
            elif s[i] in '0123456789-':
                j = i
                while j < len(s) and s[j] not in ',);':
                    j += 1
                fields.append(s[i:j])
                i = j
            elif s[i:i+4] == 'NULL':
                fields.append(None)
                i += 4
            else:
                j = i
                while j < len(s) and s[j] not in ',);':
                    j += 1
                fields.append(s[i:j])
                i = j
            if i < len(s) and s[i] == ',':
                i += 1
            elif i < len(s) and s[i] in ');':
                break
    except (IndexError, ValueError):
        return None

    if len(fields) < 21:
        return None

    return {
        'id': fields[0],
        'author': fields[1],
        'date': fields[2],
        'content': fields[4],
        'title': fields[5],
        'excerpt': fields[6],
        'status': fields[7],
        'slug': fields[11],
        'parent_id': fields[17],
        'guid': fields[18] if len(fields) > 18 else '',
        'menu_order': fields[19] if len(fields) > 19 else '0',
        'post_type': fields[20],
    }


def parse_postmeta(sql_path):
    """Extract postmeta for riverlog posts."""
    meta = {}  # post_id -> {key: value}

    with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if not line.startswith('INSERT INTO `SERVMASK_PREFIX_postmeta`'):
                continue

            idx = line.find('VALUES (')
            if idx == -1:
                continue

            s = line[idx + 8:]
            fields = []
            i = 0

            try:
                while i < len(s) and len(fields) < 5:
                    while i < len(s) and s[i] in ' \t':
                        i += 1
                    if i >= len(s):
                        break
                    if s[i] == "'":
                        val, i = parse_sql_string(s, i)
                        fields.append(val)
                    elif s[i] in '0123456789-':
                        j = i
                        while j < len(s) and s[j] not in ',);':
                            j += 1
                        fields.append(s[i:j])
                        i = j
                    elif s[i:i+4] == 'NULL':
                        fields.append(None)
                        i += 4
                    else:
                        j = i
                        while j < len(s) and s[j] not in ',);':
                            j += 1
                        fields.append(s[i:j])
                        i = j
                    if i < len(s) and s[i] == ',':
                        i += 1
                    elif i < len(s) and s[i] in ');':
                        break
            except (IndexError, ValueError):
                continue

            if len(fields) >= 4:
                # postmeta: meta_id, post_id, meta_key, meta_value
                post_id = fields[1]
                meta_key = fields[2]
                meta_value = fields[3]

                if post_id not in meta:
                    meta[post_id] = {}
                meta[post_id][meta_key] = meta_value

    return meta


def clean_html(content):
    """Strip HTML tags and decode entities."""
    if not content:
        return ''
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&#8217;|&#039;', "'", text)
    text = re.sub(r'&#8211;', '-', text)
    text = re.sub(r'&#8220;|&#8221;|&quot;', '"', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&#8230;', '...', text)
    text = re.sub(r'&#\d+;', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # First pass: extract all riverlog posts
    riverlog_types = {'riverlog-page', 'riverlog-image', 'riverlog-chapter', 'riverlog-section', 'river-log'}
    posts_by_type = {t: [] for t in riverlog_types}
    all_posts = {}

    print(f"Reading SQL dump: {SQL_PATH}")

    with open(SQL_PATH, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if not line.startswith('INSERT INTO `SERVMASK_PREFIX_posts`'):
                continue
            row = parse_insert_row(line)
            if row and row['post_type'] in riverlog_types:
                posts_by_type[row['post_type']].append(row)
                all_posts[row['id']] = row

    for pt, posts in posts_by_type.items():
        print(f"  {pt}: {len(posts)} entries")

    # Extract postmeta for riverlog posts
    print("\nExtracting postmeta (this may take a moment)...")
    all_meta = parse_postmeta(SQL_PATH)

    # Filter to just riverlog post meta
    riverlog_ids = set(all_posts.keys())
    riverlog_meta = {pid: m for pid, m in all_meta.items() if pid in riverlog_ids}
    print(f"  Found metadata for {len(riverlog_meta)} riverlog posts")

    # Analyze what meta keys exist for riverlog posts
    meta_keys = {}
    for pid, m in riverlog_meta.items():
        for k in m:
            if k.startswith('_'):
                continue  # Skip internal WP keys
            meta_keys[k] = meta_keys.get(k, 0) + 1

    print(f"\nCustom meta fields for riverlog posts:")
    for k, v in sorted(meta_keys.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v} entries")

    # Build section hierarchy
    sections = sorted(posts_by_type['riverlog-section'], key=lambda x: int(x.get('menu_order', '0')))
    chapters = sorted(posts_by_type['riverlog-chapter'], key=lambda x: int(x.get('menu_order', '0')))
    pages = sorted(posts_by_type['riverlog-page'], key=lambda x: int(x.get('menu_order', '0')))

    print(f"\n{'='*80}")
    print(f"RIVER LOG STRUCTURE")
    print(f"{'='*80}")

    # Build the hierarchy
    structure = []
    for section in sections:
        s_id = section['id']
        s_meta = riverlog_meta.get(s_id, {})
        section_info = {
            'id': s_id,
            'title': section['title'],
            'slug': section['slug'],
            'order': section.get('menu_order', '0'),
            'meta': {k: v for k, v in s_meta.items() if not k.startswith('_')},
            'chapters': [],
        }

        # Find chapters belonging to this section
        section_chapters = [c for c in chapters if c['parent_id'] == s_id]
        section_chapters.sort(key=lambda x: int(x.get('menu_order', '0')))

        for chapter in section_chapters:
            c_id = chapter['id']
            c_meta = riverlog_meta.get(c_id, {})
            chapter_info = {
                'id': c_id,
                'title': chapter['title'],
                'slug': chapter['slug'],
                'order': chapter.get('menu_order', '0'),
                'meta': {k: v for k, v in c_meta.items() if not k.startswith('_')},
                'pages': [],
            }

            # Find pages belonging to this chapter
            chapter_pages = [p for p in pages if p['parent_id'] == c_id]
            chapter_pages.sort(key=lambda x: int(x.get('menu_order', '0')))

            for page in chapter_pages:
                p_id = page['id']
                p_meta = riverlog_meta.get(p_id, {})
                content = page.get('content', '')
                clean_text = clean_html(content)

                page_info = {
                    'id': p_id,
                    'title': page['title'],
                    'slug': page['slug'],
                    'order': page.get('menu_order', '0'),
                    'content_chars': len(clean_text),
                    'raw_chars': len(content) if content else 0,
                    'meta': {k: v for k, v in p_meta.items() if not k.startswith('_')},
                }
                chapter_info['pages'].append(page_info)

            section_info['chapters'].append(chapter_info)

        structure.append(section_info)

        # Print hierarchy
        print(f"\n  SECTION: {section['title']} (ID:{s_id}, order:{section.get('menu_order','0')})")
        if s_meta:
            for k, v in sorted(s_meta.items()):
                if not k.startswith('_') and v:
                    val = v[:80] if isinstance(v, str) else v
                    print(f"    meta.{k} = {val}")

        for chapter in section_chapters:
            c_id = chapter['id']
            c_pages = [p for p in pages if p['parent_id'] == c_id]
            c_pages.sort(key=lambda x: int(x.get('menu_order', '0')))
            print(f"    CHAPTER: {chapter['title']} (ID:{c_id}, {len(c_pages)} pages)")

            for p in c_pages[:5]:
                content = p.get('content', '')
                clen = len(clean_html(content))
                print(f"      PAGE: {p['title']} ({clen} chars) [order:{p.get('menu_order','0')}]")
            if len(c_pages) > 5:
                print(f"      ... and {len(c_pages) - 5} more pages")

    # Also find orphan pages (not assigned to a chapter)
    assigned_pages = set()
    for chapter in chapters:
        for p in pages:
            if p['parent_id'] == chapter['id']:
                assigned_pages.add(p['id'])

    orphan_pages = [p for p in pages if p['id'] not in assigned_pages]
    if orphan_pages:
        print(f"\n  ORPHAN PAGES (not assigned to any chapter): {len(orphan_pages)}")
        for p in orphan_pages[:10]:
            content = p.get('content', '')
            clen = len(clean_html(content))
            print(f"    {p['title']} (ID:{p['id']}, parent:{p['parent_id']}, {clen} chars)")
        if len(orphan_pages) > 10:
            print(f"    ... and {len(orphan_pages) - 10} more")

    # Save the full structure as JSON
    structure_path = os.path.join(OUTPUT_DIR, 'riverlog-structure.json')
    with open(structure_path, 'w', encoding='utf-8') as f:
        json.dump(structure, f, indent=2)
    print(f"\nStructure saved to: {structure_path}")

    # Save all riverlog page content
    content_dir = os.path.join(OUTPUT_DIR, 'pages')
    os.makedirs(content_dir, exist_ok=True)

    saved = 0
    total_text = 0
    for page in pages:
        content = page.get('content', '')
        if not content:
            continue

        clean_text = clean_html(content)
        if len(clean_text) < 10:
            continue

        p_meta = riverlog_meta.get(page['id'], {})

        # Build filename from hierarchy
        parent = all_posts.get(page['parent_id'])
        grandparent = all_posts.get(parent['parent_id']) if parent else None

        parts = []
        if grandparent:
            parts.append(grandparent['slug'])
        if parent:
            parts.append(parent['slug'])
        parts.append(page['slug'] or f"page-{page['id']}")

        filename = '__'.join(parts)

        # Save HTML
        html_path = os.path.join(content_dir, f"{filename}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(f"<!-- ID: {page['id']} -->\n")
            f.write(f"<!-- Title: {page['title']} -->\n")
            f.write(f"<!-- Order: {page.get('menu_order', '0')} -->\n")
            for k, v in sorted(p_meta.items()):
                if not k.startswith('_') and v:
                    f.write(f"<!-- Meta {k}: {v[:200]} -->\n")
            f.write(content)

        # Save text
        txt_path = os.path.join(content_dir, f"{filename}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"TITLE: {page['title']}\n")
            f.write(f"ID: {page['id']}\n")
            f.write(f"ORDER: {page.get('menu_order', '0')}\n")
            for k, v in sorted(p_meta.items()):
                if not k.startswith('_') and v:
                    f.write(f"META {k}: {v[:200]}\n")
            f.write(f"{'='*60}\n\n")
            f.write(clean_text)

        saved += 1
        total_text += len(clean_text)

    print(f"\nSaved {saved} riverlog pages")
    print(f"Total text: {total_text:,} characters ({total_text/1000:.0f}K)")
    print(f"Content directory: {content_dir}")

    # Save images data
    images = posts_by_type['riverlog-image']
    image_data = []
    for img in images:
        i_meta = riverlog_meta.get(img['id'], {})
        image_data.append({
            'id': img['id'],
            'title': img['title'],
            'slug': img['slug'],
            'parent_id': img['parent_id'],
            'content': img.get('content', ''),
            'guid': img.get('guid', ''),
            'meta': {k: v for k, v in i_meta.items() if not k.startswith('_')},
        })

    images_path = os.path.join(OUTPUT_DIR, 'riverlog-images.json')
    with open(images_path, 'w', encoding='utf-8') as f:
        json.dump(image_data, f, indent=2)
    print(f"Image records: {len(image_data)}, saved to {images_path}")


if __name__ == '__main__':
    main()
