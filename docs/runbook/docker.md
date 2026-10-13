# Runbook: Docker & Containerization

Panduan operasional pengelolaan kontainer Docker, Docker Compose, dan service terkait (Django, PostgreSQL, pgAdmin).

---

## 🚀 Perintah Dasar Docker Compose

### 1. Menjalankan Seluruh Layanan (Background Mode)
```bash
docker compose up --build -d
```
Perintah ini akan:
- Membangun image aplikasi web Django (Python 3.11-slim).
- Menjalankan kontainer PostgreSQL 15 (`water_pay_db`).
- Menjalankan kontainer pgAdmin 4 (`water_pay_pgadmin`).
- Menjalankan migrasi database dan pengumpulan static files secara otomatis via [entrypoint.sh](file:///d:/Randi/water_pay/entrypoint.sh).

### 2. Memeriksa Status Kontainer
```bash
docker compose ps
```

### 3. Memantau Log Aplikasi (Real-time)
```bash
# Seluruh service
docker compose logs -f

# Hanya service web Django
docker compose logs -f web

# Hanya service database
docker compose logs -f db
```

### 4. Menghentikan Seluruh Layanan
```bash
# Menghentikan kontainer tanpa menghapus data
docker compose down

# Menghentikan kontainer dan menghapus volume database (HATI-HATI)
docker compose down -v
```

---

## 🛠️ Menjalankan Django Management Command di Kontainer

### 1. Membuat Superuser Admin
```bash
docker compose exec web python manage.py createsuperuser
```

### 2. Menjalankan Migrasi Manual
```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### 3. Masuk ke Django Shell atau Bash Kontainer
```bash
# Django Interactive Shell
docker compose exec web python manage.py shell

# Bash Shell di dalam kontainer
docker compose exec web /bin/sh
```

---

## 🖥️ Akses Layanan Web & Port Mapping

| Layanan | URL Akses | Kredensial Default |
|---|---|---|
| **Aplikasi Web** | `http://localhost:8010` | Superuser Django |
| **Django Admin** | `http://localhost:8010/admin` | Superuser Django |
| **Portal Dokumentasi (MkDocs)** | `http://localhost:8011` | Publik (tanpa login) |
| **pgAdmin 4** | `http://localhost:5055` | `admin@admin.com` / `admin` |
| **PostgreSQL Port (Host)** | `localhost:5433` | `postgres` / `postgres` |

---

## 🔍 Troubleshooting Masalah Umum

### 1. Masalah Line-Ending CRLF pada Windows (`/entrypoint.sh: line 2: $'\r': command not found`)
- **Penyebab:** Git checkout di Windows mengubah line endings menjadi CRLF.
- **Solusi:** [Dockerfile](file:///d:/Randi/water_pay/Dockerfile) telah dilengkapi perintah `sed -i 's/\r$//' /app/entrypoint.sh` untuk otomatis menormalkan ke format Unix (LF).

### 2. Database Belum Siap saat Web Booting
- [entrypoint.sh](file:///d:/Randi/water_pay/entrypoint.sh) menggunakan utilitas `nc -z` (*netcat*) untuk menunggu port PostgreSQL terbuka penuh sebelum mengeksekusi migrasi.

### 3. Port Konflik (Misal: Port 5432 atau 8000 Telah Digunakan)
- Hentikan PostgreSQL lokal di host Windows (`net stop postgresql-x64-15` di PowerShell) atau ubah port mapping pada `docker-compose.yml` (misal `"5433:5432"`).
