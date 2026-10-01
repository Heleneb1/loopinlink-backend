from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .auth_views import LogoutView, get_my_profile, login_email, register
from .views import upload_avatar

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_email),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('my-profile/', get_my_profile),
    path('avatar/', upload_avatar, name='upload_avatar'),

]
