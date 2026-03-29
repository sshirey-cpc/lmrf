"""
Build static site from:
  1. WordPress XML export (content/structure)
  2. Mirror crawl (CSS, JS, images, fonts — exact Squarespace rendering)

Strategy: Use the mirrored homepage HTML as the template (header, nav, footer,
all CSS/JS includes), then inject XML content into each page.
"""

import os
import re
import shutil
import xml.etree.ElementTree as ET
from html import unescape

BASE_DIR = os.path.dirname(__file__)
MIRROR_DIR = os.path.join(BASE_DIR, "mirror")
OUTPUT_DIR = os.path.join(BASE_DIR, "static-site")
XML_FILE = os.path.join(BASE_DIR, "Squarespace-Wordpress-Export-03-23-2026.xml")

PAYPAL_DONATE = "https://www.paypal.com/donate?token=fPg9LuFa9121K_HDyZVHkUs4L6Xuwg3gKG4w_MSfisa1zzrcq-PtnNC190Fc_6-8vZjTLSvpb0Lmd7eL"

GOOGLE_CALENDAR = '<iframe src="https://calendar.google.com/calendar/embed?src=c_1ef3475e4f299305a635b1d46e77d427818dae70fffeed0e56306c2926e14bc1%40group.calendar.google.com&ctz=America%2FChicago" style="border: 0" width="800" height="600" frameborder="0" scrolling="no"></iframe>'


def main():
    print(f"Building static site...")
    print(f"  Mirror: {MIRROR_DIR}")
    print(f"  XML:    {XML_FILE}")
    print(f"  Output: {OUTPUT_DIR}")
    print()

    # Step 1: Copy the entire mirror as the base
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(MIRROR_DIR, OUTPUT_DIR)
    print(f"Copied mirror to {OUTPUT_DIR}")

    # Step 2: Parse XML for additional content/metadata
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    ns = {
        'wp': 'http://wordpress.org/export/1.2/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'dc': 'http://purl.org/dc/elements/1.1/',
    }

    items = root.findall('.//item')
    print(f"XML has {len(items)} items")

    # Step 3: Apply targeted modifications
    # 3a: Replace calendar page with Google Calendar embed
    apply_calendar_fix()

    # 3b: Fix all donate links to point to PayPal
    apply_donate_fix()

    # 3c: Wire contact form to mailto
    apply_contact_fix()

    # 3d: Fix any broken Squarespace-specific JS/dynamic elements
    apply_static_fixes()

    print("\nDone!")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Open {os.path.join(OUTPUT_DIR, 'index.html')} in a browser to preview.")


def find_html_files():
    """Find all HTML files in the output directory."""
    for dirpath, _, filenames in os.walk(OUTPUT_DIR):
        for f in filenames:
            if f.endswith(".html"):
                yield os.path.join(dirpath, f)


