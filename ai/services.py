import json
import logging
import time

import requests
from django.conf import settings
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class AIUnavailable(APIException):
    status_code = 503
    default_detail = "Service IA temporairement indisponible."
    default_code = "ai_unavailable"


class GeminiTextProvider:
    RETRY_STATUS = {429, 500, 503}
    MAX_ATTEMPTS = 3

    def _post(self, payload: dict) -> dict:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent"
        )
        headers = {"x-goog-api-key": settings.GEMINI_API_KEY}

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=60)
                if r.status_code in self.RETRY_STATUS and attempt < self.MAX_ATTEMPTS:
                    time.sleep(attempt * 2)
                    continue
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                response = getattr(e, "response", None)
                status = response.status_code if response is not None else None
                retryable = status is None or status in self.RETRY_STATUS

                if not retryable or attempt == self.MAX_ATTEMPTS:
                    logger.error(
                        "Erreur Gemini (%s) : %s",
                        status,
                        response.text[:300] if response is not None else e,
                    )
                    raise AIUnavailable()
                time.sleep(attempt * 2)

    @staticmethod
    def _extract_text(data: dict) -> str:
        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError):
            logger.exception("Réponse Gemini inattendue")
            raise AIUnavailable()

    def generate(self, prompt: str) -> str:
        data = self._post(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 2048},
            }
        )
        return self._extract_text(data)

    def generate_json(self, prompt: str, schema: dict, max_tokens: int = 2048):
        data = self._post(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "responseMimeType": "application/json",
                    "responseJsonSchema": schema,
                },
            }
        )
        try:
            return json.loads(self._extract_text(data))
        except json.JSONDecodeError:
            logger.exception("JSON Gemini invalide")
            raise AIUnavailable()

class CloudflareImageProvider:
    def generate(self, prompt: str) -> str:
        """Retourne l'image en base64."""
        url = (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{settings.CF_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        )
        try:
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {settings.CF_API_TOKEN}"},
                json={"prompt": prompt, "steps": 4},
                timeout=60,
            )
            r.raise_for_status()
            return r.json()["result"]["image"]
        except (requests.RequestException, KeyError):
            logger.exception("Erreur Cloudflare")
            raise AIUnavailable()


text_provider = GeminiTextProvider()
image_provider = CloudflareImageProvider()
