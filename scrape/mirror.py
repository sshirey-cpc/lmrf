"""
Mirror crawl of www.lowermsfoundation.org
Downloads all HTML pages with their CSS, JS, images, fonts, and other assets.
Rewrites URLs to work as a local static site.
"""

import os
import re
import time
import hashlib
from urllib.parse import urljoin, urlparse, unquote
from collections import deque

import requests
from bs4 import BeautifulSoup

SITE = "https://www.lowermsfoundation.org"
OUT_DIR = os.path.join(os.path.dirname(__file__), "mirror")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

visited_pages = set()
downloaded_assets = {}  # url -> local_path
failed = []


def safe_path(url):
    """Convert a URL to a safe local file path."""
    parsed = urlparse(url)
    host = parsed.netloc
    path = unquote(parsed.path).strip("/")

    if not path:
        path = "index.html"

    # For the main site pages
    if host in ("www.lowermsfoundation.org", ""):
        if not os.path.splitext(path)[1]:
            path = path + "/index.html"
        return path

    # For external assets (CDN images, fonts, etc.)
    # Flatten into assets/ directory with hashed name to avoid collisions
    ext = os.path.splitext(parsed.path)[1] or ""
    if not ext:
        # guess from common patterns
        if "font" in url.lower():
            ext = ".woff2"
        elif "css" in url.lower():
            ext = ".css"
        elif "js" in url.lower():
            ext = ".js"
    name_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    # Try to keep a readable basename
    basename = os.path.basename(parsed.path) or name_hash
    # Clean the basename
    basename = re.sub(r'[^\w.\-]', '_', unquote(basename))
    if len(basename) > 80:
        basename = name_hash + ext
    return os.path.join("assets", host.replace(":", "_"), basename)


def download(url):
    """Download a URL, return (content_bytes, content_type) or (None, None)."""
    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content, resp.headers.get("Content-Type", "")
    except Exception as e:
        print(f"  FAIL: {url} ({e})")
        failed.append(url)
        return None, None


