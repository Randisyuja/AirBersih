# Modul Rumah (Master Properti & Pemukiman Warga)

Modul `rumah` mengelola inventaris unit rumah tinggal warga, pemetaan Rukun Tetangga (RT), nomor unik rumah, serta kalkulasi otomatis status okupansi (*Dihuni* atau *Kosong*).

---

## 🎯 Lingkup & Tujuan Domain
1. **Pencatatan Unit Rumah (`Rumah`):** Pengelompokan berdasarkan zona RT dan nomor rumah (contoh: RT 01, No. D1-05).
2. **Kalkulasi Status Hunian Otomatis:** Menghitung apakah rumah sedang ditempati pelanggan aktif atau dalam kondisi kosong.
3. **Filter Unit Kosong:** Menyediakan kueri khusus bagi modul `pelanggan` agar saat mendaftarkan warga baru hanya unit rumah tanpa penghuni yang dapat dipilih (`penghuni__isnull=True`).

---

## 🗄️ Spesifikasi Model Database

```python
class Rumah(models.Model):
    id_rumah = models.AutoField(primary_key=True)
    rt = models.CharField(max_length=5)           # contoh: "01", "02"
    no_rumah = models.CharField(max_length=10, unique=True) # contoh: "A1", "B12"

    class Meta:
        unique_together = ("rt", "no_rumah")

    @property
    def status(self):
        """Kalkulasi dinamis status hunian"""
        return "Dihuni" if hasattr(self, "penghuni") else "Kosong"
```

---

## 🔒 Aturan Domain & Batasan Bisnis

1. **Keunikan Identitas Rumah:**
   - Nomor rumah bersifat unik secara global (`unique=True`) dan memiliki batasan komposit unik terhadap RT (`unique_together = ("rt", "no_rumah")`).
2. **Perlindungan Penghapusan Rumah Terisi:**
   - Model `Pelanggan` mengikat relasi `OneToOneField(Rumah, on_delete=models.PROTECT)`. Unit rumah yang sedang memiliki penghuni dilarang dihapus dari database sebelum data pelanggan dimutasikan terlebih dahulu.
3. **Sorting Pintar Nomor Rumah (Smart Sorting):**
   - Penomoran rumah warga memiliki format alfabet-blok dan digit (contoh: "D2 NO 14"). Pada laporan rekapitulasi penagihan, nomor rumah diekstrak blok dan nomornya secara numerik menggunakan `Substr` dan `Cast` agar urutan cetak teratur.
