"""
Authentication URLs
"""
from django.urls import path
from . import auth_views

urlpatterns = [
    # Custom endpoints
    path('login/', auth_views.login, name='auth_login'),
    path('register/', auth_views.register, name='auth_register'),
    path('me/', auth_views.me, name='auth_me'),
]

# Add JWT endpoints if package is available
try:
    from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
    urlpatterns += [
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    ]
except ImportError:
    # JWT not installed
    pass
