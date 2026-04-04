"""
Build clean Markdown from the 655 extracted riverlog pages.
Stitches sequential pages back into chapter-length documents.
Also converts the Paddler's Guide pages from the scraped HTML.

Output: Clean markdown files organized by section/chapter, ready for Ghost CMS import
and book publishing.
"""

import os
import re
import json
import glob

RIVERLOG_PAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "riverlog-data", "pages")
SCRAPED_TEXT_DIR = os.path.join(os.path.dirname(__file__), "..", "scraped-text")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "content-markdown")

# Section ordering and display names
SECTIONS = [
    ("stlouis-to-caruthersville", "St. Louis to Caruthersville", "Mile 195-850"),
    ("caruthersville-to-memphis", "Caruthersville to Memphis", "Mile 850-737"),
    ("memphis-to-helena", "Memphis to Helena", "Mile 737-663"),
    ("helena-to-greenville", "Helena to Greenville", "Mile 663-537"),
    ("greenville-to-vicksburg", "Greenville to Vicksburg", "Mile 537-437"),
    ("vicksburg-to-baton-rouge", "Vicksburg to Baton Rouge", "Mile 437-225"),
    ("atchafalaya-river", "Atchafalaya River", "Mile 159-0"),
    ("baton-rouge-to-venice", "Baton Rouge to Venice", "Mile 229-10"),
    ("birdsfoot-delta", "Birdsfoot Delta", "Mile 10-0"),
]


def clean_text_to_markdown(text):
    """Convert extracted plain text to cleaner markdown."""
    if not text:
        return ''

    lines = text.split('\n')
    md_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            md_lines.append('')
            continue

        # Detect mile marker patterns and format as headers
        # Pattern: "195 RBD" or "663.5 LBD" at start of a section
        mile_match = re.match(r'^(\d{1,3}(?:\.\d)?)\s+(RBD|LBD|R\.?B\.?D\.?|L\.?B\.?D\.?)\s+(.+)', line)
        if mile_match:
            mile = mile_match.group(1)
            bank = mile_match.group(2).replace('.', '').upper()
            name = mile_match.group(3)
            md_lines.append(f'\n### Mile {mile} {bank} — {name}\n')
            continue

        # Detect "MILE XXX" style markers
        mile_match2 = re.match(r'^(?:MILE|Mile)\s+(\d{1,3}(?:\.\d)?)\s*(.*)', line)
        if mile_match2:
            mile = mile_match2.group(1)
            rest = mile_match2.group(2).strip()
            if rest:
                md_lines.append(f'\n### Mile {mile} — {rest}\n')
            else:
                md_lines.append(f'\n### Mile {mile}\n')
            continue

        # Detect water level section headers
        wl_match = re.match(r'^(Low Water|Medium Water|High Water|Flood Stage|Extreme Low Water|Extreme High Water):\s*(.*)', line)
        if wl_match:
            level = wl_match.group(1)
            rest = wl_match.group(2).strip()
            md_lines.append(f'\n**{level}:** {rest}')
            continue

        # Detect gauge references and make them bold
        line = re.sub(r'(\w+ Gage \(\w+\))', r'**\1**', line)

        # Detect "Appendix X -" patterns
        appendix_match = re.match(r'^(Appendix\s+\d+)\s*[-–]\s*(.*)', line)
        if appendix_match:
            num = appendix_match.group(1)
            title = appendix_match.group(2)
            md_lines.append(f'\n#### {num}: {title}\n')
            continue

        md_lines.append(line)

    result = '\n'.join(md_lines)

    # Clean up excessive blank lines
    result = re.sub(r'\n{4,}', '\n\n\n', result)

    return result.strip()


def stitch_chapter_pages(pages_dir, section_slug, chapter_slug):
    """Find all numbered pages for a chapter and stitch them together in order."""
    pattern = f"{section_slug}-{chapter_slug}-*.txt"
    files = glob.glob(os.path.join(pages_dir, pattern))

    if not files:
        return None, []

    # Extract page numbers and sort
    page_files = []
    for f in files:
        basename = os.path.basename(f)
        # Extract the trailing number
        match = re.search(r'-(\d+)\.txt$', basename)
        if match:
            page_num = int(match.group(1))
            page_files.append((page_num, f))

    page_files.sort(key=lambda x: x[0])

    # Read and concatenate
    combined_text = []
    page_titles = []
    for page_num, filepath in page_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip the header lines (TITLE, ID, ORDER, META, ===)
        lines = content.split('\n')
        body_start = 0
        for i, line in enumerate(lines):
            if line.startswith('=' * 20):
                body_start = i + 1
                break

        body = '\n'.join(lines[body_start:]).strip()
        if body:
            combined_text.append(body)

        # Get title from first line
        if lines:
            page_titles.append(lines[0].replace('TITLE: ', ''))

    full_text = '\n\n---\n\n'.join(combined_text)
    return full_text, page_titles


