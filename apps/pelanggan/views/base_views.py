from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from apps.pelanggan.models import Pelanggan, Langganan, Tagihan
from apps.layanan.models import JenisLayanan
from django.http import JsonResponse, HttpResponseBadRequest
from apps.rumah.models import Rumah
from django.contrib.auth.decorators import login_required
from apps.core.permissions import FeaturePermissionMixin, feature_permission_required
from apps.pelanggan.forms import PelangganForm, LanggananForm, TagihanForm
from django.contrib import messages
from django.db.models import ProtectedError
from apps.pelanggan.utils import generate_tagihan_setahun
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone


class DaftarPelanggan(FeaturePermissionMixin, ListView):
    permission_required = "pelanggan.view_pelanggan"
    model = Pelanggan
    template_name = "pelanggan/daftar_pelanggan.html"
    context_object_name = "pelanggan_list"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("rumah")
        q = self.request.GET.get("q", "").strip()
        if q:
            import re
            from django.db.models import Q
            clean_q = q.strip()
            no_spaces_q = re.sub(r"\s+", "", clean_q)
            rt_stripped = re.sub(r"^(rt|no\.?)\s*", "", clean_q, flags=re.IGNORECASE).strip()
            rt_stripped_no_spaces = re.sub(r"^(rt|no\.?)\s*", "", no_spaces_q, flags=re.IGNORECASE).strip()

            candidates = {clean_q}
            if no_spaces_q:
                candidates.add(no_spaces_q)
            if rt_stripped:
                candidates.add(rt_stripped)
                if rt_stripped.isdigit():
                    candidates.add(rt_stripped.zfill(2))
                    candidates.add(rt_stripped.lstrip("0"))
            if rt_stripped_no_spaces:
                candidates.add(rt_stripped_no_spaces)

            query_filter = Q()
            for term in candidates:
                if term:
                    query_filter |= (
                        Q(nama__icontains=term)
                        | Q(rumah__rt__icontains=term)
                        | Q(rumah__no_rumah__icontains=term)
                        | Q(no_hp__icontains=term)
                        | Q(barcode__icontains=term)
                    )
            queryset = queryset.filter(query_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["total_count"] = self.get_queryset().count()
        return context


class TambahPelanggan(FeaturePermissionMixin, CreateView):
    permission_required = "pelanggan.add_pelanggan"
    model = Pelanggan
    form_class = PelangganForm
    template_name = "pelanggan/form_pelanggan.html"
    success_url = reverse_lazy("daftar_pelanggan")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["rumah"].queryset = Rumah.objects.filter(penghuni__isnull=True)
        return form


class UpdatePelanggan(FeaturePermissionMixin, UpdateView):
    permission_required = "pelanggan.change_pelanggan"
    model = Pelanggan
    form_class = PelangganForm
    template_name = "pelanggan/form_pelanggan.html"
    success_url = reverse_lazy("daftar_pelanggan")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        from django.db.models import Q
        current_rumah_id = self.object.rumah_id if self.object and self.object.rumah_id else None
        form.fields["rumah"].queryset = Rumah.objects.filter(Q(penghuni__isnull=True) | Q(id_rumah=current_rumah_id))
        return form


@feature_permission_required("pelanggan.delete_pelanggan")
def hapus_pelanggan(request, pk):
    if request.method == "POST":
        data = get_object_or_404(Pelanggan, pk=pk)
        nama = data.nama
        try:
            data.delete()
            messages.success(request, f"Pelanggan '{nama}' berhasil dihapus.")
        except ProtectedError as exc:
            referenced = [str(obj) for obj in getattr(exc, "protected_objects", [])]
            detail = f" (terhubung dengan: {', '.join(referenced)})" if referenced else ""
            messages.error(
                request,
                f"Gagal menghapus Pelanggan '{nama}' karena masih terhubung dengan transaksi/tagihan aktif{detail}. "
                f"Silakan selesaikan data terkait terlebih dahulu.",
            )
        return redirect("daftar_pelanggan")
    return redirect("daftar_pelanggan")


class DaftarLangganan(FeaturePermissionMixin, ListView):
    permission_required = "pelanggan.view_langganan"
    model = Langganan
    template_name = "pelanggan/daftar_langganan.html"
    context_object_name = "langganan_list"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "pelanggan",
                "pelanggan__rumah",
                "jenis_layanan",
                "jenis_layanan__layanan",
            )
            .order_by("pelanggan__nama")
        )


