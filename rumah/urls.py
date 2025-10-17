from django.urls import path
from rumah.views import DaftarRumah, TambahRumah, UpdateRumah, hapus_rumah

urlpatterns = [
    path("", DaftarRumah.as_view(), name="daftar_rumah"),
    path("tambah/", TambahRumah.as_view(), name="tambah_rumah"),
    path("<int:pk>/edit/", UpdateRumah.as_view(), name="edit_rumah"),
    path("<int:pk>/hapus/", hapus_rumah, name="hapus_rumah"),
]