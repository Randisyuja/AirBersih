from typing import Any

from django.db import transaction

from apps.core.dto.excel_dto import ImportResultDTO, ImportRowErrorDTO
from apps.core.exports.excel_base import parse_workbook
from apps.users.exports.excel_export import KASIR_HEADERS
from apps.users.repositories.excel_repositories import (
    create_kasir,
    is_kasir_exists,
    upsert_kasir,
)


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "ya", "yes", "aktif"}


@transaction.atomic
def import_kasir_from_excel(file_obj: Any) -> ImportResultDTO:
    """Parse and import Kasir rows from an uploaded .xlsx file."""
    rows = parse_workbook(file_obj, KASIR_HEADERS)
    result = ImportResultDTO(total_rows=len(rows))
    seen_usernames: set[str] = set()

    for row_num, data in rows:
        username = str(data.get("username") or "").strip()
        first_name = str(data.get("first_name") or "").strip()
        last_name = str(data.get("last_name") or "").strip()
        email = str(data.get("email") or "").strip()
        no_hp = str(data.get("no_hp") or "").strip() or None
        is_active = _parse_bool(data.get("is_active", True))

        if not username:
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num, "username", "Username wajib diisi."
                )
            )
            continue

        if is_kasir_exists(username) or (username.lower() in seen_usernames):
            result.skipped_count += 1
            result.errors.append(
                ImportRowErrorDTO(
                    row_num, "username", f"Username '{username}' sudah terdaftar."
                )
            )
            continue

        create_kasir(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            no_hp=no_hp,
            is_active=is_active,
        )
        seen_usernames.add(username.lower())
        result.created_count += 1

    return result


import_users_from_excel = import_kasir_from_excel

