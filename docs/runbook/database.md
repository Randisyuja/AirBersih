# Runbook: Pengelolaan Database (PostgreSQL)

Panduan operasional administrasi basis data PostgreSQL untuk pemeliharaan, migrasi skema, pencadangan (*backup*), dan pemulihan (*restore*).

---

## 🗄️ Konfigurasi Koneksi

Aplikasi mendukung konfigurasi database melalui variabel lingkungan di [.env](file:///d:/Randi/water_pay/.env.example):
1. **Model Parameter Terpisah:**
   - `DB_NAME`: Nama database (default: `airbersih_db`)
   - `DB_USER`: User database (default: `postgres`)
   - `DB_PASSWORD`: Kata sandi
   - `DB_HOST`: Host/service name (default: `db` di Docker)
   - `DB_PORT`: Port PostgreSQL (default: `5432`)
2. **Model Unified URL:**
   - `DATABASE_URL=postgresql://postgres:postgres@db:5432/airbersih_db`

---

## 🔄 Prosedur Migrasi Skema (Django Migrations)

### 1. Membuat & Menerapkan Migrasi
```bash
# 1. Generate file migrasi baru setelah modifikasi models.py
docker compose exec web python manage.py makemigrations

# 2. Tinjau SQL mentah yang akan dieksekusi (opsional tapi disarankan)
docker compose exec web python manage.py sqlmigrate <nama_app> <nomor_migrasi>

# 3. Terapkan migrasi ke database
docker compose exec web python manage.py migrate
```

### 2. Aturan Aman Migrasi Produksi (Zero-Downtime Rule)
- **Hindari Default Non-Nullable pada Kolom Baru:** Tambahkan `null=True, blank=True` terlebih dahulu, migrasi data jika diperlukan, baru tambahkan batasan `null=False` pada tahap rilis berikutnya.
- **Hindari Rename Kolom Secara Langsung:** Rename kolom langsung dapat memicu *downtime* saat worker versi lama masih berjalan. Gunakan pendekatan multi-fase (*Add new column -> Dual write -> Backfill -> Deprecate old column*).

---

## 💾 Prosedur Backup & Restore

### 1. Melakukan Backup Rutin (pg_dump)
Eksekusi dump dari kontainer database:
```bash
docker compose exec db pg_dump -U postgres -d airbersih_db -F c -b -v -f /tmp/backup_airbersih_$(date +%Y%m%d_%H%M%S).dump

# Salin file dump dari kontainer ke host:
docker cp water_pay_db:/tmp/backup_airbersih_*.dump ./backups/
```

### 2. Memulihkan Database (Restore via pg_restore)
```bash
# Salin file backup ke kontainer:
docker cp ./backups/backup_airbersih_target.dump water_pay_db:/tmp/restore_target.dump

# Jalankan restore:
docker compose exec db pg_restore -U postgres -d airbersih_db -c -v /tmp/restore_target.dump
```

---

## ⚡ Pemeliharaan Performa & Indeks

### 1. Re-index & Vacuuming
Lakukan secara berkala pada jam beban trafik rendah:
```sql
VACUUM ANALYZE;
REINDEX DATABASE airbersih_db;
```

### 2. Monitoring Kueri Lambat (Slow Queries)
Gunakan ekstensi `pg_stat_statements` untuk mendeteksi kueri yang memicu latensi tinggi:
```sql
SELECT query, calls, total_exec_time, mean_exec_time 
FROM pg_stat_statements 
ORDER BY total_exec_time DESC 
LIMIT 10;
```
