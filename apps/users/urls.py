from django.urls import path
from django.views.generic import TemplateView
from apps.users.views import (
    Dashboard,
    get_layanan_by_rumah,
    UserLoginView,
    UserLogoutView,
    SignUpView,
    DaftarKasir,
    TambahKasir,
    UpdateKasir,
    DeleteKasir,
    laporan_recent,
)
from apps.users.views.excel_views import (
    export_users_excel,
    import_users_excel,
    template_users_excel,
)

urlpatterns = [
    # Dashboard & Auth
    path('', Dashboard.as_view(), name='dashboard'),
    path('403/', TemplateView.as_view(template_name='403.html'), name='preview_403'),
    path("get-layanan/", get_layanan_by_rumah, name="get_layanan_by_rumah"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("signup/", SignUpView.as_view(), name="signup"),

    # AJAX Dashboard Paginate
    path("laporan-recent/", laporan_recent, name="laporan_recent"),

    # Manajemen Users / Kasir
    path("users/", DaftarKasir.as_view(), name="daftar_users"),
    path("users/export/", export_users_excel, name="export_users"),
    path("users/import/", import_users_excel, name="import_users"),
    path("users/template/", template_users_excel, name="template_users"),
    path("kasir/", DaftarKasir.as_view(), name="daftar_kasir"),
    path("kasir/export/", export_users_excel, name="export_kasir"),
    path("kasir/import/", import_users_excel, name="import_kasir"),
    path("kasir/template/", template_users_excel, name="template_kasir"),
    path("users/tambah/", TambahKasir.as_view(), name="tambah_users"),
    path("kasir/tambah/", TambahKasir.as_view(), name="tambah_kasir"),
    path("users/<int:pk>/edit/", UpdateKasir.as_view(), name="update_users"),
    path("users/<int:pk>/update/", UpdateKasir.as_view(), name="edit_users"),
    path("kasir/<int:pk>/edit/", UpdateKasir.as_view(), name="update_kasir"),
    path("users/<int:pk>/hapus/", DeleteKasir.as_view(), name="delete_users"),
    path("users/<int:pk>/delete/", DeleteKasir.as_view(), name="hapus_users"),
    path("kasir/<int:pk>/hapus/", DeleteKasir.as_view(), name="delete_kasir"),
]
