from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DesignViewSet

router = DefaultRouter()
router.register(r'', DesignViewSet, basename='design')

urlpatterns = [
    path('', include(router.urls)),
]
