from django.db.models import QuerySet

from apps.pelanggan.models import Langganan, Pelanggan


def get_pelanggan_export_queryset() -> QuerySet[Pelanggan]:
    """Return read-only Pelanggan queryset with related Rumah."""
    return Pelanggan.objects.select_related("rumah").order_by("nama")


def get_langganan_export_queryset() -> QuerySet[Langganan]:
    """Return read-only Langganan queryset with related Pelanggan and JenisLayanan."""
    return Langganan.objects.select_related(
        "pelanggan", "jenis_layanan"
    ).order_by("pelanggan__nama", "jenis_layanan__nama_jenis")
