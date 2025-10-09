from django import forms
from pembayaran.models import Pembayaran
from pelanggan.models import Langganan


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


class PembayaranUpdate(forms.ModelForm):
    class Meta:
        model = Pembayaran
        fields = [
            "pelanggan",
            "jenis_layanan",
            "bulan"
        ]