def apply_calendar_fix():
    """Replace the calendar page content with Google Calendar embed."""
    print("\n--- Calendar: replacing with Google Calendar embed ---")
    cal_dir = os.path.join(OUTPUT_DIR, "calendar")
    cal_index = os.path.join(cal_dir, "index.html")

    if not os.path.exists(cal_index):
        print("  WARNING: calendar/index.html not found")
        return

    with open(cal_index, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()

    # Find the main content area and replace the old events listing
    # The Squarespace calendar page has event listings in the main content
    # We'll look for the main content section and replace it

    # Strategy: find the content area between header/nav and footer, replace events
    # Look for the calendar-specific content wrapper
    patterns = [
        # Squarespace event list wrapper
        r'(<section[^>]*class="[^"]*events[^"]*"[^>]*>).*?(</section>)',
        # Generic main content area with event items
        r'(<div[^>]*class="[^"]*eventlist[^"]*"[^>]*>).*?(</div>\s*</div>)',
        # Broader: the main/content area
        r'(<main[^>]*>).*?(</main>)',
    ]

    replaced = False
    for pattern in patterns:
        if re.search(pattern, html, re.DOTALL | re.IGNORECASE):
            replacement = f'''\\1
<div style="max-width:900px; margin:40px auto; text-align:center; padding: 20px;">
  <h1 style="margin-bottom:30px;">Calendar</h1>
  {GOOGLE_CALENDAR}
</div>
\\2'''
            html = re.sub(pattern, replacement, html, count=1, flags=re.DOTALL | re.IGNORECASE)
            replaced = True
            break

    if not replaced:
        # Fallback: inject after the header/nav section
        # Find </header> or the nav closing and inject after
        inject_point = html.find('</header>')
        if inject_point == -1:
            inject_point = html.find('</nav>')
        if inject_point != -1:
            # Find the end of that tag
            inject_point = html.find('>', inject_point) + 1
            calendar_html = f'''
<div style="max-width:900px; margin:60px auto; text-align:center; padding: 20px;">
  <h1 style="font-size:2rem; font-weight:300; text-transform:uppercase; letter-spacing:3px; margin-bottom:40px;">Calendar</h1>
  {GOOGLE_CALENDAR}
</div>
'''
            # Find the footer and insert before it
            footer_pos = html.find('<footer')
            if footer_pos == -1:
                footer_pos = html.find('class="Footer')
            if footer_pos != -1:
                # Remove everything between header and footer (the old content)
                html = html[:inject_point] + calendar_html + html[footer_pos:]
                replaced = True

    if replaced:
        with open(cal_index, "w", encoding="utf-8") as f:
            f.write(html)
        print("  Replaced calendar page content with Google Calendar embed")
    else:
        print("  WARNING: Could not find content area to replace")


def apply_donate_fix():
    """Update all donate links across the site to point to PayPal."""
    print("\n--- Donate: updating all donate links ---")
    count = 0
    for filepath in find_html_files():
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()

        original = html

        # Replace donate page links in nav with PayPal
        # Match links that have "Donate" text and point to the donate page
        html = re.sub(
            r'(<a[^>]*href=")(?:[^"]*donate[^"]*index\.html|/donate/?)"',
            f'\\1{PAYPAL_DONATE}" target="_blank" rel="noopener"',
            html,
            flags=re.IGNORECASE,
        )

        # Also add target="_blank" to PayPal links if not present
        html = re.sub(
            r'(<a[^>]*href="' + re.escape(PAYPAL_DONATE) + r'")',
            lambda m: m.group(0) if 'target=' in m.group(0) else m.group(0) + ' target="_blank" rel="noopener"',
            html,
        )

        if html != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            count += 1

    print(f"  Updated donate links in {count} files")


def apply_contact_fix():
    """Wire the contact form to mailto:info@lowermsfoundation.org."""
    print("\n--- Contact: wiring form to email ---")
    contact_index = os.path.join(OUTPUT_DIR, "contact", "index.html")

    if not os.path.exists(contact_index):
        print("  WARNING: contact/index.html not found")
        return

    with open(contact_index, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()

    # Add a mailto form handler script before </body>
    contact_script = '''
<script>
(function() {
  // Find any form on the contact page
  var forms = document.querySelectorAll('form');
  forms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var data = new FormData(form);
      var name = '', email = '', message = '', subject = 'Website Contact';
      for (var pair of data.entries()) {
        var key = pair[0].toLowerCase();
        var val = pair[1];
        if (key.includes('name') && !key.includes('email')) name = val;
        else if (key.includes('email')) email = val;
        else if (key.includes('message') || key.includes('comment') || key.includes('text')) message = val;
        else if (key.includes('subject')) subject = val;
      }
      if (!subject && name) subject = 'Website Contact from ' + name;
      var body = '';
      if (name) body += 'From: ' + name + '\\n';
      if (email) body += 'Email: ' + email + '\\n\\n';
      body += message || '';
      window.location.href = 'mailto:info@lowermsfoundation.org?subject=' +
        encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      // Show feedback
      var btn = form.querySelector('input[type=submit], button[type=submit], .form-submit-button');
      if (btn) {
        btn.value = 'Opening email client...';
        btn.textContent = 'Opening email client...';
      }
    });
  });
})();
</script>
'''

    if '</body>' in html:
        html = html.replace('</body>', contact_script + '\n</body>')
    elif '</html>' in html:
        html = html.replace('</html>', contact_script + '\n</html>')

    with open(contact_index, "w", encoding="utf-8") as f:
        f.write(html)
    print("  Added mailto form handler to contact page")


def apply_static_fixes():
    """Fix Squarespace-specific issues for static hosting."""
    print("\n--- Static fixes ---")
    count = 0

    for filepath in find_html_files():
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()

        original = html

        # Remove Squarespace analytics/tracking scripts that will fail
        # Remove inline scripts that try to load from squarespace.com dynamically
        html = re.sub(
            r'<script[^>]*>\s*Static\.SQUARESPACE_CONTEXT\s*=.*?</script>',
            '', html, flags=re.DOTALL
        )

        # Remove broken form action URLs that point to Squarespace backend
        html = re.sub(
            r'action="https?://[^"]*squarespace[^"]*"',
            'action="#"',
            html,
            flags=re.IGNORECASE,
        )

        # Fix any remaining absolute URLs to the site that should be relative
        # (the mirror script should have caught most of these, but just in case)
        html = html.replace('https://www.lowermsfoundation.org/', '/')
        html = html.replace('http://www.lowermsfoundation.org/', '/')

        if html != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            count += 1

    print(f"  Applied static fixes to {count} files")


if __name__ == "__main__":
    main()