class DetailLangganan(FeaturePermissionMixin, DetailView):
    permission_required = "pelanggan.view_langganan"
    model = Langganan
    template_name = "pelanggan/detail_langganan.html"
    context_object_name = "langganan"


class TambahLangganan(FeaturePermissionMixin, CreateView):
    permission_required = "pelanggan.add_langganan"
    model = Langganan
    form_class = LanggananForm
    template_name = "pelanggan/form_langganan.html"
    success_url = reverse_lazy("daftar_langganan")


class UpdateLangganan(FeaturePermissionMixin, UpdateView):
    permission_required = "pelanggan.change_langganan"
    model = Langganan
    form_class = LanggananForm
    template_name = "pelanggan/form_langganan.html"
    success_url = reverse_lazy("daftar_langganan")


@feature_permission_required("pelanggan.delete_langganan")
def hapus_langganan(request, pk):
    if request.method == "POST":
        data = get_object_or_404(Langganan, pk=pk)
        label = f"{data.pelanggan.nama} ({data.jenis_layanan})"
        try:
            data.delete()
            messages.success(request, f"Langganan '{label}' berhasil dihapus.")
        except ProtectedError as exc:
            referenced = [str(obj) for obj in getattr(exc, "protected_objects", [])]
            detail = f" (terhubung dengan: {', '.join(referenced)})" if referenced else ""
            messages.error(
                request,
                f"Gagal menghapus Langganan '{label}' karena masih terhubung dengan tagihan/transaksi aktif{detail}.",
            )
        return redirect("daftar_langganan")
    return redirect("daftar_langganan")


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


class DaftarTagihan(FeaturePermissionMixin, ListView):
    permission_required = "pelanggan.view_tagihan"
    model = Tagihan
    template_name = "pelanggan/daftar_tagihan.html"
    context_object_name = "tagihan_list"
    paginate_by = 25

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "pelanggan",
                "pelanggan__rumah",
                "jenis_layanan",
                "jenis_layanan__layanan",
            )
            .order_by("-tahun", "-bulan", "pelanggan__nama")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bulan_list"] = range(1, 13)
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
                "pelanggan/includes/_tagihan_rows.html",
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


class TambahTagihan(FeaturePermissionMixin, CreateView):
    permission_required = "pelanggan.add_tagihan"
    model = Tagihan
    form_class = TagihanForm
    template_name = "pelanggan/form_tagihan.html"
    success_url = reverse_lazy("daftar_tagihan")


class UpdateTagihan(FeaturePermissionMixin, UpdateView):
    permission_required = "pelanggan.change_tagihan"
    model = Tagihan
    form_class = TagihanForm
    template_name = "pelanggan/form_tagihan.html"
    success_url = reverse_lazy("daftar_tagihan")


@feature_permission_required("pelanggan.delete_tagihan")
def hapus_tagihan(request, pk):
    if request.method == 'POST':
        data = get_object_or_404(Tagihan, pk=pk)
        data.delete()
        return redirect('daftar_tagihan')
    return redirect('daftar_tagihan')


@feature_permission_required("pelanggan.add_tagihan")
def generate_tagihan(request):
    if request.method == "POST":
        tahun = int(request.POST.get("year", timezone.now().year))
        jumlah = generate_tagihan_setahun(tahun)
        messages.success(request, f"Berhasil generate {jumlah} tagihan untuk tahun {tahun}.")
        return redirect("daftar_tagihan")
    return redirect("daftar_tagihan")
