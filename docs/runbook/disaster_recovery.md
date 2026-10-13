# Runbook: Disaster Recovery & Mitigasi Insiden

Panduan rencana tanggap darurat dan pemulihan sistem dari kegagalan fatal, kehilangan data, atau bencana infrastruktur.

---

## 🎯 Target Pemulihan Layanan (SLA / Objectives)

- **Recovery Point Objective (RPO):** Maksimal 12 jam (toleransi kehilangan data transaksi maksimal sejak backup terakhir).
- **Recovery Time Objective (RTO):** Maksimal 60 menit (waktu maksimum yang dibutuhkan untuk memulihkan sistem hingga dapat diakses kembali oleh pengguna).

---

## 🚨 Skenario Bencana & Prosedur Penanganan

### Skenario A: Kerusakan Data atau Kesalahan Operasional (Data Corruption)
*Kondisi: Terjadi modifikasi atau penghapusan tabel transaksi secara tidak sengaja oleh operator atau query manual.*

1. **Segera Isolasi Akses Web:**
   Hentikan sementara kontainer web untuk mencegah penulisan data baru:
   ```bash
   docker compose stop web
   ```
2. **Identifikasi Titik Snapshot Terakhir:**
   Cari file dump database terdekat dari direktori backup atau cloud storage.
3. **Restore ke Database Sementara (Staging):**
   Lakukan restore ke instance database uji coba untuk memverifikasi integritas data sebelum ditimpa ke produksi.
4. **Ekstrak & Pulihkan Tabel Terpapar:**
   Pulihkan baris data yang rusak ke database utama.
5. **Hidupkan Kembali Web:**
   ```bash
   docker compose start web
   ```

---

### Skenario B: Kerusakan Fisik Host Server / Disk Failure
*Kondisi: Server VPS / host utama mati total atau storage disk rusak permanen.*

1. **Provisioning Host / VPS Baru:**
   Aktifkan server baru dengan sistem operasi Ubuntu 22.04 LTS atau Docker Desktop yang kompatibel.
2. **Kloning Repositori:**
   ```bash
   git clone git@github.com:Randisyuja/AirBersih.git water_pay
   cd water_pay
   ```
3. **Konfigurasi Environment:**
   Siapkan file `.env` dengan kredensial produksi yang aman.
4. **Unduh Backup Terakhir:**
   Unduh file snapshot database terenkripsi dari cold storage (AWS S3 / Google Drive / Offsite server).
5. **Jalankan Docker Compose:**
   ```bash
   docker compose up -d --build
   ```
6. **Restore Data:**
   Impor file snapshot database ke kontainer PostgreSQL baru.
7. **Pembaruan DNS:**
   Arahkan DNS domain utama (`A Record` / `CNAME`) ke alamat IP server baru.

---

## 📅 Jadwal & Retensi Pencadangan (Backup Retention)

| Frekuensi | Waktu Eksekusi | Lokasi Penyimpanan | Masa Retensi |
|---|---|---|---|
| **Harian** | Pukul 01:00 UTC | Local Storage Host + S3 Bucket | 14 Hari |
| **Mingguan**| Setiap Minggu 02:00 UTC | S3 Cold Tier Glacier | 3 Bulan |
| **Bulanan** | Akhir Bulan | Offline Encrypted Storage | 1 Tahun |

---

## 🧪 Uji Coba Simulasi Pemulihan (Disaster Drill)
Simulasi pemulihan wajib dieksekusi secara berkala minimal **setiap 6 bulan sekali** untuk memvalidasi:
1. File dump cadangan tidak korup (*valid archive*).
2. Waktu eksekusi restore berada di bawah target RTO (< 60 menit).
3. Integritas relasi tabel dan total saldo transaksi konsisten.
