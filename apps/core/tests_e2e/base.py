import io
from typing import Any

import openpyxl
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

User = get_user_model()

XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def make_xlsx_file(
    headers: list[str],
    rows: list[list[Any]],
    filename: str = "upload.xlsx",
) -> SimpleUploadedFile:
    """Create an in-memory .xlsx file wrapped in a SimpleUploadedFile."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return SimpleUploadedFile(
        name=filename,
        content=buf.read(),
        content_type=XLSX_CONTENT_TYPE,
    )


def make_empty_xlsx_file(
    include_headers: bool = False,
    headers: list[str] | None = None,
    filename: str = "empty.xlsx",
) -> SimpleUploadedFile:
    """Create an empty .xlsx file, optionally with only headers."""
    wb = openpyxl.Workbook()
    ws = wb.active
    if include_headers and headers:
        ws.append(headers)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return SimpleUploadedFile(
        name=filename,
        content=buf.read(),
        content_type=XLSX_CONTENT_TYPE,
    )


def make_corrupt_xlsx_file(filename: str = "corrupt.xlsx") -> SimpleUploadedFile:
    """Create a corrupt file with .xlsx extension containing invalid bytes."""
    return SimpleUploadedFile(
        name=filename,
        content=b"THIS_IS_NOT_A_VALID_ZIP_OR_XLSX_DATA",
        content_type=XLSX_CONTENT_TYPE,
    )


class BaseExcelE2ETestCase(TestCase):
    """Base TestCase providing setup, authentication, and assertions for Excel E2E tests."""

    def setUp(self) -> None:
        super().setUp()
        self.admin_user = User.objects.create_user(
            username="qa_e2e_admin",
            password="E2ePassword123!",
            email="qa_admin@example.com",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.admin_user)

    def resolve_url(self, route_name: str, fallback_path: str = "") -> str:
        """Resolve route name with fallback to absolute path if not yet registered."""
        try:
            return reverse(route_name)
        except NoReverseMatch:
            if fallback_path:
                return fallback_path
            raise

    def assert_excel_download_response(
        self,
        response,
        expected_headers: list[str] | None = None,
        min_data_rows: int = 0,
        expected_filename_part: str | None = None,
    ) -> list[list[Any]]:
        """Verify an HTTP response is a valid Excel download attachment."""
        self.assertEqual(
            response.status_code,
            200,
            f"Expected HTTP 200, got {response.status_code}",
        )
        self.assertEqual(
            response.get("Content-Type"),
            XLSX_CONTENT_TYPE,
            f"Expected Content-Type '{XLSX_CONTENT_TYPE}', got '{response.get('Content-Type')}'",
        )
        content_disp = response.get("Content-Disposition", "")
        self.assertIn("attachment", content_disp.lower())
        if expected_filename_part:
            self.assertIn(expected_filename_part.lower(), content_disp.lower())

        try:
            wb = openpyxl.load_workbook(io.BytesIO(response.content), data_only=True)
        except Exception as exc:
            self.fail(f"Downloaded content is not a valid Excel workbook: {exc}")

        ws = wb.active
        self.assertIsNotNone(ws, "Active worksheet not found in downloaded workbook")
        rows = list(ws.iter_rows(values_only=True))

        if expected_headers is not None:
            self.assertGreaterEqual(
                len(rows), 1, "Downloaded workbook is completely empty (no header row)"
            )
            actual_headers = [
                str(h).strip().lower() if h is not None else "" for h in rows[0]
            ]
            normalized_expected = [h.strip().lower() for h in expected_headers]
            self.assertEqual(
                actual_headers,
                normalized_expected,
                f"Headers mismatch. Expected: {normalized_expected}, Got: {actual_headers}",
            )

        data_rows = [list(r) for r in rows[1:]] if len(rows) > 1 else []
        if min_data_rows > 0:
            self.assertGreaterEqual(
                len(data_rows),
                min_data_rows,
                f"Expected at least {min_data_rows} data rows, found {len(data_rows)}",
            )
        return data_rows

    def get_flash_messages(self, response) -> list[str]:
        """Extract flash messages from response context."""
        if hasattr(response, "context") and response.context and "messages" in response.context:
            return [str(m) for m in response.context["messages"]]
        return []
