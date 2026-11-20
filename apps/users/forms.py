from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import Group, Permission
from django.db.models import Q

from apps.core.permissions import APP_FEATURE_PERMISSIONS
from apps.users.models import Kasir


def _get_managed_permissions_queryset():
    query = Q()
    for _, items in APP_FEATURE_PERMISSIONS:
        for perm_key, _ in items:
            app_label, codename = perm_key.split(".", 1)
            query |= Q(content_type__app_label=app_label, codename=codename)
    return Permission.objects.filter(query).select_related("content_type")


class PenggunaForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Role / Grup Akses",
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Hak Akses Fitur Khusus (Per-Fitur)",
    )

    class Meta:
        model = Kasir
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "no_hp",
            "password",
            "is_active",
            "groups",
            "user_permissions",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Masukkan username"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nama depan"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nama belakang"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "contoh@email.com"}),
            "no_hp": forms.TextInput(attrs={"class": "form-control", "placeholder": "08123456789"}),
            "password": forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Masukkan password"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].queryset = Group.objects.all().order_by("name")
        self.fields["user_permissions"].queryset = _get_managed_permissions_queryset()
        self._original_password = self.instance.password if (self.instance and self.instance.pk) else None
        if self.instance and self.instance.pk:
            self.fields["password"].required = False
            self.fields["password"].widget.attrs["placeholder"] = "Kosongkan jika tidak ingin mengubah password"
        else:
            self.fields["is_active"].initial = True

    def get_grouped_permissions(self):
        """Returns permissions grouped by feature category with human-readable Indonesian labels."""
        perm_map = {}
        for p in self.fields["user_permissions"].queryset:
            perm_map[f"{p.content_type.app_label}.{p.codename}"] = p

        selected_ids = set()
        if self.is_bound:
            selected_ids = {str(v) for v in self.data.getlist("user_permissions")}
        elif self.instance and self.instance.pk:
            selected_ids = {str(pk) for pk in self.instance.user_permissions.values_list("pk", flat=True)}

        grouped = []
        for group_title, items in APP_FEATURE_PERMISSIONS:
            entries = []
            for perm_key, label in items:
                perm_obj = perm_map.get(perm_key)
                if perm_obj:
                    entries.append(
                        {
                            "id": perm_obj.pk,
                            "label": label,
                            "checked": str(perm_obj.pk) in selected_ids,
                        }
                    )
            if entries:
                grouped.append({"title": group_title, "items": entries})
        return grouped

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
            self.save_m2m()
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
