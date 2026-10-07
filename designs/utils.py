import io
import uuid

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 Mo (fichier envoyé)
MAX_IMAGE_PIXELS = 50_000_000      # 50 mégapixels max (protection contre les "decompression bombs")
MAX_DIMENSION = 2000               # plus grand côté par défaut, en pixels
WEBP_QUALITY = 85
ALLOWED_CONTENT_TYPES = {'image/png', 'image/jpeg', 'image/webp'}


def validate_image_file(file):
    if file.size > MAX_IMAGE_SIZE:
        return 'Fichier trop volumineux (10 Mo max).'
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return 'Type de fichier non autorisé.'
    try:
        img = Image.open(file)
        width, height = img.size
        if width * height > MAX_IMAGE_PIXELS:
            return 'Image trop grande (dimensions excessives).'
        img.verify()
        file.seek(0)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        return 'Fichier image invalide ou corrompu.'
    return None


def _has_transparency(img):
    """True si l'image RGBA contient au moins un pixel non opaque."""
    if img.mode != 'RGBA':
        return False
    alpha_min, _ = img.getchannel('A').getextrema()
    return alpha_min < 255


def process_image(image_file, max_dimension=MAX_DIMENSION, quality=WEBP_QUALITY, square=False):
    """
    Allège l'image avant stockage :
    - corrige l'orientation EXIF (photos de téléphone)
    - redimensionne à max_dimension px max, sans jamais agrandir
    - square=True : recadre au centre en carré (utile pour les avatars)
    - conserve la transparence si elle existe, sinon repasse en RGB (plus léger)
    - encode en WebP
    Retourne un ContentFile avec un nom UUID généré côté serveur.
    """
    image_file.seek(0)
    img = Image.open(image_file)

    # Orientation EXIF : sans ça, certaines photos s'affichent tournées
    img = ImageOps.exif_transpose(img)

    # Normaliser le mode (gère aussi les PNG en palette avec transparence)
    img = img.convert('RGBA')

    if square:
        side = min(max_dimension, *img.size)  # ne grossit jamais l'image
        img = ImageOps.fit(img, (side, side), Image.Resampling.LANCZOS)
    else:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    # Sans transparence réelle, RGB donne un fichier plus petit
    if not _has_transparency(img):
        img = img.convert('RGB')

    buffer = io.BytesIO()
    img.save(buffer, format='WEBP', quality=quality, method=4)

    return ContentFile(buffer.getvalue(), name=f'{uuid.uuid4().hex}.webp')
