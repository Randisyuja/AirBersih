from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import Pelanggan, Langganan, Tagihan
from layanan.models import JenisLayanan
from django.http import JsonResponse, HttpResponseBadRequest
from rumah.models import Rumah
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from pelanggan.forms import PelangganForm, LanggananForm, TagihanForm
from django.contrib import messages
from pelanggan.utils import generate_tagihan_setahun
from django.shortcuts import redirect, get_object_or_404


class DaftarPelanggan(LoginRequiredMixin, ListView):
    model = Pelanggan
    template_name = "pelanggan/daftar_pelanggan.html"
    context_object_name = "pelanggan_list"


class TambahPelanggan(LoginRequiredMixin, CreateView):
    model = Pelanggan
    form_class = PelangganForm
    template_name = "pelanggan/form_pelanggan.html"
    success_url = reverse_lazy("daftar_pelanggan")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["rumah"].queryset = Rumah.objects.filter(penghuni__isnull=True)
        return form


class UpdatePelanggan(LoginRequiredMixin, UpdateView):
    model = Pelanggan
    form_class = PelangganForm
    template_name = "pelanggan/form_pelanggan.html"
    success_url = reverse_lazy("daftar_pelanggan")


def hapus_pelanggan(request, pk):
    if request.method == 'POST':
        data = get_object_or_404(Pelanggan, pk=pk)
        data.delete()
        return redirect('daftar_pelanggan')
    return redirect('daftar_pelanggan')


class DaftarLangganan(LoginRequiredMixin, ListView):
    model = Langganan
    template_name = "pelanggan/daftar_langganan.html"
    context_object_name = "langganan_list"


class DetailLangganan(LoginRequiredMixin, DetailView):
    model = Langganan
    template_name = "pelanggan/detail_langganan.html"
    context_object_name = "langganan"


class TambahLangganan(LoginRequiredMixin, CreateView):
    model = Langganan
    form_class = LanggananForm
    template_name = "pelanggan/form_langganan.html"
    success_url = reverse_lazy("daftar_langganan")


class UpdateLangganan(LoginRequiredMixin, UpdateView):
    model = Langganan
    form_class = LanggananForm
    template_name = "pelanggan/form_langganan.html"
    success_url = reverse_lazy("daftar_langganan")


def hapus_langganan(request, pk):
    if request.method == 'POST':
        data = get_object_or_404(Langganan, pk=pk)
        data.delete()
        return redirect('daftar_langganan')
    return redirect('daftar_langganan')


@login_required()
def get_harga_jenis(request):
    jenis_id = request.GET.get("jenis_id")
    # print("DEBUG >>> jenis_id diterima:", jenis_id)
    try:
        jenis = JenisLayanan.objects.get(pk=jenis_id)
        # print("DEBUG >>> tarif", rupiah(jenis.tarif))
        # print(type(tarif))
        return JsonResponse({"harga": jenis.tarif})
    except JenisLayanan.DoesNotExist:
        return HttpResponseBadRequest("Jenis tidak ditemukan")


class DaftarTagihan(LoginRequiredMixin, ListView):
    model = Tagihan
    template_name = "pelanggan/daftar_tagihan.html"
    context_object_name = "tagihan_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bulan_list"] = range(1, 13)
        return context


class TambahTagihan(LoginRequiredMixin, CreateView):
    model = Tagihan
    form_class = TagihanForm
    template_name = "pelanggan/form_tagihan.html"
    success_url = reverse_lazy("daftar_tagihan")


class UpdateTagihan(LoginRequiredMixin, UpdateView):
    model = Tagihan
    form_class = TagihanForm
    template_name = "pelanggan/form_tagihan.html"
    success_url = reverse_lazy("daftar_tagihan")


def hapus_tagihan(request, pk):
    if request.method == 'POST':
        data = get_object_or_404(Tagihan, pk=pk)
        data.delete()
        return redirect('daftar_tagihan')
    return redirect('daftar_tagihan')


@login_required()
def generate_tagihan(request):
    jumlah = generate_tagihan_setahun()
    messages.success(request, f"Berhasil generate {jumlah} tagihan baru bulan ini.")
    return redirect("daftar_tagihan")
