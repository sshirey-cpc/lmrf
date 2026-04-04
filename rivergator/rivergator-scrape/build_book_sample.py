"""
Build a sample book chapter as HTML — demonstrates what the Rivergator
would look like as a printed paddler's guide.

Generates a styled HTML file that can be opened in a browser and printed to PDF.
"""

import os
import re
import markdown

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "..", "content-markdown")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "book-preview")

BOOK_CSS = """
@page {
    size: 6in 9in;
    margin: 0.75in 0.625in;
}

body {
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a1a1a;
    max-width: 7in;
    margin: 0 auto;
    padding: 40px;
}

h1 {
    font-family: 'Helvetica Neue', 'Arial', sans-serif;
    font-size: 24pt;
    font-weight: 700;
    color: #1B4965;
    border-bottom: 3px solid #1B4965;
    padding-bottom: 12px;
    margin-top: 60px;
    margin-bottom: 20px;
    page-break-before: always;
}

h1:first-of-type {
    page-break-before: avoid;
}

h2 {
    font-family: 'Helvetica Neue', 'Arial', sans-serif;
    font-size: 16pt;
    font-weight: 600;
    color: #2E6F8E;
    margin-top: 36px;
    margin-bottom: 12px;
}

h3 {
    font-family: 'Helvetica Neue', 'Arial', sans-serif;
    font-size: 12pt;
    font-weight: 700;
    color: #1B4965;
    margin-top: 24px;
    margin-bottom: 8px;
    background: #f0f5f8;
    padding: 6px 10px;
    border-left: 4px solid #1B4965;
}

h4 {
    font-family: 'Helvetica Neue', 'Arial', sans-serif;
    font-size: 11pt;
    font-weight: 600;
    color: #2E6F8E;
    margin-top: 18px;
}

p {
    margin: 8px 0;
    text-align: justify;
    hyphens: auto;
}

em {
    color: #444;
}

strong {
    color: #1B4965;
}

hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 24px 0;
}

.title-page {
    text-align: center;
    padding-top: 120px;
    page-break-after: always;
}

.title-page h1 {
    font-size: 36pt;
    border: none;
    color: #1B4965;
    margin-bottom: 8px;
    page-break-before: avoid;
}

.title-page .subtitle {
    font-size: 16pt;
    color: #2E6F8E;
    font-style: italic;
    margin-bottom: 40px;
}

.title-page .author {
    font-size: 14pt;
    color: #555;
    margin-top: 40px;
}

.title-page .org {
    font-size: 11pt;
    color: #888;
    margin-top: 8px;
}

.section-header {
    text-align: center;
    padding-top: 80px;
    page-break-before: always;
    page-break-after: always;
}

.section-header h1 {
    border: none;
    page-break-before: avoid;
}

.section-header .mile-range {
    font-size: 14pt;
    color: #2E6F8E;
    font-style: italic;
}

.toc {
    page-break-after: always;
}

.toc h2 {
    text-align: center;
}

.toc ul {
    list-style: none;
    padding: 0;
}

.toc li {
    padding: 4px 0;
    border-bottom: 1px dotted #ccc;
}

.warning-box {
    background: #fff3cd;
    border: 1px solid #e6c34d;
    padding: 12px;
    margin: 16px 0;
    border-radius: 4px;
}

.mile-marker {
    background: #f0f5f8;
    padding: 4px 8px;
    border-left: 3px solid #1B4965;
    margin: 12px 0 6px 0;
    font-weight: bold;
}

footer {
    font-size: 9pt;
    color: #999;
    text-align: center;
    margin-top: 40px;
    border-top: 1px solid #ddd;
    padding-top: 8px;
}
"""


def read_chapter(section_slug, chapter_slug):
    """Read a markdown chapter file."""
    path = os.path.join(CONTENT_DIR, "river-log", section_slug, f"{chapter_slug}.md")
    if not os.path.exists(path):
        return None

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Strip frontmatter
    if content.startswith('---'):
        end = content.index('---', 3)
        content = content[end + 3:].strip()

    return content


def md_to_html(md_text):
    """Convert markdown to HTML with some enhancements."""
    html = markdown.markdown(md_text, extensions=['extra'])

    # Enhance mile markers with special styling
    html = re.sub(
        r'<h3>(Mile \d+(?:\.\d+)?.*?)</h3>',
        r'<h3 class="mile-marker">\1</h3>',
        html
    )

    return html


