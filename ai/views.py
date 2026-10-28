import base64

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from .carousel import CAROUSEL_SCHEMA, build_prompt, clean_slides
from .image_prompt import to_image_prompt
from .quotas import check_global_quota
from .services import AIUnavailable, image_provider, text_provider
from .utils import add_visible_label, optimize_image


class TextThrottle(UserRateThrottle):
    scope = "ai_text"
    rate = "30/hour"


class ImageThrottle(UserRateThrottle):
    scope = "ai_image"
    rate = "10/hour"


class CarouselThrottle(UserRateThrottle):
    scope = "ai_carousel"
    rate = "10/hour"


class PromptSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=1000)


class CarouselSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=500)
    slides = serializers.IntegerField(min_value=3, max_value=10, default=6)
    tone = serializers.ChoiceField(
        choices=["professional", "friendly", "inspiring", "direct"],
        default="professional",
    )
    language = serializers.ChoiceField(choices=["fr", "en"], default="fr")


class GenerateTextView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [TextThrottle]

    def post(self, request):
        serializer = PromptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prompt = serializer.validated_data["prompt"]
        check_global_quota("text")
        text = text_provider.generate(f"{prompt}\n\nRéponds en texte brut, sans markdown.")
        return Response({"text": text})


class GenerateImageView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ImageThrottle]

    def post(self, request):
        serializer = PromptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        check_global_quota("image")
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'fr')
        lang = 'fr' if 'fr' in accept_language.lower() else 'en'
        image_b64 = image_provider.generate(serializer.validated_data["prompt"])
        data, mime = optimize_image(image_b64)
        data = add_visible_label(data, lang=lang)
        encoded = base64.b64encode(data).decode()
        return Response({"image": f"data:{mime};base64,{encoded}"})

class GenerateCarouselView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [CarouselThrottle]

    def post(self, request):
        serializer = CarouselSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        check_global_quota("text")
        raw = text_provider.generate_json(
            build_prompt(d["topic"], d["slides"], d["tone"], d["language"]),
            CAROUSEL_SCHEMA,
        )
        slides = clean_slides(raw, d["slides"])
        if not slides:
            raise AIUnavailable()
        return Response({"slides": slides})

class ImprovePromptView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [TextThrottle]

    def post(self, request):
        serializer = PromptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        check_global_quota("text")
        improved = to_image_prompt(serializer.validated_data["prompt"])[:1000]
        if not improved:
            raise AIUnavailable()
        return Response({"prompt": improved})