def save(local_path, content):
    """Save content to disk under OUT_DIR."""
    full = os.path.join(OUT_DIR, local_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    mode = "wb"
    with open(full, mode) as f:
        f.write(content if isinstance(content, bytes) else content.encode("utf-8"))
    return full


def download_asset(url):
    """Download an asset (CSS, JS, image, font) and return local path."""
    if url in downloaded_assets:
        return downloaded_assets[url]

    local = safe_path(url)
    content, ctype = download(url)
    if content is None:
        downloaded_assets[url] = None
        return None

    # If it's a CSS file, also process its internal url() references
    if "css" in (ctype or "") or local.endswith(".css"):
        content = process_css(content, url)

    save(local, content)
    downloaded_assets[url] = local
    print(f"  ASSET: {local}")
    return local


def process_css(css_bytes, base_url):
    """Find url() references in CSS and download those assets too."""
    css_text = css_bytes.decode("utf-8", errors="replace")

    def replace_url(match):
        raw = match.group(1).strip("'\"")
        if raw.startswith("data:") or raw.startswith("#"):
            return match.group(0)
        abs_url = urljoin(base_url, raw)
        local = download_asset(abs_url)
        if local:
            # Calculate relative path from CSS file to the asset
            css_local = safe_path(base_url)
            css_dir = os.path.dirname(css_local)
            rel = os.path.relpath(local, css_dir).replace("\\", "/")
            return f"url({rel})"
        return match.group(0)

    css_text = re.sub(r'url\(([^)]+)\)', replace_url, css_text)
    return css_text.encode("utf-8")


def relative_url(from_page, to_asset):
    """Get relative path from an HTML page to a downloaded asset."""
    from_dir = os.path.dirname(from_page)
    return os.path.relpath(to_asset, from_dir).replace("\\", "/")


def process_page(url):
    """Download and process an HTML page. Rewrite asset URLs to local paths."""
    if url in visited_pages:
        return
    visited_pages.add(url)

    print(f"\nPAGE: {url}")
    content, ctype = download(url)
    if content is None:
        return

    page_local = safe_path(url)
    soup = BeautifulSoup(content, "html.parser")

    # Collect internal links to crawl
    internal_links = []

    # Process all tags with src/href attributes
    for tag in soup.find_all(["link", "script", "img", "source", "video", "audio"]):
        for attr in ["src", "href"]:
            val = tag.get(attr)
            if not val or val.startswith("data:") or val.startswith("#") or val.startswith("mailto:") or val.startswith("tel:"):
                continue

            abs_url = urljoin(url, val)

            # Skip non-http
            if not abs_url.startswith("http"):
                continue

            # For <link rel="stylesheet"> and <script src>, download as asset
            if tag.name == "link" and tag.get("rel") and "stylesheet" in tag.get("rel", []):
                local = download_asset(abs_url)
                if local:
                    tag[attr] = relative_url(page_local, local)
                continue

            if tag.name == "script" and attr == "src":
                local = download_asset(abs_url)
                if local:
                    tag[attr] = relative_url(page_local, local)
                continue

            if tag.name in ("img", "source", "video", "audio"):
                local = download_asset(abs_url)
                if local:
                    tag[attr] = relative_url(page_local, local)
                continue

    # Process srcset attributes
    for tag in soup.find_all(attrs={"srcset": True}):
        srcset = tag["srcset"]
        parts = []
        for entry in srcset.split(","):
            entry = entry.strip()
            if not entry:
                continue
            pieces = entry.split()
            img_url = pieces[0]
            descriptor = " ".join(pieces[1:]) if len(pieces) > 1 else ""
            abs_url = urljoin(url, img_url)
            local = download_asset(abs_url)
            if local:
                rel = relative_url(page_local, local)
                parts.append(f"{rel} {descriptor}".strip())
            else:
                parts.append(entry)
        tag["srcset"] = ", ".join(parts)

    # Process inline style background-image urls
    for tag in soup.find_all(style=True):
        style = tag["style"]
        def replace_bg(match):
            raw = match.group(1).strip("'\"")
            if raw.startswith("data:"):
                return match.group(0)
            abs_url = urljoin(url, raw)
            local = download_asset(abs_url)
            if local:
                rel = relative_url(page_local, local)
                return f"url({rel})"
            return match.group(0)
        tag["style"] = re.sub(r'url\(([^)]+)\)', replace_bg, style)

    # Process <a> tags — rewrite internal links to local HTML files
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("#"):
            continue
        abs_url = urljoin(url, href)
        parsed = urlparse(abs_url)

        # Internal link?
        if parsed.netloc in ("www.lowermsfoundation.org", ""):
            path = parsed.path.rstrip("/")
            if not path:
                path = "/"

            # Downloadable files
            if path.startswith("/s/"):
                local = download_asset(abs_url)
                if local:
                    tag["href"] = relative_url(page_local, local)
                continue

            # Internal page link
            if not os.path.splitext(path)[1] or path.endswith(".html"):
                internal_links.append(abs_url)
                # Rewrite to local path
                target_local = safe_path(abs_url)
                tag["href"] = relative_url(page_local, target_local)
                continue

    # Process <style> blocks
    for tag in soup.find_all("style"):
        if tag.string:
            def replace_style_url(match):
                raw = match.group(1).strip("'\"")
                if raw.startswith("data:"):
                    return match.group(0)
                abs_url = urljoin(url, raw)
                local = download_asset(abs_url)
                if local:
                    rel = relative_url(page_local, local)
                    return f"url({rel})"
                return match.group(0)
            tag.string = re.sub(r'url\(([^)]+)\)', replace_style_url, tag.string)

    # Save the processed HTML
    html_out = str(soup)
    save(page_local, html_out.encode("utf-8"))
    print(f"  SAVED: {page_local}")

    # Crawl discovered internal links
    for link in internal_links:
        # Normalize
        parsed = urlparse(link)
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if clean not in visited_pages:
            process_page(clean)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Mirroring {SITE} to {OUT_DIR}\n")

    # Start with the homepage
    process_page(SITE + "/")

    # Also explicitly crawl known pages that might not be linked directly
    known_pages = [
        "/who-we-are",
        "/our-programs",
        "/summer-camps",
        "/new-page-2",
        "/get-involved",
        "/calendar",
        "/lmrf",
        "/contact",
        "/donate",
        "/volunteer-1",
        "/home-1",
        "/camp-application",
        "/delta-day-camp",
        "/lmrf/2019/6/8/meet-the-disciples",
        "/lmrf/2019/6/8/day-5-smiths-point-to-home",
        "/lmrf/2019/6/8/day-4-island-67-to-smiths-point",
        "/lmrf/2019/6/8/day-3-island-64-to-island-67",
        "/lmrf/2019/6/8/day-2-island-62-to-island-64",
        "/lmrf/2019/6/8/day-1-helena-to-island-62",
        "/lmrf/2019/4/22/summer-camp-video",
        "/lmrf/2018/7/11/delta-adventure-day-camp",
        "/lmrf/2018/6/16/day-5-circles-and-boxes",
        "/lmrf/2018/6/16/day-4-genesis",
        "/lmrf/2018/6/16/day-3-leadership",
        "/lmrf/2018/6/16/day-2-challenge",
        "/lmrf/2018/6/11/day-1-no-fear",
        "/lmrf/2018/6/4/creating-a-new-generation-of-stewards",
    ]
    for path in known_pages:
        full_url = SITE + path
        if full_url not in visited_pages:
            process_page(full_url)

    print(f"\n{'='*60}")
    print(f"Done! Pages: {len(visited_pages)}, Assets: {len(downloaded_assets)}")
    if failed:
        print(f"Failed downloads: {len(failed)}")
        for f in failed:
            print(f"  - {f}")
    print(f"Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
