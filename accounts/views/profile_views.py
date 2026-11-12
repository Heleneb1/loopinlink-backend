import uuid

from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import UserProfile


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
