import uuid
from django.conf import settings
from django.db import models

from accounts.fields import EncryptedCharField


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    nickname = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    groq_api_key = EncryptedCharField(max_length=256, blank=True, default="")
    # MyAgent 访问门禁 —— 默认 False，需用 owner 发的邀请码兑换后才能用。
    # owner（settings.AI_LAB_OWNER_USERNAMES 列出的用户名 / email、或 is_superuser）
    # 不受此字段约束。
    ai_lab_enabled = models.BooleanField(default=False)
    ai_lab_activated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.nickname or self.user.username


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_orgs"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class OrganizationMember(models.Model):
    ROLE_OWNER = "owner"
    ROLE_MEMBER = "member"
    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner"),
        (ROLE_MEMBER, "Member"),
    ]

    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="org_memberships"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("org", "user")

    def __str__(self) -> str:
        return f"{self.user} @ {self.org} ({self.role})"


class InviteLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="invites")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(default=0)  # 0 = unlimited
    use_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Invite {self.id} → {self.org}"
