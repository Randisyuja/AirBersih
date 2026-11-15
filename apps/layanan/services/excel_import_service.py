from typing import Any

from django.db import transaction

from apps.core.dto.excel_dto import ImportResultDTO, ImportRowErrorDTO
from apps.core.exports.excel_base import parse_workbook
from apps.layanan.exports.excel_export import (
    JENIS_LAYANAN_HEADERS,
    LAYANAN_HEADERS,
)
from apps.layanan.repositories.excel_repositories import (
    create_jenis_layanan,
    create_layanan,
    get_layanan_by_name,
    is_jenis_layanan_exists,
    is_layanan_exists,
    upsert_jenis_layanan,
    upsert_layanan,
)


@transaction.atomic
def import_layanan_from_excel(file_obj: Any) -> ImportResultDTO:
    """Parse and import Layanan rows from an uploaded .xlsx file."""
    rows = parse_workbook(file_obj, LAYANAN_HEADERS)
    result = ImportResultDTO(total_rows=len(rows))
    seen_layanan: set[str] = set()

    for row_num, data in rows:
        nama_layanan = str(data.get("nama_layanan") or "").strip()
        if not nama_layanan:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num, "nama_layanan", "Nama layanan wajib diisi."
                )
            )
            continue

        if is_layanan_exists(nama_layanan) or (nama_layanan.lower() in seen_layanan):
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num,
                    "nama_layanan",
                    f"Layanan '{nama_layanan}' sudah terdaftar.",
                )
            )
            continue

        create_layanan(nama_layanan=nama_layanan)
        seen_layanan.add(nama_layanan.lower())
        result.created_count += 1

    return result


@transaction.atomic
def import_jenis_layanan_from_excel(file_obj: Any) -> ImportResultDTO:
    """Parse and import JenisLayanan rows from an uploaded .xlsx file."""
    rows = parse_workbook(file_obj, JENIS_LAYANAN_HEADERS)
    result = ImportResultDTO(total_rows=len(rows))
    seen_jenis: set[tuple[int, str]] = set()

    for row_num, data in rows:
        layanan_name = str(data.get("layanan") or "").strip()
        nama_jenis = str(data.get("nama_jenis") or "").strip()
        raw_tarif = data.get("tarif")

        if not layanan_name:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(row_num, "layanan", "Nama layanan wajib diisi.")
            )
            continue

        layanan = get_layanan_by_name(layanan_name)
        if layanan is None:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num,
                    "layanan",
                    f"Layanan '{layanan_name}' tidak ditemukan.",
                )
            )
            continue

        if not nama_jenis:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num, "nama_jenis", "Nama jenis wajib diisi."
                )
            )
            continue

        try:
            tarif = int(float(str(raw_tarif).strip()))
        except (TypeError, ValueError):
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(row_num, "tarif", "Tarif harus berupa angka.")
            )
            continue

        if tarif < 0:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num, "tarif", "Tarif tidak boleh negatif."
                )
            )
            continue

        jenis_key = (layanan.id_layanan, nama_jenis.lower())
        if is_jenis_layanan_exists(layanan, nama_jenis) or (jenis_key in seen_jenis):
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num,
                    "nama_jenis",
                    f"Jenis layanan '{nama_jenis}' untuk layanan '{layanan_name}' sudah terdaftar.",
                )
            )
            continue

        create_jenis_layanan(
            layanan=layanan, nama_jenis=nama_jenis, tarif=tarif
        )
        seen_jenis.add(jenis_key)
        result.created_count += 1

    return result
