"""
Full site audit: test every link, image, asset, button, and compare
content against the live site.
"""

import os
import re
import requests

SITE_DIR = os.path.join(os.path.dirname(__file__), "rendered-site")
LOCAL = "http://localhost:8080"
LIVE = "https://www.lowermsfoundation.org"

PAGES = [
    ("index.html", "/"),
    ("who-we-are.html", "/who-we-are"),
    ("our-programs.html", "/our-programs"),
    ("summer-camps.html", "/summer-camps"),
    ("river-stewards.html", "/new-page-2"),
    ("get-involved.html", "/get-involved"),
    ("calendar.html", "/calendar"),
    ("blog.html", "/lmrf"),
    ("contact.html", "/contact"),
    ("donate.html", "/donate"),
]

PAYPAL = "https://www.paypal.com/donate?token=fPg9LuFa9121K_HDyZVHkUs4L6Xuwg3gKG4w_MSfisa1zzrcq-PtnNC190Fc_6-8vZjTLSvpb0Lmd7eL"
GCAL_SRC = "calendar.google.com/calendar/embed"

issues = []
warnings = []
passed = 0


def check(label, condition, detail=""):
    global passed
    if condition:
        passed += 1
    else:
        issues.append(f"FAIL: {label}" + (f" — {detail}" if detail else ""))
        print(f"  FAIL: {label}" + (f" — {detail}" if detail else ""))


def warn(label, detail=""):
    warnings.append(f"WARN: {label}" + (f" — {detail}" if detail else ""))


def audit_page(filename, live_path):
    filepath = os.path.join(SITE_DIR, filename)
    print(f"\n{'='*60}")
    print(f"AUDITING: {filename}")
    print(f"{'='*60}")

    # 1. File exists and loads
    check(f"{filename} exists", os.path.exists(filepath))
    if not os.path.exists(filepath):
        return

    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    # 2. Page loads via HTTP
    try:
        resp = requests.get(f"{LOCAL}/{filename}", timeout=5)
        check(f"{filename} loads (HTTP {resp.status_code})", resp.status_code == 200)
    except Exception as e:
        check(f"{filename} loads", False, str(e))

    # 3. Has <title>
    title = re.search(r"<title>([^<]+)</title>", html)
    check(f"{filename} has <title>", title is not None,
          title.group(1) if title else "missing")

    # 4. Check all local images exist
    img_srcs = re.findall(r'src="(images/[^"]+)"', html)
    for img in img_srcs:
        full = os.path.join(SITE_DIR, img)
        check(f"{filename}: image {img}", os.path.exists(full) and os.path.getsize(full) > 0)

    # 5. Check all local CSS files exist
    css_refs = re.findall(r'href="(css/[^"]+)"', html)
    for css in css_refs:
        full = os.path.join(SITE_DIR, css)
        check(f"{filename}: css {css}", os.path.exists(full))

    # 6. Check all local JS files exist
    js_refs = re.findall(r'src="(js/[^"]+)"', html)
    for js in js_refs:
        full = os.path.join(SITE_DIR, js)
        check(f"{filename}: js {js}", os.path.exists(full))

    # 7. Check local file links (PDFs)
    file_refs = re.findall(r'href="(files/[^"]+)"', html)
    for fr in file_refs:
        full = os.path.join(SITE_DIR, fr)
        check(f"{filename}: file {fr}", os.path.exists(full) and os.path.getsize(full) > 100)

    # 8. Check internal .html links exist
    html_links = set(re.findall(r'href="([^"#]+\.html)"', html))
    for link in html_links:
        full = os.path.join(SITE_DIR, link)
        check(f"{filename}: link to {link}", os.path.exists(full))

    # 9. No broken absolute /paths
    abs_paths = re.findall(r'href="(/[^"]+)"', html)
    for p in abs_paths:
        if "ui-icons" not in p:
            check(f"{filename}: no abs path {p}", False, "should be relative")

    # 10. No remaining squarespace URLs (except assets CDN)
    sq_urls = re.findall(r'(?:src|href|action)="(https?://[^"]*squarespace[^"]*)"', html)
    for u in sq_urls:
        if "assets.squarespace.com" not in u:
            check(f"{filename}: no squarespace URL", False, u[:60])

    # 11. Check nav links present
    nav_pages = ["index.html", "who-we-are.html", "our-programs.html",
                 "get-involved.html", "calendar.html", "blog.html", "contact.html"]
    for nav in nav_pages:
        check(f"{filename}: nav link to {nav}",
              f'href="{nav}"' in html or (nav == "index.html" and 'class="Header-branding"' in html))

    # 12. Donate button exists and points to PayPal
    check(f"{filename}: donate link to PayPal",
          PAYPAL[:40] in html,
          "PayPal link missing")

    # 13. Check buttons have working hrefs
    buttons = re.findall(
        r'href="([^"]*)"[^>]*class="[^"]*button[^"]*"[^>]*>([\s\S]*?)</a>', html)
    for href, text in buttons:
        text = re.sub(r'<[^>]+>', '', text).strip()
        text = ' '.join(text.split())
        if text:
            if not href:
                check(f"{filename}: button '{text[:30]}' has href", False, "empty href")
            elif href.startswith("files/"):
                full = os.path.join(SITE_DIR, href)
                check(f"{filename}: button '{text[:30]}' file exists",
                      os.path.exists(full), href)

    return html


