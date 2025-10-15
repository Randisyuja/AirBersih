from django import forms
from users.models import Kasir
from django.contrib.auth.forms import AuthenticationForm


class PenggunaForm(forms.ModelForm):
    class Meta:
        model = Kasir
        fields = ["username", "first_name", "last_name", "email", "no_hp", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control w-25"}),
            "first_name": forms.TextInput(attrs={"class": "form-control w-25"}),
            "last_name": forms.TextInput(attrs={"class": "form-control w-25"}),
            "email": forms.EmailInput(attrs={"class": "form-control w-25"}),
            "no_hp": forms.TextInput(attrs={"class": "form-control w-25"}),
            "password": forms.PasswordInput(attrs={"class": "form-control w-25"}),
        }


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control form-control-user',
                'placeholder': 'Username atau Email'
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-user',
                'placeholder': 'Password'
            }
        )
    )
