# Modul Users (Kasir, Autentikasi & Dashboard)

Modul `users` bertanggung jawab atas autentikasi petugas kasir, manajemen profil pengguna, serta penyediaan ringkasan KPI dan transaksi cepat pada Dashboard operasional.

---

## 🎯 Lingkup & Tujuan Domain
1. **Model Pengguna Kustom (`Kasir`):** Menggunakan `AbstractUser` dengan field tambahan kontak petugas (`no_hp`).
2. **Autentikasi & Otorisasi:** Sistem Login (`UserLoginView`), Logout (`UserLogoutView`), dan registrasi staf kasir baru.
3. **Pusat Kontrol Dashboard:**
   - Menghitung total penerimaan uang kas masuk bulan ini dan tahun ini.
   - Menampilkan jumlah tunggakan tagihan per jenis layanan (Air, WiFi, dll.).
   - Menangani loket pembayaran cepat (*quick checkout*) tagihan warga langsung dari Dashboard.
4. **API Endpoint AJAX Rumah & Layanan:** Menyediakan data layanan aktif berdasarkan nomor rumah warga (`get_layanan_by_rumah`).

---

## 🗄️ Model Database Utama

```text
Kasir (AbstractUser)
├── id: AutoField (PK)
├── username: CharField
├── first_name: CharField
├── last_name: CharField
├── email: EmailField
├── no_hp: CharField (max_length=20, optional)
└── is_active / is_staff: BooleanField
```

---

## 🔄 Alur Transaksi Cepat di Dashboard (Quick Payment Flow)

```text
Kasir Membuka Dashboard 
       │
       ▼
Input Nomor Rumah / Pilih Pelanggan & Bulan Tagihan
       │
       ▼
[ Dashboard.post ]
       ├── 1. Validasi Keberadaan Pelanggan & Tagihan (StatusChoice.Belum)
       ├── 2. Update Status Tagihan -> StatusChoice.Lunas
       ├── 3. Buat Catatan Pembayaran Baru (Set kasir = request.user, tgl_pembayaran = now)
       └── 4. Redirect ke Dashboard dengan Flash Message Feedback
```

---

## 🧩 Rekomendasi Refaktorisasi Clean Architecture

Saat ini logika pada `Dashboard.post` di [users/views.py](file:///d:/Randi/water_pay/users/views.py) menjalankan kueri ORM dan mutasi transaksi secara langsung. Sesuai [ADR 0002](file:///d:/Randi/water_pay/docs/adr/0002-clean-architecture.md), alur ini direfaktor ke:

1. **`users/selectors/dashboard_selectors.py`**:
   - `get_dashboard_summary_metrics(bulan, tahun) -> DashboardMetricDTO`: Mengambil akumulasi total uang masuk (`Sum("jumlah_bayar")`) dan rekap tagihan tertunggak.
2. **`pembayaran/services/payment_service.py`**:
   - `process_quick_payment(dto: QuickPaymentDTO) -> Pembayaran`: Membungkus transisi lunas dan pembuatan record transaksi di dalam `@transaction.atomic`.