def build_all_markdown():
    """Build markdown files for all sections and chapters."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Create section directories
    for section_slug, section_name, mile_range in SECTIONS:
        section_dir = os.path.join(OUTPUT_DIR, "river-log", section_slug)
        os.makedirs(section_dir, exist_ok=True)

    # Find all unique chapter slugs per section
    all_files = glob.glob(os.path.join(RIVERLOG_PAGES_DIR, "*.txt"))
    chapters_by_section = {}

    for f in all_files:
        basename = os.path.basename(f).replace('.txt', '')
        # Parse: section-slug-chapter-slug-pagenum
        # The tricky part is that both section and chapter slugs can have hyphens
        # We know the section slugs, so match against those
        for section_slug, _, _ in SECTIONS:
            if basename.startswith(section_slug + '-'):
                remainder = basename[len(section_slug) + 1:]
                # remainder is "chapter-slug-pagenum"
                # Extract page number from end
                match = re.match(r'(.+)-(\d+)$', remainder)
                if match:
                    chapter_slug = match.group(1)
                    if section_slug not in chapters_by_section:
                        chapters_by_section[section_slug] = set()
                    chapters_by_section[section_slug].add(chapter_slug)
                break

    total_chapters = sum(len(chs) for chs in chapters_by_section.values())
    total_chars = 0
    chapter_count = 0

    print(f"Building markdown for {total_chapters} chapters across {len(SECTIONS)} sections")
    print("=" * 70)

    # Table of contents
    toc_lines = ["# The Rivergator: A Paddler's Guide to the Lower Mississippi River\n"]
    toc_lines.append("*By John Ruskey*\n")
    toc_lines.append("---\n")
    toc_lines.append("## Table of Contents\n")

    for section_slug, section_name, mile_range in SECTIONS:
        chapters = chapters_by_section.get(section_slug, set())
        if not chapters:
            print(f"\n  SECTION: {section_name} — no chapters found")
            continue

        # Sort chapters (try to detect natural order from page content)
        sorted_chapters = sorted(chapters)

        # Prioritize intro/preamble first, appendix last
        def chapter_sort_key(ch):
            if 'intro' in ch.lower() or 'preamble' in ch.lower():
                return (0, ch)
            elif 'appendix' in ch.lower() or 'addendum' in ch.lower():
                return (2, ch)
            else:
                return (1, ch)

        sorted_chapters = sorted(chapters, key=chapter_sort_key)

        print(f"\n  SECTION: {section_name} ({mile_range}) — {len(sorted_chapters)} chapters")
        toc_lines.append(f"\n### {section_name} ({mile_range})\n")

        section_dir = os.path.join(OUTPUT_DIR, "river-log", section_slug)

        for chapter_slug in sorted_chapters:
            text, page_titles = stitch_chapter_pages(RIVERLOG_PAGES_DIR, section_slug, chapter_slug)
            if not text:
                continue

            # Build a nice chapter title from the slug
            chapter_title = chapter_slug.replace('-', ' ').replace('_', ' ')
            # Capitalize properly
            chapter_title = ' '.join(
                word.capitalize() if word.lower() not in ('to', 'and', 'the', 'of', 'vs', 'in', 'a')
                else word
                for word in chapter_title.split()
            )
            # Always capitalize first word
            if chapter_title:
                chapter_title = chapter_title[0].upper() + chapter_title[1:]

            # Convert to markdown
            markdown = clean_text_to_markdown(text)

            # Add frontmatter
            full_md = f"""---
title: "{chapter_title}"
section: "{section_name}"
section_slug: "{section_slug}"
mile_range: "{mile_range}"
chapter_slug: "{chapter_slug}"
pages_stitched: {len(page_titles)}
---

# {chapter_title}

*{section_name} — {mile_range}*

{markdown}
"""
            # Write file
            filename = f"{chapter_slug}.md"
            filepath = os.path.join(section_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_md)

            chars = len(markdown)
            total_chars += chars
            chapter_count += 1

            toc_lines.append(f"- [{chapter_title}](river-log/{section_slug}/{filename}) ({len(page_titles)} pages, {chars:,} chars)")
            print(f"    {chapter_title}: {len(page_titles)} pages stitched, {chars:,} chars")

    # Write TOC
    toc_path = os.path.join(OUTPUT_DIR, "TABLE_OF_CONTENTS.md")
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(toc_lines))

    # Also convert Paddler's Guide pages from scraped text
    guide_dir = os.path.join(OUTPUT_DIR, "paddlers-guide")
    os.makedirs(guide_dir, exist_ok=True)

    guide_pages = glob.glob(os.path.join(SCRAPED_TEXT_DIR, "paddlers-guide__*.txt"))
    guide_count = 0

    print(f"\n\n  PADDLER'S GUIDE — {len(guide_pages)} pages")
    for gp in sorted(guide_pages):
        with open(gp, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip header lines
        lines = content.split('\n')
        body_start = 0
        for i, line in enumerate(lines):
            if line.startswith('=' * 20):
                body_start = i + 1
                break

        body = '\n'.join(lines[body_start:]).strip()
        if len(body) < 50:
            continue

        # Get source URL from first line
        source = lines[0].replace('SOURCE: ', '') if lines else ''

        basename = os.path.basename(gp).replace('.txt', '')
        # Clean up the slug
        slug = basename.replace('paddlers-guide__', '').replace('__', '-')

        title = slug.replace('-', ' ').title()

        md = f"""---
title: "{title}"
source: "{source}"
type: "paddlers-guide"
---

# {title}

{clean_text_to_markdown(body)}
"""
        out_path = os.path.join(guide_dir, f"{slug}.md")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(md)

        guide_count += 1
        print(f"    {title}: {len(body):,} chars")

    print(f"\n{'='*70}")
    print(f"COMPLETE:")
    print(f"  River Log: {chapter_count} chapters, {total_chars:,} characters")
    print(f"  Paddler's Guide: {guide_count} pages")
    print(f"  Output: {os.path.abspath(OUTPUT_DIR)}")
    print(f"  Table of Contents: {toc_path}")


if __name__ == '__main__':
    build_all_markdown()