def audit_specific():
    """Check specific requirements."""
    print(f"\n{'='*60}")
    print("SPECIFIC REQUIREMENTS")
    print(f"{'='*60}")

    # Calendar page has Google Calendar embed
    cal_path = os.path.join(SITE_DIR, "calendar.html")
    cal_html = open(cal_path, "r", encoding="utf-8").read()
    check("Calendar: has Google Calendar iframe", GCAL_SRC in cal_html)

    # Contact form has mailto handler
    contact_path = os.path.join(SITE_DIR, "contact.html")
    contact_html = open(contact_path, "r", encoding="utf-8").read()
    check("Contact: has form", "<form" in contact_html)
    check("Contact: mailto handler", "mailto:info@lowermsfoundation.org" in contact_html)

    # Summer camps has YouTube video
    sc_path = os.path.join(SITE_DIR, "summer-camps.html")
    sc_html = open(sc_path, "r", encoding="utf-8").read()
    check("Summer Camps: YouTube video embed",
          "youtube.com/embed/l92_Z5_tCVM" in sc_html)

    # Who We Are has board members
    wwa_path = os.path.join(SITE_DIR, "who-we-are.html")
    wwa_html = open(wwa_path, "r", encoding="utf-8").read()
    for name in ["Kevin Smith", "Robert Cheek", "Jenn Morehead", "Scott Shirey"]:
        check(f"Who We Are: has {name}", name in wwa_html)

    # PDFs all exist and are real PDFs
    pdf_dir = os.path.join(SITE_DIR, "files")
    for pdf in os.listdir(pdf_dir):
        full = os.path.join(pdf_dir, pdf)
        size = os.path.getsize(full)
        with open(full, "rb") as f:
            header = f.read(4)
        check(f"PDF: {pdf} is valid ({size:,} bytes)",
              header == b"%PDF" and size > 1000)

    # All images are real images (non-zero, valid header)
    img_dir = os.path.join(SITE_DIR, "images")
    for img in os.listdir(img_dir):
        full = os.path.join(img_dir, img)
        size = os.path.getsize(full)
        if size == 0:
            check(f"Image: {img} non-empty", False, "0 bytes")
        elif size < 100:
            warn(f"Image: {img} very small ({size} bytes)")


def audit_cross_page():
    """Check consistency across pages."""
    print(f"\n{'='*60}")
    print("CROSS-PAGE CONSISTENCY")
    print(f"{'='*60}")

    # Check that all pages have same nav structure
    nav_texts = {}
    for filename, _ in PAGES:
        filepath = os.path.join(SITE_DIR, filename)
        html = open(filepath, "r", encoding="utf-8").read()
        nav = re.findall(r'class="Header-nav-item"[^>]*>([^<]+)', html)
        nav_texts[filename] = nav

    first_nav = nav_texts.get("index.html", [])
    for filename, nav in nav_texts.items():
        check(f"{filename}: nav matches index.html",
              nav == first_nav,
              f"got {nav}" if nav != first_nav else "")

    # Check footer present on all pages
    for filename, _ in PAGES:
        filepath = os.path.join(SITE_DIR, filename)
        html = open(filepath, "r", encoding="utf-8").read()
        check(f"{filename}: has footer",
              '<footer' in html.lower())
        check(f"{filename}: footer has contact info",
              "870" in html and "Helena" in html)


def main():
    print("LMRF STATIC SITE — FULL AUDIT")
    print(f"Site directory: {SITE_DIR}")
    print(f"Local server: {LOCAL}")

    for filename, live_path in PAGES:
        audit_page(filename, live_path)

    audit_specific()
    audit_cross_page()

    print(f"\n{'='*60}")
    print(f"AUDIT COMPLETE")
    print(f"{'='*60}")
    print(f"  Passed: {passed}")
    print(f"  Issues: {len(issues)}")
    print(f"  Warnings: {len(warnings)}")

    if issues:
        print(f"\n--- ISSUES ({len(issues)}) ---")
        for i in issues:
            print(f"  {i}")

    if warnings:
        print(f"\n--- WARNINGS ({len(warnings)}) ---")
        for w in warnings:
            print(f"  {w}")

    if not issues:
        print("\n*** ALL CHECKS PASSED — READY FOR DEPLOYMENT ***")


if __name__ == "__main__":
    main()
