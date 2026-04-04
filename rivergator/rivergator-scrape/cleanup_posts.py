"""
Clean up all Ghost posts:
1. Set correct publish dates based on when John wrote each section
2. Strip boilerplate copyright headers from post content
3. Fix titles that have trailing descriptions
"""

import re
import json
import hashlib
import http.client
import time

SITE = "35.188.103.101"
API_KEY = "69cdd2c882a89443a06c4758:acd2dd504ed3e680d3a9d0514479e75a7b82a3a27d7549ab0695ae6753b3d6bc"
CONTENT_KEY = "e7387ee5394ff913c8b7d38c51"

# Original publish dates per section (from copyright notices in content)
SECTION_DATES = {
    "stlouis-to-caruthersville": "2014-06-01T12:00:00.000Z",
    "caruthersville-to-memphis": "2013-06-01T12:00:00.000Z",
    "memphis-to-helena": "2013-06-01T12:00:00.000Z",
    "helena-to-greenville": "2013-06-01T12:00:00.000Z",
    "greenville-to-vicksburg": "2013-06-01T12:00:00.000Z",
    "vicksburg-to-baton-rouge": "2014-06-01T12:00:00.000Z",
    "atchafalaya-river": "2015-06-01T12:00:00.000Z",
    "baton-rouge-to-venice": "2015-06-01T12:00:00.000Z",
    "birdsfoot-delta": "2015-06-01T12:00:00.000Z",
}

# Boilerplate patterns to strip from the beginning of content
BOILERPLATE_PATTERNS = [
    # "Rivergator: Section Name MM NNN - NNN © YYYY John Ruskey For the Rivergator..."
    re.compile(
        r'^<p>\s*Rivergator:?\s*.*?©\s*\d{4}\s*John Ruskey\s*'
        r'For the Rivergator\s*:?\s*(?:Lower Mississippi River Water Trail)?\s*'
        r'(?:The)?\s*(?:www\.rivergator\.org)?\s*'
        r'(?:is a free public use website presented by the Lower Mississippi River Foundation\.?)?\s*'
        r'(?:Re-printing of text and photos by permission only with proper credits\.?)?\s*'
        r'</p>',
        re.IGNORECASE | re.DOTALL
    ),
    # Simpler version: anything starting with "Rivergator:" up to the first real content
    re.compile(
        r'^<p>\s*Rivergator[\s:]+.*?(?:permission only with proper credits\.?|Re-printing.*?credits\.?)\s*</p>',
        re.IGNORECASE | re.DOTALL
    ),
    # Just the copyright line
    re.compile(
        r'^<p>\s*©\s*\d{4}\s*John Ruskey.*?</p>',
        re.IGNORECASE | re.DOTALL
    ),
    # "Rivergator: Section..." as first paragraph
    re.compile(
        r'^<p>\s*Rivergator[\s:]+[^<]{10,200}</p>\s*',
        re.IGNORECASE
    ),
]

# Additional patterns to strip anywhere in content
STRIP_PATTERNS = [
    # Google Maps URLs
    re.compile(r'https?://mapsengine\.google\.com/\S+'),
    # Old rivergator.org URLs
    re.compile(r'https?://www\.rivergator\.org\S*'),
    # "For the Rivergator: Lower Mississippi River Water Trail"
    re.compile(r'For the Rivergator\s*:\s*Lower Mississippi River Water Trail'),
    # "The www.rivergator.org is a free public use website..."
    re.compile(r'The\s+www\.rivergator\.org\s+is a free public use website.*?proper credits\.?'),
    # Re-printing notice
    re.compile(r'Re-printing of text and photos by permission only with proper credits\.?'),
]


def make_token():
    import hmac as hmac_mod
    key_id, secret = API_KEY.split(':')
    import base64
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT", "kid": key_id}).encode()).rstrip(b'=').decode()
    now = int(time.time())
    payload = base64.urlsafe_b64encode(json.dumps({"iat": now, "exp": now + 300, "aud": "/admin/"}).encode()).rstrip(b'=').decode()
    sig_input = f"{header}.{payload}"
    sig = hmac_mod.new(bytes.fromhex(secret), sig_input.encode(), 'sha256').digest()
    signature = base64.urlsafe_b64encode(sig).rstrip(b'=').decode()
    return f"{header}.{payload}.{signature}"


def api_get(path):
    conn = http.client.HTTPConnection(SITE)
    conn.request("GET", path, headers={"Authorization": f"Ghost {make_token()}"})
    resp = conn.getresponse()
    data = resp.read().decode()
    conn.close()
    return json.loads(data)


def api_put(path, body):
    body_bytes = json.dumps(body).encode()
    conn = http.client.HTTPConnection(SITE)
    conn.request("PUT", path, body=body_bytes, headers={
        "Authorization": f"Ghost {make_token()}",
        "Content-Type": "application/json",
        "Content-Length": str(len(body_bytes)),
    })
    resp = conn.getresponse()
    data = resp.read().decode()
    conn.close()
    return resp.status, json.loads(data) if data else {}


