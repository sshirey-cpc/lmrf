"""Cleanup v2 — strip boilerplate text within paragraphs."""

import re
import json
import http.client
import time
import base64
import hmac as hmac_mod

SITE = "35.188.103.101"
API_KEY = "69cdd2c882a89443a06c4758:acd2dd504ed3e680d3a9d0514479e75a7b82a3a27d7549ab0695ae6753b3d6bc"

# Patterns to strip from within content (not just whole paragraphs)
BOILERPLATE = [
    # "Rivergator: Section Name MM NNN - NNN © YYYY John Ruskey"
    re.compile(r'Rivergator[\s:]+[^©]*©\s*\d{4}\s*John Ruskey\s*'),
    # "For the Rivergator : Lower Mississippi River Water Trail"
    re.compile(r'For the Rivergator\s*:?\s*(?:Lower Mississippi River Water Trail)?\s*'),
    # "The www.rivergator.org is a free public use website..."
    re.compile(r'(?:The\s+)?www\.rivergator\.org\s*(?:is a free public use website presented by the Lower Mississippi River Foundation\.?)?\s*'),
    # "Re-printing of text and photos..."
    re.compile(r'Re-?printing of text and photos by permission only with proper credits\.?\s*'),
    # Google Maps URLs
    re.compile(r'https?://mapsengine\.google\.com/\S+\s*'),
    # Other rivergator URLs
    re.compile(r'https?://(?:www\.)?rivergator\.org\S*\s*'),
    # "Rivergator: Paddler's Guide to..." headers
    re.compile(r"Rivergator[\s:]+Paddler'?s?\s*Guide to\s+[^©]*©\s*\d{4}\s*John Ruskey\s*"),
    # Standalone copyright line
    re.compile(r'©\s*\d{4}\s*John Ruskey\s*'),
    # "Intro:" prefix
    re.compile(r'^Intro:\s*', re.MULTILINE),
]


def make_token():
    key_id, secret = API_KEY.split(':')
    header = base64.urlsafe_b64encode(json.dumps({"alg":"HS256","typ":"JWT","kid":key_id}).encode()).rstrip(b'=').decode()
    now = int(time.time())
    payload = base64.urlsafe_b64encode(json.dumps({"iat":now,"exp":now+300,"aud":"/admin/"}).encode()).rstrip(b'=').decode()
    sig = hmac_mod.new(bytes.fromhex(secret), f"{header}.{payload}".encode(), 'sha256').digest()
    return f"{header}.{payload}.{base64.urlsafe_b64encode(sig).rstrip(b'=').decode()}"


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
    return resp.status, data


def clean_html(html):
    if not html:
        return html, False

    original = html
    for pattern in BOILERPLATE:
        html = pattern.sub('', html)

    # Clean up leftover whitespace in tags
    html = re.sub(r'<p>\s+', '<p>', html)
    html = re.sub(r'\s+</p>', '</p>', html)
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'^\s+', '', html)

    # Capitalize first letter if it's now lowercase
    m = re.match(r'^(<p>)([a-z])', html)
    if m:
        html = m.group(1) + m.group(2).upper() + html[m.end():]

    return html, html != original


def main():
    all_posts = []
    page = 1
    while True:
        result = api_get(f"/ghost/api/admin/posts/?limit=50&page={page}&formats=html")
        posts = result.get('posts', [])
        if not posts: break
        all_posts.extend(posts)
        page += 1

    print(f"Total posts: {len(all_posts)}")

    fixed = 0
    for post in all_posts:
        html = post.get('html', '')
        clean, changed = clean_html(html)

        if changed:
            status, resp = api_put(
                f"/ghost/api/admin/posts/{post['id']}/?source=html",
                {"posts": [{"html": clean, "updated_at": post['updated_at']}]}
            )
            if status == 200:
                fixed += 1
                if fixed <= 5:
                    print(f"  Fixed: {post['title'][:50]}")
                    print(f"    Before: {html[:100]}")
                    print(f"    After:  {clean[:100]}")
                elif fixed % 50 == 0:
                    print(f"  Fixed {fixed}...")
            else:
                print(f"  FAILED: {post['title'][:40]}")

    print(f"\nFixed {fixed} posts")


if __name__ == '__main__':
    main()
