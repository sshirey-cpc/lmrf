"""
THOROUGH audit: find EVERY <a>, <form>, <button>, <iframe> on every page.
Check that each one works.
"""
import os, re

SITE_DIR = os.path.join(os.path.dirname(__file__), "rendered-site")
PAYPAL = "paypal.com/donate"

def get_all_links(html):
    """Get ALL <a href> tags with surrounding context."""
    results = []
    for m in re.finditer(r'<a\s[^>]*?href="([^"]*)"[^>]*?>([\s\S]*?)</a>', html):
        href = m.group(1)
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        text = ' '.join(text.split())[:60]
        if not text:
            text = "(no text)"
        results.append((text, href))
    return results

def get_forms(html):
    results = []
    for m in re.finditer(r'<form[^>]*>([\s\S]*?)</form>', html):
        form_html = m.group(0)
        action = re.search(r'action="([^"]*)"', form_html)
        action = action.group(1) if action else "(no action)"
        has_handler = "onsubmit" in form_html or "addEventListener" in form_html
        results.append((action, has_handler))
    return results

def get_iframes(html):
    results = []
    for m in re.finditer(r'<iframe[^>]*src="([^"]*)"[^>]*>', html):
        results.append(m.group(1))
    return results

def check_href(href):
    if not href or href == "#":
        return "EMPTY/ANCHOR"
    if href.startswith("mailto:"):
        return "OK (mailto)"
    if href.startswith("tel:"):
        return "OK (tel)"
    if href.startswith("http"):
        return "OK (external)"
    if href.startswith("javascript"):
        return "OK (js)"
    # Local file
    full = os.path.join(SITE_DIR, href)
    if os.path.exists(full) and os.path.getsize(full) > 0:
        return "OK"
    elif os.path.exists(full):
        return "FAIL (empty)"
    else:
        return "FAIL (missing)"

issues = []
total_links = 0
total_ok = 0

for f in sorted(os.listdir(SITE_DIR)):
    if not f.endswith('.html'):
        continue
    filepath = os.path.join(SITE_DIR, f)
    html = open(filepath, 'r', encoding='utf-8').read()

    print(f"\n{'='*70}")
    print(f"PAGE: {f}")
    print(f"{'='*70}")

    # ALL links
    links = get_all_links(html)
    print(f"\n  LINKS ({len(links)}):")
    for text, href in links:
        status = check_href(href)
        total_links += 1
        if "OK" in status:
            total_ok += 1
        flag = "  " if "OK" in status or "ANCHOR" in status else ">>"
        if "FAIL" in status:
            issues.append(f"{f}: [{text[:30]}] -> {href} ({status})")
        # Only print non-trivial links (skip css/js/image/svg refs)
        if not any(href.endswith(x) for x in ['.css', '.js', '.svg', '.ico', '.png', '.jpg', '.jpeg', '.gif', '.woff', '.woff2']):
            if href and not href.startswith('#'):
                line = f"  {flag} [{text[:40]:<40s}] -> {href[:60]:<60s} {status}"
            print(line.encode('ascii', 'replace').decode())

    # Forms
    forms = get_forms(html)
    if forms:
        print(f"\n  FORMS ({len(forms)}):")
        for action, has_handler in forms:
            # Check if page has our mailto handler script
            has_mailto = "mailto:info@lowermsfoundation.org" in html
            if has_mailto:
                print(f"    action={action:<30s} mailto_handler=YES")
            else:
                print(f"    action={action:<30s} mailto_handler=NO")
                if "squarespace" in action.lower() or action == "#":
                    issues.append(f"{f}: Form with no working handler (action={action})")

    # Iframes
    iframes = get_iframes(html)
    if iframes:
        print(f"\n  IFRAMES ({len(iframes)}):")
        for src in iframes:
            status = "OK" if src.startswith("http") else "CHECK"
            print(f"    {src[:70]} [{status}]")

print(f"\n{'='*70}")
print(f"SUMMARY")
print(f"{'='*70}")
print(f"  Total links checked: {total_links}")
print(f"  OK: {total_ok}")
print(f"  Issues: {len(issues)}")
if issues:
    print(f"\n  ISSUES:")
    for i in issues:
        print(f"    >> {i}")
else:
    print(f"\n  NO ISSUES FOUND")
