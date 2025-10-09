from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from pembayaran.choices import StatusChoice
from pembayaran.models import Pembayaran
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from pembayaran.utils import generate_tagihan_bulanan
from pembayaran.forms import PembayaranForm
from pelanggan.models import Langganan, Pelanggan
from django.http import JsonResponse, HttpResponse
import io
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


class DaftarPembayaran(LoginRequiredMixin, ListView):
    model = Pembayaran
    template_name = "pembayaran/daftar_pembayaran.html"
    context_object_name = "pembayaran_list"
    paginate_by = 20

    def get_queryset(self):
        qs = Pembayaran.objects.select_related(
            "pelanggan", "pelanggan__rumah", "jenis_layanan", "kasir"
        ).order_by("-tahun", "-bulan", "-tgl_pembayaran")
        bulan = self.request.GET.get("bulan")
        tahun = self.request.GET.get("tahun")
        if bulan and tahun:
            qs = qs.filter(bulan=bulan, tahun=tahun)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bulan_list"] = range(1, 13)
        return context


class TambahPembayaran(LoginRequiredMixin, CreateView):
    model = Pembayaran
    form_class = PembayaranForm
    template_name = "pembayaran/form_pembayaran.html"
    success_url = reverse_lazy("daftar_pembayaran")


class UpdatePembayaran(LoginRequiredMixin, UpdateView):
    model = Pembayaran
    fields = [
        "pelanggan",
        "jenis_layanan",
        "kasir",
        "bulan",
        "tahun",
        "status_bayar",
        "tgl_pembayaran",
        "jumlah_bayar",
    ]
    template_name = "pembayaran/form_pembayaran.html"
    success_url = reverse_lazy("daftar_pembayaran")


class DeletePembayaran(LoginRequiredMixin, DeleteView):
    model = Pembayaran
    template_name = "pembayaran/delete_pembayaran.html"
    success_url = reverse_lazy("daftar_pembayaran")


@login_required()
def generate_tagihan(request):
    jumlah = generate_tagihan_bulanan()
    messages.success(request, f"Berhasil generate {jumlah} tagihan baru bulan ini.")
    return redirect("daftar_pembayaran")


@login_required()
def load_jenis_layanan(request):
    pelanggan_id = request.GET.get("pelanggan_id")
    langganan = Langganan.objects.filter(pelanggan_id=pelanggan_id).select_related("jenis_layanan")
    data = [
        {"id": l.jenis_layanan.id_jenis, "nama": str(l.jenis_layanan.nama_jenis)}
        for l in langganan
    ]
    return JsonResponse(data, safe=False)


@login_required()
def export_pembayaran_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Pembayaran"

    # Header
    ws.append([
        "ID", "Nama", "No. Rumah", "Layanan",
        "Bulan", "Tahun", "Status", "Tanggal Bayar",
        "Kasir", "Jumlah"
    ])

    queryset = Pembayaran.objects.select_related(
        "pelanggan", "pelanggan__rumah", "jenis_layanan", "kasir"
    ).order_by("-tahun", "-bulan")

    for p in queryset:
        ws.append([
            p.id_pembayaran,
            p.pelanggan.nama,
            p.pelanggan.rumah.no_rumah,
            p.jenis_layanan.nama_jenis,
            p.bulan,
            p.tahun,
            p.status_bayar,
            p.tgl_pembayaran.strftime("%d-%m-%Y") if p.tgl_pembayaran else "-",
            p.kasir.user.username if p.kasir else "-",
            float(p.jumlah_bayar)
        ])

    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = 'attachment; filename="laporan_pembayaran.xlsx"'
    wb.save(response)
    return response


@login_required()
def export_pembayaran_pdf(request):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    queryset = Pembayaran.objects.select_related(
        "pelanggan", "pelanggan__rumah", "jenis_layanan", "kasir"
    ).order_by("-tahun", "-bulan")

    y = 800
    p.setFont("Helvetica-Bold", 12)
    p.drawString(200, y, "Laporan Pembayaran")
    y -= 30

    p.setFont("Helvetica", 9)
    for pembayaran in queryset[:100]:  # batasi 100 record biar tidak overflow
        line = f"{pembayaran.id_pembayaran} | {pembayaran.pelanggan.nama} | {pembayaran.pelanggan.rumah.no_rumah} | {pembayaran.jenis_layanan.nama_jenis} | {pembayaran.bulan}/{pembayaran.tahun} | {pembayaran.status_bayar} | {pembayaran.tgl_pembayaran or '-'} | {pembayaran.jumlah_bayar}"
        p.drawString(30, y, line)
        y -= 15
        if y < 50:
            p.showPage()
            y = 800

    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type="application/pdf")


# class LaporanPembayaran(ListView):
#     model = Pembayaran
#     template_name = "pembayaran/laporan_pembayaran.html"
#     context_object_name = "pembayaran_list"
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         la = Pembayaran.objects.filter(
#             status_bayar=StatusChoice.Lunas,
#             jenis_layanan__layanan__nama_layanan="AIR"
#         ).select_related(
#             "pelanggan", "pelanggan__rumah", "jenis_layanan", "kasir"
#         ).order_by("-tahun", "-bulan", "-tgl_pembayaran")
#         tahun = self.request.GET.get("tahun")
#
#         lw = Pembayaran.objects.filter(
#             status_bayar=StatusChoice.Lunas,
#             jenis_layanan__layanan__nama_layanan="WIFI"
#         )
#
#         context["laporan_air"] = la
#         context["laporan_wifi"] = lw
#         return context

@login_required()
def laporan_tahunan(request):
    AIR = 4
    WIFI = 5
    tahun = timezone.now().year

    # struktur pivot
    laporan = []
    pelanggan_list = Pelanggan.objects.select_related("rumah").all()

    for pelanggan in pelanggan_list:
        # ambil semua pembayaran pelanggan untuk layanan tertentu di tahun ini
        pembayaran_list = Pembayaran.objects.filter(
            pelanggan=pelanggan,
            jenis_layanan_id=5,
            tahun=tahun
        )

        # jadikan dict: {bulan: "Lunas"/"Belum"}
        status = {p.bulan: ("Lunas" if p.status_bayar == "Sudah" else "Belum")
                  for p in pembayaran_list}

        # tambahkan ke laporan (list 12 bulan, Jan–Des)
        laporan.append({
            "nama": pelanggan.nama,
            "rumah": pelanggan.rumah.no_rumah if pelanggan.rumah else "-",
            "status": [status.get(bulan, "Belum") for bulan in range(1, 13)],
        })

    context = {
        "laporan": laporan,
        "tahun": tahun,
        "bulan_list": [
            (1, "Jan"), (2, "Feb"), (3, "Mar"), (4, "Apr"), (5, "Mei"), (6, "Jun"),
            (7, "Jul"), (8, "Aug"), (9, "Sep"), (10, "Okt"), (11, "Nov"), (12, "Des")
        ],
    }
    return render(request, "pembayaran/laporan_pembayaran.html", context)

