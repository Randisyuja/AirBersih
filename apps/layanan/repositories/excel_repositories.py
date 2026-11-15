from apps.layanan.models import JenisLayanan, Layanan


def is_layanan_exists(nama_layanan: str) -> bool:
    """Check if a Layanan with the given name exists (case-insensitive)."""
    return Layanan.objects.filter(nama_layanan__iexact=nama_layanan.strip()).exists()


def create_layanan(nama_layanan: str) -> Layanan:
    """Create a new Layanan record."""
    normalized = nama_layanan.strip().upper()
    return Layanan.objects.create(nama_layanan=normalized)


def upsert_layanan(nama_layanan: str) -> tuple[Layanan, bool]:
    """Create or update a Layanan record keyed by uppercase nama_layanan."""
    normalized = nama_layanan.strip().upper()
    return Layanan.objects.update_or_create(
        nama_layanan=normalized,
        defaults={"nama_layanan": normalized},
    )


def get_layanan_by_name(nama_layanan: str) -> Layanan | None:
    """Look up a Layanan by case-insensitive name."""
    return Layanan.objects.filter(nama_layanan__iexact=nama_layanan.strip()).first()


def is_jenis_layanan_exists(layanan: Layanan, nama_jenis: str) -> bool:
    """Check if a JenisLayanan exists for the given Layanan and nama_jenis."""
    return JenisLayanan.objects.filter(
        layanan=layanan,
        nama_jenis__iexact=nama_jenis.strip(),
    ).exists()


def create_jenis_layanan(
    layanan: Layanan, nama_jenis: str, tarif: int
) -> JenisLayanan:
    """Create a new JenisLayanan record."""
    return JenisLayanan.objects.create(
        layanan=layanan,
        nama_jenis=nama_jenis.strip(),
        tarif=tarif,
    )


def upsert_jenis_layanan(
    layanan: Layanan, nama_jenis: str, tarif: int
) -> tuple[JenisLayanan, bool]:
    """Create or update a JenisLayanan record keyed by (layanan, nama_jenis)."""
    return JenisLayanan.objects.update_or_create(
        layanan=layanan,
        nama_jenis=nama_jenis,
        defaults={"tarif": tarif},
    )

