import os
import uuid

from django.core.exceptions import ValidationError


def validate_image_size(value):

    """Bloque les fichiers de plus de 5 Mo"""

    max_size = 5 * 1024 * 1024

    if value.size > max_size:

        raise ValidationError("L'image dépasse la limite autorisée de 5 Mo.")



def validate_image_extension(value):

    """Vérifie l'extension du fichier (sécurité)"""

    ext = os.path.splitext(value.name)[1].lower()

    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']

    if ext not in valid_extensions:

        raise ValidationError("Format d'image non supporté. Utilise JPG, PNG, WEBP ou GIF.")



def rename_image(instance, filename):

    """

    Génère un nom de fichier anonyme et unique (UUID4).

    Détermine le dossier de destination selon la classe du modèle.

    """

    ext = os.path.splitext(filename)[1].lower()

    new_filename = f"{uuid.uuid4()}{ext}"



    model_name = instance.__class__.__name__



    if model_name == 'UserProfile':

        return os.path.join('avatars', new_filename)

    elif model_name == 'Design':

        return os.path.join('designs', 'previews', new_filename)



    return os.path.join('uploads', new_filename)

