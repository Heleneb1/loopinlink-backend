

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import UserSerializer


class AdminUserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self,request):
        users = User.objects.all()
        serializer = UserSerializer(
            users,
            many=True,
            context={'request': request}
            )

        return Response(serializer.data)

class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request, pk):
        user = get_object_or_404(User, id=pk)
        serializer = UserSerializer(
                user,
                many=False,
                context={'request': request}
                )
        return Response(serializer.data)



    def delete(self,request, pk):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    def patch(self,request, pk):
        user = get_object_or_404(User, pk=pk)

        serializer = UserSerializer(
            user,               # Instance existante
            data=request.data,  # Nouvelles données
            partial=True,       # Modification partielle
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)


    def put(self,request, pk):
        user = get_object_or_404(User, pk=pk)

        serializer = UserSerializer(
            user,               # Instance existante
            data=request.data,  # Nouvelles données
            partial=False,      # Modification complète
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def search(request):
    query = request.query_params.get('q', '')
    if not query:
        return Response([])

    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )

    serializer = UserSerializer(
        users,
        many=True,
        context={'request': request}
    )

    return Response(serializer.data)


