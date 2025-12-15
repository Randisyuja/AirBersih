from django.contrib import admin
from django.utils.html import format_html
from .models import Pelanggan, Langganan, Tagihan


class LanggananInline(admin.TabularInline):
    model = Langganan
    extra = 1


@admin.register(Pelanggan)
class PelangganAdmin(admin.ModelAdmin):
    list_display = (
        'nama',
        'rumah',
        'status_rumah',
        'no_hp',
    )

    search_fields = ('nama', 'rumah__no_rumah')
    list_filter = ('rumah__rt',)

    autocomplete_fields = ('rumah',)
    inlines = [LanggananInline]

    def status_rumah(self, obj):
        if obj.rumah:
            return format_html('<span style="color:green;font-weight:bold">Dihuni</span>')
        return format_html('<span style="color:red;font-weight:bold">Tanpa Rumah</span>')

    status_rumah.short_description = "Status Rumah"


@admin.register(Langganan)
class LanggananAdmin(admin.ModelAdmin):
    list_display = (
        'pelanggan',
        'jenis_layanan',
        'harga',
        'aktif',
    )

    list_filter = ('aktif', 'jenis_layanan')
    search_fields = ('pelanggan__nama',)
    autocomplete_fields = ('pelanggan', 'jenis_layanan')


@admin.register(Tagihan)
class TagihanAdmin(admin.ModelAdmin):
    list_display = (
        'pelanggan',
        'jenis_layanan',
        'bulan',
        'tahun',
        'jumlah_bayar',
        'status_colored',
    )

    list_filter = (
        'status_tagihan',
        'jenis_layanan',
        'bulan',
        'tahun',
    )

    search_fields = (
        'pelanggan__nama',
        'jenis_layanan__nama_jenis',
    )

    ordering = ('-tahun', '-bulan')
    autocomplete_fields = ('pelanggan', 'jenis_layanan')

    def status_colored(self, obj):
        color = "green" if obj.status_tagihan == "Lunas" else "red"
        return format_html(
            '<b style="color:{}">{}</b>',
            color,
            obj.status_tagihan
        )

    status_colored.short_description = "Status"

