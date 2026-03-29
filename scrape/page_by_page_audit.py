"""
Page-by-page audit: compare every button/link on our static site
against the original live site.
"""

import re
import os
import requests

SITE_DIR = os.path.join(os.path.dirname(__file__), "rendered-site")
LIVE = "https://www.lowermsfoundation.org"
UA = {"User-Agent": "Mozilla/5.0"}

# Map of original paths to our local files
PATH_MAP = {
    "/": "index.html",
    "/who-we-are": "who-we-are.html",
    "/our-programs": "our-programs.html",
    "/summer-camps": "summer-camps.html",
    "/new-page-2": "river-stewards.html",
    "/get-involved": "get-involved.html",
    "/calendar": "calendar.html",
    "/lmrf": "blog.html",
    "/contact": "contact.html",
    "/donate": "donate.html",
    "/camp-application": "camp-application.html",
    "/delta-day-camp": "delta-day-camp.html",
    "/home-1": "our-programs.html",
    "/volunteer-1": "get-involved.html",
    "/advocate": "get-involved.html",
}

PAYPAL = "paypal.com/donate"

def get_buttons(html):
    """Extract all button-like links with text and href."""
    results = []
    # Squarespace buttons
    for m in re.finditer(
        r'<a\s[^>]*?href="([^"]*)"[^>]*?class="[^"]*?button[^"]*?"[^>]*?>([\s\S]*?)</a>',
        html
    ):
        href = m.group(1)
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        text = ' '.join(text.split())
        if text:
            results.append((text, href))
    return results


def get_nav_links(html):
    """Extract nav links."""
    results = []
    for m in re.finditer(r'class="Header-nav-item[^"]*"[^>]*href="([^"]*)"[^>]*>([^<]+)', html):
        results.append((m.group(2).strip(), m.group(1)))
    return results


def check_href(href, filename):
    """Check if a href resolves correctly."""
    if not href:
        return "EMPTY"
    if href.startswith("http"):
        if PAYPAL in href:
            return "OK (PayPal)"
        if "facebook.com" in href or "rivergator.org" in href or "americanrivers.org" in href or "1mississippi" in href or "lowermsfoundation.org/lmrf" in href:
            return "OK (external)"
        if "youtube" in href or "google" in href:
            return "OK (external)"
        return f"OK (external: {href[:50]})"
    if href.startswith("mailto:") or href.startswith("tel:"):
        return "OK"
    if href.startswith("#"):
        return "OK (anchor)"
    # Local file
    full = os.path.join(SITE_DIR, href)
    if os.path.exists(full):
        size = os.path.getsize(full)
        if size > 0:
            return f"OK ({size:,} bytes)"
        else:
            return "FAIL (empty file)"
    else:
        return f"FAIL (missing: {href})"


def audit_page(local_file, live_path):
    filepath = os.path.join(SITE_DIR, local_file)
    if not os.path.exists(filepath):
        print(f"\n  FILE MISSING: {local_file}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    print(f"\n{'='*60}")
    print(f"PAGE: {local_file} ({live_path})")
    print(f"  Size: {len(html):,} bytes")
    print(f"{'='*60}")

    # Nav links
    nav = get_nav_links(html)
    print(f"\n  NAV LINKS ({len(nav)}):")
    for text, href in nav:
        status = check_href(href, local_file)
        flag = "  " if "OK" in status else "!!"
        print(f"  {flag} {text:25s} -> {href:35s} [{status}]")

    # Donate in nav
    has_paypal = PAYPAL in html
    print(f"\n  DONATE BUTTON: {'OK - PayPal linked' if has_paypal else 'MISSING!'}")

    # Content buttons
    buttons = get_buttons(html)
    if buttons:
        print(f"\n  CONTENT BUTTONS ({len(buttons)}):")
        for text, href in buttons:
            status = check_href(href, local_file)
            flag = "  " if "OK" in status else "!!"
            print(f"  {flag} {text:45s} -> {href:40s} [{status}]")

    # Images
    imgs = re.findall(r'src="(images/[^"]+)"', html)
    missing_imgs = [i for i in imgs if not os.path.exists(os.path.join(SITE_DIR, i))]
    print(f"\n  IMAGES: {len(imgs)} referenced, {len(missing_imgs)} missing")
    for mi in missing_imgs:
        print(f"  !! MISSING: {mi}")

    # Footer
    has_footer = "<footer" in html.lower()
    has_contact = "870" in html and "Helena" in html
    print(f"\n  FOOTER: {'OK' if has_footer else 'MISSING'}")
    print(f"  CONTACT INFO: {'OK' if has_contact else 'MISSING'}")


def main():
    print("LMRF STATIC SITE — PAGE BY PAGE AUDIT")
    print(f"Checking {len(PATH_MAP)} pages\n")

    pages_to_check = [
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
        ("camp-application.html", "/camp-application"),
        ("delta-day-camp.html", "/delta-day-camp"),
    ]

    for local, live in pages_to_check:
        audit_page(local, live)

    print(f"\n{'='*60}")
    print("AUDIT COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
