import base64
import io

from PIL import Image, ImageDraw, ImageFont

MAX_SIZE = 1024   # côté maximum en pixels
QUALITY = 80      # 1-100 : plus bas = plus léger
WATERMARK_TEXTS = {
    "fr": "Généré par IA",
    "en": "AI Generated",
}
_exif = Image.Exif()
_exif[0x0131] = "LoopInLink AI"            # Software
_exif[0x010E] = "AI-generated image"       # ImageDescription
AI_EXIF = _exif.tobytes()

AI_XMP = b"""<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="" xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/">
   <Iptc4xmpExt:DigitalSourceType>http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia</Iptc4xmpExt:DigitalSourceType>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""


def optimize_image(image_b64: str) -> tuple[bytes, str]:
    """Décode l'image base64, la redimensionne et la convertit en WebP.
    Retourne (octets, type MIME)."""
    raw = base64.b64decode(image_b64)
    with Image.open(io.BytesIO(raw)) as img:
        img = img.convert("RGB")
        img.thumbnail((MAX_SIZE, MAX_SIZE))  # ne l'agrandit jamais
        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=QUALITY, method=6)
    return buffer.getvalue(), "image/webp"



def add_visible_label(image_bytes: bytes, lang: str = "en") -> bytes:
    watermark_text = WATERMARK_TEXTS.get(lang, WATERMARK_TEXTS["en"])
    with Image.open(io.BytesIO(image_bytes)) as src:
        image = src.convert("RGBA")

    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

   # Remplace l'ancienne ligne de police par ceci pour gérer les accents (é, à...) :
   # Réduire la taille de la police 0.02 au leu de 0.03
    try:
        font = ImageFont.truetype("arial.ttf", size=max(11, int(image.height * 0.02)))
    except IOError:
        font = ImageFont.load_default()

    # 2. Mesure du texte
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # 3. Calcul de la marge et de la position (haut à droite)
    # Position en haut à gauche x = margin
     # Réduire la taille de la marge 0.010 au lieu de 0.015
    margin = max(6, int(image.height * 0.010))
    x = image.width - w - margin * 3
    y = margin * 3

    # 4. Dessin de la pastille sombre de fond (badge)
    draw.rounded_rectangle(
        (x - margin, y - margin, x + w + margin, y + h + margin),
        radius=margin,
        fill=(0, 0, 0, 120),
    )

    # 5. Écriture du texte en blanc semi-transparent
    draw.text((x - bbox[0], y - bbox[1]), watermark_text, font=font, fill=(255, 255, 255, 235))

    # 6. Fusion des calques et export WebP
    result = Image.alpha_composite(image, layer).convert("RGB")
    buffer = io.BytesIO()
    result.save(buffer, format="WEBP", quality=80, method=6, exif=AI_EXIF, xmp=AI_XMP)
    return buffer.getvalue()
