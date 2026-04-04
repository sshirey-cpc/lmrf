"""
Extract all pages from the WordPress database SQL dump.
Parses INSERT INTO wp_posts statements and extracts page content.
"""

import re
import json
import os

SQL_PATH = os.path.join(os.path.dirname(__file__), "..", "wpress-extracted", "database.sql")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "db-extracted-pages")


def parse_sql_string(s, start=0):
    """Parse a SQL quoted string starting at position start (which should be a quote char).
    Handles escaped quotes (\') and returns (parsed_string, end_position)."""
    if s[start] != "'":
        raise ValueError(f"Expected quote at position {start}, got {s[start]}")

    result = []
    i = start + 1
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            # Escaped character
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
    """Parse a single INSERT INTO wp_posts VALUES (...) line.
    Returns a dict with the key fields or None if parsing fails."""

    # Find the VALUES part
    idx = line.find('VALUES (')
    if idx == -1:
        return None

    s = line[idx + 8:]  # Skip 'VALUES ('

    fields = []
    i = 0

    try:
        while i < len(s) and len(fields) < 23:  # wp_posts has ~23 columns
            # Skip whitespace
            while i < len(s) and s[i] in ' \t':
                i += 1

            if i >= len(s):
                break

            if s[i] == "'":
                # String field
                val, i = parse_sql_string(s, i)
                fields.append(val)
            elif s[i] in '0123456789-':
                # Numeric field
                j = i
                while j < len(s) and s[j] not in ',);':
                    j += 1
                fields.append(s[i:j])
                i = j
            elif s[i:i+4] == 'NULL':
                fields.append(None)
                i += 4
            else:
                # Unknown, skip to next comma
                j = i
                while j < len(s) and s[j] not in ',);':
                    j += 1
                fields.append(s[i:j])
                i = j

            # Skip comma or closing paren
            if i < len(s) and s[i] == ',':
                i += 1
            elif i < len(s) and s[i] in ');':
                break
    except (IndexError, ValueError):
        return None

    if len(fields) < 21:
        return None

    # WordPress wp_posts columns:
    # 0: ID, 1: post_author, 2: post_date, 3: post_date_gmt,
    # 4: post_content, 5: post_title, 6: post_excerpt,
    # 7: post_status, 8: comment_status, 9: ping_status,
    # 10: post_password, 11: post_name (slug), 12: to_ping,
    # 13: pinged, 14: post_modified, 15: post_modified_gmt,
    # 16: post_content_filtered, 17: post_parent, 18: guid,
    # 19: menu_order, 20: post_type, 21: post_mime_type, 22: comment_count

    return {
        'id': fields[0],
        'date': fields[2],
        'content': fields[4],
        'title': fields[5],
        'excerpt': fields[6],
        'status': fields[7],
        'slug': fields[11],
        'parent_id': fields[17],
        'post_type': fields[20],
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pages = []
    all_types = {}

    print(f"Reading SQL dump: {SQL_PATH}")
    print(f"Output directory: {OUTPUT_DIR}")

    with open(SQL_PATH, 'r', encoding='utf-8', errors='replace') as f:
        line_num = 0
        for line in f:
            line_num += 1
            if not line.startswith('INSERT INTO `SERVMASK_PREFIX_posts`'):
                continue

            row = parse_insert_row(line)
            if row is None:
                continue

            post_type = row['post_type']
            all_types[post_type] = all_types.get(post_type, 0) + 1

            if post_type == 'page':
                pages.append(row)

    print(f"\nPost types found:")
    for pt, count in sorted(all_types.items(), key=lambda x: -x[1]):
        print(f"  {pt}: {count}")

    print(f"\nTotal pages: {len(pages)}")

    # Build parent lookup
    id_to_page = {p['id']: p for p in pages}

    # Sort by parent then slug
    pages.sort(key=lambda p: (p['parent_id'], p['slug']))

    # Save each page
    saved = 0
    for p in pages:
        content = p['content'] or ''
        title = p['title'] or ''
        slug = p['slug'] or f"page-{p['id']}"
        status = p['status']
        parent_id = p['parent_id']

        # Build path from parent chain
        path_parts = [slug]
        current_parent = parent_id
        depth = 0
        while current_parent and current_parent != '0' and depth < 5:
            parent = id_to_page.get(current_parent)
            if parent:
                path_parts.insert(0, parent['slug'] or f"page-{parent['id']}")
                current_parent = parent['parent_id']
            else:
                break
            depth += 1

        full_path = '/'.join(path_parts)

        # Strip Fusion Builder shortcodes for clean text version
        clean = re.sub(r'\[/?fusion_[^\]]*\]', '', content)
        clean = re.sub(r'<[^>]+>', ' ', clean)
        clean = re.sub(r'&amp;', '&', clean)
        clean = re.sub(r'&lt;', '<', clean)
        clean = re.sub(r'&gt;', '>', clean)
        clean = re.sub(r'&#8217;', "'", clean)
        clean = re.sub(r'&#8211;', '-', clean)
        clean = re.sub(r'&#8220;|&#8221;', '"', clean)
        clean = re.sub(r'&nbsp;', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()

        content_len = len(clean)

        marker = "***" if content_len > 1000 else ""
        print(f"  [{p['id']:>5}] {status:<8} /{full_path:<60} ({content_len:>6} chars) {title} {marker}")

        if content_len > 100:  # Only save pages with real content
            # Save raw HTML content
            safe_slug = full_path.replace('/', '__')
            html_path = os.path.join(OUTPUT_DIR, f"{safe_slug}.html")
            with open(html_path, 'w', encoding='utf-8') as out:
                out.write(f"<!-- ID: {p['id']} -->\n")
                out.write(f"<!-- Title: {title} -->\n")
                out.write(f"<!-- Slug: {slug} -->\n")
                out.write(f"<!-- Path: /{full_path} -->\n")
                out.write(f"<!-- Status: {status} -->\n")
                out.write(f"<!-- Parent ID: {parent_id} -->\n")
                out.write(f"<!-- Date: {p['date']} -->\n")
                out.write(content)

            # Save clean text
            txt_path = os.path.join(OUTPUT_DIR, f"{safe_slug}.txt")
            with open(txt_path, 'w', encoding='utf-8') as out:
                out.write(f"TITLE: {title}\n")
                out.write(f"PATH: /{full_path}\n")
                out.write(f"ID: {p['id']}\n")
                out.write(f"STATUS: {status}\n")
                out.write(f"DATE: {p['date']}\n")
                out.write(f"{'='*60}\n\n")
                out.write(clean)

            saved += 1

    # Save page inventory as JSON
    inventory = []
    for p in pages:
        content = p['content'] or ''
        clean = re.sub(r'\[/?fusion_[^\]]*\]', '', content)
        clean = re.sub(r'<[^>]+>', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()

        # Build path
        path_parts = [p['slug'] or f"page-{p['id']}"]
        current_parent = p['parent_id']
        depth = 0
        while current_parent and current_parent != '0' and depth < 5:
            parent = id_to_page.get(current_parent)
            if parent:
                path_parts.insert(0, parent['slug'] or f"page-{parent['id']}")
                current_parent = parent['parent_id']
            else:
                break
            depth += 1

        inventory.append({
            'id': p['id'],
            'title': p['title'],
            'slug': p['slug'],
            'path': '/' + '/'.join(path_parts),
            'status': p['status'],
            'parent_id': p['parent_id'],
            'content_chars': len(clean),
            'raw_chars': len(content),
        })

    inv_path = os.path.join(OUTPUT_DIR, 'page-inventory.json')
    with open(inv_path, 'w', encoding='utf-8') as out:
        json.dump(inventory, out, indent=2)

    print(f"\nSaved {saved} pages with content")
    print(f"Inventory: {inv_path}")


if __name__ == '__main__':
    main()
