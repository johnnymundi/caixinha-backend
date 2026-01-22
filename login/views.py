''' login/views.py'''
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from .serializers import (
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

COOKIE_SECURE = False  # True em produção com https
COOKIE_SAMESITE = "Lax"  # "None" se front/back em domínios diferentes + https

def set_auth_cookies(response: Response, refresh: RefreshToken):
    response.set_cookie(
        "access_token",
        str(refresh.access_token),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=60 * 15,
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        str(refresh),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=60 * 60 * 24 * 7, #
        path="/",
    )

def clear_auth_cookies(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                }
            },
            status=status.HTTP_201_CREATED,
        )

token_gen = PasswordResetTokenGenerator()

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = PasswordResetRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        login = s.validated_data["login"].strip()

        # procura por email ou username
        user = User.objects.filter(email__iexact=login).first() or User.objects.filter(username=login).first()

        if not user or not user.email:
            return Response({"ok": True})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_gen.make_token(user)

        # url do front /reset/:uid/:token
        reset_link = f"http://localhost:5173/reset/{uid}/{token}"

        send_mail(
            subject="Caixinha — Redefinir senha",
            message=f"Use este link para redefinir sua senha:\n\n{reset_link}\n\nSe não foi você, ignore.",
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )

        return Response({"ok": True})

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, uidb64: str, token: str):
        s = PasswordResetConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Link inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if not token_gen.check_token(user, token):
            return Response({"detail": "Token inválido ou expirado."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(s.validated_data["new_password"])
        user.save()
        return Response({"ok": True})

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({"detail": "Credenciais inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        response = Response(
            {"user": {
                "id": user.id,
                "email": user.email,
                "username": user.get_username(),
                "first_name": user.first_name,
                "last_name": user.last_name,
            }}
        )
        set_auth_cookies(response, refresh)
        return response

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({
            "id": u.id,
            "email": u.email,
            "username": u.get_username(),
            "first_name": u.first_name,
            "last_name": u.last_name,
        })
    
class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Espera: { "refresh": "<refresh_token>" }
        Retorna: { "access": "<new_access>" } (e às vezes refresh se ROTATE enabled)
        """
        serializer = TokenRefreshSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            return Response({"detail": "refresh inválido"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    def post(self, request):
        response = Response({"ok": True})
        clear_auth_cookies(response)
        return response
