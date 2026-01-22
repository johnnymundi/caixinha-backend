from django.urls import path
from .views import LoginView, MeView, LogoutView, RefreshView, RegisterView, PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    path("login/", LoginView.as_view()),
    path("me/", MeView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("register/", RegisterView.as_view()),
    path("password-reset/", PasswordResetRequestView.as_view()),
    path("password-reset/<str:uidb64>/<str:token>/", PasswordResetConfirmView.as_view()),
    path("refresh/", RefreshView.as_view(), name="auth_refresh"),
]
