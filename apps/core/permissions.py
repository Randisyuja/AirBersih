"""Centralized RBAC & feature-level authorization utilities (ADR 002)."""

from functools import wraps
from typing import Dict, Iterable, List, Sequence, Tuple, Union

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse


class FeaturePermissionMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """
    CBV mixin enforcing authentication + Django permission(s).
    - Anonymous users are redirected to the login page.
    - Authenticated users without permission receive HTTP 403 (renders templates/403.html).
    """

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied(
                "Anda tidak memiliki hak akses untuk membuka halaman atau fitur ini."
            )
        return super().handle_no_permission()


def feature_permission_required(
    perm: Union[str, Sequence[str]],
    is_api: bool = False,
):
    """
    FBV decorator enforcing authentication + Django permission(s).
    Returns JSON 401/403 when `is_api=True`, otherwise redirects to login or raises 403.
    """
    perms = (perm,) if isinstance(perm, str) else tuple(perm)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return login_required(view_func)(request, *args, **kwargs)

            if not request.user.has_perms(perms):
                if is_api:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "Akses ditolak. Anda tidak memiliki izin untuk fitur ini.",
                        },
                        status=403,
                    )
                raise PermissionDenied(
                    "Anda tidak memiliki hak akses untuk fitur ini."
                )
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


# Human-readable feature permission groups for UI checklists & default role setup
APP_FEATURE_PERMISSIONS: List[Tuple[str, List[Tuple[str, str]]]] = [
    (
        "Transaksi Pembayaran & Loket",
        [
            ("pembayaran.view_pembayaran", "Lihat Data Pembayaran, Laporan & Cetak Struk"),
            ("pembayaran.add_pembayaran", "Input Pembayaran & Loket Scan QR"),
            ("pembayaran.change_pembayaran", "Edit Data Pembayaran"),
            ("pembayaran.delete_pembayaran", "Hapus Data Pembayaran"),
        ],
    ),
    (
        "Kelola Tagihan",
        [
            ("pelanggan.view_tagihan", "Lihat Daftar Tagihan"),
            ("pelanggan.add_tagihan", "Tambah & Generate Tagihan Tahunan"),
            ("pelanggan.change_tagihan", "Edit Tagihan"),
            ("pelanggan.delete_tagihan", "Hapus Tagihan"),
        ],
    ),
    (
        "Master Pelanggan & Langganan",
        [
            ("pelanggan.view_pelanggan", "Lihat Master Pelanggan"),
            ("pelanggan.add_pelanggan", "Tambah / Import Pelanggan"),
            ("pelanggan.change_pelanggan", "Edit Pelanggan"),
            ("pelanggan.delete_pelanggan", "Hapus Pelanggan"),
            ("pelanggan.view_langganan", "Lihat Langganan & Kartu Member"),
            ("pelanggan.add_langganan", "Tambah / Import Langganan"),
            ("pelanggan.change_langganan", "Edit Langganan"),
            ("pelanggan.delete_langganan", "Hapus Langganan"),
        ],
    ),
    (
        "Master Rumah",
        [
            ("rumah.view_rumah", "Lihat Master Rumah"),
            ("rumah.add_rumah", "Tambah / Import Rumah"),
            ("rumah.change_rumah", "Edit Rumah"),
            ("rumah.delete_rumah", "Hapus Rumah"),
        ],
    ),
    (
        "Master Layanan & Paket",
        [
            ("layanan.view_layanan", "Lihat Master Layanan"),
            ("layanan.add_layanan", "Tambah / Import Layanan"),
            ("layanan.change_layanan", "Edit Layanan"),
            ("layanan.delete_layanan", "Hapus Layanan"),
            ("layanan.view_jenislayanan", "Lihat Jenis Layanan / Paket"),
            ("layanan.add_jenislayanan", "Tambah / Import Jenis Layanan"),
            ("layanan.change_jenislayanan", "Edit Jenis Layanan"),
            ("layanan.delete_jenislayanan", "Hapus Jenis Layanan"),
        ],
    ),
    (
        "Manajemen Akun Pengguna",
        [
            ("users.view_kasir", "Lihat Daftar Akun Pengguna"),
            ("users.add_kasir", "Tambah / Import Akun Pengguna"),
            ("users.change_kasir", "Edit Akun & Hak Akses Pengguna"),
            ("users.delete_kasir", "Hapus Akun Pengguna"),
        ],
    ),
]

ALL_MANAGED_PERMS: List[str] = [
    perm_key
    for _, items in APP_FEATURE_PERMISSIONS
    for perm_key, _ in items
]

DEFAULT_ROLE_GROUPS: Dict[str, List[str]] = {
    "Administrator": ALL_MANAGED_PERMS,
    "Kasir": [
        "pembayaran.view_pembayaran",
        "pembayaran.add_pembayaran",
        "pembayaran.change_pembayaran",
        "pembayaran.delete_pembayaran",
        "pelanggan.view_tagihan",
        "pelanggan.add_tagihan",
        "pelanggan.change_tagihan",
        "pelanggan.delete_tagihan",
    ],
    "Viewer": [
        "pembayaran.view_pembayaran",
        "pelanggan.view_tagihan",
    ],
}


def _resolve_permissions(perm_keys: Iterable[str]) -> List[Permission]:
    """Resolves 'app_label.codename' strings to Permission objects."""
    resolved: List[Permission] = []
    for key in perm_keys:
        if "." not in key:
            continue
        app_label, codename = key.split(".", 1)
        perm_obj = Permission.objects.filter(
            content_type__app_label=app_label,
            codename=codename,
        ).first()
        if perm_obj:
            resolved.append(perm_obj)
    return resolved


def sync_default_groups() -> Dict[str, Group]:
    """Creates or updates default RBAC Groups (Administrator, Kasir, Viewer)."""
    groups: Dict[str, Group] = {}
    for group_name, perm_keys in DEFAULT_ROLE_GROUPS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        perms = _resolve_permissions(perm_keys)
        group.permissions.set(perms)
        groups[group_name] = group
    return groups
