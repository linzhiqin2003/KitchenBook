from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Organization, OrganizationMember, InviteLink, UserProfile
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    OrganizationSerializer,
    OrganizationMemberSerializer,
    InviteLinkSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "注册成功"}, status=status.HTTP_201_CREATED)


class UserProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={"nickname": request.user.email.split("@")[0] if request.user.email else request.user.username},
        )
        serializer = UserProfileSerializer(profile, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={"nickname": request.user.email.split("@")[0] if request.user.email else request.user.username},
        )
        serializer = UserProfileSerializer(profile, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class OrganizationListCreateView(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(
            members__user=self.request.user
        ).distinct().order_by("-created_at")

    def perform_create(self, serializer):
        org = serializer.save(created_by=self.request.user)
        OrganizationMember.objects.create(
            org=org, user=self.request.user, role=OrganizationMember.ROLE_OWNER
        )


class OrganizationMembersView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrganizationMemberSerializer

    def get_queryset(self):
        org_id = self.kwargs["org_id"]
        # Only members of the org can view its members
        if not OrganizationMember.objects.filter(org_id=org_id, user=self.request.user).exists():
            return OrganizationMember.objects.none()
        return OrganizationMember.objects.filter(org_id=org_id).select_related("user", "user__profile")


class InviteLinkCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, org_id):
        if not OrganizationMember.objects.filter(org_id=org_id, user=request.user).exists():
            return Response({"detail": "无权操作"}, status=status.HTTP_403_FORBIDDEN)

        expires_at = request.data.get("expires_at")
        max_uses = request.data.get("max_uses", 0)

        invite = InviteLink.objects.create(
            org_id=org_id,
            created_by=request.user,
            expires_at=expires_at,
            max_uses=max_uses,
        )
        serializer = InviteLinkSerializer(invite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LeaveOrgView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, org_id):
        membership = OrganizationMember.objects.filter(org_id=org_id, user=request.user).first()
        if not membership:
            return Response({"detail": "你不是该组织的成员"}, status=status.HTTP_404_NOT_FOUND)

        org = membership.org
        total_members = OrganizationMember.objects.filter(org=org).count()
        is_owner = membership.role == OrganizationMember.ROLE_OWNER
        owner_count = OrganizationMember.objects.filter(org=org, role=OrganizationMember.ROLE_OWNER).count()

        if is_owner and owner_count == 1 and total_members > 1:
            return Response(
                {"detail": "请先转让管理员权限或移除所有成员"},
                status=status.HTTP_403_FORBIDDEN,
            )

        membership.delete()

        # 唯一 owner 且无其他成员 → 自动解散
        if is_owner and owner_count == 1 and total_members == 1:
            org.delete()
            return Response({"detail": "已退出并解散组织"})

        return Response({"detail": "已退出组织"})


class RemoveMemberView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, org_id, member_id):
        my_membership = OrganizationMember.objects.filter(
            org_id=org_id, user=request.user, role=OrganizationMember.ROLE_OWNER
        ).first()
        if not my_membership:
            return Response({"detail": "无权操作"}, status=status.HTTP_403_FORBIDDEN)

        target = OrganizationMember.objects.filter(org_id=org_id, id=member_id).first()
        if not target:
            return Response({"detail": "成员不存在"}, status=status.HTTP_404_NOT_FOUND)
        if target.user == request.user:
            return Response({"detail": "不能移除自己，请使用退出接口"}, status=status.HTTP_400_BAD_REQUEST)
        if target.role == OrganizationMember.ROLE_OWNER:
            return Response({"detail": "不能移除其他管理员"}, status=status.HTTP_403_FORBIDDEN)

        target.delete()
        return Response({"detail": "已移除成员"})


class DissolveOrgView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, org_id):
        my_membership = OrganizationMember.objects.filter(
            org_id=org_id, user=request.user, role=OrganizationMember.ROLE_OWNER
        ).first()
        if not my_membership:
            return Response({"detail": "无权操作"}, status=status.HTTP_403_FORBIDDEN)

        Organization.objects.filter(id=org_id).delete()
        return Response({"detail": "组织已解散"})


class InviteAcceptView(APIView):
    authentication_classes = [JWTAuthentication]
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request, invite_id):
        """Get invite info without accepting."""
        try:
            invite = InviteLink.objects.select_related("org").get(id=invite_id)
        except InviteLink.DoesNotExist:
            return Response({"detail": "邀请链接无效"}, status=status.HTTP_404_NOT_FOUND)

        if not invite.is_active:
            return Response({"detail": "邀请链接已失效"}, status=status.HTTP_400_BAD_REQUEST)
        if invite.expires_at and invite.expires_at < timezone.now():
            return Response({"detail": "邀请链接已过期"}, status=status.HTTP_400_BAD_REQUEST)
        if invite.max_uses and invite.use_count >= invite.max_uses:
            return Response({"detail": "邀请链接已达使用上限"}, status=status.HTTP_400_BAD_REQUEST)

        already_member = False
        if request.user and request.user.is_authenticated:
            already_member = OrganizationMember.objects.filter(
                org=invite.org, user=request.user
            ).exists()

        return Response({
            "id": str(invite.id),
            "org_id": str(invite.org_id),
            "org_name": invite.org.name,
            "already_member": already_member,
        })

    def post(self, request, invite_id):
        try:
            invite = InviteLink.objects.select_related("org").get(id=invite_id)
        except InviteLink.DoesNotExist:
            return Response({"detail": "邀请链接无效"}, status=status.HTTP_404_NOT_FOUND)

        if not invite.is_active:
            return Response({"detail": "邀请链接已失效"}, status=status.HTTP_400_BAD_REQUEST)
        if invite.expires_at and invite.expires_at < timezone.now():
            return Response({"detail": "邀请链接已过期"}, status=status.HTTP_400_BAD_REQUEST)
        if invite.max_uses and invite.use_count >= invite.max_uses:
            return Response({"detail": "邀请链接已达使用上限"}, status=status.HTTP_400_BAD_REQUEST)

        membership, created = OrganizationMember.objects.get_or_create(
            org=invite.org, user=request.user,
            defaults={"role": OrganizationMember.ROLE_MEMBER},
        )

        if created:
            invite.use_count += 1
            invite.save(update_fields=["use_count"])

        return Response({
            "detail": "已加入组织" if created else "已是组织成员",
            "org_id": str(invite.org_id),
            "org_name": invite.org.name,
        })
