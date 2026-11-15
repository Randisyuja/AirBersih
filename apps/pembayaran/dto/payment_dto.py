from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PaymentRecordInputDTO:
    tagihan_id: int
    jumlah_dibayar: Optional[int] = None
    metode_pembayaran: str = "Tunai"
    kasir_id: Optional[int] = None


@dataclass(frozen=True)
class PaymentSummaryDTO:
    total_pemasukan: int
    total_transaksi: int
    bulan: int
    tahun: int
