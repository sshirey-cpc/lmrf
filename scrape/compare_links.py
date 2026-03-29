"""
Side-by-side comparison: every link on our static site vs the original.
Fetches each page from the live site and compares all hrefs.
"""

import re
import os
import requests

SITE_DIR = os.path.join(os.path.dirname(__file__), "rendered-site")
LIVE = "https://www.lowermsfoundation.org"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

PAGES = [
    ("index.html", "/"),
    ("who-we-are.html", "/who-we-are"),
    ("our-programs.html", "/our-programs"),
    ("summer-camps.html", "/summer-camps"),
    ("river-stewards.html", "/new-page-2"),
    ("get-involved.html", "/get-involved"),
    ("blog.html", "/lmrf"),
    ("donate.html", "/donate"),
]

# How original paths map to our local files
LOCAL_MAP = {
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

PAYPAL = "https://www.paypal.com/donate?token=fPg9LuFa9121K_HDyZVHkUs4L6Xuwg3gKG4w_MSfisa1zzrcq-PtnNC190Fc_6-8vZjTLSvpb0Lmd7eL"


def extract_content_links(html):
    """Extract button/content links (not nav/footer boilerplate)."""
    results = []
    # Find all <a> tags with button classes
    for m in re.finditer(
        r'<a\s[^>]*?href="([^"]*)"[^>]*?class="[^"]*?button[^"]*?"[^>]*?>([\s\S]*?)</a>',
        html
    ):
        href = m.group(1).strip()
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        text = ' '.join(text.split())
        if text:
            results.append((text, href))
    return results


def normalize_href(href):
    """Normalize an href for comparison."""
    if not href:
        return "(empty)"
    # Strip trailing slashes
    href = href.rstrip("/")
    # Remove query params for comparison
    if "?" in href and "paypal" not in href:
        href = href.split("?")[0]
    return href


def expected_local(orig_href):
    """What should the local version of an original href be?"""
    if not orig_href or orig_href == "#":
        return orig_href

    # External links should stay the same
    if orig_href.startswith("http") and "lowermsfoundation.org" not in orig_href:
        return orig_href

    # Donate page should go to PayPal
    if orig_href.rstrip("/") in ("/donate", "https://www.lowermsfoundation.org/donate"):
        return PAYPAL

    # Strip the domain
    path = orig_href
    if "lowermsfoundation.org" in path:
        path = "/" + path.split("lowermsfoundation.org/", 1)[-1]
    path = path.rstrip("/")

    # PDF downloads
    if path.startswith("/s/"):
        return "files/" + path[3:]

    # Map to local file
    if path in LOCAL_MAP:
        return LOCAL_MAP[path]

    # Blog posts -> live site
    if path.startswith("/lmrf/"):
        return LIVE + path

    return f"(unmapped: {path})"


def compare_page(local_file, live_path):
    print(f"\n{'='*70}")
    print(f"COMPARING: {local_file} vs {LIVE}{live_path}")
    print(f"{'='*70}")

    # Load local
    local_path = os.path.join(SITE_DIR, local_file)
    with open(local_path, "r", encoding="utf-8") as f:
        local_html = f.read()

    # Fetch live
    try:
        resp = requests.get(f"{LIVE}{live_path}", headers=UA, timeout=15)
        live_html = resp.text
    except Exception as e:
        print(f"  ERROR fetching live page: {e}")
        return

    # Extract buttons from both
    local_buttons = extract_content_links(local_html)
    live_buttons = extract_content_links(live_html)

    print(f"\n  Live site buttons: {len(live_buttons)}")
    print(f"  Our buttons:       {len(local_buttons)}")

    # Compare side by side
    max_len = max(len(live_buttons), len(local_buttons))

    if max_len == 0:
        print("  (no content buttons on this page)")
        return

    print(f"\n  {'#':>3} {'BUTTON TEXT':<45} {'ORIGINAL HREF':<45} {'OUR HREF':<45} {'STATUS'}")
    print(f"  {'---':>3} {'-'*45} {'-'*45} {'-'*45} {'-'*10}")

    issues = 0
    for i in range(max_len):
        live_text = live_buttons[i][0] if i < len(live_buttons) else "(missing on live)"
        live_href = live_buttons[i][1] if i < len(live_buttons) else ""
        local_text = local_buttons[i][0] if i < len(local_buttons) else "(missing locally)"
        local_href = local_buttons[i][1] if i < len(local_buttons) else ""

        # What should our href be?
        expected = expected_local(live_href)
        norm_local = normalize_href(local_href)
        norm_expected = normalize_href(expected)

        # Check match
        if norm_local == norm_expected:
            status = "OK"
        elif local_href and os.path.exists(os.path.join(SITE_DIR, local_href)):
            status = "OK (file)"
        elif local_href.startswith("http"):
            status = "OK (ext)"
        else:
            status = "MISMATCH"
            issues += 1

        flag = "  " if status.startswith("OK") else ">>"

        print(f"{flag}{i+1:>3} {live_text[:44]:<45} {live_href[:44]:<45} {local_href[:44]:<45} {status}")

        if status == "MISMATCH":
            print(f"      EXPECTED: {expected}")

    if issues == 0:
        print(f"\n  ALL {max_len} BUTTONS MATCH")
    else:
        print(f"\n  {issues} MISMATCHES FOUND")


def main():
    print("LMRF — LINK-BY-LINK COMPARISON: STATIC SITE vs LIVE SITE")
    print("=" * 70)

    for local_file, live_path in PAGES:
        compare_page(local_file, live_path)

    print(f"\n{'='*70}")
    print("COMPARISON COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
