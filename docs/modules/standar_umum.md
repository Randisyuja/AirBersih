# Standar Umum Rekayasa Modul (Engineering Guidelines)

Dokumen ini mendefinisikan standar arsitektur kode, konvensi penamaan, dan pola perancangan yang berlaku untuk seluruh Django App dalam proyek **WaterPay / AirBersih** (`apps.users`, `apps.layanan`, `apps.rumah`, `apps.pelanggan`, `apps.pembayaran`).

---

## 📁 Struktur Standar Django App

Seluruh aplikasi modular ditempatkan di bawah folder `apps/`:

```text
apps/<app_name>/
├── __init__.py
├── apps.py                  <-- name = 'apps.<app_name>', label = '<app_name>'
├── urls.py
├── models.py
├── forms.py
├── choices.py               <-- models.TextChoices / models.IntegerChoices
├── selectors/               <-- Kueri ORM murni (Read-Only)
│   ├── __init__.py
│   └── <feature>_selectors.py
├── services/                <-- Logika bisnis, validasi domain, transaksi atomic
│   ├── __init__.py
│   └── <feature>_services.py
├── exports/                 <-- Generator file laporan (PDF ReportLab, Excel OpenPyXL)
│   ├── __init__.py
│   └── <feature>_exporter.py
├── views/                   <-- HTTP Controllers (Thin Views)
│   ├── __init__.py
│   └── <feature>_views.py
└── tests/                   <-- Unit tests terisolasi
    ├── __init__.py
    ├── test_selectors.py
    └── test_services.py
```

---

## ⚙️ Prinsip Pemisahan Lapisan (Separation of Concerns)

### 1. View Layer (Thin Controller)
- **Tanggung Jawab:** Ekstraksi parameter HTTP (`request.GET`, `request.POST`), pemanggilan Service/Selector, feedback notifikasi `messages`, dan rendering template.
- **Dilarang Keras:** Menjalankan mutasi transaksi langsung seperti `Pembayaran.objects.create(...)` atau `tagihan.save()` langsung di dalam View handler.

### 2. Service Layer (Business Core)
- Dilarang mengimpor atau mengakses objek `request`. Gunakan parameter tipe data murni Python atau DTO.
- Seluruh mutasi yang melibatkan relasi `Tagihan` dan `Pembayaran` **wajib dibungkus `@transaction.atomic`** untuk mencegah inkonsistensi status.

```python
from django.db import transaction
from django.utils import timezone
from apps.pembayaran.models import Pembayaran
from apps.pelanggan.models import Tagihan
from apps.pembayaran.choices import StatusChoice

@transaction.atomic
def bayar_tagihan(tagihan_id: int, kasir_user) -> Pembayaran:
    tagihan = Tagihan.objects.select_for_update().get(pk=tagihan_id)
    if tagihan.status_tagihan == StatusChoice.Lunas:
        raise ValueError("Tagihan sudah berstatus lunas.")
        
    tagihan.status_tagihan = StatusChoice.Lunas
    tagihan.save()
    
    pembayaran, _ = Pembayaran.objects.get_or_create(
        pelanggan=tagihan.pelanggan,
        jenis_layanan=tagihan.jenis_layanan,
        bulan=tagihan.bulan,
        tahun=tagihan.tahun,
        defaults={
            "status_bayar": StatusChoice.Lunas,
            "kasir": kasir_user,
            "tgl_pembayaran": timezone.now(),
            "jumlah_bayar": tagihan.jumlah_bayar
        }
    )
    return pembayaran
```

### 3. Selector Layer (Pure Queries)
- Seluruh kueri pembacaan data, aggregasi, dan sorting khusus (seperti pemilahan blok nomor rumah via `Substr` dan `Cast`) diisolasi ke dalam fungsi selector.
- Gunakan `.select_related()` untuk relasi foreign key tunggal (`pelanggan__rumah`, `jenis_layanan`, `kasir`) untuk mencegah masalah **N+1 query**.

### 4. Export Layer (PDF & Excel)
- Seluruh perakitan dokumen biner (ReportLab dan OpenPyXL) ditempatkan di `exports/` dan wajib mengembalikan buffer biner (`io.BytesIO`), bukan `HttpResponse` langsung, agar dapat diuji secara terisolasi tanpa server web.
