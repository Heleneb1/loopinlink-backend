from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    email = request.data.get("email")
    if not email:
        return Response({'message': 'Si un compte correspond à cette adresse, un lien de réinitialisation sera envoyé.'}, status=status.HTTP_200_OK)

# Une récupération de l'e-mail envoyé dans request.data.
    user = User.objects.filter(email=email).first()
    if user:
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        recipient_list=[user.email]
        from_email = None
        reset_url = f"https://loopinlink.com/reset-password/{uid}/{token}"

        message = (
            f"Bonjour {user.first_name},\n\n"
            "Suite à votre demande, veuillez trouver ci-dessous "
            "le lien pour réinitialiser votre mot de passe :\n\n"
            f"{reset_url}\n\n"
            "Ce lien est temporaire, il a une durée de 15 minutes.\n\n"
            "\n\n"
            "LoopInLink vous remercie et vous souhaite une bonne journée"

        )
        subject="Réinitialisation"
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
        )
    return Response({'message': 'Si un compte correspond à cette adresse, un lien de réinitialisation sera envoyé.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request, uidb64, token):
# 1. Décoder uidb64.
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
    except (
        TypeError,
        ValueError,
        OverflowError,
        UnicodeDecodeError,
    ):
        return Response(status=status.HTTP_400_BAD_REQUEST)

# 2. Retrouver l'utilisateur.
    try:
        user = User.objects.get(pk=uid)
    except User.DoesNotExist:
            return Response(
                {'detail': "Lien de réinitialisation invalide ou expiré"},
                status=status.HTTP_404_NOT_FOUND
            )
# 3. Vérifier le token avec check_token().
    token_generator = PasswordResetTokenGenerator()
    is_valid= token_generator.check_token(user,token)
    if not is_valid:
        return Response({"message" : "Lien de réinitialisation invalide ou expiré"}, status=status.HTTP_400_BAD_REQUEST)
# 4. Récupérer le nouveau mot de passe.
    password = request.data.get("password")

    confirm_password = request.data.get("confirm_password")
    if not confirm_password or not password or password != confirm_password:
        return Response({"message":"Les deux mots de passe sont obligatoires et doivent être identiques"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        validate_password(password, user)
    except ValidationError as error:
        return Response(
            {'error': 'password_invalid', 'details': error.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )
# 5. Le valider et l'enregistrer.
    user.set_password(password)
    user.save()
    return Response({"message":"Mot de passe modifié avec succès"}, status=status.HTTP_200_OK)



