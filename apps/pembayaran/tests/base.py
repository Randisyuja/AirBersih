"""
apps/pembayaran/tests/base.py
Base test case and data factory for authentic E2E tests.
Provides authentic database fixtures, authenticated Kasir login,
model setup, and resilient routing helpers.
"""

import json
import os
from typing import Tuple, Optional, List, Dict, Any

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.conf import settings

from apps.layanan.models import Layanan, JenisLayanan
from apps.pelanggan.models import Pelanggan, Langganan, Tagihan
from apps.pembayaran.choices import BulanChoice, StatusChoice
from apps.pembayaran.models import Pembayaran
from apps.rumah.models import Rumah

User = get_user_model()


class E2ETestDataFactory:
    """Helper factory for creating consistent master data and customer tariffs in E2E tests."""

    @staticmethod
    def create_admin_kasir(
        username: str = "kasir_e2e_factory",
        password: str = "Password123!",
        first_name: str = "Budi",
        last_name: str = "Kasir",
        no_hp: str = "081234567890",
    ) -> User:
        """Create authenticated staff Kasir."""
        return User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=f"{username}@example.com",
            no_hp=no_hp,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )

    @staticmethod
    def create_standard_services() -> Tuple[Layanan, JenisLayanan, Layanan, JenisLayanan]:
        """Creates standard Water and WiFi services with default packages."""
        layanan_air, _ = Layanan.objects.get_or_create(nama_layanan="AIR")
        tarif_air, _ = JenisLayanan.objects.get_or_create(
            layanan=layanan_air,
            nama_jenis="Air Rumah Tangga",
            defaults={"tarif": 25000},
        )

        layanan_wifi, _ = Layanan.objects.get_or_create(nama_layanan="WIFI")
        tarif_wifi, _ = JenisLayanan.objects.get_or_create(
            layanan=layanan_wifi,
            nama_jenis="WiFi Warga 20Mbps",
            defaults={"tarif": 50000},
        )

        return layanan_air, tarif_air, layanan_wifi, tarif_wifi

    @staticmethod
    def create_customer_with_house(
        nama: str,
        rt: str = "01",
        no_rumah: str = "A-01",
        no_hp: str = "08123456789",
        barcode: Optional[str] = None,
    ) -> Tuple[Pelanggan, Rumah]:
        """Create a valid resident customer attached to a unique house."""
        rumah = Rumah.objects.create(rt=rt, no_rumah=no_rumah)
        fields = {
            "nama": nama,
            "no_hp": no_hp,
            "rumah": rumah,
        }
        if hasattr(Pelanggan, "barcode"):
            fields["barcode"] = barcode or f"PLG-{no_rumah.replace('-', '')}"

        pelanggan = Pelanggan.objects.create(**fields)
        return pelanggan, rumah

    @classmethod
    def create_dual_service_customer(
        cls,
        nama: str = "Siti Rahma",
        rt: str = "02",
        no_rumah: str = "B-05",
        barcode: str = "PLG00001",
    ) -> Tuple[Pelanggan, Langganan, Langganan, JenisLayanan, JenisLayanan]:
        """Instantiates a customer subscribed to BOTH active Water and WiFi tariffs."""
        _, tarif_air, _, tarif_wifi = cls.create_standard_services()
        pelanggan, _ = cls.create_customer_with_house(
            nama=nama, rt=rt, no_rumah=no_rumah, barcode=barcode
        )

        langganan_air = Langganan.objects.create(
            pelanggan=pelanggan,
            jenis_layanan=tarif_air,
            harga=tarif_air.tarif,
            aktif=True,
        )
        langganan_wifi = Langganan.objects.create(
            pelanggan=pelanggan,
            jenis_layanan=tarif_wifi,
            harga=tarif_wifi.tarif,
            aktif=True,
        )
        return pelanggan, langganan_air, langganan_wifi, tarif_air, tarif_wifi

    @staticmethod
    def create_unpaid_due(
        pelanggan: Pelanggan,
        jenis_layanan: JenisLayanan,
        bulan: int = BulanChoice.NOVEMBER,
        tahun: int = 2026,
        jumlah_bayar: Optional[int] = None,
    ) -> Tagihan:
        """Create an unpaid pending due for barcode dues resolution testing."""
        return Tagihan.objects.create(
            pelanggan=pelanggan,
            jenis_layanan=jenis_layanan,
            bulan=bulan,
            tahun=tahun,
            status_tagihan=StatusChoice.Belum,
            jumlah_bayar=jumlah_bayar if jumlah_bayar is not None else jenis_layanan.tarif,
        )

    @staticmethod
    def record_paid_bill(
        pelanggan: Pelanggan,
        jenis_layanan: JenisLayanan,
        bulan: int = BulanChoice.NOVEMBER,
        tahun: int = 2026,
        jumlah_bayar: Optional[int] = None,
        kasir: Optional[User] = None,
        paid_at: Optional[timezone.datetime] = None,
    ) -> Pembayaran:
        """Record a completed payment for revenue analytics and reporting tests."""
        return Pembayaran.objects.create(
            pelanggan=pelanggan,
            jenis_layanan=jenis_layanan,
            kasir=kasir,
            bulan=bulan,
            tahun=tahun,
            status_bayar=StatusChoice.Lunas,
            tgl_pembayaran=paid_at or timezone.now(),
            jumlah_bayar=jumlah_bayar if jumlah_bayar is not None else jenis_layanan.tarif,
        )


