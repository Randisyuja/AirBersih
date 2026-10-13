# Panduan Pengaturan Lokal (Local Development Setup)

Panduan langkah-demi-langkah bagi pengembang untuk menyiapkan lingkungan pengembangan lokal (*developer environment*) di mesin Windows, Mac, atau Linux.

---

## 💻 Prasyarat Sistem (Prerequisites)

Pastikan perangkat Anda telah terpasang:
1. **Git:** Untuk manajemen source code.
2. **Docker Desktop:** Versi 24+ (disertai Docker Compose v2).
3. *(Opsional untuk non-Docker)* **Python:** Versi 3.11.x dan **PostgreSQL 15**.

---

## 🐳 Metode 1: Menjalankan Menggunakan Docker Compose (Direkomendasikan)

Metode ini memastikan lingkungan pengembangan terisolasi sempurna dan identik dengan lingkungan server tanpa perlu menginstal dependensi manual di host.

### 1. Kloning Repositori & Salin Konfigurasi
```bash
git clone git@github.com:Randisyuja/AirBersih.git water_pay
cd water_pay
cp .env.example .env
```

### 2. Jalankan Kontainer
```bash
docker compose up --build -d
```
Docker Compose akan secara otomatis:
- Menyiapkan kontainer Python Django, PostgreSQL 15, dan pgAdmin 4.
- Menjalankan migrasi database (`migrate`).
- Mengumpulkan file statis (`collectstatic`).

### 3. Buat Akun Pengguna Administrator (Superuser)
```bash
docker compose exec web python manage.py createsuperuser
```
Ikuti instruksi di terminal untuk mengisi username, email, dan password.

### 4. Buka Aplikasi di Browser
- **Aplikasi Web:** [http://localhost:8010](http://localhost:8010)
- **Django Admin:** [http://localhost:8010/admin](http://localhost:8010/admin)
- **Portal Dokumentasi (MkDocs):** [http://localhost:8011](http://localhost:8011)
- **pgAdmin 4:** [http://localhost:5055](http://localhost:5055) (Login: `admin@admin.com` / `admin`)

---

## 🐍 Metode 2: Menjalankan Manual dengan Virtual Environment Python

Jika Anda ingin menjalankan Django langsung di host tanpa kontainer Docker:

### 1. Buat Virtual Environment (Python 3.11)
```bash
python -m venv venv

# Aktivasi di Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Aktivasi di Linux / macOS:
source venv/bin/activate
```

### 2. Pasang Dependensi Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Konfigurasi Variabel Lingkungan
Sesuaikan file `.env` dengan kredensial database lokal Anda:
```env
SECRET_KEY=django-insecure-local-dev-key
DEBUG=True
DB_NAME=airbersih_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

### 4. Terapkan Migrasi & Jalankan Server Dev
```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

---

## 🧪 Menjalankan Pengujian (Testing)
```bash
# Melalui Docker:
docker compose exec web python manage.py test

# Melalui Local Python:
python manage.py test
```
