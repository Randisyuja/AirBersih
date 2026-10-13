from django import forms
from apps.pembayaran.models import Pembayaran
from apps.pelanggan.models import Langganan
from django.utils import timezone


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
            "pelanggan": forms.Select(attrs={"class": "form-control"}),
            "jenis_layanan": forms.Select(attrs={"class": "form-control"}),
            "bulan": forms.Select(attrs={"class": "form-control"}),
            "tahun": forms.NumberInput(attrs={"class": "form-control"}),
            "status_bayar": forms.Select(attrs={"class": "form-control"}),
            "tgl_pembayaran": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "jumlah_bayar": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["jenis_layanan"].queryset = Langganan.objects.none()

        if "pelanggan" in self.data:
            try:
                pelanggan_id = int(self.data.get("pelanggan"))
                self.fields["jenis_layanan"].queryset = Langganan.objects.filter(pelanggan_id=pelanggan_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields["jenis_layanan"].queryset = Langganan.objects.filter(pelanggan=self.instance.pelanggan)


class TahunForm(forms.Form):
    tahun = forms.ChoiceField(
        label="Tahun",
        required=False,
        widget=forms.Select(attrs={
            "class": "form-control",
            "onchange": "this.form.submit();"
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        current_year = timezone.now().year
        self.fields["tahun"].choices = [
            (y, y) for y in range(current_year, current_year - 6, -1)
        ]
