"""Create a small image-only PDF so the OCR path can be demonstrated locally."""
from pathlib import Path
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "scanned_policy.pdf"
PNG = Path("/tmp/aia_scanned_policy.png")

def main():
    # Test fixture only: create a reproducible image-only PDF to exercise OCR.
    image = Image.new("RGB", (1600, 1100), "white")
    draw = ImageDraw.Draw(image)
    lines = [
        "Scanned Policy Fixture",
        "Security incidents must be reported to the Security team within one business day.",
        "Sensitive data must not be copied into logs or sample datasets.",
    ]
    for i, line in enumerate(lines):
        draw.text((80, 120 + i * 100), line, fill="black")
    image.save(PNG)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(OUT), pagesize=(612, 792))
    pdf.drawImage(str(PNG), 40, 80, width=532, height=632)
    pdf.save()
    print(f"Created {OUT}")

if __name__ == "__main__":
    main()
