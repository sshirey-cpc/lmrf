"""
Rivergator River Log Scraper
Captures all mile-by-mile River Log pages + Paddler's Guide pages from rivergator.org.
Saves raw HTML and extracted clean text for each page.

Usage: python scrape_riverlog.py
"""

import urllib.request
import urllib.error
import os
import re
import time
import json
from html.parser import HTMLParser

BASE_URL = "https://www.rivergator.org"
OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "..", "scraped-html")
OUTPUT_TEXT = os.path.join(os.path.dirname(__file__), "..", "scraped-text")

# All known River Log sub-pages (from site analysis)
RIVER_LOG_PAGES = [
    # St. Louis to Caruthersville
    "/river-log/stlouis-to-caruthersville/stl-car-preamble",
    "/river-log/stlouis-to-caruthersville/intro-st-car",
    "/river-log/stlouis-to-caruthersville/st-louis",
    "/river-log/stlouis-to-caruthersville/stl-cairo",
    "/river-log/stlouis-to-caruthersville/cairo-caruthersville",
    "/river-log/stlouis-to-caruthersville/stl-car-appendix",
    # Caruthersville to Memphis
    "/river-log/caruthersville-to-memphis/intro",
    "/river-log/caruthersville-to-memphis/caruthersville-to-osceola",
    "/river-log/caruthersville-to-memphis/osceola-to-shelby-forest",
    "/river-log/caruthersville-to-memphis/shelby-forest-to-memphis",
    # Memphis to Helena
    "/river-log/memphis-to-helena/introduction",
    "/river-log/memphis-to-helena/memphis-to-tunica",
    "/river-log/memphis-to-helena/tunica-to-helena",
    "/river-log/memphis-to-helena/helena-to-friars",
    "/river-log/memphis-to-helena/appendix",
    # Helena to Greenville
    "/river-log/helena-to-greenville/st-francis-to-helena",
    "/river-log/helena-to-greenville/helena-to-island-63",
    "/river-log/helena-to-greenville/island-63-to-hurricane",
    "/river-log/helena-to-greenville/hurricane-to-rosedale",
    "/river-log/helena-to-greenville/rosedale-to-arkansas-city",
    "/river-log/helena-to-greenville/addendum",
    # Greenville to Vicksburg
    "/river-log/greenville-to-vicksburg/introductionGtoV",
    "/river-log/greenville-to-vicksburg/greenville-to-lake-providence",
    "/river-log/greenville-to-vicksburg/lake-providence-to-vicksburg",
    "/river-log/greenville-to-vicksburg/appendixABCD",
    # Vicksburg to Baton Rouge
    "/river-log/vicksburg-to-baton-rouge/introV-B",
    "/river-log/vicksburg-to-baton-rouge/vicksburg-to-natchez",
    "/river-log/vicksburg-to-baton-rouge/natchez-to-stfrancisville",
    "/river-log/vicksburg-to-baton-rouge/stfrancisville-to-baton-rouge",
    "/river-log/vicksburg-to-baton-rouge/appendixV-B",
    # Atchafalaya River
    "/river-log/atchafalaya-river/atchafalaya_upper",
    "/river-log/atchafalaya-river/atchafalaya_lower",
    "/river-log/atchafalaya-river/appendixAR",
    # Baton Rouge to Venice
    "/river-log/baton-rouge-to-venice/introBRtoV",
    "/river-log/baton-rouge-to-venice/baton-rouge-to-new-orleans",
    "/river-log/baton-rouge-to-venice/new-orleans-to-venice",
    "/river-log/baton-rouge-to-venice/appendixBR-V",
    # Birdsfoot Delta
    "/river-log/birdsfoot-delta/introBD",
    "/river-log/birdsfoot-delta/venice-to-gulf",
    "/river-log/birdsfoot-delta/appendixBD",
]

# River Log section landing pages (image maps)
RIVER_LOG_SECTIONS = [
    "/river-log/",
    "/river-log/stlouis-to-caruthersville/",
    "/river-log/caruthersville-to-memphis/",
    "/river-log/memphis-to-helena/",
    "/river-log/helena-to-greenville/",
    "/river-log/greenville-to-vicksburg/",
    "/river-log/vicksburg-to-baton-rouge/",
    "/river-log/atchafalaya-river/",
    "/river-log/baton-rouge-to-venice/",
    "/river-log/birdsfoot-delta/",
]

# Paddler's Guide pages (already in WP export but good to have clean copies)
PADDLERS_GUIDE_PAGES = [
    "/paddlers-guide/",
    "/paddlers-guide/introduction/",
    "/paddlers-guide/foreword/",
    "/paddlers-guide/river-guide/",
    "/paddlers-guide/how-to-paddle-the-big-river/",
    "/paddlers-guide/how-to-paddle-the-big-river/beginners-options/",
    "/paddlers-guide/how-to-paddle-the-big-river/forecasting-and-monitoring-river-levels/",
    "/paddlers-guide/how-to-paddle-the-big-river/main-channel-vs-back-channel/",
    "/paddlers-guide/how-to-paddle-the-big-river/monitoring-river-rise-with-a-stick/",
    "/paddlers-guide/how-to-paddle-the-big-river/options-for-moderate-intermediate-paddlers/",
    "/paddlers-guide/how-to-paddle-the-big-river/paddling-through-a-lock-and-dam/",
    "/paddlers-guide/how-to-paddle-the-big-river/safe-travel-through-a-notched-or-overtopped-back-channel-dike/",
    "/paddlers-guide/how-to-paddle-the-big-river/what-color-is-the-mississippi/",
    "/paddlers-guide/safety/",
    "/paddlers-guide/safety/canoe-self-rescue/",
    "/paddlers-guide/safety/kayak-self-rescue/",
    "/paddlers-guide/safety/paddle-signals/",
    "/paddlers-guide/safety/sup-self-rescue/",
    "/paddlers-guide/safety/whistle-signals/",
    "/paddlers-guide/phytoplankton/",
    "/paddlers-guide/when-to-paddle-the-big-river/",
]

