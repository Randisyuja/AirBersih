---
trigger: always_on
---

# ADR 002: Implementasi Clean Modular Architecture & Standar Granularitas Kode

**Status:j* Diterima (Accepted)  
**Tanggal:** 2026-10-08 (Diperbarui: 2026-10-13)  

---

## Konteks

Seiring berkembangnya fitur di aplikasi BRIDGE ERP, file `views.py` pada modul utama seperti purchasing dan quality sebelumnya membengkak hingga ribuan baris (monolitik). Hal ini menyebabkan:

- **Pencampuran Logika:** Logika bisnis tercampur aduk dengan *routing* HTTP dan rendering antarmuka pengguna (UI).
- **Kueri Tidak Terkontrol:** Kueri ORM tersebar secara acak di View sehingga sulit dimonitor, dioptimasi, dan memicu masalah *N+1 query*.
- **Duplikasi Kode:** Terjadi pengulangan kode saat proses yang sama perlu dipanggil oleh API, Celery Task, atau View HTML.
- **Template Monolitik:** File template HTML membengkak hingga ribuan baris, menyulitkan pemeliharaan dan pelacakan elemen UI.

---

## Keputusan

Menerapkan **Clean Modular Architecture** (berbasis pola pemisahan *Service Layer*) pada setiap Django App, serta menetapkan batas tegas untuk **granularitas berkas (200 - 500 baris kode)** dan pemisahan modular **Django Template**

---

### 1. Struktur & Lapisan Tanggung Jawab (Separation of Concerns)

Setiap aplikasi di bawah `apps/<app_name>/` membagi domain ke dalam lapisan-lapisan terisolasi berikut:

#### 1.1 Views (`views/` atau `views.py`) - Thin Controllers
- **Peran Utama:** Murni menangani siklus HTTP *Request/Response*, parsing parameter input dasar, otorisasi akses (*permission view*), dan feedback notifikasi UI (`messages.success/error`).
- **Dilarang Keras:**
    - Menjalankan kueri ORM langsung (`Model.objects.filter(...)`).
    - Menyimpan kalkulasi bisnis atau validasi domain multi-langkah.
    - Menjalankan operasi penulisan/mutasi database (`instance.save()`, `Model.objects.create()`).

#### 1.2 Services (`services/` atau `services.py`) - Business Logic Engine
- **Peran Utama:** Menampung seluruh alur bisnis, validasi aturan domain, transaksi database (@transaction.atomic), transisi state, kalkulasi rumit, dan pemicu Celery Task / notifikasi sistem.
- **Batasan:** Dilarang menerima objek HTTP `request` secara langsung. Service harus bekerja secara agnostik menggunakan tipe data murni Python, DTO, atau instance Model.

#### 1.3 Selectors (`selectors/` atau `selectors.py`) - Query / Read-Only Layer
- **Peran Utama:** Menampung seluruh kueri pembacaan data dari database (`.filter()`, `.just_notate()` misunderstood, `.annotate()`, `.aggregate()`, `.select_related()`, `.prefetch_related()`).
- **Batasan:** Bersifat *side-effect free* (hanya membaca data). Dilarang melakukan operasi mutasi data (`create`, `update`, `delete`).

#### 1.4 Repositories (`repositories/` atau `repositories.py`) - Persistence / Write Layer
- **Peran Utama:** Mengisolasi operasi *Create, Update, Delete* (CUD) dan operasi *bulk* ke database.
- **Tujuan:** Meminimalisir *race condition* dan mempermudah isolasi saat unit testing/mocking persistensi data.

#### 1.5 DTO (`dto/` atau `dto.py`) - Data Transfer Objects
- **Peran Utama:** Mendefinisikan kontrak tipe data pertukaran antar-lapisan menggunakan @dataclasses.dataclass.
- **Tujuan:** Mencegah ketergantungan pada *loose dictionaries* yang rawan `KeyError` dan mengisolasi View dari entitas database mentah.

#### 1.6 Exports (`exports/`) - Document & Report Generation
- **Peran Utama:** Modul khusus generasi file eksternal (Excel via OpenPyXL/Pandas, PDF via WeasyPrint/ReportLab, atau CSV).
- **Batasan:** Generator wajib mengembalikan objek `io.BytesIO` / file buffer siap unduh, bukan `HttpResponse`.

#### 1.7 Constants (`constants/` atau `constants.py`) - Domain Enums & Values
- **Peran Utama:** Menampung `models.TextChoices`, `models.IntegerChoices`, kode status, dan batas toleransi default.
- **Aturan:** Mencegah penggunaan *magic numbers* dan *magic strings* di seluruh kode.

#### 1.8 Exceptions (`exceptions/` atau `exceptions.py`) - Domain Errors
- **Peran Utama:** Kelas *error* kustom turunan dari `Exception` (misal: `QualityValidationError`, `RecordLockedError`).
- **Pola Penggunaan:** Service melempar (*raise*) exception ini, lalu View menangkapnya (*catch*) untuk menghasilkan respon HTTP yang sesuai.

