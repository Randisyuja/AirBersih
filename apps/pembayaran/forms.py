from django import forms
from django.utils import timezone
from apps.layanan.models import JenisLayanan
from apps.pelanggan.models import Pelanggan
from apps.pembayaran.models import Pembayaran


class PembayaranForm(forms.ModelForm):
    class Meta:
        model = Pembayaran
        fields = [
            "pelanggan",
            "jenis_layanan",
            "bulan",
            "tahun",
            "status_bayar",
            "tgl_pembayaran",
            "jumlah_bayar",
        ]
        widgets = {
            "pelanggan": forms.Select(attrs={"class": "form-control", "id": "id_pelanggan"}),
            "jenis_layanan": forms.Select(attrs={"class": "form-control", "id": "id_jenis_layanan"}),
            "bulan": forms.Select(attrs={"class": "form-control", "id": "id_bulan"}),
            "tahun": forms.NumberInput(attrs={"class": "form-control", "id": "id_tahun"}),
            "status_bayar": forms.Select(attrs={"class": "form-control", "id": "id_status_bayar"}),
            "tgl_pembayaran": forms.DateInput(attrs={"class": "form-control", "type": "date", "id": "id_tgl_pembayaran"}),
            "jumlah_bayar": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "id": "id_jumlah_bayar",
                    "placeholder": "Masukkan nominal pembayaran (Rp)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pelanggan"].queryset = Pelanggan.objects.select_related("rumah").all()
        self.fields["jenis_layanan"].queryset = JenisLayanan.objects.select_related("layanan").all()
        self.fields["tgl_pembayaran"].required = False
        if not self.instance.pk:
            self.fields["tahun"].initial = timezone.now().year
            self.fields["bulan"].initial = timezone.now().month

    def clean_jumlah_bayar(self):
        val = self.cleaned_data.get("jumlah_bayar")
        if val is None or val <= 0:
            raise forms.ValidationError("Nominal pembayaran harus lebih dari Rp 0.")
        return val


class TahunForm(forms.Form):
    tahun = forms.ChoiceField(
        label="Tahun",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "onchange": "this.form.submit();",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_year = timezone.now().year
        self.fields["tahun"].choices = [
            (y, y) for y in range(current_year, current_year - 6, -1)
        ]
