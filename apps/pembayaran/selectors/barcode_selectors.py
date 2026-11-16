"""Barcode and subscription (Langganan.kode_pelanggan) selectors (ADR 002 §1.3)."""

from typing import List, Optional
from django.utils import timezone
from apps.pelanggan.models import Langganan, Pelanggan, Tagihan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.dto.barcode_dto import (
    BarcodeResolutionDTO,
    CustomerProfileDTO,
    DueDTO,
    TariffDTO,
)


def get_langganan_by_kode(code: str) -> Optional[Langganan]:
    """Retrieves Langganan by unique kode_pelanggan with preloaded customer, house, and service."""
    if not code:
        return None
    cleaned = code.strip()
    return (
        Langganan.objects.filter(kode_pelanggan__iexact=cleaned)
        .select_related(
            "pelanggan",
            "pelanggan__rumah",
            "jenis_layanan",
            "jenis_layanan__layanan",
        )
        .first()
    )


def get_pelanggan_by_barcode(barcode: str) -> Optional[Pelanggan]:
    """
    Retrieves Pelanggan by Langganan.kode_pelanggan OR Pelanggan.barcode
    with prefetched house relation.
    """
    if not barcode:
        return None
    cleaned = barcode.strip()
    pelanggan = (
        Pelanggan.objects.filter(barcode__iexact=cleaned)
        .select_related("rumah")
        .first()
    )
    if pelanggan:
        return pelanggan

    langganan = get_langganan_by_kode(cleaned)
    return langganan.pelanggan if langganan else None


def get_active_tariffs_by_pelanggan(pelanggan: Pelanggan) -> List[TariffDTO]:
    """Retrieves all active tariffs/subscriptions for a customer."""
    subscriptions = (
        Langganan.objects.filter(pelanggan=pelanggan, aktif=True)
        .select_related("jenis_layanan", "jenis_layanan__layanan")
        .order_by("jenis_layanan__layanan__nama_layanan")
    )
    return [
        TariffDTO(
            jenis_layanan_id=s.jenis_layanan_id,
            kode_pelanggan=s.kode_pelanggan or "",
            layanan=s.jenis_layanan.layanan.nama_layanan,
            nama_jenis=s.jenis_layanan.nama_jenis,
            tarif=s.harga,
        )
        for s in subscriptions
    ]


def get_pending_dues_by_pelanggan(
    pelanggan: Pelanggan, jenis_layanan_id: Optional[int] = None
) -> List[DueDTO]:
    """Retrieves unpaid dues (Tagihan Belum) for a customer (optionally prioritized/filtered)."""
    qs = Tagihan.objects.filter(
        pelanggan=pelanggan, status_tagihan=StatusChoice.Belum
    ).select_related("jenis_layanan", "jenis_layanan__layanan")

    dues_all = list(qs.order_by("tahun", "bulan", "id_tagihan"))
    if jenis_layanan_id is not None:
        dues_all.sort(key=lambda t: (0 if t.jenis_layanan_id == jenis_layanan_id else 1, t.tahun, t.bulan))

    return [
        DueDTO(
            id=t.id_tagihan,
            jenis_layanan_id=t.jenis_layanan_id,
            nama_jenis=t.jenis_layanan.nama_jenis,
            layanan=t.jenis_layanan.layanan.nama_layanan,
            bulan=t.bulan,
            nama_bulan=t.get_bulan_display(),
            tahun=t.tahun,
            jumlah=t.jumlah_bayar or 0,
            is_dynamic_tariff=bool(
                not t.jenis_layanan.tarif
                or t.jenis_layanan.tarif <= 0
                or not t.jumlah_bayar
                or t.jumlah_bayar <= 0
            ),
        )
        for t in dues_all
    ]


def get_customer_dues_by_barcode(barcode: str) -> Optional[BarcodeResolutionDTO]:
    """
    Look up subscription (`Langganan.kode_pelanggan`) or customer (`Pelanggan.barcode`)
    and assemble full BarcodeResolutionDTO containing customer profile, matched subscription
    (jenis_layanan + harga), active tariffs, and pending dues.
    """
    if not barcode:
        return None
    cleaned = barcode.strip()

    matched_langganan = get_langganan_by_kode(cleaned)
    if matched_langganan:
        pelanggan = matched_langganan.pelanggan
        resolved_code = matched_langganan.kode_pelanggan or pelanggan.barcode or ""
    else:
        pelanggan = get_pelanggan_by_barcode(cleaned)
        if not pelanggan:
            return None
        resolved_code = pelanggan.barcode or ""
        matched_langganan = (
            Langganan.objects.filter(pelanggan=pelanggan, aktif=True)
            .select_related("jenis_layanan", "jenis_layanan__layanan")
            .first()
        )

    alamat = pelanggan.rumah.no_rumah if pelanggan.rumah else "-"
    rt = pelanggan.rumah.rt if pelanggan.rumah else "-"
    customer_dto = CustomerProfileDTO(
        id=pelanggan.id_pelanggan,
        nama=pelanggan.nama,
        alamat=alamat,
        rt=rt,
        no_hp=pelanggan.no_hp,
        barcode=resolved_code,
    )

    preferred_jenis_id = (
        matched_langganan.jenis_layanan_id if matched_langganan else None
    )
    tariffs = get_active_tariffs_by_pelanggan(pelanggan)
    dues = get_pending_dues_by_pelanggan(pelanggan, jenis_layanan_id=preferred_jenis_id)
    total_due = sum(d.jumlah for d in dues)

    now = timezone.now()
    next_bulan = dues[0].bulan if dues else now.month
    next_tahun = dues[0].tahun if dues else now.year

    subscription_dict = None
    if matched_langganan:
        subscription_dict = {
            "langganan_id": matched_langganan.pk,
            "kode_pelanggan": matched_langganan.kode_pelanggan or resolved_code,
            "jenis_layanan_id": matched_langganan.jenis_layanan_id,
            "layanan": matched_langganan.jenis_layanan.layanan.nama_layanan,
            "nama_jenis": matched_langganan.jenis_layanan.nama_jenis,
            "harga": matched_langganan.harga,
            "next_bulan": next_bulan,
            "next_tahun": next_tahun,
        }

    return BarcodeResolutionDTO(
        customer=customer_dto,
        tariffs=tariffs,
        dues=dues,
        total_due=total_due,
        status="success",
        subscription=subscription_dict,
    )
