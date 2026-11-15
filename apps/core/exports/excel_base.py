import io
from typing import Any

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from apps.core.exceptions.excel_exceptions import ExcelHeaderError, ExcelValidationError

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_cell_value(value: Any) -> Any:
    """Prevent Excel formula injection by prefixing dangerous leading characters."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return f"'{value}"
    return value


def build_workbook(
    headers: list[str],
    rows: list[list[Any]],
    sheet_title: str = "Data",
) -> io.BytesIO:
    """Build a styled .xlsx workbook in memory and return it as a BytesIO buffer."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")

    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    for row in rows:
        ws.append([_sanitize_cell_value(val) for val in row])

    for col_idx, header in enumerate(headers, start=1):
        max_len = len(str(header))
        for row_idx in range(2, len(rows) + 2):
            val = ws.cell(row=row_idx, column=col_idx).value
            if val is not None:
                max_len = max(max_len, len(str(val)))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 50)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def parse_workbook(
    file_obj: Any,
    expected_headers: list[str],
) -> list[tuple[int, dict[str, Any]]]:
    """Validate an uploaded .xlsx file and return (1-based row_number, row_dict) pairs."""
    if file_obj is None:
        raise ExcelValidationError("File tidak ditemukan.")

    filename = getattr(file_obj, "name", "")
    if not filename.lower().endswith(".xlsx"):
        raise ExcelValidationError("Format file harus .xlsx.")

    size = getattr(file_obj, "size", None)
    if size is not None and size > MAX_UPLOAD_SIZE_BYTES:
        raise ExcelValidationError("Ukuran file maksimal 5 MB.")

    try:
        wb = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    except Exception as exc:
        raise ExcelValidationError(f"File Excel tidak valid atau rusak: {exc}") from exc

    try:
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        try:
            raw_headers = next(rows_iter)
        except StopIteration as exc:
            raise ExcelHeaderError("File Excel kosong, header tidak ditemukan.") from exc

        actual_headers = [
            str(h).strip().lower() if h is not None else "" for h in raw_headers
        ]
        normalized_expected = [h.strip().lower() for h in expected_headers]

        missing = [h for h in normalized_expected if h not in actual_headers]
        if missing:
            raise ExcelHeaderError(
                f"Kolom wajib tidak ditemukan: {', '.join(missing)}"
            )

        header_index = {h: idx for idx, h in enumerate(actual_headers)}
        parsed_rows: list[tuple[int, dict[str, Any]]] = []

        for row_num, raw_row in enumerate(rows_iter, start=2):
            if raw_row is None or all(
                cell is None or str(cell).strip() == "" for cell in raw_row
            ):
                continue
            row_dict: dict[str, Any] = {}
            for exp_h, norm_h in zip(expected_headers, normalized_expected):
                idx = header_index[norm_h]
                val = raw_row[idx] if idx < len(raw_row) else None
                row_dict[exp_h] = val.strip() if isinstance(val, str) else val
            parsed_rows.append((row_num, row_dict))

        return parsed_rows
    finally:
        wb.close()
