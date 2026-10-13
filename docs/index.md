# Dokumentasi Sistem WaterPay / AirBersih (Docs-as-Code)

Selamat datang di portal dokumentasi arsitektur, modul aplikasi, dan operasional proyek **WaterPay / AirBersih**. Dokumentasi ini dikelola bersama repositori kode (*Docs-as-Code*) untuk menjamin keselarasan antara desain sistem dan implementasi nyata.

---

## 🗺️ Peta Navigasi Dokumentasi

### 1. 🏛️ Architecture Decision Records (ADR)
Keputusan arsitektural penting yang disepakati untuk sistem penagihan dan pembayaran:
- [ADR 0001: Implementasi Celery untuk Penanganan Tugas Asinkron](file:///d:/Randi/water_pay/docs/adr/0001-celery-async-tasks.md) – Otomasi pembuatan tagihan massal 12 bulan dan ekspor PDF ReportLab di latar belakang.
- [ADR 0002: Implementasi Clean Modular Architecture & Batasan Granularitas](file:///d:/Randi/water_pay/docs/adr/0002-clean-architecture.md) – Pemisahan Service Layer, Selector, Repository, dan batas 150–500 baris kode per file.
- [ADR 0003: Dekomposisi Layanan Penagihan & Pembayaran (Split MPBService)](file:///d:/Randi/water_pay/docs/adr/0003-split-mpbservice.md) – Pemisahan alur kalkulasi tagihan, transaksi kasir, dan generator ekspor.

### 2. 📦 Modul Sistem (Django Apps)
Spesifikasi aturan bisnis, alur data, dan model database per modul aplikasi:
- [Standar Umum Modul](file:///d:/Randi/water_pay/docs/modules/standar_umum.md) – Pedoman arsitektur clean layer pada seluruh Django app.
- [Modul Users (Kasir & Dashboard)](file:///d:/Randi/water_pay/docs/modules/users.md) – Profil staf kasir, autentikasi, dan loket bayar cepat di dashboard.
- [Modul Layanan (Katalog & Tarif)](file:///d:/Randi/water_pay/docs/modules/layanan.md) – Master kategori layanan (Air, WiFi) dan paket tarif bulanan.
- [Modul Rumah (Pemukiman & RT)](file:///d:/Randi/water_pay/docs/modules/rumah.md) – Inventaris unit rumah warga, nomor blok, dan status okupansi hunian.
- [Modul Pelanggan (Warga & Tagihan)](file:///d:/Randi/water_pay/docs/modules/pelanggan.md) – Data warga pelanggan, langganan aktif, dan generator tagihan 12 bulan.
- [Modul Pembayaran (Transaksi & Laporan)](file:///d:/Randi/water_pay/docs/modules/pembayaran.md) – Transaksi pembayaran kasir, ekspor Excel, dan matriks PDF ReportLab.

### 3. 🛠️ Runbooks Operasional
Panduan pemeliharaan teknis dan administrasi sistem:
- [Runbook Docker & Compose](file:///d:/Randi/water_pay/docs/runbook/docker.md) – Manajemen kontainer web, database PostgreSQL, dan pgAdmin 4.
- [Runbook Database PostgreSQL](file:///d:/Randi/water_pay/docs/runbook/database.md) – Migrasi Django, backup `pg_dump`, restore, dan optimasi query.
- [Runbook Deployment](file:///d:/Randi/water_pay/docs/runbook/deployment.md) – Prosedur deployment ke Railway / VPS, konfigurasi SSL, dan WhiteNoise.
- [Runbook Disaster Recovery](file:///d:/Randi/water_pay/docs/runbook/disaster_recovery.md) – Target SLA (RTO < 60 menit, RPO < 12 jam) dan mitigasi insiden data transaksi.

### 4. 📐 Panduan Desain & Setup
- [Architecture Draft](file:///d:/Randi/water_pay/docs/architecture_draft.md) – Blueprint diagram C4, tumpukan teknologi, dan siklus transaksi.
- [Frontend Guidelines](file:///d:/Randi/water_pay/docs/frontend_guidelines.md) – Standar modularitas template Django, format rupiah, dan Driver.js.
- [Local Setup Guide](file:///d:/Randi/water_pay/docs/local-setup.md) – Panduan instalasi lokal via Docker Compose maupun Python venv.
