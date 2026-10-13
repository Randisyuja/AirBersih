# Modul Pembayaran (Transaksi, Rekapitulasi & Ekspor Laporan)

Modul `pembayaran` merupakan inti transaksi keuangan aplikasi WaterPay / AirBersih, bertanggung jawab atas pencatatan penerimaan uang kas, verifikasi pelunasan, serta penyusunan laporan cetak PDF matriks 12 bulan dan ekspor Excel.

---

## 🎯 Lingkup & Tujuan Domain
1. **Pencatatan Transaksi (`Pembayaran`):** Menyimpan histori penerimaan dana dari pelanggan, mencatat staf `Kasir` yang melayani, stempel waktu transaksi (`tgl_pembayaran`), dan nominal rupiah.
2. **Monitoring Bulanan (`PembayaranBulananView`):** Filter dinamis transaksi berdasarkan bulan dan tahun, kalkulasi total pemasukan kas masuk (`Sum("jumlah_bayar")`).
3. **Ekspor Spreadsheet Excel (`export_pembayaran_excel`):** Menghasilkan file `.xlsx` menggunakan library **OpenPyXL** untuk arsip akuntansi bendahara.
4. **Ekspor Matriks Tahunan PDF (`export_pembayaran_pdf`):** Menghasilkan cetakan rekap matriks tabel Januari–Desember untuk seluruh warga per blok rumah menggunakan library **ReportLab**.

---

## 🗄️ Spesifikasi Model Pembayaran

```text
Pembayaran
├── id_pembayaran: AutoField (PK)
├── pelanggan: ForeignKey(Pelanggan, related_name="pembayaran")
├── jenis_layanan: ForeignKey(JenisLayanan)
├── kasir: ForeignKey(Kasir, null=True, blank=True)
├── bulan: PositiveSmallIntegerField (BulanChoice: 1=Jan, 2=Feb ... 12=Des)
├── tahun: PositiveSmallIntegerField
├── status_bayar: CharField (StatusChoice: "Lunas" / "Belum")
├── tgl_pembayaran: DateTimeField (null=True)
└── jumlah_bayar: IntegerField
```

---

## 📄 Spesifikasi Mesin Ekspor Laporan

### 1. Ekspor Excel (OpenPyXL)
- Endpoint: `/pembayaran/export/excel/`
- Query dioptimalkan dengan `select_related("pelanggan", "pelanggan__rumah", "jenis_layanan", "kasir")`.
- Format output: File biner `application/ms-excel` dengan nama lampiran `laporan_pembayaran.xlsx`.

### 2. Ekspor Matriks PDF (ReportLab Document Engine)
- Endpoint: `/pembayaran/export/pdf/<layanan>/<tahun>/`
- Menggunakan `SimpleDocTemplate(..., pagesize=landscape(A4))` dari ReportLab.
- **Sorting Khusus Alamat Rumah Warga:** Menggunakan casting SQL `Substr` pada `rumah__no_rumah` untuk mengurutkan blok alfabet dan nomor numerik rumah secara rapi:
  ```python
  blok = Cast(Substr("rumah__no_rumah", 2, 1), IntegerField())
  nomor = Cast(Substr("rumah__no_rumah", 5), IntegerField())
  ```
- Membangun tabel grid 12 kolom (Januari hingga Desember) yang menandai status pelunasan setiap warga.

---

## 🧩 Penerapan Clean Architecture pada Pembayaran

Saat ini [pembayaran/views.py](file:///d:/Randi/water_pay/pembayaran/views.py) berukuran 322 baris dan menggabungkan view controller, perakitan styling ReportLab, dan pembuatan spreadsheet OpenPyXL.

Sesuai [ADR 0002](file:///d:/Randi/water_pay/docs/adr/0002-clean-architecture.md) & [ADR 0003](file:///d:/Randi/water_pay/docs/adr/0003-split-mpbservice.md), modul ini dipecah ke:
1. **`pembayaran/selectors/pembayaran_selectors.py`**: Seluruh kueri agregasi pendapatan, filter bulanan, dan data pelanggan aktif.
2. **`pembayaran/services/payment_service.py`**: Logika validasi dan transaksi pelunasan.
3. **`pembayaran/exports/pdf_report_exporter.py`**: Seluruh perakitan dokumen PDF ReportLab (mengembalikan objek `io.BytesIO`).
4. **`pembayaran/exports/excel_report_exporter.py`**: Pembuatan worksheet OpenPyXL.
