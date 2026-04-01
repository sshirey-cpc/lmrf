"""Convert 'Who We Are' from a simple nav link to a dropdown with Mission, Our Story, Board Members."""
import glob

files = glob.glob(r"C:\Users\scott\lmrf\website\site\*.html")
files += glob.glob(r"C:\Users\scott\lmrf\website\site\lmrf\**\index.html", recursive=True)

updated = 0
for filepath in files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # DESKTOP NAV: Replace the simple "Who We Are" link with a folder dropdown
    # Current: <a href="who-we-are.html" class="Header-nav-item" data-test="template-nav">Who We Are</a>
    # Need: same structure as the Programs folder

    old_desktop = '<a href="who-we-are.html" class="Header-nav-item" data-test="template-nav">Who We Are</a>'
    new_desktop = '''<span class="Header-nav-item Header-nav-item--folder">
      <a href="who-we-are.html" class="Header-nav-folder-title" data-controller="HeaderNavFolderTouch" data-controllers-bound="HeaderNavFolderTouch">Who We Are</a>
      <span class="Header-nav-folder">
        <a href="who-we-are.html" class="Header-nav-folder-item" data-test="template-nav">Mission</a>
        <a href="our-story.html" class="Header-nav-folder-item" data-test="template-nav">Our Story</a>
        <a href="board-members.html" class="Header-nav-folder-item" data-test="template-nav">Board Members</a>
      </span>
    </span>'''
    content = content.replace(old_desktop, new_desktop)

    # MOBILE NAV: Replace the simple "Who We Are" mobile link with a folder button + items
    # Current: <a href="who-we-are.html" class="Mobile-overlay-nav-item">Who We Are</a> (or similar)
    # The mobile nav items are in Mobile-overlay-nav-item elements
    # We need to add a folder button like Programs has

    # Find and replace the mobile Who We Are link
    old_mobile = '''<a href="who-we-are.html" class="Mobile-overlay-nav-item">
            Who We Are
          </a>'''
    new_mobile = '''<button class="Mobile-overlay-nav-item Mobile-overlay-nav-item--folder" data-controller-folder-toggle="who-we-are">
            <span class="Mobile-overlay-nav-item--folder-label">Who We Are</span>
          </button>
          <div class="mobile-subnav">
            <a href="who-we-are.html">Mission</a>
            <a href="our-story.html">Our Story</a>
            <a href="board-members.html">Board Members</a>
          </div>'''
    content = content.replace(old_mobile, new_mobile)

    # Also handle blog post variant with relative paths
    old_blog_desktop = '<a href="../../../../../who-we-are/index.html" class="Header-nav-item" data-test="template-nav">Who We Are</a>'
    new_blog_desktop = '''<span class="Header-nav-item Header-nav-item--folder">
      <a href="../../../../../who-we-are/index.html" class="Header-nav-folder-title" data-controller="HeaderNavFolderTouch" data-controllers-bound="HeaderNavFolderTouch">Who We Are</a>
      <span class="Header-nav-folder">
        <a href="../../../../../who-we-are/index.html" class="Header-nav-folder-item" data-test="template-nav">Mission</a>
        <a href="../../../../../our-story/index.html" class="Header-nav-folder-item" data-test="template-nav">Our Story</a>
        <a href="../../../../../board-members/index.html" class="Header-nav-folder-item" data-test="template-nav">Board Members</a>
      </span>
    </span>'''
    content = content.replace(old_blog_desktop, new_blog_desktop)

    old_blog_mobile = '''<a href="../../../../../who-we-are/index.html" class="Mobile-overlay-nav-item">
            Who We Are
          </a>'''
    new_blog_mobile = '''<button class="Mobile-overlay-nav-item Mobile-overlay-nav-item--folder" data-controller-folder-toggle="who-we-are">
            <span class="Mobile-overlay-nav-item--folder-label">Who We Are</span>
          </button>
          <div class="mobile-subnav">
            <a href="../../../../../who-we-are/index.html">Mission</a>
            <a href="../../../../../our-story/index.html">Our Story</a>
            <a href="../../../../../board-members/index.html">Board Members</a>
          </div>'''
    content = content.replace(old_blog_mobile, new_blog_mobile)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        updated += 1

print(f"Updated {updated} files")
