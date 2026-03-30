"""Reorder blog posts on the blog listing page."""
import re

with open(r"C:\Users\scott\lmrf\website\site\blog.html", "r", encoding="utf-8") as f:
    content = f.read()

# Extract all article elements
articles = []
pattern = r'(<article[^>]*>.*?</article>)'
matches = list(re.finditer(pattern, content, re.DOTALL))

for m in matches:
    html = m.group(1)
    # Extract title
    title_match = re.search(r'data-content-field="title">([^<]+)<', html)
    title = title_match.group(1) if title_match else "Unknown"
    articles.append({"html": html, "title": title, "start": m.start(), "end": m.end()})

print("Current order:")
for i, a in enumerate(articles):
    print(f"  {i+1}. {a['title']}")

# Define desired order
desired_order = [
    "Meet the Disciples",
    "Day 1: Helena to Island 62",
    "Day 2: Island 62 to Island 64",
    "Day 3: Island 64 to Island 67",
    "Day 4: Island 67 to Smith's Point",
    "Day 5: Smith's Point to Home",
    "Summer Camp Video",
    "Creating a New Generation of Stewards",
    "Day 1: No Fear",
    "Day 2: Challenge",
    "Day 3: Leadership",
    "Day 4: Genesis",
    "Day 5: Circles and Boxes",
    "Delta Adventure Day Camp",
]

# Build lookup
article_map = {}
for a in articles:
    article_map[a["title"]] = a

# Reorder
reordered = []
for title in desired_order:
    if title in article_map:
        reordered.append(article_map[title])
    else:
        # Try partial match
        for a in articles:
            if title.lower() in a["title"].lower():
                reordered.append(a)
                break
        else:
            print(f"  WARNING: Could not find '{title}'")

# Add any articles not in our desired order
used_titles = {a["title"] for a in reordered}
for a in articles:
    if a["title"] not in used_titles:
        reordered.append(a)
        print(f"  Added unmatched: {a['title']}")

print("\nNew order:")
for i, a in enumerate(reordered):
    print(f"  {i+1}. {a['title']}")

# Now rebuild the content
# Find the region containing all articles
first_start = articles[0]["start"]
last_end = articles[-1]["end"]

# Get the separator between articles (whitespace/newlines)
# Extract what's between articles[0] end and articles[1] start
separator = "\n    "

# Build new articles section with updated article-index
new_articles_html = ""
for i, a in enumerate(reordered):
    html = a["html"]
    # Update article-index
    html = re.sub(r'article-index-\d+', f'article-index-{i+1}', html)
    new_articles_html += html + separator

# Replace the old articles section
new_content = content[:first_start] + new_articles_html.rstrip() + content[last_end:]

with open(r"C:\Users\scott\lmrf\website\site\blog.html", "w", encoding="utf-8") as f:
    f.write(new_content)

print("\nBlog reordered and saved.")
