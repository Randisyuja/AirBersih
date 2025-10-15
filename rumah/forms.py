from django import forms
from rumah.models import Rumah


class RumahForm(forms.ModelForm):
    class Meta:
        model = Rumah
        fields = ["rt", "no_rumah"]
        widgets = {
            "rt": forms.TextInput(attrs={"class": "form-control w-25"}),
            "no_rumah": forms.TextInput(attrs={"class": "form-control w-25"}),
        }

