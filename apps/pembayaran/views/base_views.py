"""Base CRUD and list views for pembayaran (ADR 002 §1.1 - Thin views)."""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.pembayaran.choices import BulanChoice
from apps.pembayaran.forms import PembayaranForm
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.selectors.payment_selectors import (
    get_active_langganan_by_pelanggan_id,
    get_pembayaran_bulanan_queryset,
    get_pembayaran_list_queryset,
    get_total_pemasukan_bulanan,
)
from apps.pembayaran.services.payment_service import delete_payment


class DaftarPembayaran(LoginRequiredMixin, ListView):
    """Lists all payment transactions with preloaded relations."""
    model = Pembayaran
    template_name = "pembayaran/daftar_pembayaran.html"
    context_object_name = "pembayaran_list"

    def get_queryset(self):
        return get_pembayaran_list_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bulan_list"] = range(1, 13)
        return context


class PembayaranBulananView(TemplateView):
    """Monthly payment breakdown and income KPI."""
    template_name = "pembayaran/pembayaran_bulanan.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        bulan = int(self.request.GET.get("bulan", now.month))
        tahun = int(self.request.GET.get("tahun", now.year))

        pembayaran = get_pembayaran_bulanan_queryset(bulan=bulan, tahun=tahun)
        total_pemasukan = get_total_pemasukan_bulanan(bulan=bulan, tahun=tahun)

        context.update({
            "pembayaran": pembayaran,
            "bulan": bulan,
            "tahun": tahun,
            "total_pemasukan": total_pemasukan,
            "bulan_choices": BulanChoice.choices,
        })
        return context


class TambahPembayaran(LoginRequiredMixin, CreateView):
    """Form view for creating a new payment."""
    model = Pembayaran
    form_class = PembayaranForm
    template_name = "pembayaran/form_pembayaran.html"
    success_url = reverse_lazy("daftar_pembayaran")


class UpdatePembayaran(LoginRequiredMixin, UpdateView):
    """Form view for updating an existing payment."""
    model = Pembayaran
    form_class = PembayaranForm
    template_name = "pembayaran/form_pembayaran.html"
    success_url = reverse_lazy("daftar_pembayaran")


def hapus_pembayaran(request: HttpRequest, pk: int) -> HttpResponse:
    """Action view for deleting payment by pk."""
    if request.method == "POST":
        delete_payment(payment_id=pk)
        return redirect("daftar_pembayaran")
    return redirect("daftar_pembayaran")


@login_required
def load_jenis_layanan(request: HttpRequest) -> JsonResponse:
    """AJAX endpoint loading subscribed services for a customer."""
    pelanggan_id = request.GET.get("pelanggan_id")
    if not pelanggan_id:
        return JsonResponse([], safe=False)

    langganan = get_active_langganan_by_pelanggan_id(int(pelanggan_id))
    data = [
        {
            "id": l.jenis_layanan.id_jenis,
            "nama": (
                f"{l.jenis_layanan.layanan.nama_layanan} - "
                f"{l.jenis_layanan.nama_jenis} "
                f"(Rp {l.jenis_layanan.tarif:,})".replace(",", ".")
            ),
        }
        for l in langganan
    ]
    return JsonResponse(data, safe=False)
