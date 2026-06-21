from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium
from PIL import Image, ImageDraw


root = Path(__file__).resolve().parents[2]
pdf_path = root / "output" / "pdf" / "guia_logica_simulacion_polideportivo_alberdi.pdf"
out_dir = root / "tmp" / "pdfs" / "render"
out_dir.mkdir(parents=True, exist_ok=True)

pdf = pdfium.PdfDocument(pdf_path)
images = []
for i, page in enumerate(pdf):
    image = page.render(scale=1.6).to_pil().convert("RGB")
    image.save(out_dir / f"pagina_{i + 1}.png")
    images.append(image)

thumb_width = 390
thumbs = []
for image in images:
    ratio = thumb_width / image.width
    thumbs.append(image.resize((thumb_width, int(image.height * ratio))))

gap = 18
cols = 2
rows = (len(thumbs) + cols - 1) // cols
cell_h = max(im.height for im in thumbs) + 35
sheet = Image.new("RGB", (cols * thumb_width + (cols + 1) * gap, rows * cell_h + gap), "#dce3e8")
draw = ImageDraw.Draw(sheet)
for i, thumb in enumerate(thumbs):
    x = gap + (i % cols) * (thumb_width + gap)
    y = gap + (i // cols) * cell_h + 22
    draw.text((x, y - 17), f"Pagina {i + 1}", fill="#173B57")
    sheet.paste(thumb, (x, y))
sheet.save(out_dir / "contacto.png")

with pdfplumber.open(pdf_path) as doc:
    texts = [(page.extract_text() or "") for page in doc.pages]
    total_chars = sum(len(text) for text in texts)
    print(f"paginas={len(doc.pages)} caracteres={total_chars}")
    for i, text in enumerate(texts, 1):
        print(f"pagina_{i}: caracteres={len(text)} ultima_linea={text.splitlines()[-1] if text.splitlines() else '-'}")

print(out_dir / "contacto.png")
