"""Fix double-encoded UTF-8 characters across site HTML files."""
import glob
import os

# These are mojibake patterns (UTF-8 smart quotes read as latin-1 then re-encoded)
replacements = {
    "\u00e2\u0080\u0099": "'",      # right single quote
    "\u00e2\u0080\u0098": "'",      # left single quote
    "\u00e2\u0080\u009c": '"',      # left double quote
    "\u00e2\u0080\u009d": '"',      # right double quote
    "\u00e2\u0080\u0093": "\u2013", # en dash
    "\u00e2\u0080\u0094": "\u2014", # em dash
    "\u00e2\u0080\u00a6": "...",    # ellipsis
    "\u00c2\u00a0": " ",            # non-breaking space
}

files = glob.glob(r"C:\Users\scott\lmrf\website\site\*.html")
total_fixed = 0

for filepath in files:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    original = content
    for bad, good in replacements.items():
        count = content.count(bad)
        if count:
            content = content.replace(bad, good)
            print(f"  {os.path.basename(filepath)}: {count}x fixed")
            total_fixed += count

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

print(f"\nTotal fixes: {total_fixed}")
if total_fixed == 0:
    print("No mojibake found. Checking for literal display...")
    # Check for the literal displayed text
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if "â€™" in content or "â€œ" in content:
            print(f"  Found literal mojibake in {os.path.basename(filepath)}")
