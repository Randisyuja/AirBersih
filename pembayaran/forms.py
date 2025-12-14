from django import forms
from pembayaran.models import Pembayaran
from pelanggan.models import Langganan
from django.utils import timezone


class PembayaranForm(forms.ModelForm):
    class Meta:
        model = Pembayaran
        fields = [
            "pelanggan",
            "jenis_layanan",
            "kasir",
            "bulan",
            "tahun",
            "status_bayar",
            "tgl_pembayaran",
            "jumlah_bayar",
        ]

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
