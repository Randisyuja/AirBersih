# ADR 001: Implementasi Celery untuk Penanganan Tugas Asinkron (Async Tasks)

**Status:** Diterima (Accepted)  
**Tanggal:** 2026-10-05  

---

## Konteks

Dalam aplikasi **WaterPay / AirBersih**, terdapat operasi komputasi dan penulisan basis data berat yang saat ini dieksekusi secara sinkron di dalam siklus HTTP request Gunicorn:

1. **Pembuatan Tagihan Massal Tahunan (`generate_tagihan_setahun`):**
   - Menghasilkan tagihan untuk 12 bulan ke seluruh warga pelanggan aktif (`pelanggan/utils.py`).
   - Dengan ratusan warga pelanggan dan puluhan jenis langganan, proses ini memicu iterasi nested loop yang mengeksekusi ratusan hingga ribuan query `exists()` dan `create()` sekaligus.
2. **Generasi Dokumen Rekapitulasi PDF Matriks 12 Bulan (`export_pembayaran_pdf`):**
   - Mengambil seluruh data pembayaran warga se-kabupaten/desa, memformat grid matriks 12 bulan menggunakan ReportLab, dan membangun file biner PDF dalam satu HTTP request.
3. **Ekspor Spreadsheet Rekap Tahunan Excel (`export_pembayaran_excel`):**
   - Membaca ribuan transaksi dan menyusun file spreadsheet OpenPyXL.

Ketika proses di atas dijalankan melalui klik tombol di browser oleh admin/kasir:
- Web worker Gunicorn mengalami *freeze* (thread blocking), menyebabkan HTTP Request Timeout (504 Gateway Timeout).
- Pengguna lain di loket pembayaran tidak dapat mengakses aplikasi selama proses berjalan.

---

## Keputusan

Kami memutuskan untuk mengimplementasikan **Celery** sebagai *Distributed Task Queue* dengan **Redis** sebagai *Message Broker* dan *Result Backend* untuk menangani seluruh tugas berat di latar belakang (*background workers*):

### 1. Pola Implementasi pada Modul AirBersih
- **`generate_tagihan_task(tahun: int)`**: Dijalankan di background; kasir mendapatkan notifikasi instan bahwa pembuatan tagihan sedang diproses, dan menerima pembaruan saat selesai.
- **`generate_pdf_report_task(layanan_id: int, tahun: int, user_email: str)`**: Worker ReportLab merender dokumen PDF di background dan menyimpannya ke storage sementara untuk diunduh.
- **`send_whatsapp_invoice_notification_task(pelanggan_id: int, tagihan_id: int)`**: Pengiriman notifikasi tagihan ke nomor WhatsApp warga secara asinkron tanpa membebani loket kasir.

### 2. Aturan Granularitas & Idempotensi Task
- Gunakan ID entitas murni (`int` ID pelanggan atau tahun) sebagai parameter task Celery; dilarang mengirim objek model Django (`Pelanggan`, `Tagihan`) secara langsung ke antrean broker.
- Task pembuatan tagihan wajib bersifat *idempotent* (menggunakan pengecekan keberadaan tagihan atau PostgreSQL `ON CONFLICT DO NOTHING` / `bulk_create(ignore_conflicts=True)`).

---

## Konsekuensi

### Dampak Positif
- **Respon Web Cepat:** Permintaan HTTP pada tombol "Generate Tagihan" dan "Cetak Laporan" langsung merespons di bawah 200 ms.
- **Stabilitas Loket Kasir:** Loket pembayaran tetap responsif dan lancar melayani antrean warga meskipun sistem sedang memproses kalkulasi tagihan tahunan massal.

### Kompromi / Tantangan
- Membutuhkan penambahan kontainer `redis` dan worker `celery` pada [docker-compose.yml](file:///d:/Randi/water_pay/docker-compose.yml).
