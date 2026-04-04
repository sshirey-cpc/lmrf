#!/bin/bash
# Build the Rivergator Paddler's Guide as a professional PDF
# Requires: pandoc, xelatex (via MiKTeX or TeX Live)
#
# Usage: bash build-book.sh
#        bash build-book.sh draft    (adds DRAFT watermark)

set -e

BOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$BOOK_DIR/../book-preview"
OUTPUT_FILE="$OUTPUT_DIR/rivergator-paddlers-guide.pdf"

# Check dependencies
if ! command -v pandoc &> /dev/null; then
    echo "ERROR: pandoc not found. Install with: winget install JohnMacFarlane.Pandoc"
    exit 1
fi

echo "=== Building The Rivergator Paddler's Guide ==="
echo ""

# Assemble the book in order
# Front matter → Paddler's Guide sections → River Log sections → Reference Appendix
CHAPTERS=(
    # Front Matter
    "INTRODUCTION.md"

    # Paddler's Guide
    "paddlers-guide/foreword.md"
    "paddlers-guide/safety.md"
    "paddlers-guide/how-to-paddle-the-big-river.md"
    "paddlers-guide/when-to-paddle-the-big-river.md"

    # River Log - Section Intros + Chapters (upstream to downstream)
    "river-log/stlouis-to-caruthersville/stl-car-preamble.md"
    "river-log/stlouis-to-caruthersville/intro-st-car.md"
    "river-log/stlouis-to-caruthersville/st-louis.md"
    "river-log/stlouis-to-caruthersville/stl-cairo.md"
    "river-log/stlouis-to-caruthersville/cairo-caruthersville.md"
    "river-log/stlouis-to-caruthersville/stl-car-appendix.md"

    "river-log/caruthersville-to-memphis/intro.md"
    "river-log/caruthersville-to-memphis/caruthersville-to-osceola.md"
    "river-log/caruthersville-to-memphis/osceola-to-shelby-forest.md"
    "river-log/caruthersville-to-memphis/shelby-forest-to-memphis.md"

    "river-log/memphis-to-helena/introduction.md"
    "river-log/memphis-to-helena/memphis-to-tunica.md"
    "river-log/memphis-to-helena/tunica-to-helena.md"
    "river-log/memphis-to-helena/helena-to-friars.md"
    "river-log/memphis-to-helena/appendix.md"

    "river-log/helena-to-greenville/helena-to-island-63.md"
    "river-log/helena-to-greenville/island-63-to-hurricane.md"
    "river-log/helena-to-greenville/hurricane-to-rosedale.md"
    "river-log/helena-to-greenville/rosedale-to-arkansas-city.md"
    "river-log/helena-to-greenville/st-francis-to-helena.md"

    "river-log/greenville-to-vicksburg/introductiongtov.md"
    "river-log/greenville-to-vicksburg/greenville-to-lake-providence.md"
    "river-log/greenville-to-vicksburg/lake-providence-to-vicksburg.md"

    "river-log/vicksburg-to-baton-rouge/introv-b.md"
    "river-log/vicksburg-to-baton-rouge/vicksburg-to-natchez.md"
    "river-log/vicksburg-to-baton-rouge/natchez-to-stfrancisville.md"
    "river-log/vicksburg-to-baton-rouge/stfrancisville-to-baton-rouge.md"
    "river-log/vicksburg-to-baton-rouge/appendixv-b.md"

    "river-log/atchafalaya-river/atchafalaya_upper.md"
    "river-log/atchafalaya-river/atchafalaya_lower.md"
    "river-log/atchafalaya-river/appendixar.md"

    "river-log/baton-rouge-to-venice/introbrtov.md"
    "river-log/baton-rouge-to-venice/baton-rouge-to-new-orleans.md"
    "river-log/baton-rouge-to-venice/new-orleans-to-venice.md"
    "river-log/baton-rouge-to-venice/appendixbr-v.md"

    "river-log/birdsfoot-delta/introbd.md"
    "river-log/birdsfoot-delta/venice-to-gulf.md"
    "river-log/birdsfoot-delta/appendixbd.md"

    # Back Matter
    "SECTION_REFERENCE.md"
)

# Build file list (only include files that exist)
INPUT_FILES=()
MISSING=()
for ch in "${CHAPTERS[@]}"; do
    if [ -f "$BOOK_DIR/$ch" ]; then
        INPUT_FILES+=("$BOOK_DIR/$ch")
    else
        MISSING+=("$ch")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "Note: ${#MISSING[@]} files not found (skipped):"
    for m in "${MISSING[@]}"; do
        echo "  - $m"
    done
    echo ""
fi

echo "Assembling ${#INPUT_FILES[@]} chapters..."

# Set draft watermark if requested
DRAFT_OPTS=""
if [ "$1" = "draft" ]; then
    DRAFT_OPTS="-V draft=true"
    echo "Adding DRAFT watermark..."
fi

# Build with Pandoc
pandoc \
    "${INPUT_FILES[@]}" \
    --defaults="$BOOK_DIR/book-defaults.yaml" \
    $DRAFT_OPTS \
    -o "$OUTPUT_FILE"

echo ""
echo "=== Done! ==="
echo "Output: $OUTPUT_FILE"
echo "Pages: $(pdfinfo "$OUTPUT_FILE" 2>/dev/null | grep Pages | awk '{print $2}' || echo '(install poppler-utils to see page count)')"
