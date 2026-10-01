import io

from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 Mo
ALLOWED_CONTENT_TYPES = {'image/png', 'image/jpeg', 'image/webp'}


def validate_image_file(file):
    if file.size > MAX_IMAGE_SIZE:
        return 'Fichier trop volumineux (10 Mo max).'
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return 'Type de fichier non autorisé.'
    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)
    except (UnidentifiedImageError, OSError):
        return 'Fichier image invalide ou corrompu.'
    return None


def process_image(image_file):
    img = Image.open(image_file)

    # Si l'image est en mode RGBA (transparence), on la garde telle quelle
    # Si on la convertit en RGB, le canal alpha devient blanc !
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    buffer = io.BytesIO()

    # FORCE LE FORMAT PNG ICI
    img.save(buffer, format='PNG', optimize=True)

    return ContentFile(buffer.getvalue(), name=image_file.name)
