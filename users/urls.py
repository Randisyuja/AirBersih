from django.urls import path
from users.views import (Dashboard, DaftarKasir, TambahKasir, UpdateKasir, hapus_tagihan, get_layanan_by_rumah,
                         UserLoginView, UserLogoutView, SignUpView)

urlpatterns = [
    path('', Dashboard.as_view(), name='dashboard'),
    path("users/", DaftarKasir.as_view(), name="daftar_users"),
    path("users/tambah/", TambahKasir.as_view(), name="tambah_users"),
    path("users/<int:pk>/edit/", UpdateKasir.as_view(), name="update_users"),
    path("users/<int:pk>/hapus/", hapus_tagihan, name="delete_users"),
    path("get-layanan/", get_layanan_by_rumah, name="get_layanan_by_rumah"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("signup/", SignUpView.as_view(), name="signup"),
]
