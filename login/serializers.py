from django.contrib.auth.models import User
from rest_framework import serializers

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    password2 = serializers.CharField(min_length=8, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Esse username já está em uso.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Esse email já está em uso.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "As senhas não coincidem."})
        return attrs

    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    # pode aceitar email OU username
    login = serializers.CharField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8, write_only=True)
    new_password2 = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password2": "As senhas não coincidem."})
        return attrs
