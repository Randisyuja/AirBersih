from apps.users.models import Kasir


def is_kasir_exists(username: str) -> bool:
    """Check if a Kasir with the given username exists (case-insensitive)."""
    return Kasir.objects.filter(username__iexact=username.strip()).exists()


def create_kasir(
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    no_hp: str | None,
    is_active: bool,
) -> Kasir:
    """Create a new Kasir record with an unusable password."""
    user = Kasir(
        username=username.strip(),
        first_name=first_name,
        last_name=last_name,
        email=email,
        no_hp=no_hp,
        is_active=is_active,
    )
    user.set_unusable_password()
    user.save()
    return user


def upsert_kasir(
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    no_hp: str | None,
    is_active: bool,
) -> tuple[Kasir, bool]:
    """Create or update a Kasir record keyed by username."""
    obj, created = Kasir.objects.update_or_create(
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "no_hp": no_hp,
            "is_active": is_active,
        },
    )
    if created:
        obj.set_unusable_password()
        obj.save(update_fields=["password"])
    return obj, created

