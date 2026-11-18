from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        email = get_user_model()._default_manager.normalize_email(attrs["email"])
        user = authenticate(
            request=self.context["request"],
            email=email,
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("E-posta veya parola geçersiz.")
        return {"user": user}
