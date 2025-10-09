from django.shortcuts import render
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from layanan.models import Layanan, JenisLayanan
from django.contrib.auth.mixins import LoginRequiredMixin


class DaftarLayanan(LoginRequiredMixin, ListView):
    model = Layanan
    template_name = "layanan/daftar_layanan.html"
    context_object_name = "layanan_list"


class TambahLayanan(LoginRequiredMixin, CreateView):
    model = Layanan
    fields = ["nama_layanan"]
    template_name = "layanan/form_layanan.html"
    success_url = reverse_lazy("daftar_layanan")


class UpdateLayanan(LoginRequiredMixin, UpdateView):
    model = Layanan
    fields = ['nama_layanan']
    template_name = "layanan/form_layanan.html"
    success_url = reverse_lazy("daftar_layanan")


class DeleteLayanan(LoginRequiredMixin, DeleteView):
    model = Layanan
    template_name = "layanan/delete_layanan.html"
    success_url = reverse_lazy("daftar_layanan")


class DaftarJenisLayanan(LoginRequiredMixin, ListView):
    model = JenisLayanan
    template_name = "layanan/daftar_jenis_layanan.html"
    context_object_name = "jenis_layanan_list"


class TambahJenisLayanan(LoginRequiredMixin, CreateView):
    model = JenisLayanan
    fields = ["layanan", "nama_jenis", "tarif"]
    template_name = "layanan/form_jenis_layanan.html"
    success_url = reverse_lazy("daftar_jenis_layanan")


class UpdateJenisLayanan(LoginRequiredMixin, UpdateView):
    model = JenisLayanan
    fields = ["layanan", "nama_jenis", "tarif"]
    template_name = "layanan/form_jenis_layanan.html"
    success_url = reverse_lazy("daftar_jenis_layanan")


class DeleteJenisLayanan(LoginRequiredMixin, DeleteView):
    model = JenisLayanan
    template_name = "layanan/delete_jenis_layanan.html"
    success_url = reverse_lazy("daftar_jenis_layanan")

