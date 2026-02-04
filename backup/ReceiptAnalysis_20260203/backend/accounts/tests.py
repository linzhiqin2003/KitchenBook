from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import Organization, OrganizationMember, InviteLink, UserProfile


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        resp = self.client.post("/api/auth/register/", {
            "email": "new@example.com",
            "password": "testpass123",
            "nickname": "New User",
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="new@example.com").exists())
        profile = UserProfile.objects.get(user__username="new@example.com")
        self.assertEqual(profile.nickname, "New User")

    def test_register_duplicate_email(self):
        User.objects.create_user(username="dup@example.com", email="dup@example.com", password="pass123")
        resp = self.client.post("/api/auth/register/", {
            "email": "dup@example.com",
            "password": "testpass123",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="login@example.com", email="login@example.com", password="correct123"
        )

    def test_login_success(self):
        resp = self.client.post("/api/auth/login/", {
            "username": "login@example.com",
            "password": "correct123",
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_wrong_password(self):
        resp = self.client.post("/api/auth/login/", {
            "username": "login@example.com",
            "password": "wrong",
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="refresh@example.com", email="refresh@example.com", password="pass123"
        )

    def test_token_refresh(self):
        login_resp = self.client.post("/api/auth/login/", {
            "username": "refresh@example.com",
            "password": "pass123",
        })
        refresh_token = login_resp.data["refresh"]
        resp = self.client.post("/api/auth/token/refresh/", {"refresh": refresh_token})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)


class UserProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="profile@example.com", email="profile@example.com", password="pass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["email"], "profile@example.com")

    def test_update_profile(self):
        resp = self.client.patch("/api/auth/me/", {"nickname": "Updated"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["nickname"], "Updated")


class OrganizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="org@example.com", email="org@example.com", password="pass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_organization(self):
        resp = self.client.post("/api/auth/orgs/", {"name": "Test Org"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["name"], "Test Org")
        # Creator should be owner
        org = Organization.objects.get(id=resp.data["id"])
        self.assertTrue(
            OrganizationMember.objects.filter(org=org, user=self.user, role="owner").exists()
        )

    def test_list_organizations(self):
        org = Organization.objects.create(name="My Org", created_by=self.user)
        OrganizationMember.objects.create(org=org, user=self.user, role="owner")
        resp = self.client.get("/api/auth/orgs/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)


class OrganizationMembersTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="owner@example.com", email="owner@example.com", password="pass123"
        )
        self.member = User.objects.create_user(
            username="member@example.com", email="member@example.com", password="pass123"
        )
        self.outsider = User.objects.create_user(
            username="outsider@example.com", email="outsider@example.com", password="pass123"
        )
        self.org = Organization.objects.create(name="Team", created_by=self.owner)
        OrganizationMember.objects.create(org=self.org, user=self.owner, role="owner")
        OrganizationMember.objects.create(org=self.org, user=self.member, role="member")

    def test_member_can_view_members(self):
        self.client.force_authenticate(user=self.member)
        resp = self.client.get(f"/api/auth/orgs/{self.org.id}/members/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    def test_outsider_sees_empty(self):
        self.client.force_authenticate(user=self.outsider)
        resp = self.client.get(f"/api/auth/orgs/{self.org.id}/members/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)


class InviteLinkTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="invowner@example.com", email="invowner@example.com", password="pass123"
        )
        self.joiner = User.objects.create_user(
            username="joiner@example.com", email="joiner@example.com", password="pass123"
        )
        self.org = Organization.objects.create(name="Invite Org", created_by=self.owner)
        OrganizationMember.objects.create(org=self.org, user=self.owner, role="owner")

    def test_create_invite(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.post(f"/api/auth/orgs/{self.org.id}/invite/", {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", resp.data)

    def test_accept_invite(self):
        invite = InviteLink.objects.create(org=self.org, created_by=self.owner)
        self.client.force_authenticate(user=self.joiner)
        resp = self.client.post(f"/api/auth/invite/{invite.id}/accept/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(
            OrganizationMember.objects.filter(org=self.org, user=self.joiner).exists()
        )

    def test_accept_invite_already_member(self):
        invite = InviteLink.objects.create(org=self.org, created_by=self.owner)
        OrganizationMember.objects.create(org=self.org, user=self.joiner, role="member")
        self.client.force_authenticate(user=self.joiner)
        resp = self.client.post(f"/api/auth/invite/{invite.id}/accept/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("已是组织成员", resp.data["detail"])

    def test_invite_get_anonymous(self):
        invite = InviteLink.objects.create(org=self.org, created_by=self.owner)
        # Unauthenticated GET should work
        resp = self.client.get(f"/api/auth/invite/{invite.id}/accept/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["org_name"], "Invite Org")

    def test_invite_expired(self):
        invite = InviteLink.objects.create(
            org=self.org, created_by=self.owner,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        resp = self.client.get(f"/api/auth/invite/{invite.id}/accept/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_max_uses(self):
        invite = InviteLink.objects.create(
            org=self.org, created_by=self.owner,
            max_uses=1, use_count=1,
        )
        resp = self.client.get(f"/api/auth/invite/{invite.id}/accept/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
