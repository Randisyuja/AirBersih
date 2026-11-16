from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.hashers import identify_hasher
from apps.users.models import Kasir


class PenggunaForm(forms.ModelForm):
    class Meta:
        model = Kasir
        fields = ["username", "first_name", "last_name", "email", "no_hp", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Masukkan username"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nama depan"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nama belakang"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "contoh@email.com"}),
            "no_hp": forms.TextInput(attrs={"class": "form-control", "placeholder": "08123456789"}),
            "password": forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Masukkan password"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_password = self.instance.password if (self.instance and self.instance.pk) else None
        if self.instance and self.instance.pk:
            self.fields["password"].required = False
            self.fields["password"].widget.attrs["placeholder"] = "Kosongkan jika tidak ingin mengubah password"

    def clean_password(self):
        raw_password = self.cleaned_data.get("password")
        if not raw_password and self._original_password:
            return self._original_password
        return raw_password

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data.get("password")
        if raw_password and not raw_password.startswith("!"):
            try:
                identify_hasher(raw_password)
                user.password = raw_password
            except ValueError:
                user.set_password(raw_password)
        elif self._original_password:
            user.password = self._original_password
        if commit:
            user.save()
        return user


class KasirCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Kasir
        fields = ("username", "first_name", "last_name", "email", "no_hp")


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-user",
                "placeholder": "Username atau Email",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-user",
                "placeholder": "Password",
            }
        )
    )
