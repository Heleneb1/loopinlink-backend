from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Classe d'authentification personnalisée pour DRF / SimpleJWT.
    Extrait le jeton JWT d'accès en priorité depuis le cookie HttpOnly 'access_token',
    puis retombe sur l'en-tête HTTP 'Authorization: Bearer <token>' standard si absent.
    """

    def authenticate(self, request):
        # 1. Tentative d'extraction depuis les cookies
        raw_token = request.COOKIES.get('access_token')

        # 2. Si présent dans le cookie, valider et retourner le couple (user, validated_token)
        if raw_token is not None:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token

        # 3. Sinon, fallback sur l'en-tête Authorization Bearer standard
        return super().authenticate(request)