class BasePaymentE2ETestCase(TestCase):
    """Base test case providing authentic database fixtures and helper utilities for E2E tests."""

    def setUp(self):
        super().setUp()
        self.kasir = User.objects.create_user(
            username="kasir_e2e",
            password="E2ePassword123!",
            first_name="Budi",
            last_name="Kasir",
            email="kasir_e2e@example.com",
            no_hp="081234567890",
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        self.client.force_login(self.kasir)

        self.layanan_air, _ = Layanan.objects.get_or_create(nama_layanan="AIR")
        self.layanan_wifi, _ = Layanan.objects.get_or_create(nama_layanan="WIFI")

        self.tarif_air, _ = JenisLayanan.objects.get_or_create(
            layanan=self.layanan_air,
            nama_jenis="Air Rumah Tangga",
            defaults={"tarif": 25000},
        )
        self.tarif_wifi, _ = JenisLayanan.objects.get_or_create(
            layanan=self.layanan_wifi,
            nama_jenis="WiFi Warga 20Mbps",
            defaults={"tarif": 50000},
        )

        self.rumah = Rumah.objects.create(rt="01", no_rumah="A-12")
        cust_kwargs = {
            "nama": "Ahmad Subagyo",
            "no_hp": "081987654321",
            "rumah": self.rumah,
        }
        if hasattr(Pelanggan, "barcode"):
            cust_kwargs["barcode"] = "PLG00001"
        self.pelanggan = Pelanggan.objects.create(**cust_kwargs)
        if hasattr(self.pelanggan, "barcode") and not self.pelanggan.barcode:
            self.pelanggan.barcode = "PLG00001"
            self.pelanggan.save(update_fields=["barcode"])

        self.sub_air = Langganan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.tarif_air,
            harga=25000,
            aktif=True,
        )
        self.sub_wifi = Langganan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.tarif_wifi,
            harga=50000,
            aktif=True,
        )

    def resolve_url(self, route_name: str, fallback_path: str = "", **kwargs) -> str:
        """Safely resolve route name or fallback to expected path."""
        try:
            return reverse(route_name, kwargs=kwargs)
        except NoReverseMatch:
            if fallback_path:
                return fallback_path
            raise

    def create_pending_due(
        self,
        pelanggan: Optional[Pelanggan] = None,
        jenis_layanan: Optional[JenisLayanan] = None,
        bulan: int = BulanChoice.NOVEMBER,
        tahun: int = 2026,
        jumlah: Optional[int] = None,
    ) -> Tagihan:
        """Helper to create a pending Tagihan record."""
        p = pelanggan or self.pelanggan
        j = jenis_layanan or self.tarif_air
        amt = jumlah if jumlah is not None else j.tarif
        return Tagihan.objects.create(
            pelanggan=p,
            jenis_layanan=j,
            bulan=bulan,
            tahun=tahun,
            status_tagihan=StatusChoice.Belum,
            jumlah_bayar=amt,
        )

    def create_settled_payment(
        self,
        pelanggan: Optional[Pelanggan] = None,
        jenis_layanan: Optional[JenisLayanan] = None,
        bulan: int = BulanChoice.NOVEMBER,
        tahun: int = 2026,
        jumlah: Optional[int] = None,
        kasir: Optional[User] = None,
        paid_at: Optional[timezone.datetime] = None,
    ) -> Pembayaran:
        """Helper to create a settled Pembayaran record."""
        p = pelanggan or self.pelanggan
        j = jenis_layanan or self.tarif_air
        k = kasir or self.kasir
        amt = jumlah if jumlah is not None else j.tarif
        return Pembayaran.objects.create(
            pelanggan=p,
            jenis_layanan=j,
            kasir=k,
            bulan=bulan,
            tahun=tahun,
            status_bayar=StatusChoice.Lunas,
            tgl_pembayaran=paid_at or timezone.now(),
            jumlah_bayar=amt,
        )
