from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from designs.utils import process_image, validate_image_file

from .models import UserProfile


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_avatar(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    avatar_file = request.FILES.get('avatar')
    if not avatar_file:
        return Response({"error": "No file"}, status=status.HTTP_400_BAD_REQUEST)

    error = validate_image_file(avatar_file)
    if error:
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

    if profile.avatar:
        profile.avatar.delete(save=False)

    processed = process_image(avatar_file)
    profile.avatar = processed
    profile.save()

    return Response({"avatar_url": profile.avatar.url}, status=status.HTTP_200_OK)
