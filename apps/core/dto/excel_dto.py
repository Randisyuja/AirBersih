from dataclasses import dataclass, field


@dataclass
class ImportRowErrorDTO:
    """Represents a validation or persistence error for a single Excel row."""

    row_number: int
    field: str
    message: str


@dataclass
class ImportResultDTO:
    """Summary of an Excel import operation."""

    total_rows: int = 0
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    errors: list[ImportRowErrorDTO] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
