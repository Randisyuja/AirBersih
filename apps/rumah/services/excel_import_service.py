from typing import Any

from django.db import transaction

from apps.core.dto.excel_dto import ImportResultDTO, ImportRowErrorDTO
from apps.core.exports.excel_base import parse_workbook
from apps.rumah.exports.excel_export import RUMAH_HEADERS
from apps.rumah.repositories.excel_repositories import (
    create_rumah,
    is_rumah_exists,
    upsert_rumah,
)


@transaction.atomic
def import_rumah_from_excel(file_obj: Any) -> ImportResultDTO:
    """Parse and import Rumah rows from an uploaded .xlsx file."""
    rows = parse_workbook(file_obj, RUMAH_HEADERS)
    result = ImportResultDTO(total_rows=len(rows))
    seen_no_rumah: set[str] = set()

    for row_num, data in rows:
        rt = str(data.get("rt") or "").strip()
        no_rumah = str(data.get("no_rumah") or "").strip()

        if not rt:
            result.skipped_count += 1
            result.errors.append(ImportRowErrorDTO(row_num, "rt", "RT wajib diisi."))
            continue
        if not no_rumah:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(row_num, "no_rumah", "Nomor rumah wajib diisi.")
            )
            continue

        if is_rumah_exists(no_rumah) or (no_rumah.lower() in seen_no_rumah):
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num, "no_rumah", f"Nomor rumah '{no_rumah}' sudah terdaftar."
                )
            )
            continue

        create_rumah(rt=rt, no_rumah=no_rumah)
        seen_no_rumah.add(no_rumah.lower())
        result.created_count += 1

    return result
