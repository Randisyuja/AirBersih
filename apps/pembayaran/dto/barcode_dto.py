from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CustomerProfileDTO:
    id: int
    nama: str
    alamat: str
    no_hp: Optional[str] = None
    barcode: str = ""
    rt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nama": self.nama,
            "alamat": self.alamat,
            "rt": self.rt,
            "no_hp": self.no_hp or "",
            "barcode": self.barcode,
        }


@dataclass(frozen=True)
class TariffDTO:
    layanan: str
    nama_jenis: str
    tarif: int
    jenis_layanan_id: Optional[int] = None
    kode_pelanggan: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "jenis_layanan_id": self.jenis_layanan_id,
            "kode_pelanggan": self.kode_pelanggan,
            "layanan": self.layanan,
            "nama_jenis": self.nama_jenis,
            "tarif": self.tarif,
        }


@dataclass(frozen=True)
class DueDTO:
    id: int
    layanan: str
    bulan: int
    tahun: int
    jumlah: int
    jenis_layanan_id: Optional[int] = None
    nama_jenis: str = ""
    nama_bulan: str = ""
    is_dynamic_tariff: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "jenis_layanan_id": self.jenis_layanan_id,
            "nama_jenis": self.nama_jenis,
            "layanan": self.layanan,
            "bulan": self.bulan,
            "nama_bulan": self.nama_bulan,
            "tahun": self.tahun,
            "jumlah": self.jumlah,
            "is_dynamic_tariff": self.is_dynamic_tariff,
        }


@dataclass(frozen=True)
class BarcodeResolutionDTO:
    customer: CustomerProfileDTO
    tariffs: List[TariffDTO] = field(default_factory=list)
    dues: List[DueDTO] = field(default_factory=list)
    total_due: int = 0
    status: str = "success"
    subscription: Optional[Dict[str, Any]] = None

    @property
    def pelanggan_id(self) -> int:
        return self.customer.id

    @property
    def nama(self) -> str:
        return self.customer.nama

    @property
    def alamat(self) -> str:
        return self.customer.alamat

    @property
    def barcode(self) -> str:
        return self.customer.barcode

    @property
    def pending_dues(self) -> List[DueDTO]:
        return self.dues

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "customer": self.customer.to_dict(),
            "subscription": self.subscription,
            "tariffs": [t.to_dict() for t in self.tariffs],
            "dues": [d.to_dict() for d in self.dues],
            "total_due": self.total_due,
        }
