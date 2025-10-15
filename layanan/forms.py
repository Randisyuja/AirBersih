from django import forms
from layanan.models import Layanan, JenisLayanan


class LayananForm(forms.ModelForm):
    class Meta:
        model = Layanan
        fields = ['nama_layanan']
        widgets = {
            "nama_layanan": forms.TextInput(attrs={"class": "form-control w-25"}),
        }


class JenisLayananForm(forms.ModelForm):
    class Meta:
        model = JenisLayanan
        fields = [
            'layanan',
            'nama_jenis',
            'tarif'
        ]
        widgets = {
            "layanan": forms.Select(attrs={"class": "form-control w-25"}),
            "nama_jenis": forms.TextInput(attrs={"class": "form-control w-25"}),
            "tarif": forms.NumberInput(attrs={"class": "form-control w-25"}),
        }
