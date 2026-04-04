"""Mile marker splitter v4 — catches inline markers in all format variations."""
import os, re, json, glob

PAGES_DIR = "C:/Users/scott/lmrf/rivergator/riverlog-data/pages"
USACE_PATH = "C:/Users/scott/lmrf/rivergator/content-markdown/usace-mile-coordinates.json"
OUTPUT = "C:/Users/scott/lmrf/rivergator/ghost-import/ghost-import-v4.json"

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

with open(USACE_PATH) as f:
    miss_coords = json.load(f).get('MISSISSIPPI-LO', {})


def extract_name(text):
    """Extract just the landmark name from text after a mile marker."""
    text = re.sub(r'https?://\S+', '', text).strip()
    # Remove leading range like "749-742 "
    text = re.sub(r'^\d{1,3}-\d{1,3}\s+', '', text)
    words = text.split()
    stop = {'the','a','an','this','these','it','its','is','are','was','were',
            'in','on','at','from','after','before','once','every','as',
            'give','watch','narrow','just','several','while','you','one',
            'during','here','there','not','but','or','if','when','don','can',
            'most','kind','for','with','and'}
    name_words = []
    for i, w in enumerate(words):
        if w.lower() in stop:
            if i == 0 and w.lower() == 'the': name_words.append(w); continue
            if i < 4 and w.lower() in ('of','the','and','at','to'): name_words.append(w); continue
            break
        if i > 0 and name_words and name_words[-1].endswith('.'): break
        if i >= 7: break
        name_words.append(w)
    name = ' '.join(name_words).strip().rstrip('.,;:')
    # Deduplicate
    ws = name.split()
    if len(ws) >= 6:
        h = len(ws)//2
        if ws[:h] == ws[h:2*h]: name = ' '.join(ws[:h])
    if len(name) > 55:
        p = name.find('(')
        if p > 10: name = name[:p].strip()
    if len(name) > 55:
        name = name[:55].rsplit(' ', 1)[0]
    return name if len(name) > 2 else "River Feature"


def find_all_markers(text):
    """Find ALL mile markers in text, handling inline occurrences."""
    markers = []
    seen = set()

    # Pattern A: "NNN.N LBD/RBD" (most common in STL, VBR, Atch, BRV sections)
    for m in re.finditer(r'(\d{1,3}\.\d)\s+(LBD|RBD)\s+', text):
        mile, bank = float(m.group(1)), m.group(2)
        key = (round(mile, 1), bank)
        if 0 <= mile <= 960 and key not in seen:
            seen.add(key)
            name = extract_name(text[m.end():m.end()+200])
            markers.append((m.start(), mile, bank, name))

    # Pattern B: "NNN LBD/RBD" (whole number miles)
    for m in re.finditer(r'(?<!\d)(\d{3})\s+(LBD|RBD)\s+', text):
        mile, bank = float(m.group(1)), m.group(2)
        key = (mile, bank)
        if 0 <= mile <= 960 and key not in seen:
            seen.add(key)
            name = extract_name(text[m.end():m.end()+200])
            markers.append((m.start(), mile, bank, name))

    # Pattern C: "LBD NNN.N Name" or "LBD NNN Name" (common in Car-Mem, Mem-Hel, Hel-Gre, Gre-Vic)
    for m in re.finditer(r'(LBD|RBD)\s+(\d{1,3}(?:\.\d)?)\s+', text):
        bank, mile = m.group(1), float(m.group(2))
        key = (round(mile, 1), bank)
        if 0 <= mile <= 960 and key not in seen:
            seen.add(key)
            name = extract_name(text[m.end():m.end()+200])
            markers.append((m.start(), mile, bank, name))

    # Pattern D: "LBD Mile NNN" or "RBD Mile NNN"
    for m in re.finditer(r'(LBD|RBD)\s+Mile\s+(\d{1,3}(?:\.\d)?)\s+', text):
        bank, mile = m.group(1), float(m.group(2))
        key = (round(mile, 1), bank)
        if 0 <= mile <= 960 and key not in seen:
            seen.add(key)
            name = extract_name(text[m.end():m.end()+200])
            markers.append((m.start(), mile, bank, name))

    # Pattern E: "LBD NNN-NNN Name" (range format like "LBD 749-742 Hickman Bar")
    for m in re.finditer(r'(LBD|RBD)\s+(\d{3})-(\d{3})\s+', text):
        bank = m.group(1)
        mile = float(m.group(2))  # Use the first (higher) mile
        key = (mile, bank)
        if 0 <= mile <= 960 and key not in seen:
            seen.add(key)
            name = extract_name(text[m.end():m.end()+200])
            markers.append((m.start(), mile, bank, name))

    markers.sort(key=lambda x: x[0])
    return markers


