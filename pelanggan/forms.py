from django import forms
from pelanggan.models import Pelanggan, Langganan, Tagihan


class PelangganForm(forms.ModelForm):
    class Meta:
        model = Pelanggan
        fields = ["rumah", "nama", "no_hp"]
        widgets = {
            "rumah": forms.Select(attrs={"class": "form-control w-25"}),
            "nama": forms.TextInput(attrs={"class": "form-control w-25"}),
            "no_hp": forms.TextInput(attrs={"class": "form-control w-25"}),
        }


class LanggananForm(forms.ModelForm):
    class Meta:
        model = Langganan
        fields = ["pelanggan", "jenis_layanan", "harga", "aktif"]
        widgets = {
            "pelanggan": forms.Select(attrs={"class": "form-control w-25"}),
            "jenis_layanan": forms.Select(attrs={"class": "form-control w-25"}),
            "harga": forms.NumberInput(attrs={"class": "form-control w-25"}),
            "aktif": forms.Select(
                choices=[('', 'Pilih...'), (True, 'Ya'), (False, 'Tidak')],
                attrs={"class": "form-control w-25"}
            )
        }


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
            "pelanggan": forms.Select(attrs={"class": "form-control"}),
            "jenis_layanan": forms.Select(attrs={"class": "form-control"}),
            "bulan": forms.Select(attrs={"class": "form-control"}),
        }