# Other important pages
OTHER_PAGES = [
    "/",
    "/about-us/",
    "/about-us/experts/",
    "/resources/",
    "/resources/essential-paddlers-links/",
    "/resources/helpful-links-for-paddlers/",
    "/resources/leave-no-trace/",
    "/resources/lower-mississippi-river-dispatch/",
    "/resources/maps/",
    "/resources/news/",
    "/resources/water-trails-in-louisiana/",
    "/resources/water-trails-in-mississippi/",
    "/resources/press-kit/",
    "/river-media/",
    "/river-media/river-photo-gallery/",
    "/river-media/river-video/",
    "/river-media/2017-celebratory-expedition/",
    "/contact-us/",
    "/map-shop/",
    "/book-shop/",
]


class TextExtractor(HTMLParser):
    """Simple HTML to text converter that preserves some structure."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_script = False
        self.in_style = False
        self.in_nav = False

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.in_script = True
        elif tag == "style":
            self.in_style = True
        elif tag == "nav":
            self.in_nav = True
        elif tag in ("br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
            self.text_parts.append("\n")
        elif tag == "hr":
            self.text_parts.append("\n---\n")

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
        elif tag == "style":
            self.in_style = False
        elif tag == "nav":
            self.in_nav = False
        elif tag in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6"):
            self.text_parts.append("\n")

    def handle_data(self, data):
        if not self.in_script and not self.in_style and not self.in_nav:
            self.text_parts.append(data)

    def get_text(self):
        text = "".join(self.text_parts)
        # Clean up whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def extract_main_content(html):
    """Try to extract just the main content area, not headers/footers/sidebars."""
    # Look for the main content container (Avada/Fusion Builder)
    patterns = [
        r'<div[^>]*class="[^"]*post-content[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>\s*</main>',
        r'<div[^>]*class="[^"]*entry-content[^"]*"[^>]*>(.*)',
        r'<article[^>]*>(.*?)</article>',
        r'<main[^>]*>(.*?)</main>',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            return match.group(1)
    return html


def slug_from_path(path):
    """Convert URL path to a filename-safe slug."""
    slug = path.strip("/").replace("/", "__")
    if not slug:
        slug = "home"
    return slug


def fetch_page(url, retries=3):
    """Fetch a URL with retries and return the HTML content."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Rivergator-Archiver/1.0"
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    return None


def scrape_all():
    """Main scraping function."""
    os.makedirs(OUTPUT_HTML, exist_ok=True)
    os.makedirs(OUTPUT_TEXT, exist_ok=True)

    all_pages = (
        [("river-log-content", p) for p in RIVER_LOG_PAGES]
        + [("river-log-section", p) for p in RIVER_LOG_SECTIONS]
        + [("paddlers-guide", p) for p in PADDLERS_GUIDE_PAGES]
        + [("other", p) for p in OTHER_PAGES]
    )

    results = []
    total = len(all_pages)

    print(f"Scraping {total} pages from rivergator.org...")
    print(f"HTML output: {os.path.abspath(OUTPUT_HTML)}")
    print(f"Text output: {os.path.abspath(OUTPUT_TEXT)}")
    print("=" * 60)

    for i, (category, path) in enumerate(all_pages, 1):
        url = BASE_URL + path
        slug = slug_from_path(path)
        print(f"[{i}/{total}] {category}: {path}")

        html = fetch_page(url)
        if html is None:
            print(f"  FAILED - could not fetch")
            results.append({
                "path": path,
                "category": category,
                "slug": slug,
                "status": "failed",
                "html_bytes": 0,
                "text_chars": 0,
            })
            continue

        # Save raw HTML
        html_file = os.path.join(OUTPUT_HTML, f"{slug}.html")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)

        # Extract and save clean text
        main_html = extract_main_content(html)
        extractor = TextExtractor()
        extractor.feed(main_html)
        clean_text = extractor.get_text()

        text_file = os.path.join(OUTPUT_TEXT, f"{slug}.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(f"SOURCE: {url}\n")
            f.write(f"CATEGORY: {category}\n")
            f.write(f"SCRAPED: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(clean_text)

        results.append({
            "path": path,
            "category": category,
            "slug": slug,
            "status": "ok",
            "html_bytes": len(html),
            "text_chars": len(clean_text),
        })

        print(f"  OK - {len(html):,} bytes HTML, {len(clean_text):,} chars text")

        # Be polite to the server
        time.sleep(0.5)

    # Save manifest
    manifest_file = os.path.join(os.path.dirname(__file__), "..", "scrape-manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump({
            "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "base_url": BASE_URL,
            "total_pages": total,
            "successful": sum(1 for r in results if r["status"] == "ok"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "pages": results,
        }, f, indent=2)

    # Summary
    print("\n" + "=" * 60)
    ok = sum(1 for r in results if r["status"] == "ok")
    fail = sum(1 for r in results if r["status"] == "failed")
    total_text = sum(r["text_chars"] for r in results)
    print(f"DONE: {ok} succeeded, {fail} failed, {total_text:,} total text chars")
    print(f"Manifest saved to: {os.path.abspath(manifest_file)}")

    if fail > 0:
        print("\nFailed pages:")
        for r in results:
            if r["status"] == "failed":
                print(f"  {r['path']}")


if __name__ == "__main__":
    scrape_all()
