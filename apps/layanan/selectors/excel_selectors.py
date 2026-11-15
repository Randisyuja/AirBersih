from django.db.models import QuerySet

from apps.layanan.models import JenisLayanan, Layanan


def get_layanan_export_queryset() -> QuerySet[Layanan]:
    """Return read-only Layanan queryset ordered by nama_layanan."""
    return Layanan.objects.all().order_by("nama_layanan")


def get_jenis_layanan_export_queryset() -> QuerySet[JenisLayanan]:
    """Return read-only JenisLayanan queryset with related Layanan."""
    return JenisLayanan.objects.select_related("layanan").order_by(
        "layanan__nama_layanan", "nama_jenis"
    )
