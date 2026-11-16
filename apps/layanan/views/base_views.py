from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from apps.layanan.forms import JenisLayananForm, LayananForm
from apps.layanan.models import JenisLayanan, Layanan


class DaftarLayanan(LoginRequiredMixin, ListView):
    model = Layanan
    template_name = "layanan/daftar_layanan.html"
    context_object_name = "layanan_list"


class TambahLayanan(LoginRequiredMixin, CreateView):
    model = Layanan
    form_class = LayananForm
    template_name = "layanan/form_layanan.html"
    success_url = reverse_lazy("daftar_layanan")


class UpdateLayanan(LoginRequiredMixin, UpdateView):
    model = Layanan
    form_class = LayananForm
    template_name = "layanan/form_layanan.html"
    success_url = reverse_lazy("daftar_layanan")


def hapus_layanan(request, pk):
    if request.method == "POST":
        data = get_object_or_404(Layanan, pk=pk)
        nama = data.nama_layanan
        try:
            data.delete()
            messages.success(request, f"Layanan '{nama}' berhasil dihapus.")
        except ProtectedError as exc:
            referenced = [str(obj) for obj in getattr(exc, "protected_objects", [])]
            detail = f" (terhubung dengan: {', '.join(referenced)})" if referenced else ""
            messages.error(
                request,
                f"Gagal menghapus Layanan '{nama}' karena masih terhubung dengan data jenis layanan/transaksi aktif{detail}. "
                f"Silakan hapus sub-layanan terkait terlebih dahulu.",
            )
        return redirect("daftar_layanan")
    return redirect("daftar_layanan")


class DaftarJenisLayanan(LoginRequiredMixin, ListView):
    model = JenisLayanan
    template_name = "layanan/daftar_jenis_layanan.html"
    context_object_name = "jenis_layanan_list"


class TambahJenisLayanan(LoginRequiredMixin, CreateView):
    model = JenisLayanan
    form_class = JenisLayananForm
    template_name = "layanan/form_jenis_layanan.html"
    success_url = reverse_lazy("daftar_jenis_layanan")


class UpdateJenisLayanan(LoginRequiredMixin, UpdateView):
    model = JenisLayanan
    form_class = JenisLayananForm
    template_name = "layanan/form_jenis_layanan.html"
    success_url = reverse_lazy("daftar_jenis_layanan")


def hapus_jenis_layanan(request, pk):
    if request.method == "POST":
        data = get_object_or_404(JenisLayanan, pk=pk)
        nama = data.nama_jenis
        try:
            data.delete()
            messages.success(request, f"Jenis layanan '{nama}' berhasil dihapus.")
        except ProtectedError as exc:
            referenced = [str(obj) for obj in getattr(exc, "protected_objects", [])]
            detail = f" (terhubung dengan: {', '.join(referenced)})" if referenced else ""
            messages.error(
                request,
                f"Gagal menghapus Jenis Layanan '{nama}' karena masih terhubung dengan langganan/tagihan aktif{detail}. "
                f"Silakan hapus atau nonaktifkan langganan terkait terlebih dahulu.",
            )
        return redirect("daftar_jenis_layanan")
    return redirect("daftar_jenis_layanan")

