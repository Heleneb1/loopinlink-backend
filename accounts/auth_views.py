import uuid

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserProfile
from accounts.throttling import LoginRateThrottle, RegisterRateThrottle


def set_jwt_cookies(response, access_token, refresh_token=None):
    """Injecte les cookies HttpOnly sécurisés dans la réponse HTTP."""
    jwt_settings = getattr(settings, 'SIMPLE_JWT', {})

    secure = jwt_settings.get('AUTH_COOKIE_SECURE', not settings.DEBUG)
    samesite = jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Lax')
    path = jwt_settings.get('AUTH_COOKIE_PATH', '/')

    access_lifetime = jwt_settings.get('ACCESS_TOKEN_LIFETIME')
    refresh_lifetime = jwt_settings.get('REFRESH_TOKEN_LIFETIME')

    access_max_age = int(access_lifetime.total_seconds()) if access_lifetime else None
    refresh_max_age = int(refresh_lifetime.total_seconds()) if refresh_lifetime else None

    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path=path,
        max_age=access_max_age,  #  le cookie survit à la fermeture du navigateur
    )

    if refresh_token:
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=secure,
            samesite=samesite,
            path=path,
            max_age=refresh_max_age,  #  idem, avec la durée du refresh token
        )

def delete_jwt_cookies(response):
    """Supprime les cookies JWT en respectant exactement les attributs utilisés à leur création."""
    jwt_settings = getattr(settings, 'SIMPLE_JWT', {})

    secure = jwt_settings.get('AUTH_COOKIE_SECURE', not settings.DEBUG)
    samesite = jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Lax')
    path = jwt_settings.get('AUTH_COOKIE_PATH', '/')

    for cookie_name in ('access_token', 'refresh_token'):
        response.set_cookie(
            key=cookie_name,
            value='',
            max_age=0,
            expires='Thu, 01 Jan 1970 00:00:00 GMT',
            httponly=True,
            secure=secure,
            samesite=samesite,
            path=path,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def register(request):
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')
    first_name = request.data.get('first_name', '').strip()
    last_name = request.data.get('last_name', '').strip()

    if not email or not password:
        return Response(
            {'error': 'Champs requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Utilisateur existe déjà'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        validate_password(password)
    except ValidationError as error:
        return Response(
            {'error': error.messages},
            status=status.HTTP_400_BAD_REQUEST
        )

    username = str(uuid.uuid4())[:8]

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    return Response({
        'message': 'Utilisateur créé',
        'id': user.id,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_email(request):
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    user = User.objects.filter(email=email).first()

    if not user:
        return Response(
            {'error': 'Identifiants incorrects'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=user.username, password=password)
    if not user:
        return Response(
            {'error': 'Identifiants incorrects'},
            status=status.HTTP_400_BAD_REQUEST
            )

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    response = Response({
        'message': 'Connexion réussie',
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username
        }
    }, status=status.HTTP_200_OK)

    set_jwt_cookies(response, access_token, refresh_token)
    return response


class CustomCookieTokenRefreshView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({'error': 'Refresh token manquant'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            if getattr(settings, 'SIMPLE_JWT', {}).get('ROTATE_REFRESH_TOKENS', False):
                refresh.blacklist()
                user_id = refresh.get('user_id')
                user = User.objects.get(id=user_id)
                new_refresh = RefreshToken.for_user(user)
                refresh_token = str(new_refresh)
                access_token = str(new_refresh.access_token)

            response = Response({'message': 'Token rafraîchi'}, status=status.HTTP_200_OK)
            set_jwt_cookies(response, access_token, refresh_token)
            return response
        except (TokenError, InvalidToken, User.DoesNotExist):
            return Response({'error': 'Token invalide ou expiré'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (TokenError, InvalidToken):
                pass

        response = Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)
        delete_jwt_cookies(response)

        return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_profile(request):
    user = request.user
    try:
        profile = user.userprofile
        avatar_url = profile.avatar.url if profile.avatar else None
    except UserProfile.DoesNotExist:
        avatar_url = None

    return Response({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "avatar": avatar_url,
        "is_staff": user.is_staff
    })
