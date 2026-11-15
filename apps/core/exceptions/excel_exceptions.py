class ExcelValidationError(Exception):
    """Raised when an uploaded Excel file fails structural or content validation."""


class ExcelHeaderError(ExcelValidationError):
    """Raised when the Excel sheet headers do not match expected columns."""
