import json
import urllib.request
import urllib.error

from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile, Organization, OrganizationMember, InviteLink


def _validate_groq_key(api_key: str):
    """Validate Groq API key via OpenAI-compatible /v1/models endpoint."""
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/models",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                raise serializers.ValidationError("Groq API Key 无效")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body).get("error", {}).get("message", body[:200])
        except Exception:
            detail = body[:200]
        raise serializers.ValidationError(f"Groq API Key 无效: {detail}")
    except urllib.error.URLError as e:
        raise serializers.ValidationError(f"无法连接 Groq: {e.reason}")


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    nickname = serializers.CharField(max_length=100, required=False, default="")
    groq_api_key = serializers.CharField(max_length=256, required=False, default="")

    def validate_email(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("该邮箱已被注册")
        return value

    def validate_groq_api_key(self, value):
        if not value:
            return value
        _validate_groq_key(value)
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        nickname = validated_data.get("nickname", "")
        groq_api_key = validated_data.get("groq_api_key", "")
        user = User.objects.create_user(
            username=email, email=email, password=password
        )
        UserProfile.objects.create(
            user=user,
            nickname=nickname or email.split("@")[0],
            groq_api_key=groq_api_key,
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    avatar_display = serializers.SerializerMethodField()
    groq_api_key = serializers.CharField(
        max_length=256, required=False, write_only=True
    )
    has_groq_key = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "id", "nickname", "avatar_url", "avatar", "avatar_display", "email",
            "groq_api_key", "has_groq_key",
        ]

    def get_avatar_display(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return obj.avatar_url or ""

    def get_has_groq_key(self, obj):
        return bool(obj.groq_api_key)

    def validate_groq_api_key(self, value):
        if not value:
            return value
        _validate_groq_key(value)
        return value


class OrganizationSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ["id", "name", "created_at", "member_count"]
        read_only_fields = ["id", "created_at"]

    def get_member_count(self, obj):
        return obj.members.count()


class OrganizationMemberSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    avatar_display = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationMember
        fields = ["id", "role", "joined_at", "nickname", "email", "avatar_display"]

    def get_nickname(self, obj):
        profile = getattr(obj.user, "profile", None)
        return profile.nickname if profile else obj.user.username

    def get_email(self, obj):
        return obj.user.email

    def get_avatar_display(self, obj):
        profile = getattr(obj.user, "profile", None)
        if not profile:
            return ""
        if profile.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(profile.avatar.url)
            return profile.avatar.url
        return profile.avatar_url or ""


class InviteLinkSerializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source="org.name", read_only=True)

    class Meta:
        model = InviteLink
        fields = ["id", "org", "org_name", "expires_at", "max_uses", "use_count", "is_active", "created_at"]
        read_only_fields = ["id", "org", "use_count", "is_active", "created_at"]
