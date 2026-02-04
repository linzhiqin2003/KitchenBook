from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Organization, OrganizationMember, UserProfile
from .models import Receipt


class PersonalReceiptTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1@example.com", email="user1@example.com", password="pass123"
        )
        UserProfile.objects.create(user=self.user1, nickname="User1")
        self.user2 = User.objects.create_user(
            username="user2@example.com", email="user2@example.com", password="pass123"
        )
        UserProfile.objects.create(user=self.user2, nickname="User2")

    def test_create_receipt_sets_user(self):
        self.client.force_authenticate(user=self.user1)
        resp = self.client.post("/api/receipts/", {"merchant": "Test Shop"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        receipt = Receipt.objects.get(id=resp.data["id"])
        self.assertEqual(receipt.user, self.user1)

    def test_user_sees_only_own_receipts(self):
        Receipt.objects.create(
            user=self.user1, merchant="Shop A", status=Receipt.STATUS_READY, total=Decimal("10.00")
        )
        Receipt.objects.create(
            user=self.user2, merchant="Shop B", status=Receipt.STATUS_READY, total=Decimal("20.00")
        )

        self.client.force_authenticate(user=self.user1)
        resp = self.client.get("/api/receipts/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["merchant"], "Shop A")


class OrgReceiptTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="orgowner@example.com", email="orgowner@example.com", password="pass123"
        )
        UserProfile.objects.create(user=self.owner, nickname="Owner")
        self.member = User.objects.create_user(
            username="orgmember@example.com", email="orgmember@example.com", password="pass123"
        )
        UserProfile.objects.create(user=self.member, nickname="Member")
        self.outsider = User.objects.create_user(
            username="orgoutsider@example.com", email="orgoutsider@example.com", password="pass123"
        )
        UserProfile.objects.create(user=self.outsider, nickname="Outsider")

        self.org = Organization.objects.create(name="TestOrg", created_by=self.owner)
        OrganizationMember.objects.create(org=self.org, user=self.owner, role="owner")
        OrganizationMember.objects.create(org=self.org, user=self.member, role="member")

    def test_create_receipt_in_org(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.post(
            "/api/receipts/",
            {"merchant": "Org Shop"},
            format="json",
            HTTP_X_ACTIVE_ORG=str(self.org.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        receipt = Receipt.objects.get(id=resp.data["id"])
        self.assertEqual(receipt.organization_id, self.org.id)

    def test_org_member_sees_org_receipts(self):
        Receipt.objects.create(
            user=self.owner, organization=self.org, merchant="Org Shop",
            status=Receipt.STATUS_READY, total=Decimal("50.00"),
        )
        self.client.force_authenticate(user=self.member)
        resp = self.client.get("/api/receipts/", HTTP_X_ACTIVE_ORG=str(self.org.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_outsider_cannot_see_org_receipts(self):
        Receipt.objects.create(
            user=self.owner, organization=self.org, merchant="Org Shop",
            status=Receipt.STATUS_READY, total=Decimal("50.00"),
        )
        self.client.force_authenticate(user=self.outsider)
        # Outsider provides org header but is not a member — falls back to personal mode
        resp = self.client.get("/api/receipts/", HTTP_X_ACTIVE_ORG=str(self.org.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)


class StatsOverviewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="stats1@example.com", email="stats1@example.com", password="pass123"
        )
        self.user2 = User.objects.create_user(
            username="stats2@example.com", email="stats2@example.com", password="pass123"
        )
        self.owner = User.objects.create_user(
            username="statsowner@example.com", email="statsowner@example.com", password="pass123"
        )
        self.org = Organization.objects.create(name="StatsOrg", created_by=self.owner)
        OrganizationMember.objects.create(org=self.org, user=self.owner, role="owner")

        # Personal receipts
        Receipt.objects.create(
            user=self.user1, merchant="Shop", status=Receipt.STATUS_READY, total=Decimal("100.00"),
        )
        Receipt.objects.create(
            user=self.user2, merchant="Shop", status=Receipt.STATUS_READY, total=Decimal("200.00"),
        )
        # Org receipt
        Receipt.objects.create(
            user=self.owner, organization=self.org, merchant="Org Shop",
            status=Receipt.STATUS_READY, total=Decimal("300.00"), payer="Owner",
        )

    def test_stats_personal_scope(self):
        self.client.force_authenticate(user=self.user1)
        resp = self.client.get("/api/stats/overview/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(resp.data["total_spend"])), Decimal("100.00"))
        self.assertEqual(resp.data["receipt_count"], 1)

    def test_stats_org_scope(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.get("/api/stats/overview/", HTTP_X_ACTIVE_ORG=str(self.org.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(resp.data["total_spend"])), Decimal("300.00"))
        self.assertIn("by_payer", resp.data)

    def test_stats_unauthenticated_returns_empty(self):
        resp = self.client.get("/api/stats/overview/")
        # Default permission requires auth, so should be 401
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class UnauthenticatedReceiptTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="authtest@example.com", email="authtest@example.com", password="pass123"
        )
        Receipt.objects.create(
            user=self.user, merchant="Secret", status=Receipt.STATUS_READY, total=Decimal("999.00"),
        )

    def test_unauthenticated_list_returns_401(self):
        resp = self.client.get("/api/receipts/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_stats_returns_401(self):
        resp = self.client.get("/api/stats/overview/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
