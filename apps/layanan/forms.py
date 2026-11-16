from django import forms
from apps.layanan.models import JenisLayanan, Layanan


class LayananForm(forms.ModelForm):
    class Meta:
        model = Layanan
        fields = ["nama_layanan"]
        widgets = {
            "nama_layanan": forms.TextInput(attrs={"class": "form-control w-25"}),
        }


class JenisLayananForm(forms.ModelForm):
    class Meta:
        model = JenisLayanan
        fields = [
            "layanan",
            "nama_jenis",
            "tarif",
        ]
        widgets = {
            "layanan": forms.Select(attrs={"class": "form-control w-25"}),
            "nama_jenis": forms.TextInput(attrs={"class": "form-control w-25", "placeholder": "Contoh: Air Meteran / WiFi 165"}),
            "tarif": forms.NumberInput(
                attrs={
                    "class": "form-control w-25",
                    "placeholder": "Kosongkan atau isi 0 untuk tarif meteran/manual",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tarif"].required = False

    def clean_tarif(self):
        val = self.cleaned_data.get("tarif")
        return val if val is not None else 0
