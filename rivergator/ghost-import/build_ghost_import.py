"""
Build a Ghost CMS import JSON file from Rivergator markdown content.

Reads:
  - content-markdown/river-log/**/*.md  (38 chapter files)
  - content-markdown/paddlers-guide/*.md (20 guide pages)
  - content-markdown/mile-markers.json   (1,618 markers)

Writes:
  - ghost-import/ghost-import.json
  - ghost-import/import-summary.txt
"""

import json
import os
import re
import time
import hashlib
from pathlib import Path

import markdown

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(r"C:/Users/scott/lmrf/rivergator")
CONTENT = BASE / "content-markdown"
RIVER_LOG = CONTENT / "river-log"
PADDLERS_GUIDE = CONTENT / "paddlers-guide"
MILE_MARKERS = CONTENT / "mile-markers.json"
OUT_DIR = BASE / "ghost-import"
OUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Sections (in order)
# ---------------------------------------------------------------------------
SECTIONS = [
    ("stlouis-to-caruthersville", "St. Louis to Caruthersville"),
    ("caruthersville-to-memphis", "Caruthersville to Memphis"),
    ("memphis-to-helena", "Memphis to Helena"),
    ("helena-to-greenville", "Helena to Greenville"),
    ("greenville-to-vicksburg", "Greenville to Vicksburg"),
    ("vicksburg-to-baton-rouge", "Vicksburg to Baton Rouge"),
    ("atchafalaya-river", "Atchafalaya River"),
    ("baton-rouge-to-venice", "Baton Rouge to Venice"),
    ("birdsfoot-delta", "Birdsfoot Delta"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
md_converter = markdown.Markdown(extensions=["tables", "fenced_code"])

def stable_id(seed: str) -> str:
    """Create a 24-char hex id from a seed string (ObjectId length)."""
    return hashlib.sha256(seed.encode()).hexdigest()[:24]

def parse_frontmatter(text: str):
    """Return (frontmatter_dict, body) from a markdown file with --- delimiters."""
    fm = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    fm[key.strip()] = val.strip().strip('"').strip("'")
            body = parts[2]
    return fm, body

def md_to_html(md_text: str) -> str:
    """Convert markdown text to HTML."""
    md_converter.reset()
    return md_converter.convert(md_text)

def make_slug(text: str) -> str:
    """Convert text to a URL slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")

def detect_content_type(filename: str, frontmatter: dict) -> str:
    """Detect whether a chapter file is an intro, appendix, or chapter."""
    name = filename.lower()
    title = frontmatter.get("title", "").lower()
    if "intro" in name or "introduction" in title or "preamble" in name:
        return "introduction"
    if "appendix" in name or "appendix" in title:
        return "appendix"
    return "chapter"

def detect_feature_tags(html_content: str) -> list:
    """Scan content for feature keywords and return matching tag slugs."""
    text = html_content.lower()
    features = {
        "camping": ["camp", "camping", "campsite", "tent", "sandbar camp"],
        "access-point": ["boat ramp", "boat launch", "landing", "access point", "put-in", "take-out", "takeout"],
        "hazard": ["hazard", "danger", "warning", "caution", "whirlpool", "strainer"],
        "wildlife": ["eagle", "pelican", "heron", "wildlife", "bird", "deer", "turtle"],
        "history": ["civil war", "historic", "history", "twain", "plantation"],
        "lock-and-dam": ["lock and dam", "lock & dam"],
        "dike": ["wing dam", "wing-dam", "dike", "revetment"],
        "island": ["island"],
        "tributary": ["tributary", "mouth of the", "confluence"],
    }
    found = []
    for tag_slug, keywords in features.items():
        for kw in keywords:
            if kw in text:
                found.append(tag_slug)
                break
    return found

# ---------------------------------------------------------------------------
# Timestamp
# ---------------------------------------------------------------------------
NOW_MS = int(time.time() * 1000)
# Use a fixed published date for consistency
PUB_DATE = "2026-03-31T12:00:00.000Z"
PUB_MS = int(time.mktime(time.strptime("2026-03-31", "%Y-%m-%d")) * 1000)

# ---------------------------------------------------------------------------
# Collect all tags (slug -> tag_record)
# ---------------------------------------------------------------------------
tags = {}
tag_order = 0

def ensure_tag(slug: str, name: str, visibility: str = "public", description: str = "") -> str:
    """Register a tag and return its id."""
    global tag_order
    if slug not in tags:
        tags[slug] = {
            "id": stable_id(f"tag-{slug}"),
            "name": name if not slug.startswith("#") else name,
            "slug": slug.lstrip("#"),
            "description": description,
            "visibility": "internal" if slug.startswith("#") else visibility,
            "created_at": PUB_MS,
            "updated_at": PUB_MS,
        }
        tag_order += 1
    return tags[slug]["id"]

# Pre-create the fixed tags
ensure_tag("#river-log", "#river-log", description="Internal: River Log content")
ensure_tag("#chapter", "#chapter", description="Internal: Chapter content type")
ensure_tag("#appendix", "#appendix", description="Internal: Appendix content type")
ensure_tag("#introduction", "#introduction", description="Internal: Introduction content type")
ensure_tag("paddlers-guide", "Paddler's Guide", description="Paddler's Guide pages")

for sec_slug, sec_name in SECTIONS:
    ensure_tag(sec_slug, sec_name, description=f"River Log section: {sec_name}")

# Feature tags will be created on demand

# ---------------------------------------------------------------------------
# Build posts
# ---------------------------------------------------------------------------
posts = []
posts_tags = []
post_sort_order = 0
stats = {
    "river_log_posts": 0,
    "paddlers_guide_posts": 0,
    "total_tags": 0,
    "total_posts_tags": 0,
    "sections": {},
    "feature_tag_counts": {},
}

def add_post_tag(post_id: str, tag_id: str, sort: int = 0):
    """Link a post to a tag."""
    posts_tags.append({
        "id": stable_id(f"pt-{post_id}-{tag_id}"),
        "post_id": post_id,
        "tag_id": tag_id,
        "sort_order": sort,
    })

# --- River Log chapters ---
for sec_idx, (sec_slug, sec_name) in enumerate(SECTIONS):
    sec_dir = RIVER_LOG / sec_slug
    if not sec_dir.is_dir():
        print(f"  WARNING: section dir not found: {sec_dir}")
        continue

    md_files = sorted(sec_dir.glob("*.md"))
    stats["sections"][sec_name] = len(md_files)

    for file_idx, md_path in enumerate(md_files):
        raw = md_path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(raw)

        title = fm.get("title", md_path.stem.replace("-", " ").title())
        chapter_slug = fm.get("chapter_slug", md_path.stem)
        mile_range = fm.get("mile_range", "")
        content_type = detect_content_type(md_path.name, fm)

        # Build full slug with section prefix
        full_slug = f"river-log-{sec_slug}-{chapter_slug}"
        post_id = stable_id(f"post-{full_slug}")

        # Convert to HTML
        html = md_to_html(body)

        # Build excerpt
        excerpt = f"{sec_name}"
        if mile_range:
            excerpt += f" | {mile_range}"

        post = {
            "id": post_id,
            "title": f"{title}",
            "slug": full_slug,
            "html": html,
            "status": "published",
            "created_at": PUB_MS + (sec_idx * 1000) + file_idx,
            "updated_at": NOW_MS,
            "published_at": PUB_MS + (sec_idx * 1000) + file_idx,
            "custom_excerpt": excerpt,
            "feature_image": None,
            "type": "post",
            "visibility": "public",
        }
        posts.append(post)
        stats["river_log_posts"] += 1
        post_sort_order += 1

        # Assign tags
        tag_sort = 0
        # Internal river-log tag
        add_post_tag(post_id, tags["#river-log"]["id"], tag_sort); tag_sort += 1
        # Section tag
        add_post_tag(post_id, tags[sec_slug]["id"], tag_sort); tag_sort += 1
        # Content type tag
        ct_tag = f"#{content_type}"
        add_post_tag(post_id, tags[ct_tag]["id"], tag_sort); tag_sort += 1

        # Feature tags from content
        features = detect_feature_tags(html)
        for feat_slug in features:
            feat_name = feat_slug.replace("-", " ").title()
            feat_tag_id = ensure_tag(feat_slug, feat_name, description=f"Feature: {feat_name}")
            add_post_tag(post_id, feat_tag_id, tag_sort); tag_sort += 1
            stats["feature_tag_counts"][feat_slug] = stats["feature_tag_counts"].get(feat_slug, 0) + 1

# --- Paddler's Guide pages ---
guide_files = sorted(PADDLERS_GUIDE.glob("*.md"))
for file_idx, md_path in enumerate(guide_files):
    raw = md_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)

    title = fm.get("title", md_path.stem.replace("-", " ").title())
    page_slug = f"paddlers-guide-{md_path.stem}"
    post_id = stable_id(f"post-{page_slug}")

    html = md_to_html(body)

    post = {
        "id": post_id,
        "title": title,
        "slug": page_slug,
        "html": html,
        "status": "published",
        "created_at": PUB_MS + 100000 + file_idx,
        "updated_at": NOW_MS,
        "published_at": PUB_MS + 100000 + file_idx,
        "custom_excerpt": "Paddler's Guide to the Lower Mississippi River",
        "feature_image": None,
        "type": "page",
        "visibility": "public",
    }
    posts.append(post)
    stats["paddlers_guide_posts"] += 1

    # Tags
    tag_sort = 0
    add_post_tag(post_id, tags["paddlers-guide"]["id"], tag_sort); tag_sort += 1

    features = detect_feature_tags(html)
    for feat_slug in features:
        feat_name = feat_slug.replace("-", " ").title()
        feat_tag_id = ensure_tag(feat_slug, feat_name, description=f"Feature: {feat_name}")
        add_post_tag(post_id, feat_tag_id, tag_sort); tag_sort += 1
        stats["feature_tag_counts"][feat_slug] = stats["feature_tag_counts"].get(feat_slug, 0) + 1

# ---------------------------------------------------------------------------
# Build Ghost import JSON
# ---------------------------------------------------------------------------
ghost_import = {
    "db": [{
        "meta": {
            "exported_on": NOW_MS,
            "version": "5.0.0"
        },
        "data": {
            "posts": posts,
            "tags": list(tags.values()),
            "posts_tags": posts_tags,
            "users": [{
                "id": stable_id("user-rivergator"),
                "name": "John Ruskey",
                "slug": "john-ruskey",
                "email": "info@lowermsfoundation.org",
                "bio": "Author of the Rivergator: Paddler's Guide to the Lower Mississippi River. Founder of Quapaw Canoe Company.",
                "created_at": PUB_MS,
                "updated_at": NOW_MS,
            }]
        }
    }]
}

# Write JSON
out_path = OUT_DIR / "ghost-import.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(ghost_import, f, indent=2, ensure_ascii=False)

file_size = out_path.stat().st_size
file_size_mb = file_size / (1024 * 1024)

# ---------------------------------------------------------------------------
# Stats / Summary
# ---------------------------------------------------------------------------
stats["total_tags"] = len(tags)
stats["total_posts_tags"] = len(posts_tags)
total_posts = stats["river_log_posts"] + stats["paddlers_guide_posts"]

summary_lines = [
    "=" * 60,
    "GHOST IMPORT SUMMARY",
    "=" * 60,
    f"Generated:            {time.strftime('%Y-%m-%d %H:%M:%S')}",
    f"Output file:          {out_path}",
    f"File size:            {file_size_mb:.2f} MB ({file_size:,} bytes)",
    "",
    "--- Content ---",
    f"Total posts/pages:    {total_posts}",
    f"  River Log posts:    {stats['river_log_posts']}",
    f"  Paddler's Guide:    {stats['paddlers_guide_posts']}",
    "",
    "--- Tags ---",
    f"Total tags:           {stats['total_tags']}",
    f"Total post-tag links: {stats['total_posts_tags']}",
    "",
    "--- River Log Sections ---",
]
for sec_name, count in stats["sections"].items():
    summary_lines.append(f"  {sec_name}: {count} chapters")

summary_lines.append("")
summary_lines.append("--- Feature Tags (post count) ---")
for feat, count in sorted(stats["feature_tag_counts"].items(), key=lambda x: -x[1]):
    summary_lines.append(f"  {feat}: {count} posts")

summary_lines.append("")
summary_lines.append("--- All Tags ---")
for slug, tag in tags.items():
    vis = tag["visibility"]
    summary_lines.append(f"  [{vis:8s}] {slug}")

summary_lines.append("")
summary_lines.append("=" * 60)

summary_text = "\n".join(summary_lines)
print(summary_text)

summary_path = OUT_DIR / "import-summary.txt"
with open(summary_path, "w", encoding="utf-8") as f:
    f.write(summary_text)

print(f"\nFiles written:")
print(f"  {out_path}")
print(f"  {summary_path}")
