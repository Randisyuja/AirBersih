from apps.layanan.models import JenisLayanan
from apps.pelanggan.models import Langganan, Pelanggan
from apps.rumah.models import Rumah


def get_rumah_by_no(no_rumah: str) -> Rumah | None:
    """Look up a Rumah by case-insensitive no_rumah."""
    return Rumah.objects.filter(no_rumah__iexact=no_rumah.strip()).first()


def is_rumah_occupied(rumah: Rumah) -> bool:
    """Check if the specified Rumah is already occupied by any Pelanggan."""
    return Pelanggan.objects.filter(rumah=rumah).exists()


def is_pelanggan_exists(nama: str) -> bool:
    """Check if a Pelanggan with the given name exists (case-insensitive)."""
    return Pelanggan.objects.filter(nama__iexact=nama.strip()).exists()


def create_pelanggan(
    nama: str, no_hp: str | None, rumah: Rumah | None
) -> Pelanggan:
    """Create a new Pelanggan record."""
    return Pelanggan.objects.create(
        nama=nama,
        no_hp=no_hp,
        rumah=rumah,
    )


def upsert_pelanggan(
    nama: str, no_hp: str | None, rumah: Rumah | None
) -> tuple[Pelanggan, bool]:
    """Create or update a Pelanggan record keyed by rumah (if present) or nama."""
    if rumah is not None:
        return Pelanggan.objects.update_or_create(
            rumah=rumah,
            defaults={"nama": nama, "no_hp": no_hp},
        )
    return Pelanggan.objects.update_or_create(
        nama=nama,
        rumah=None,
        defaults={"no_hp": no_hp},
    )


def get_pelanggan_by_name(nama: str) -> Pelanggan | None:
    """Look up a Pelanggan by case-insensitive nama."""
    return Pelanggan.objects.filter(nama__iexact=nama.strip()).first()


def get_jenis_layanan_by_name(nama_jenis: str) -> JenisLayanan | None:
    """Look up a JenisLayanan by case-insensitive nama_jenis."""
    return JenisLayanan.objects.filter(
        nama_jenis__iexact=nama_jenis.strip()
    ).first()


def is_langganan_exists(
    pelanggan: Pelanggan, jenis_layanan: JenisLayanan
) -> bool:
    """Check if a Langganan record exists for (pelanggan, jenis_layanan)."""
    return Langganan.objects.filter(
        pelanggan=pelanggan,
        jenis_layanan=jenis_layanan,
    ).exists()


def create_langganan(
    pelanggan: Pelanggan,
    jenis_layanan: JenisLayanan,
    harga: int,
    aktif: bool,
) -> Langganan:
    """Create a new Langganan record."""
    return Langganan.objects.create(
        pelanggan=pelanggan,
        jenis_layanan=jenis_layanan,
        harga=harga,
        aktif=aktif,
    )


def upsert_langganan(
    pelanggan: Pelanggan,
    jenis_layanan: JenisLayanan,
    harga: int,
    aktif: bool,
) -> tuple[Langganan, bool]:
    """Create or update a Langganan record keyed by (pelanggan, jenis_layanan)."""
    return Langganan.objects.update_or_create(
        pelanggan=pelanggan,
        jenis_layanan=jenis_layanan,
        defaults={"harga": harga, "aktif": aktif},
    )

