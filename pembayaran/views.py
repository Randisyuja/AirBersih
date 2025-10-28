from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from pembayaran.models import Pembayaran
from django.shortcuts import render
from pembayaran.forms import PembayaranForm
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
    nama_layanan = layanan
    tahun = tahun
    current_year = timezone.now().year

    try:
        tahun = int(tahun) if tahun else current_year
    except ValueError:
        tahun = current_year

    data = [
        ["Nama Pelanggan", "Alamat Rumah", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov",
         "Des"],
    ]

    pelanggan_aktif = Pelanggan.objects.filter(
        langganan__jenis_layanan__layanan__nama_layanan=nama_layanan.upper(),
        langganan__aktif=True
    ).distinct()

    for pelanggan in pelanggan_aktif:
        status_bulan = []
        for bulan in range(1, 13):
            pembayaran = Pembayaran.objects.filter(
                jenis_layanan__layanan__nama_layanan=nama_layanan.upper(),
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

    # Create a BytesIO buffer to write the PDF in memory
    buffer = BytesIO()

    # Create the PDF document in landscape A4
    pdf = SimpleDocTemplate(buffer, pagesize=landscape(A4))

    # Define a style for the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ])

    # 🔹 Tentukan total lebar halaman (A4 landscape = 842 point)
    total_width = 9.5 * inch  # lebar A4 dalam landscape
    col_count = len(data[0])

    # Misal: kolom pertama 1.5x lebih lebar, kolom kedua 1.2x, sisanya rata
    weights = [2.2, 1.6] + [1] * (col_count - 2)
    total_weight = sum(weights)
    colWidths = [(w / total_weight) * total_width for w in weights]

    table = Table(data, colWidths=colWidths, repeatRows=1)
    table.setStyle(style)

    table.hAlign = 'LEFT'

    # Add heading
    styles = getSampleStyleSheet()
    title = Paragraph(f"Laporan Pembayaran {nama_layanan.capitalize()} {tahun}", styles['Heading1'])

    # Build the PDF content
    pdf.build([title, table])

    # Move buffer to the beginning
    buffer.seek(0)

    # Return as a downloadable PDF response
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Laporan_Warga.pdf"'
    return response


@login_required()
def laporan_tahunan(request, layanan):
    tahun = request.GET.get("tahun")
    nama_layanan = layanan.upper()
    current_year = timezone.now().year

    try:
        tahun = int(tahun) if tahun else current_year
    except ValueError:
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
        "data_laporan": data_laporan,
        "tahun": tahun,
        "bulan_labels": [
            "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
            "Jul", "Agu", "Sep", "Okt", "Nov", "Des"
        ]
    }

    return render(request, f"pembayaran/laporan_pembayaran_{nama_layanan.lower()}.html", context)