def text_to_html(text):
    """Convert to HTML with proper paragraphs."""
    text = re.sub(r'https?://\S+', '', text)
    # Boilerplate
    text = re.sub(r'Rivergator[\s:]+[^©]*©\s*\d{4}\s*John Ruskey\s*', '', text)
    text = re.sub(r'For the Rivergator\s*:?\s*(?:Lower Mississippi River Water Trail)?\s*', '', text)
    text = re.sub(r'(?:The\s+)?www\.rivergator\.org\s*(?:is a free public use website.*?credits\.?)?\s*', '', text)
    text = re.sub(r'Re-?printing.*?credits\.?\s*', '', text)

    text = re.sub(r'\n{2,}', '\n\n', text)
    parts = text.split('\n\n')
    html = []
    for p in parts:
        p = p.strip()
        if not p: continue
        if len(p) > 1200:
            sents = re.split(r'(?<=[.!?])\s+', p)
            chunk = ""
            for s in sents:
                chunk += s + " "
                if len(chunk) > 500:
                    html.append(f'<p>{chunk.strip()}</p>')
                    chunk = ""
            if chunk.strip():
                html.append(f'<p>{chunk.strip()}</p>')
        else:
            html.append(f'<p>{p}</p>')
    return '\n'.join(html)


def make_slug(mile, bank, name):
    sn = re.sub(r'[^a-z0-9\s]', '', name.lower())
    sn = '-'.join(sn.split()[:4])
    ms = str(mile).replace('.', '-')
    slug = f"mile-{ms}-{sn}"
    return slug[:55]


all_posts = []

for section_slug, section_name in SECTIONS:
    files = glob.glob(os.path.join(PAGES_DIR, f"{section_slug}-*.txt"))
    chapters = {}
    for fp in files:
        bn = os.path.basename(fp).replace('.txt', '')
        rem = bn[len(section_slug) + 1:]
        m = re.match(r'(.+)-(\d+)$', rem)
        if m:
            ch, pn = m.group(1), int(m.group(2))
            if ch not in chapters: chapters[ch] = []
            chapters[ch].append((pn, fp))

    section_count = 0
    for ch_slug, pages in sorted(chapters.items()):
        pages.sort(key=lambda x: x[0])
        full = ""
        for pn, fp in pages:
            with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            lines = content.split('\n')
            bs = 0
            for i, ln in enumerate(lines):
                if ln.startswith('=' * 20): bs = i + 1; break
            full += '\n'.join(lines[bs:]).strip() + "\n\n"

        is_intro = any(x in ch_slug.lower() for x in ['intro', 'preamble'])
        is_appendix = any(x in ch_slug.lower() for x in ['appendix', 'addendum'])

        if is_intro or is_appendix:
            nice = "Introduction" if is_intro else "Appendix"
            all_posts.append({
                "title": f"{section_name} \u2014 {nice}",
                "slug": f"{section_slug}-{nice.lower()}",
                "html": text_to_html(full[:20000]),
                "section": section_slug, "section_name": section_name,
                "mile": None, "bank": "", "post_type": nice.lower(),
                "excerpt": f"{section_name} \u2014 {nice}",
            })
            continue

        markers = find_all_markers(full)

        if not markers:
            all_posts.append({
                "title": f"{section_name} \u2014 {ch_slug.replace('-',' ').title()}",
                "slug": f"{section_slug}-{ch_slug}",
                "html": text_to_html(full[:15000]),
                "section": section_slug, "section_name": section_name,
                "mile": None, "bank": "", "post_type": "chapter",
                "excerpt": section_name,
            })
            continue

        for i, (pos, mile, bank, name) in enumerate(markers):
            start = pos
            end = markers[i+1][0] if i+1 < len(markers) else len(full)
            chunk = full[start:end].strip()
            if len(chunk) < 50: continue

            coord = miss_coords.get(str(int(round(mile))))
            post = {
                "title": f"Mile {mile} {bank} \u2014 {name}",
                "slug": make_slug(mile, bank, name),
                "html": text_to_html(chunk),
                "section": section_slug, "section_name": section_name,
                "mile": mile, "bank": bank, "post_type": "mile-marker",
                "excerpt": f"{section_name} \u2014 Mile {mile} {bank}",
            }
            if coord:
                post["lng"], post["lat"] = coord
            all_posts.append(post)
            section_count += 1

        print(f"  {ch_slug}: {len(markers)} markers")

    print(f"{section_name}: {section_count} mile marker posts")

mile_posts = [p for p in all_posts if p["post_type"] == "mile-marker"]
print(f"\nTOTAL: {len(all_posts)} posts ({len(mile_posts)} mile markers)")
print(f"\nSample titles:")
for p in mile_posts[::max(1, len(mile_posts)//15)][:15]:
    print(f"  {p['title'][:65]}")

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(all_posts, f)
print(f"\nSaved: {OUTPUT}")
