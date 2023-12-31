from django.urls import path
from accounts import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("users/register/", views.RegistrationView.as_view(), name="register"),
    path("users/login/", views.LoginView.as_view(), name="login"),
    path("refresh-token/", TokenRefreshView.as_view(), name="token_refresh"),
]
