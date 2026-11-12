
from django.contrib.auth.models import User
from django.db import models
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):


        avatar = serializers.ImageField(
            source="userprofile.avatar",
            read_only=True
        )
        designs = serializers.PrimaryKeyRelatedField(
            many=True,
            read_only=True
        )
        class Meta :
            model = User
            fields = [
                "id",
                "username",
                "is_staff",
                "avatar",
                "designs"
            ]


