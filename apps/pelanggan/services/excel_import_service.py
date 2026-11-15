from typing import Any

from django.db import transaction

from apps.core.dto.excel_dto import ImportResultDTO, ImportRowErrorDTO
from apps.core.exports.excel_base import parse_workbook
from apps.pelanggan.exports.excel_export import (
    LANGGANAN_HEADERS,
    PELANGGAN_HEADERS,
)
from apps.pelanggan.repositories.excel_repositories import (
    create_langganan,
    create_pelanggan,
    get_jenis_layanan_by_name,
    get_pelanggan_by_name,
    get_rumah_by_no,
    is_langganan_exists,
    is_pelanggan_exists,
    is_rumah_occupied,
    upsert_langganan,
    upsert_pelanggan,
)


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "ya", "yes", "aktif"}


@transaction.atomic
def import_pelanggan_from_excel(file_obj: Any) -> ImportResultDTO:
    """Parse and import Pelanggan rows from an uploaded .xlsx file."""
    rows = parse_workbook(file_obj, PELANGGAN_HEADERS)
    result = ImportResultDTO(total_rows=len(rows))
    seen_names: set[str] = set()
    seen_rumah_ids: set[int] = set()

    for row_num, data in rows:
        nama = str(data.get("nama") or "").strip()
        no_hp = str(data.get("no_hp") or "").strip() or None
        no_rumah = str(data.get("no_rumah") or "").strip()

        if not nama:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(row_num, "nama", "Nama pelanggan wajib diisi.")
            )
            continue

        if is_pelanggan_exists(nama) or (nama.lower() in seen_names):
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num, "nama", f"Pelanggan '{nama}' sudah terdaftar."
                )
            )
            continue

        rumah = None
        if no_rumah:
            rumah = get_rumah_by_no(no_rumah)
            if rumah is None:
                result.skipped_count += 1
                result.errors.append(
                    ImportRowErrorDTO(
                        row_num,
                        "no_rumah",
                        f"Rumah '{no_rumah}' tidak ditemukan.",
                    )
                )
                continue

            if is_rumah_occupied(rumah) or (rumah.id_rumah in seen_rumah_ids):
                result.skipped_count += 1
                result.errors.append(
                    ImportRowErrorDTO(
                        row_num,
                        "no_rumah",
                        f"Rumah '{no_rumah}' sudah dihuni oleh pelanggan lain.",
                    )
                )
                continue

        create_pelanggan(nama=nama, no_hp=no_hp, rumah=rumah)
        seen_names.add(nama.lower())
        if rumah is not None:
            seen_rumah_ids.add(rumah.id_rumah)
        result.created_count += 1

    return result


@transaction.atomic
def import_langganan_from_excel(file_obj: Any) -> ImportResultDTO:
    """Parse and import Langganan rows from an uploaded .xlsx file."""
    rows = parse_workbook(file_obj, LANGGANAN_HEADERS)
    result = ImportResultDTO(total_rows=len(rows))
    seen_langganan: set[tuple[int, int]] = set()

    for row_num, data in rows:
        pelanggan_name = str(data.get("pelanggan") or "").strip()
        jenis_name = str(data.get("jenis_layanan") or "").strip()
        raw_harga = data.get("harga")
        aktif = _parse_bool(data.get("aktif", True))

        if not pelanggan_name:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num, "pelanggan", "Nama pelanggan wajib diisi."
                )
            )
            continue

        pelanggan = get_pelanggan_by_name(pelanggan_name)
        if pelanggan is None:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num,
                    "pelanggan",
                    f"Pelanggan '{pelanggan_name}' tidak ditemukan.",
                )
            )
            continue

        if not jenis_name:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num, "jenis_layanan", "Nama jenis layanan wajib diisi."
                )
            )
            continue

        jenis_layanan = get_jenis_layanan_by_name(jenis_name)
        if jenis_layanan is None:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num,
                    "jenis_layanan",
                    f"Jenis layanan '{jenis_name}' tidak ditemukan.",
                )
            )
            continue

        try:
            harga = int(float(str(raw_harga).strip()))
        except (TypeError, ValueError):
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(row_num, "harga", "Harga harus berupa angka.")
            )
            continue

        if harga < 0:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num, "harga", "Harga tidak boleh negatif."
                )
            )
            continue

        langganan_key = (pelanggan.id_pelanggan, jenis_layanan.id_jenis)
        if is_langganan_exists(pelanggan, jenis_layanan) or (
            langganan_key in seen_langganan
        ):
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num,
                    "jenis_layanan",
                    f"Langganan '{pelanggan_name}' untuk '{jenis_name}' sudah ada.",
                )
            )
            continue

        create_langganan(
            pelanggan=pelanggan,
            jenis_layanan=jenis_layanan,
            harga=harga,
            aktif=aktif,
        )
        seen_langganan.add(langganan_key)
        result.created_count += 1

    return result
