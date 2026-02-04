from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile, Organization, OrganizationMember, InviteLink


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    nickname = serializers.CharField(max_length=100, required=False, default="")

    def validate_email(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("该邮箱已被注册")
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        nickname = validated_data.get("nickname", "")
        user = User.objects.create_user(
            username=email, email=email, password=password
        )
        UserProfile.objects.create(user=user, nickname=nickname or email.split("@")[0])
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    avatar_display = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ["id", "nickname", "avatar_url", "avatar", "avatar_display", "email"]

    def get_avatar_display(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return obj.avatar_url or ""


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
