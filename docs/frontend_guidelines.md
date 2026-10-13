# Panduan Frontend & Antarmuka Pengguna (Frontend Guidelines)

Panduan tata kelola template Django, pemisahan komponen antarmuka (*partials/includes*), dan standarisasi elemen UI pada aplikasi **WaterPay / AirBersih**.

---

## 📐 Standar Granularitas Template

Untuk menjaga keterbacaan kode antarmuka dan mempermudah kolaborasi:
- **Batas Ukuran Template Utama:** Maksimal **200 – 300 baris kode**.
- **Komponen Modular (Includes / Partials):** Halaman kompleks (seperti `dashboard.html`, `pembayaran/daftar_pembayaran.html`, dan `pelanggan/daftar_tagihan.html`) wajib dipecah ke dalam folder `templates/<app>/includes/`:

```text
templates/
├── dashboard.html                    <-- Template induk ringkas
├── includes/
│   ├── _kpi_cards.html               <-- Kartu ringkasan total uang & tagihan
│   ├── _quick_pay_form.html          <-- Formulir loket bayar cepat kasir
│   └── _recent_unpaid_table.html     <-- Tabel transaksi tertunggak terbaru
├── pembayaran/
│   ├── daftar_pembayaran.html
│   └── includes/
│       ├── _filter_bulan_tahun.html  <-- Baris dropdown filter periode
│       ├── _pembayaran_table.html    <-- Tabel daftar transaksi lunas
│       └── _export_buttons.html      <-- Tombol unduh Excel & cetak PDF
```

---

## 💰 Format Mata Uang & Angka (Django Humanize)

Sesuai konfigurasi di [airBersih/settings.py](file:///d:/Randi/water_pay/airBersih/settings.py) (`django.contrib.humanize`), format nominal rupiah wajib menggunakan filter standar Django:

```django
{% load humanize %}

<!-- Menampilkan nominal uang dengan pemisah ribuan -->
<span class="badge badge-success">
    Rp {{ pembayaran.jumlah_bayar|intcomma }}
</span>
```

---

## 🏷️ Atribut ID Semantik untuk Onboarding Kasir (Driver.js)

Aplikasi kasir membutuhkan alur kerja yang cepat dan ramah bagi petugas baru. Setiap elemen penting **wajib memiliki atribut `id="..."` unik** untuk mendukung tur interaktif menggunakan **Driver.js**:

| Komponen | Standar Penamaan ID | Contoh Penggunaan di Driver.js |
|---|---|---|
| **Input No. Rumah** | `id="input-nomor-rumah"` | Langkah 1: "Ketik nomor rumah warga di sini" |
| **Pilih Layanan** | `id="select-jenis-layanan"` | Langkah 2: "Pilih layanan yang akan dibayar" |
| **Tombol Bayar** | `id="btn-proses-bayar"` | Langkah 3: "Klik untuk mencatat pelunasan" |
| **Tombol Cetak PDF** | `id="btn-export-pdf-rekap"` | Langkah 4: "Klik untuk mengunduh rekap tahunan" |
| **Filter Bulan** | `id="filter-periode-bulan"` | Langkah 5: "Pilih bulan untuk melihat arsip" |

---

## 🎨 Konsistensi Status Tagihan (Badge Styling)

Gunakan penanda status visual yang konsisten di seluruh tabel:
- Status **Lunas**: `<span class="badge badge-success">Lunas</span>`
- Status **Belum / Tertunggak**: `<span class="badge badge-danger">Belum</span>`
- Rumah **Dihuni**: `<span class="badge badge-primary">Dihuni</span>`
- Rumah **Kosong**: `<span class="badge badge-secondary">Kosong</span>`
