from django.utils import timezone
from pelanggan.models import Langganan
from pembayaran.models import Pembayaran


def generate_tagihan_bulanan():
    bulan = timezone.now().month
    tahun = timezone.now().year
    count = 0

    for langganan in Langganan.objects.filter(aktif=True):
        exists = Pembayaran.objects.filter(
            pelanggan=langganan.pelanggan,
            jenis_layanan=langganan.jenis_layanan,
            bulan=bulan,
            tahun=tahun
        ).exists()

        if not exists:
            Pembayaran.objects.create(
                pelanggan=langganan.pelanggan,
                jenis_layanan=langganan.jenis_layanan,
                bulan=bulan,
                tahun=tahun,
                status_bayar="Belum",
                tgl_pembayaran=None,
                kasir=None,
                jumlah_bayar=langganan.jenis_layanan.tarif
            )
            count += 1

    return count
