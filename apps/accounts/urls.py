from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import EmailOrUsernameTokenObtainPairView, UserMeView

urlpatterns = [
    path("token/", EmailOrUsernameTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", UserMeView.as_view(), name="user_me"),
]
