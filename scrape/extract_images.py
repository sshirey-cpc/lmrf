import fitz  # PyMuPDF
import os

doc = fitz.open(os.path.expanduser("~/Downloads/Summer-Camp-Application-2019.pdf"))

os.makedirs(os.path.expanduser("~/lmrf/scrape/pdf-images"), exist_ok=True)

for page_num in range(len(doc)):
    page = doc[page_num]
    images = page.get_images(full=True)
    for img_idx, img in enumerate(images):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        w = base_image["width"]
        h = base_image["height"]
        filename = f"page{page_num+1}_img{img_idx+1}.{image_ext}"
        filepath = os.path.expanduser(f"~/lmrf/scrape/pdf-images/{filename}")
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        print(f"Extracted: {filename} ({w}x{h})")

doc.close()