def clean_html(html):
    """Remove boilerplate from HTML content."""
    if not html:
        return html

    original = html

    # Strip boilerplate from the beginning
    for pattern in BOILERPLATE_PATTERNS:
        html = pattern.sub('', html, count=1).strip()

    # Strip patterns anywhere
    for pattern in STRIP_PATTERNS:
        html = pattern.sub('', html)

    # Clean up empty paragraphs left behind
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'^\s+', '', html)

    changed = html != original
    return html, changed


def clean_title(title):
    """Clean up post titles."""
    original = title

    # Remove trailing descriptions after the landmark name
    # "Mile 736.0 LBD — Memphis, Tennessee, Mud Island Harbor https://..."
    title = re.sub(r'\s*https?://\S+', '', title)

    # Remove "Mark Twain said that..." type suffixes
    # Keep just "Mile NNN BANK — Landmark Name"
    m = re.match(r'(Mile \d+(?:\.\d+)?\s+(?:LBD|RBD)?\s*—\s*)(.+)', title)
    if m:
        prefix = m.group(1)
        name = m.group(2)
        # Trim name to just the landmark (stop at lowercase continuation)
        words = name.split()
        clean_words = []
        stop = {'the','a','an','this','these','it','its','is','are','was','were',
                'in','on','at','from','after','before','once','every','as',
                'give','watch','narrow','just','several','while','you','one',
                'during','here','there','not','but','or','if','when','don','can'}
        for i, w in enumerate(words):
            if w.lower() in stop:
                if i == 0 and w.lower() == 'the': clean_words.append(w); continue
                if i < 4 and w.lower() in ('of','the','and','at','to'): clean_words.append(w); continue
                break
            if i > 0 and clean_words and clean_words[-1].endswith('.'): break
            if i >= 7: break
            clean_words.append(w)
        name = ' '.join(clean_words).strip().rstrip('.,;:')

        # Deduplicate
        ws = name.split()
        if len(ws) >= 6:
            h = len(ws)//2
            if ws[:h] == ws[h:2*h]: name = ' '.join(ws[:h])

        title = prefix + name

    # Intro/appendix titles
    title = re.sub(r'^Memphis to Helena: Introduction$', 'Memphis to Helena — Introduction', title)

    changed = title != original
    return title, changed


def get_section_from_tags(tags):
    """Determine which section a post belongs to based on its tags."""
    for tag in tags:
        slug = tag.get('slug', '')
        for section_slug in SECTION_DATES:
            if slug == section_slug:
                return section_slug
    return None


def main():
    # Get all posts
    all_posts = []
    page = 1
    while True:
        result = api_get(f"/ghost/api/admin/posts/?limit=50&page={page}&formats=html&include=tags")
        posts = result.get('posts', [])
        if not posts:
            break
        all_posts.extend(posts)
        total = result.get('meta', {}).get('pagination', {}).get('total', 0)
        print(f"  Fetched page {page} ({len(all_posts)}/{total} posts)")
        page += 1

    print(f"\nTotal posts: {len(all_posts)}")

    updated = 0
    date_fixes = 0
    content_fixes = 0
    title_fixes = 0

    for post in all_posts:
        changes = {}

        # 1. Fix date
        section = get_section_from_tags(post.get('tags', []))
        if section and section in SECTION_DATES:
            correct_date = SECTION_DATES[section]
            if post.get('published_at', '')[:10] != correct_date[:10]:
                changes['published_at'] = correct_date
                changes['created_at'] = correct_date
                date_fixes += 1

        # 2. Clean content
        html = post.get('html', '')
        if html:
            clean, changed = clean_html(html)
            if changed:
                changes['html'] = clean
                content_fixes += 1

        # 3. Clean title
        title = post.get('title', '')
        clean_t, changed_t = clean_title(title)
        if changed_t:
            changes['title'] = clean_t
            title_fixes += 1

        # Apply changes
        if changes:
            changes['updated_at'] = post['updated_at']  # Required for Ghost API
            status, resp = api_put(
                f"/ghost/api/admin/posts/{post['id']}/?source=html",
                {"posts": [changes]}
            )
            if status == 200:
                updated += 1
                if updated % 25 == 0:
                    print(f"  Updated {updated} posts...")
            else:
                err = resp.get('errors', [{}])[0].get('message', 'unknown')
                print(f"  FAILED: {post['title'][:40]} — {err}")

    print(f"\n{'='*50}")
    print(f"Updated: {updated} posts")
    print(f"  Date fixes: {date_fixes}")
    print(f"  Content fixes: {content_fixes}")
    print(f"  Title fixes: {title_fixes}")


if __name__ == '__main__':
    main()
