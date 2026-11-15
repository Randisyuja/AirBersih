from apps.rumah.models import Rumah


def is_rumah_exists(no_rumah: str) -> bool:
    """Check if a Rumah record exists with the specified no_rumah (case-insensitive)."""
    return Rumah.objects.filter(no_rumah__iexact=no_rumah.strip()).exists()


def create_rumah(rt: str, no_rumah: str) -> Rumah:
    """Create a new Rumah record."""
    return Rumah.objects.create(
        rt=rt.strip(),
        no_rumah=no_rumah.strip(),
    )


def upsert_rumah(rt: str, no_rumah: str) -> tuple[Rumah, bool]:
    """Create or update a Rumah record keyed by no_rumah."""
    return Rumah.objects.update_or_create(
        no_rumah=no_rumah,
        defaults={"rt": rt},
    )

