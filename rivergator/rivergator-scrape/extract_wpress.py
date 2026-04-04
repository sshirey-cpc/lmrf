"""
Extract .wpress archive (All-in-One WP Migration format).

The .wpress format is a custom archive with a simple structure:
- Each entry: 255-byte filename (null-padded) + 14-byte size (null-padded) + 14-byte mtime (null-padded) + 4096-byte prefix/path (null-padded) + content

We only need:
- package.json (site metadata)
- database.sql (the full MySQL dump — this has ALL the content)
- A list of media files (we'll extract selectively)

Usage: python extract_wpress.py
"""

import os
import struct
import sys
import json

WPRESS_FILE = os.path.join(
    os.path.dirname(__file__),
    "www-rivergator-org-20260401-032955-wkzlexi6qgo1.wpress"
)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "wpress-extracted")

# Header sizes in .wpress format
HEADER_SIZE = 4377  # 255 (name) + 14 (size) + 14 (mtime) + 4096 (prefix) - 2 (adjustment)
NAME_LEN = 255
SIZE_LEN = 14
MTIME_LEN = 14
PREFIX_LEN = 4094


def extract_wpress(wpress_path, output_dir):
    """Extract files from .wpress archive."""
    os.makedirs(output_dir, exist_ok=True)

    file_size = os.path.getsize(wpress_path)
    print(f"Archive size: {file_size / (1024**3):.1f} GB")

    # Track what we find
    manifest = []
    extracted_count = 0
    skipped_count = 0

    with open(wpress_path, "rb") as f:
        while True:
            pos = f.tell()
            if pos >= file_size - HEADER_SIZE:
                break

            # Read header
            name_bytes = f.read(NAME_LEN)
            size_bytes = f.read(SIZE_LEN)
            mtime_bytes = f.read(MTIME_LEN)
            prefix_bytes = f.read(PREFIX_LEN)

            if not name_bytes or len(name_bytes) < NAME_LEN:
                break

            # Parse header
            name = name_bytes.split(b'\x00')[0].decode('utf-8', errors='replace')
            size_str = size_bytes.split(b'\x00')[0].decode('utf-8', errors='replace')
            prefix = prefix_bytes.split(b'\x00')[0].decode('utf-8', errors='replace')

            if not name or not size_str:
                break

            try:
                content_size = int(size_str)
            except ValueError:
                print(f"  Invalid size '{size_str}' for {name} at offset {pos}, stopping.")
                break

            full_path = os.path.join(prefix, name) if prefix else name

            entry = {
                "path": full_path,
                "size": content_size,
                "offset": pos,
            }
            manifest.append(entry)

            # Decide what to extract
            should_extract = False
            extract_reason = ""

            if name == "database.sql":
                should_extract = True
                extract_reason = "DATABASE"
            elif name == "package.json":
                should_extract = True
                extract_reason = "METADATA"
            elif name.endswith(('.sql', '.json')) and content_size < 100_000_000:
                should_extract = True
                extract_reason = "data file"
            elif full_path.startswith("uploads/") and name.endswith(('.pdf', '.PDF')):
                should_extract = True
                extract_reason = "PDF"
            # Skip large media for now — we'll catalog them
            else:
                skipped_count += 1
                if skipped_count <= 20 or skipped_count % 500 == 0:
                    size_label = f"{content_size:,}" if content_size < 1_000_000 else f"{content_size/1_000_000:.1f}M"
                    print(f"  skip [{skipped_count}]: {full_path} ({size_label})")

            if should_extract:
                out_path = os.path.join(output_dir, full_path)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                print(f"  EXTRACT [{extract_reason}]: {full_path} ({content_size:,} bytes)")

                with open(out_path, "wb") as out_f:
                    remaining = content_size
                    while remaining > 0:
                        chunk = f.read(min(remaining, 1_048_576))
                        if not chunk:
                            break
                        out_f.write(chunk)
                        remaining -= len(chunk)

                extracted_count += 1
                entry["extracted"] = True
            else:
                # Skip content
                f.seek(content_size, 1)
                entry["extracted"] = False

            # Progress
            pct = f.tell() / file_size * 100
            if extracted_count % 10 == 0 or should_extract:
                print(f"  Progress: {pct:.1f}% ({f.tell() / (1024**3):.2f} GB)")

    # Save manifest
    manifest_path = os.path.join(output_dir, "file-manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump({
            "total_files": len(manifest),
            "extracted": extracted_count,
            "skipped": skipped_count,
            "files": manifest,
        }, mf, indent=2)

    print(f"\n{'='*60}")
    print(f"Total files in archive: {len(manifest)}")
    print(f"Extracted: {extracted_count}")
    print(f"Skipped (media): {skipped_count}")
    print(f"Manifest saved to: {manifest_path}")

    # Summarize media by type
    extensions = {}
    for entry in manifest:
        ext = os.path.splitext(entry["path"])[1].lower()
        if ext not in extensions:
            extensions[ext] = {"count": 0, "total_bytes": 0}
        extensions[ext]["count"] += 1
        extensions[ext]["total_bytes"] += entry["size"]

    print(f"\nFile types in archive:")
    for ext, info in sorted(extensions.items(), key=lambda x: -x[1]["total_bytes"]):
        print(f"  {ext or '(none)':>8}: {info['count']:>5} files, {info['total_bytes']/(1024**2):>8.1f} MB")


if __name__ == "__main__":
    extract_wpress(WPRESS_FILE, OUTPUT_DIR)