def build_sample_book():
    """Build a sample book showing 2 sections."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Build a sample with: Title page + TOC + Memphis to Helena section (good narrative)
    sample_sections = [
        ("memphis-to-helena", "Memphis to Helena", "Mile 737-663", [
            ("introduction", "Introduction"),
            ("memphis-to-tunica", "Memphis to Tunica"),
            ("tunica-to-helena", "Tunica to Helena"),
            ("helena-to-friars", "Helena to Friars Point"),
            ("appendix", "Appendix"),
        ]),
    ]

    html_parts = []

    # Title page
    html_parts.append("""
    <div class="title-page">
        <h1>The Rivergator</h1>
        <div class="subtitle">A Paddler's Guide to the<br>Lower Mississippi River Water Trail</div>
        <div class="author">By John Ruskey</div>
        <div class="org">Lower Mississippi River Foundation</div>
        <div style="margin-top: 60px; font-size: 10pt; color: #aaa;">
            SAMPLE CHAPTER: Memphis to Helena<br>
            Mile 737 to Mile 663
        </div>
    </div>
    """)

    # TOC
    html_parts.append('<div class="toc">')
    html_parts.append('<h2>Table of Contents</h2>')
    html_parts.append('<p style="text-align:center; font-style:italic; color:#666;">Complete guide covers 1,100 miles: St. Louis to the Gulf of Mexico</p>')
    html_parts.append('<ul>')

    all_sections = [
        ("St. Louis to Caruthersville", "Mile 195-850"),
        ("Caruthersville to Memphis", "Mile 850-737"),
        ("Memphis to Helena", "Mile 737-663"),
        ("Helena to Greenville", "Mile 663-537"),
        ("Greenville to Vicksburg", "Mile 537-437"),
        ("Vicksburg to Baton Rouge", "Mile 437-225"),
        ("Atchafalaya River", "Mile 159-0"),
        ("Baton Rouge to Venice", "Mile 229-10"),
        ("Birdsfoot Delta", "Mile 10-0"),
    ]
    for name, miles in all_sections:
        bold = ' style="font-weight:bold; color:#1B4965;"' if name == "Memphis to Helena" else ''
        html_parts.append(f'<li{bold}>{name} <span style="float:right">{miles}</span></li>')

    html_parts.append('</ul>')
    html_parts.append('<p style="margin-top:20px; font-size:10pt; color:#888;">Plus: Paddler\'s Guide | Safety | How to Paddle the Big River | Resources | Maps</p>')
    html_parts.append('</div>')

    # Chapters
    for section_slug, section_name, mile_range, chapters in sample_sections:
        # Section divider page
        html_parts.append(f"""
        <div class="section-header">
            <h1>{section_name}</h1>
            <div class="mile-range">{mile_range}</div>
        </div>
        """)

        for chapter_slug, chapter_name in chapters:
            md = read_chapter(section_slug, chapter_slug)
            if md is None:
                continue

            # Truncate very long chapters for the sample
            if len(md) > 40000:
                # Find a good break point
                break_at = md.find('\n---\n', 30000)
                if break_at > 0:
                    md = md[:break_at] + '\n\n*[Chapter continues...]*\n'

            html = md_to_html(md)
            html_parts.append(f'<h1>{chapter_name}</h1>')
            html_parts.append(html)

    # Assemble
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Rivergator — Sample Chapter</title>
    <style>{BOOK_CSS}</style>
</head>
<body>
{''.join(html_parts)}

<footer>
    The Rivergator: A Paddler's Guide to the Lower Mississippi River Water Trail<br>
    &copy; John Ruskey / Lower Mississippi River Foundation<br>
    rivergator.org
</footer>
</body>
</html>"""

    output_path = os.path.join(OUTPUT_DIR, "rivergator-sample-chapter.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"Book sample generated: {output_path}")
    print(f"Open in browser and Print > Save as PDF for a book-quality preview")

    # Also build a full TOC with all chapters and word counts
    toc_path = os.path.join(OUTPUT_DIR, "full-book-stats.txt")
    total_words = 0
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write("THE RIVERGATOR — FULL BOOK STATISTICS\n")
        f.write("=" * 60 + "\n\n")

        sections_data = [
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

        for section_slug, section_name in sections_data:
            section_dir = os.path.join(CONTENT_DIR, "river-log", section_slug)
            if not os.path.exists(section_dir):
                continue

            section_words = 0
            chapter_lines = []

            import glob
            for md_file in sorted(glob.glob(os.path.join(section_dir, "*.md"))):
                with open(md_file, 'r', encoding='utf-8') as mf:
                    content = mf.read()
                words = len(content.split())
                section_words += words
                chapter_name = os.path.basename(md_file).replace('.md', '').replace('-', ' ').title()
                pages_est = words // 250  # ~250 words per printed page
                chapter_lines.append(f"    {chapter_name:<45} {words:>8,} words  (~{pages_est} pages)")

            total_words += section_words
            pages_est = section_words // 250

            f.write(f"\n{section_name}\n")
            f.write(f"  Total: {section_words:,} words (~{pages_est} printed pages)\n")
            for cl in chapter_lines:
                f.write(cl + "\n")

        # Paddler's Guide
        guide_dir = os.path.join(CONTENT_DIR, "paddlers-guide")
        guide_words = 0
        if os.path.exists(guide_dir):
            for md_file in glob.glob(os.path.join(guide_dir, "*.md")):
                with open(md_file, 'r', encoding='utf-8') as mf:
                    guide_words += len(mf.read().split())
        total_words += guide_words

        f.write(f"\nPaddler's Guide: {guide_words:,} words (~{guide_words // 250} pages)\n")

        f.write(f"\n{'=' * 60}\n")
        f.write(f"TOTAL: {total_words:,} words\n")
        f.write(f"Estimated printed pages (at 250 words/page): {total_words // 250}\n")
        f.write(f"Estimated book length: ~{total_words // 250} pages\n")
        f.write(f"\nFor reference:\n")
        f.write(f"  - A typical novel: 80,000-100,000 words\n")
        f.write(f"  - This guide: {total_words:,} words\n")
        f.write(f"  - That's {total_words / 90000:.1f}x the length of a typical novel\n")

    with open(toc_path, 'r') as f:
        print(f.read())


if __name__ == '__main__':
    build_sample_book()
