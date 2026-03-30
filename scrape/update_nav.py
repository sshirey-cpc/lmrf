"""Update nav across all pages: rename Youth Programs → Programs, reorder dropdown, add Community Canoe."""
import glob
import re

files = glob.glob(r"C:\Users\scott\lmrf\website\site\*.html")
files += glob.glob(r"C:\Users\scott\lmrf\website\site\lmrf\**\index.html", recursive=True)

for filepath in files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # 1. Rename "Youth Programs" → "Programs" everywhere in nav
    content = content.replace(">Youth Programs<", ">Programs<")

    # 2. Reorder desktop nav folder items
    # Current order: School Programs, Summer Camps, River Stewards
    # New order: Community Canoe Trips, Summer Camps, School Programs, River Stewards

    # Desktop nav: Header-nav-folder-item links
    old_desktop = '''<a href="our-programs.html" class="Header-nav-folder-item" data-test="template-nav">School Programs</a>
<a href="summer-camps.html" class="Header-nav-folder-item" data-test="template-nav">Summer Camps</a>
<a href="river-stewards.html" class="Header-nav-folder-item" data-test="template-nav">River Stewards</a>'''

    new_desktop = '''<a href="community-canoe.html" class="Header-nav-folder-item" data-test="template-nav">Community Canoe Trips</a>
<a href="summer-camps.html" class="Header-nav-folder-item" data-test="template-nav">Summer Camps</a>
<a href="our-programs.html" class="Header-nav-folder-item" data-test="template-nav">School Programs</a>
<a href="river-stewards.html" class="Header-nav-folder-item" data-test="template-nav">River Stewards</a>'''

    content = content.replace(old_desktop, new_desktop)

    # 3. Mobile nav: folder items
    # The mobile nav has the items in a Mobile-overlay-folder div
    # Find and replace the folder items for the programs folder
    old_mobile_items = '''<a href="our-programs.html" class="Mobile-overlay-folder-item">
            School Programs
          </a><a href="summer-camps.html" class="Mobile-overlay-folder-item">
            Summer Camps
          </a><a href="river-stewards.html" class="Mobile-overlay-folder-item">
            River Stewards
          </a>'''

    new_mobile_items = '''<a href="community-canoe.html" class="Mobile-overlay-folder-item">
            Community Canoe Trips
          </a><a href="summer-camps.html" class="Mobile-overlay-folder-item">
            Summer Camps
          </a><a href="our-programs.html" class="Mobile-overlay-folder-item">
            School Programs
          </a><a href="river-stewards.html" class="Mobile-overlay-folder-item">
            River Stewards
          </a>'''

    content = content.replace(old_mobile_items, new_mobile_items)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated: {}".format(filepath.split("site\\")[-1] if "site\\" in filepath else filepath.split("site/")[-1]))

print("Done")
