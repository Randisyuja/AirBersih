from django.db.models import QuerySet

from apps.rumah.models import Rumah


def get_rumah_export_queryset() -> QuerySet[Rumah]:
    """Return read-only Rumah queryset ordered by RT and house number."""
    return Rumah.objects.all().order_by("rt", "no_rumah")