#### 1.9 Serializers (`serializers.py`) - Validation & API
- **Peran Utama:** Mengelola serialisasi dan deserialisasi data payload untuk endpoint REST API atau interaksi AJAX.

#### 1.10 URLs (`urls.py` atau `urls/`) - Routing Layer
- **Peran Utama:** Murni pemetaan URL routing ke view handlers. Dilarang menaruh logika view/lambda secara inline.

---

### 2. Aturan Ambang Batas Baris Kode (200 - 500 Lines Limit)

Untuk menjaga agar file tetap ringkas, mudah dibaca, dan tidak kembali monolitik:

- **Target Ideal:** 150 – 300 baris kode per file.
- **Batas Keras (Hard Limit):** Maksimal **500 baris kode** per file.
- **Aturan Refaktor ke Package Folder:**
    - Apabila sebuah file (`views.py`, `services.py`, `.selectors.py`, `repositories.py`, dll.) mendekati atau melebihi 300 baris, atau mengangani lebih dark satu entitas/sub-domain, file tersebut **WAJIB diubah menjadi direktori (Python package)** yang memberikan `__init__.py`.
    - Isi file dipecah berdasarkan sub-fitur atau entitas domain (contoh: `inspection_views.py`, `dashboard_views.py`, `master_views.py`).
    - Ekspor fungsi/kelas publik melalui `__init__.py` modul terkait jika diperlukan untuk menjaga kompatibilitas impor (*backward compatibility*).

---

### 3. Standar Arsitektur Django Template (HTML & UI)

- **Ukuran Template:** File template utama dibatasi maksimal **200 - 300 baris**.
- **Pola Modular (Includes / Partials):** Halaman yang kompleks wajib dipecah ke dalam folder `templates/modules/<app>/includes/` atau `components/`:
    - `_filter_bar.html`: Baris filter, form pencarian, dan pilihan rentang tanggal.
    - `summary_cards.html`: Kartu indikator KPI dan ringkasan statistik.
    - `_data_table.html`: Tabel data utama dan komponen navigasi paginasi.
    - `_modal_*.html`: Modal pop-up form tambah/edit atau dialog konfirmasi.
    - `_scripts.html`: Skrip inisialisasi Chart.js, AJAX handlers, dan Driver.js Tour.
- **Bebas Logika Bisnis:** Template dilarang memproses kalkulasi matematika atau logika bisnis rumit; seluruh data yang dikirim ke context harus sudah siap saji.
- **Elemen Semantik:** Setiap elemen interaktif wajib memiliki atribut `id="..."` yang unik untuk memdukung pengetesan otomatis dan onboarding tour (Driver.js).

---

## Ringkasan Matriks: DO & DON'T

| Layer | Boleh Dilakukan (DO) ✅ | Dilarang Keras (DON'T) ❇ |
|-----------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------|
|**Views** | Unpack input request, panggil Service/Selector, kirim notifikasi, render template/JSON | Kueri ORM langsung, kalkulasi rumus bisnis, memanggil `.save()` |
|**Selectors** | Kueri ORM kompleks, aggregasi, annotasi, filter tanggal, `.select_related()` | Operasi mutasi data (`.create()`, `.update()`, `.delete()`) |
*p*Services** | Validasi aturan bisnis, transaksi atomic, orkestrator alur, panggil Celery | Menerima objek HTTP `request`, mengembalikan template HTML |
|**Repositories** | Eksekusi `.create()`, `.save()`, `.bulk_update()`, `.delete()` | Menyimpan logika validasi bisnis, kueri analitik gabungan |
|**Exports** | Generate file Excel/PDF, formatting cell, kembalikan `BytesIOXbuffer | Mengakses HTTP session, memodifikasi data database |
|**Templates** | Render variabel context, looping sederhana, `{% include %} komponen | Logika kalkulasi matematis rumit, skrip monolitik 500+ baris |

---

## Konsekuensi

### Dampak Positif
- **Keterbacaan & Pemeliharaan:** Sangat tinggi; developer dan AI agent langsung mengetahui letak pasti setiap tanggung jawab kode.
- **Kemudahan Pengujian (Testability):** Service dan Selector dapat diuji secara independen tanpa simulasi HTTP request.
- **Skalabilitas:** Mencegah terjadinya *fat-views* dan mempermudah integrasi lintas modul, worker Celery, maupun API eksternal.
- **Frontend Terkelola:** Template modular mencegah kekacauan DOM dan mempermudah kolaborasi antarmuka pengguna.

### Kompromi / Tantangan
- Jumlah file dalam struktur proyek bertambah secara signifikan.
- Dibutuhkan kedisiplinan tinggi dari tim developer dan AI agent untuk tidak mengambil jalan pintas (misal: langsung memanggil `.objects.create()` di dalam *views*).