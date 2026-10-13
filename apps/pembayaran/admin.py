from django.contrib import admin
from .models import Pembayaran


@admin.register(Pembayaran)
class PembayaranAdmin(admin.ModelAdmin):
    list_display = (
        'pelanggan',
        'jenis_layanan',
        'bulan',
        'tahun',
        'jumlah_bayar',
        'status_bayar',
        'tgl_pembayaran',
        'kasir',
    )

    list_filter = (
        'status_bayar',
        'jenis_layanan',
        'bulan',
        'tahun',
    )

    search_fields = (
        'pelanggan__nama',
        'jenis_layanan__nama',
    )

    ordering = ('-tahun', '-bulan')
    list_per_page = 25

    autocomplete_fields = ('pelanggan', 'jenis_layanan', 'kasir')

    readonly_fields = ('tgl_pembayaran',)
