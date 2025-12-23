from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from pembayaran.models import Pembayaran
from django.shortcuts import render
from pembayaran.forms import PembayaranForm, TahunForm
from pelanggan.models import Langganan, Pelanggan
from django.http import JsonResponse, HttpResponse
from io import BytesIO
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.db.models import IntegerField
from django.db.models.functions import Cast, Substr


class DaftarPembayaran(LoginRequiredMixin, ListView):
    model = Pembayaran
    template_name = "pembayaran/daftar_pembayaran.html"
    context_object_name = "pembayaran_list"

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
    form_class = PembayaranForm
    template_name = "pembayaran/form_pembayaran.html"
    success_url = reverse_lazy("daftar_pembayaran")


def hapus_pembayaran(request, pk):
    if request.method == 'POST':
        data = get_object_or_404(Pembayaran, pk=pk)
        data.delete()
        return redirect('daftar_pembayaran')
    return redirect('daftar_pembayaran')


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
def export_pembayaran_pdf(request, layanan, tahun):
    nama_layanan = layanan.upper()
    current_year = timezone.now().year

    try:
        tahun = int(tahun) if tahun else current_year
    except ValueError:
        tahun = current_year

    # Header tabel
    data = [
        [
            "Nama Pelanggan",
            "Alamat Rumah",
            "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
            "Jul", "Aug", "Sep", "Okt", "Nov", "Des",
        ],
    ]

    # Query pelanggan AKTIF + SORTING no_rumah
    pelanggan_aktif = (
        Pelanggan.objects.filter(
            langganan__jenis_layanan__layanan__nama_layanan=nama_layanan,
            langganan__aktif=True
        )
        .select_related("rumah")
        .annotate(
            # Ambil angka setelah huruf D → blok
            blok=Cast(
                Substr("rumah__no_rumah", 2, 1),
                IntegerField()
            ),
            # Ambil angka setelah NO → nomor rumah
            nomor=Cast(
                Substr("rumah__no_rumah", 5),
                IntegerField()
            )
        )
        .order_by("blok", "nomor")
        .distinct()
    )

    # Isi data tabel
    for pelanggan in pelanggan_aktif:
        status_bulan = []

        for bulan in range(1, 13):
            pembayaran = Pembayaran.objects.filter(
                jenis_layanan__layanan__nama_layanan=nama_layanan,
                pelanggan=pelanggan,
                bulan=bulan,
                tahun=tahun
            ).first()

            if pembayaran and pembayaran.status_bayar == "Lunas":
                status_bulan.append("Lunas")
            else:
                status_bulan.append("")

        data.append([
            pelanggan.nama,
            pelanggan.rumah.no_rumah,
            *status_bulan
        ])

    # ===== PDF GENERATION =====
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=landscape(A4))

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ])

    # Lebar kolom
    total_width = 9.5 * inch
    col_count = len(data[0])

    weights = [2.2, 1.6] + [1] * (col_count - 2)
    total_weight = sum(weights)
    colWidths = [(w / total_weight) * total_width for w in weights]

    table = Table(data, colWidths=colWidths, repeatRows=1)
    table.setStyle(style)
    table.hAlign = 'LEFT'

    styles = getSampleStyleSheet()
    title = Paragraph(
        f"Laporan Pembayaran {nama_layanan.capitalize()} {tahun}",
        styles['Heading1']
    )

    pdf.build([title, table])

    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Laporan_Warga.pdf"'
    return response


@login_required()
def laporan_tahunan(request, layanan):
    nama_layanan = layanan
    current_year = timezone.now().year

    form = TahunForm(request.GET or None)

    if form.is_valid():
        tahun = int(form.cleaned_data.get("tahun") or current_year)
    else:
        tahun = current_year

    data_laporan = []

    pelanggan_aktif = Pelanggan.objects.filter(
        langganan__jenis_layanan__layanan__nama_layanan=nama_layanan,
        langganan__aktif=True
    ).distinct()

    for pelanggan in pelanggan_aktif:
        status_bulan = []
        for bulan in range(1, 13):
            pembayaran = Pembayaran.objects.filter(
                jenis_layanan__layanan__nama_layanan=nama_layanan,
                pelanggan=pelanggan,
                bulan=bulan,
                tahun=tahun
            ).first()

            if pembayaran and pembayaran.status_bayar == "Lunas":
                status_bulan.append("Lunas")
            else:
                status_bulan.append("Belum")

        data_laporan.append({
            "pelanggan": pelanggan.nama,
            "alamat": pelanggan.rumah.no_rumah,
            "status_bulan": status_bulan
        })

    context = {
        "layanan": layanan,
        "data_laporan": data_laporan,
        "tahun": tahun,
        "form": form,
        "bulan_labels": [
            "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
            "Jul", "Agu", "Sep", "Okt", "Nov", "Des"
        ]
    }

    return render(request, f"pembayaran/laporan_pembayaran_layanan.html", context)

