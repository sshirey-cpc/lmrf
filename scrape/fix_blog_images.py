"""Fix all Squarespace CDN image references in blog posts."""
import glob
import re

blog_files = glob.glob(r"C:\Users\scott\lmrf\website\site\lmrf\**\index.html", recursive=True)
fixed = 0

for filepath in blog_files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Replace ALL references to squarespace-cdn paths with /images/FILENAME
    content = re.sub(
        r'(?:\.\./)*(?:assets/)?images\.squarespace-cdn\.com/([A-Za-z0-9_\-]+\.(?:jpg|jpeg|png|gif|JPG|JPEG|PNG))',
        r'/images/\1',
        content,
    )

    # Also handle content/v1/ paths from squarespace-cdn (meta tags, og:image etc)
    content = re.sub(
        r'(?:\.\./)*(?:assets/)?images\.squarespace-cdn\.com/content/v1/[^"]+',
        '/images/LMRF_social_media_icon-03.png',
        content,
    )

    # Clean up srcset entries - deduplicate repeated /images/FILE Nw entries
    def simplify_srcset(match):
        srcset = match.group(1)
        imgs = re.findall(r'/images/([A-Za-z0-9_\-]+\.(?:jpg|jpeg|png|gif|JPG|JPEG|PNG))', srcset)
        if imgs:
            return 'srcset="/images/{}"'.format(imgs[0])
        return match.group(0)

    content = re.sub(r'srcset="([^"]*(?:/images/)[^"]*)"', simplify_srcset, content)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        remaining = content.count("squarespace-cdn")
        print("Fixed: {} (remaining cdn refs: {})".format(filepath.split("site\\")[1], remaining))
        fixed += 1

print("Total: {} files fixed".format(fixed))
