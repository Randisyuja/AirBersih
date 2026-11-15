from django.db.models import QuerySet

from apps.users.models import Kasir


def get_kasir_export_queryset() -> QuerySet[Kasir]:
    """Return read-only Kasir queryset ordered by username."""
    return Kasir.objects.all().order_by("username")
