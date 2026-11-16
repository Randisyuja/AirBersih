from django import forms
from apps.pelanggan.models import Pelanggan, Langganan, Tagihan
from apps.layanan.models import JenisLayanan


class PelangganForm(forms.ModelForm):
    class Meta:
        model = Pelanggan
        fields = ["rumah", "nama", "no_hp", "barcode"]
        widgets = {
            "rumah": forms.Select(attrs={"class": "form-control", "id": "id_rumah"}),
            "nama": forms.TextInput(attrs={"class": "form-control", "placeholder": "Masukkan nama lengkap pelanggan"}),
            "no_hp": forms.TextInput(attrs={"class": "form-control", "placeholder": "Contoh: 08123456789"}),
            "barcode": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Kosongkan untuk generate otomatis (misal: PLG00001)"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["barcode"].required = False


class LanggananForm(forms.ModelForm):
    class Meta:
        model = Langganan
        fields = ["pelanggan", "jenis_layanan", "harga", "aktif", "kode_pelanggan"]
        widgets = {
            "pelanggan": forms.Select(attrs={"class": "form-control", "id": "id_pelanggan"}),
            "jenis_layanan": forms.Select(attrs={"class": "form-control", "id": "id_jenis_layanan"}),
            "harga": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "id_harga",
                "placeholder": "Contoh: 25000",
                "style": "border-radius: 0 8px 8px 0; border-color: var(--slate-300); height: 44px;"
            }),
            "aktif": forms.Select(
                choices=[(True, "Aktif (Ya)"), (False, "Tidak Aktif (Tidak)")],
                attrs={"class": "form-control", "id": "id_aktif", "style": "border-radius: 8px; border-color: var(--slate-300); height: 44px;"}
            ),
            "kode_pelanggan": forms.TextInput(attrs={
                "class": "form-control font-mono",
                "id": "id_kode_pelanggan",
                "placeholder": "Kosongkan untuk generate otomatis (misal: MBR00001)"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pelanggan"].queryset = Pelanggan.objects.select_related("rumah").all()
        self.fields["jenis_layanan"].queryset = JenisLayanan.objects.select_related("layanan").all()
        self.fields["kode_pelanggan"].required = False
        self.fields["harga"].required = False
        if not self.instance.pk:
            self.fields["aktif"].initial = True

    def clean_harga(self):
        val = self.cleaned_data.get("harga")
        if val is None:
            jenis = self.cleaned_data.get("jenis_layanan")
            return (jenis.tarif if (jenis and jenis.tarif) else 0)
        return val


class TagihanForm(forms.ModelForm):
    class Meta:
        model = Tagihan
        fields = [
            "pelanggan",
            "jenis_layanan",
            "bulan",
            "tahun",
            "status_tagihan",
            "jumlah_bayar"
        ]
        widgets = {
            "pelanggan": forms.Select(attrs={"class": "form-control"}),
            "jenis_layanan": forms.Select(attrs={"class": "form-control"}),
            "bulan": forms.Select(attrs={"class": "form-control"}),
            "tahun": forms.NumberInput(attrs={"class": "form-control"}),
            "status_tagihan": forms.Select(attrs={"class": "form-control"}),
            "jumlah_bayar": forms.NumberInput(attrs={"class": "form-control"}),
        }


class TagihanUpdate(forms.ModelForm):
    class Meta:
        model = Tagihan
        fields = [
            "pelanggan",
            "jenis_layanan",
            "bulan"
        ]
        widgets = {
            "pelanggan": forms.Select(attrs={"class": "form-control", "id": "id_pelanggan"}),
            "jenis_layanan": forms.Select(attrs={"class": "form-control", "id": "id_jenis_layanan"}),
            "bulan": forms.Select(attrs={"class": "form-control", "id": "id_bulan"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pelanggan"].queryset = Pelanggan.objects.select_related("rumah").all()
        self.fields["jenis_layanan"].queryset = JenisLayanan.objects.select_related("layanan").all()
        bulan_choices = [("", "-- Pilih Periode Bulan --")]
        bulan_names = [
            (1, "1 - Januari"),
            (2, "2 - Februari"),
            (3, "3 - Maret"),
            (4, "4 - April"),
            (5, "5 - Mei"),
            (6, "6 - Juni"),
            (7, "7 - Juli"),
            (8, "8 - Agustus"),
            (9, "9 - September"),
            (10, "10 - Oktober"),
            (11, "11 - November"),
            (12, "12 - Desember"),
        ]
        bulan_choices.extend(bulan_names)
        self.fields["bulan"].choices = bulan_choices
