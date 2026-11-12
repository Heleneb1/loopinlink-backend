from django.urls import path

from accounts.views.admin_views import (
    AdminUserDetailView,
    AdminUserListView,
    search,
)
from accounts.views.auth_views import (
    CustomCookieTokenRefreshView,
    LogoutView,
    login_email,
    register,
)
from accounts.views.password_views import password_reset_confirm, password_reset_request
from accounts.views.profile_views import get_my_profile
from accounts.views.views import upload_avatar

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_email),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('token/refresh/', CustomCookieTokenRefreshView.as_view(), name='token_refresh'),
    path('my-profile/', get_my_profile),
    path('avatar/', upload_avatar, name='upload_avatar'),
    path('users/', AdminUserListView.as_view(), name='admin-users'),
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('search/', search, name='search'),
    path('password-reset/',
        password_reset_request,
        name='reset-password'
        ),
    path(
        'password-reset-confirm/<str:uidb64>/<str:token>/',
        password_reset_confirm,
        name='password-reset-confirm'
        ),
]
