"""Base CRUD and list views for pembayaran (ADR 002 §1.1 - Thin views)."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.core.permissions import FeaturePermissionMixin, feature_permission_required
from apps.pembayaran.choices import BulanChoice
from apps.pembayaran.forms import PembayaranForm
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.selectors.payment_selectors import (
    get_active_langganan_by_pelanggan_id,
    get_all_jenis_layanan_options,
    get_all_layanan_options,
    get_pembayaran_bulanan_queryset,
    get_pembayaran_list_queryset,
    get_total_pemasukan_bulanan,
)
from apps.pembayaran.services.payment_service import delete_payment


class DaftarPembayaran(FeaturePermissionMixin, ListView):
    """Lists all payment transactions with preloaded relations, search/filter, and infinite scroll support."""
    permission_required = "pembayaran.view_pembayaran"
    model = Pembayaran
    template_name = "pembayaran/daftar_pembayaran.html"
    context_object_name = "pembayaran_list"
    paginate_by = 25

    def get_queryset(self):
        return get_pembayaran_list_queryset(
            q=self.request.GET.get("q"),
            layanan=self.request.GET.get("layanan"),
            jenis_layanan_id=self.request.GET.get("jenis_layanan"),
            tgl_mulai=self.request.GET.get("tgl_mulai"),
            tgl_akhir=self.request.GET.get("tgl_akhir"),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bulan_list"] = range(1, 13)
        context["layanan_options"] = get_all_layanan_options()
        context["jenis_layanan_options"] = get_all_jenis_layanan_options()
        context["q"] = (self.request.GET.get("q") or "").strip()
        context["selected_layanan"] = (self.request.GET.get("layanan") or "").strip()
        context["selected_jenis_layanan"] = (self.request.GET.get("jenis_layanan") or "").strip()
        context["tgl_mulai"] = (self.request.GET.get("tgl_mulai") or "").strip()
        context["tgl_akhir"] = (self.request.GET.get("tgl_akhir") or "").strip()
        return context

    def render_to_response(self, context, **response_kwargs):
        is_ajax = (
            self.request.headers.get("x-requested-with") == "XMLHttpRequest"
            or self.request.GET.get("ajax") == "1"
        )
        if is_ajax:
            from django.template.loader import render_to_string
            page_obj = context.get("page_obj")
            context["is_ajax"] = True
            html = render_to_string(
                "pembayaran/includes/_pembayaran_rows.html",
                context,
                request=self.request,
            )
            return JsonResponse(
                {
                    "html": html,
                    "has_next": page_obj.has_next() if page_obj else False,
                    "next_page": page_obj.next_page_number() if page_obj and page_obj.has_next() else None,
                    "current_page": page_obj.number if page_obj else 1,
                    "total_count": context["paginator"].count if "paginator" in context else 0,
                }
            )
        return super().render_to_response(context, **response_kwargs)


class PembayaranBulananView(FeaturePermissionMixin, TemplateView):
    """Monthly payment breakdown and income KPI."""
    permission_required = "pembayaran.view_pembayaran"
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


class TambahPembayaran(FeaturePermissionMixin, CreateView):
    """Form view for creating a new payment."""
    permission_required = "pembayaran.add_pembayaran"
    model = Pembayaran
    form_class = PembayaranForm
    template_name = "pembayaran/form_pembayaran.html"
    success_url = reverse_lazy("daftar_pembayaran")

    def form_valid(self, form):
        if not form.instance.kasir_id and self.request.user.is_authenticated:
            form.instance.kasir = self.request.user
        if not form.instance.tgl_pembayaran:
            form.instance.tgl_pembayaran = timezone.now()
        return super().form_valid(form)


class UpdatePembayaran(FeaturePermissionMixin, UpdateView):
    """Form view for updating an existing payment."""
    permission_required = "pembayaran.change_pembayaran"
    model = Pembayaran
    form_class = PembayaranForm
    template_name = "pembayaran/form_pembayaran.html"
    success_url = reverse_lazy("daftar_pembayaran")


@feature_permission_required("pembayaran.delete_pembayaran")
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
            "tarif": l.harga if (l.harga and l.harga > 0) else (l.jenis_layanan.tarif or 0),
            "nama": (
                f"{l.jenis_layanan.layanan.nama_layanan} - {l.jenis_layanan.nama_jenis} "
                + (
                    f"(Rp {l.jenis_layanan.tarif:,})".replace(",", ".")
                    if (l.jenis_layanan.tarif and l.jenis_layanan.tarif > 0)
                    else "(Tarif Manual / Meteran)"
                )
            ),
        }
        for l in langganan
    ]
    return JsonResponse(data, safe=False)
