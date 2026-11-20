"""Unit and integration tests for RBAC / feature-level authorization (ADR 002)."""

import json
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.core.permissions import sync_default_groups
from apps.users.models import Kasir


class FeatureAuthorizationTests(TestCase):
    def setUp(self):
        self.groups = sync_default_groups()

        self.admin_user = Kasir.objects.create_user(
            username="admin_rbac", password="password123"
        )
        self.admin_user.groups.add(self.groups["Administrator"])

        self.kasir_user = Kasir.objects.create_user(
            username="kasir_rbac", password="password123"
        )
        self.kasir_user.groups.add(self.groups["Kasir"])

        self.viewer_user = Kasir.objects.create_user(
            username="viewer_rbac", password="password123"
        )
        self.viewer_user.groups.add(self.groups["Viewer"])

    def test_kasir_allowed_operational_features_and_blocked_master_data(self):
        """Kasir can access pembayaran, tagihan, and laporan, but gets 403 on Master Data & Users."""
        self.client.force_login(self.kasir_user)

        # Allowed operational features
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("daftar_pembayaran")).status_code, 200)
        self.assertEqual(self.client.get(reverse("tambah_pembayaran")).status_code, 200)
        self.assertEqual(self.client.get(reverse("daftar_tagihan")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("laporan_tahunan", kwargs={"layanan": "AIR"})).status_code,
            200,
        )

        # Blocked Master Data & User Management
        self.assertEqual(self.client.get(reverse("daftar_pelanggan")).status_code, 403)
        self.assertEqual(self.client.get(reverse("daftar_rumah")).status_code, 403)
        self.assertEqual(self.client.get(reverse("daftar_layanan")).status_code, 403)
        self.assertEqual(self.client.get(reverse("daftar_users")).status_code, 403)

        # Sidebar hides Master Data for Kasir
        dash_res = self.client.get(reverse("dashboard"))
        self.assertNotContains(dash_res, 'id="navMasterMenu"')
        self.assertContains(dash_res, 'id="cardLoketBayarCepat"')

    def test_viewer_read_only_and_blocked_mutations(self):
        """Viewer can view dashboard/reports/lists, but gets 403 on add/pay/generate/master."""
        self.client.force_login(self.viewer_user)

        dash_res = self.client.get(reverse("dashboard"))
        self.assertEqual(dash_res.status_code, 200)
        self.assertNotContains(dash_res, 'id="cardLoketBayarCepat"')
        self.assertNotContains(dash_res, 'id="btnGenerateTagihanDash"')

        self.assertEqual(self.client.get(reverse("daftar_pembayaran")).status_code, 200)
        self.assertEqual(self.client.get(reverse("daftar_tagihan")).status_code, 200)
        self.assertEqual(self.client.get(reverse("tambah_pembayaran")).status_code, 403)

        # API returns JSON 403 for unauthorized pay attempt
        pay_res = self.client.post(
            reverse("pay_by_barcode_api"),
            data=json.dumps({"barcode": "PLG00001", "tagihan_id": 1}),
            content_type="application/json",
        )
        self.assertEqual(pay_res.status_code, 403)
        self.assertEqual(pay_res.json()["status"], "error")

    def test_custom_per_feature_permission_grant(self):
        """Admin can grant an individual feature permission (e.g. view_rumah) to a Kasir."""
        perm_view_rumah = Permission.objects.get(
            content_type__app_label="rumah", codename="view_rumah"
        )
        self.kasir_user.user_permissions.add(perm_view_rumah)

        self.client.force_login(self.kasir_user)
        self.assertEqual(self.client.get(reverse("daftar_rumah")).status_code, 200)
        # Other master data still blocked
        self.assertEqual(self.client.get(reverse("daftar_pelanggan")).status_code, 403)

    def test_administrator_has_full_access(self):
        """Administrator group can access every module including Master Data & Users."""
        self.client.force_login(self.admin_user)

        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("daftar_pembayaran")).status_code, 200)
        self.assertEqual(self.client.get(reverse("daftar_pelanggan")).status_code, 200)
        self.assertEqual(self.client.get(reverse("daftar_rumah")).status_code, 200)
        self.assertEqual(self.client.get(reverse("daftar_layanan")).status_code, 200)
        self.assertEqual(self.client.get(reverse("daftar_users")).status_code, 200)
