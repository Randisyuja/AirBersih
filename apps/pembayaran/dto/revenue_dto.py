"""Revenue analytics DTOs for pembayaran (ADR 002 §1.5)."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class MonthlyRevenueItemDTO:
    """Single month revenue breakdown item."""
    bulan: int
    label: str
    total: int


@dataclass(frozen=True)
class ServiceRevenueSummaryDTO:
    """Complete annual and monthly revenue summary for a service."""
    layanan: str
    tahun: int
    annual_total: int
    selected_bulan: Optional[int]
    selected_month_total: int
    monthly_breakdown: List[int]
