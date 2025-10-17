from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from layanan.models import Layanan, JenisLayanan
from django.contrib.auth.mixins import LoginRequiredMixin
from layanan.forms import LayananForm, JenisLayananForm


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
    if request.method == 'POST':
        data = get_object_or_404(Layanan, pk=pk)
        data.delete()
        return redirect('daftar_layanan')
    return redirect('daftar_layanan')


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
    if request.method == 'POST':
        data = get_object_or_404(JenisLayanan, pk=pk)
        data.delete()
        return redirect('daftar_jenis_layanan')  # ganti dengan nama url list kamu
    return redirect('daftar_jenis_layanan')

