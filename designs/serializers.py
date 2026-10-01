import base64
import uuid

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Design, DesignImage


class DesignImageSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = DesignImage
        fields = ["element_id", "file_url"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class DesignSerializer(serializers.ModelSerializer):
    preview_url = serializers.SerializerMethodField()
    images = DesignImageSerializer(
        source="designimage_set", many=True, read_only=True
    )

    class Meta:
        model = Design
        fields = [
            "id",
            "type",
            "data",
            "name",
            "images",
            "preview_image",
            "preview_url",
            "created_at",
            "updated_at",
            "is_template",
        ]

    def get_preview_url(self, obj):
        request = self.context.get("request")
        if obj.preview_image and request:
            return request.build_absolute_uri(obj.preview_image.url)
        return None

    def validate(self, attrs):
        data_field = attrs.get("data", {})
        request = self.context.get("request")
        print("\n--- DEBUG STRUCTURE JSON ---")
        print(f"TYPE DE DESIGN : {attrs.get('type')}")
        print(f"CONTENU DE DATA : {data_field}")
        print("-----------------------------\n")

        if not data_field or "slides" not in data_field:
            return attrs

        # Récupère dynamiquement le type actuel ('carousel', 'banner', ou 'feature')
        design_type = attrs.get(
            "type", self.instance.type if self.instance else "carousel"
        )

        # Fonction locale pour convertir le Base64 en URL de fichier physique
        def convert_base64_to_url(src_value, element_id):
            if src_value and src_value.startswith("data:image"):
                try:
                    format_str, imgstr = src_value.split(";base64,")
                    ext = format_str.split("/")[-1].split("+")[0]
                    file_name = f"{uuid.uuid4()}.{ext}"
                    image_file = ContentFile(
                        base64.b64decode(imgstr), name=file_name
                    )

                    # Instanciation de l'image liée au design actuel (si en update)
                    design_image = DesignImage(
                        design=self.instance,
                        element_id=element_id,
                        file=image_file,
                    )

                    # On remplit le champ 'type' obligatoire s'il existe sur DesignImage
                    if hasattr(design_image, "type"):
                        design_image.type = design_type

                    design_image.save()
                    return (
                        request.build_absolute_uri(design_image.file.url)
                        if request
                        else design_image.file.url
                    )
                except Exception as e:
                    print(f"!!! ERREUR CRITIQUE BASE64 : {str(e)}")
            return src_value

        # Traitement de toutes les slides du JSON (commun aux 3 types de designs)
        for slide in data_field.get("slides", []):

            # 1. Traitement du Fond (backgroundImage)
            bg_image = slide.get("backgroundImage")
            if bg_image and isinstance(bg_image, dict):
                bg_url = bg_image.get("url", "")
                slide_id = slide.get("id", str(uuid.uuid4()))
                bg_image["url"] = convert_base64_to_url(
                    bg_url, f"bg_{slide_id}"
                )

            # 2. Traitement des images superposées (Stickers, formes...)
            for img in slide.get("images", []):
                if isinstance(img, dict):
                    src_value = img.get("src", "")
                    img_id = img.get("id", str(uuid.uuid4()))
                    img["src"] = convert_base64_to_url(src_value, img_id)

        attrs["data"] = data_field
        return attrs

    def create(self, validated_data):
        design = super().create(validated_data)
        self._link_images(design)
        return design

    def update(self, instance, validated_data):
        design = super().update(instance, validated_data)
        self._link_images(design)
        return design

    def _link_images(self, design):
        """Associe rétroactivement les images créées pendant le validate()

        lors du tout premier enregistrement (POST).
        """
        data_field = design.data
        if data_field and "slides" in data_field:
            element_ids = []
            for slide in data_field.get("slides", []):
                if slide.get("id"):
                    element_ids.append(f"bg_{slide.get('id')}")
                for img in slide.get("images", []):
                    if img.get("id"):
                        element_ids.append(img.get("id"))

            if element_ids:
                DesignImage.objects.filter(
                    element_id__in=element_ids, design__isnull=True
                ).update(design=design)


class EmailTokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable")

        user = authenticate(username=user.username, password=password)

        if not user:
            raise serializers.ValidationError("Mot de passe incorrect")

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["is_staff"] = user.is_staff

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
