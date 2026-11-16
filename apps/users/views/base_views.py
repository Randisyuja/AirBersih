from django.views.generic import CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from apps.users.models import Kasir
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from apps.rumah.models import Rumah
from apps.pelanggan.models import Langganan, Pelanggan, Tagihan
from apps.pembayaran.models import Pembayaran
from django.http import JsonResponse
from apps.pelanggan.forms import TagihanUpdate
from apps.pembayaran.choices import BulanChoice, StatusChoice
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from apps.users.forms import KasirCreationForm, LoginForm, PenggunaForm
from django.db.models import Sum
from apps.layanan.models import JenisLayanan, Layanan


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bulan = timezone.now().month
        tahun = timezone.now().year
        layanan = Layanan.objects.all()

        context["status_layanan"] = {}
        context["daftar_tunggakan_layanan"] = {}

        for i in layanan:
            tunggakan_qs = (
                Tagihan.objects.filter(
                    jenis_layanan__layanan__nama_layanan=i.nama_layanan,
                    bulan=bulan,
                    tahun=tahun,
                    status_tagihan=StatusChoice.Belum,
                )
                .select_related(
                    "pelanggan",
                    "pelanggan__rumah",
                    "jenis_layanan",
                    "jenis_layanan__layanan",
                )
                .order_by("pelanggan__nama")
            )
            tunggakan_list = list(tunggakan_qs)
            context["status_layanan"][i] = len(tunggakan_list)
            context["daftar_tunggakan_layanan"][i.nama_layanan] = tunggakan_list

        context["recent"] = (
            Pembayaran.objects.filter(status_bayar=StatusChoice.Lunas)
            .select_related("pelanggan", "pelanggan__rumah", "jenis_layanan", "jenis_layanan__layanan", "kasir")
            .order_by("-tgl_pembayaran", "-id_pembayaran")[:10]
        )

        context["uang_bulan_ini"] = (
            Pembayaran.objects.filter(
                bulan=bulan,
                tahun=tahun,
                status_bayar=StatusChoice.Lunas,
            ).aggregate(total_uang=Sum("jumlah_bayar"))["total_uang"]
            or 0
        )

        context["uang_tahun_ini"] = (
            Pembayaran.objects.filter(
                tahun=tahun,
                status_bayar=StatusChoice.Lunas,
            ).aggregate(total_uang=Sum("jumlah_bayar"))["total_uang"]
            or 0
        )

        context["bulan"] = bulan
        context["nama_bulan_ini"] = BulanChoice(bulan).label if bulan in BulanChoice.values else str(bulan)
        context["tahun"] = tahun
        context["layanan"] = layanan
        context["form_pembayaran"] = TagihanUpdate()

        return context

    def post(self, request):
        pelanggan = request.POST.get("pelanggan")  # input dari form
        id_layanan = request.POST.get("jenis_layanan")
        bulan = request.POST.get("bulan")
        tahun = timezone.now().year

        layanan = JenisLayanan.objects.get(pk=id_layanan)

        try:

            pelanggan = Pelanggan.objects.get(id_pelanggan=pelanggan)

            tagihan = Tagihan.objects.get(
                pelanggan=pelanggan,
                jenis_layanan_id=id_layanan,
                bulan=bulan,
                tahun=tahun,
                status_tagihan=StatusChoice.Belum
            )

            # Update status pembayaran
            tagihan.status_tagihan = StatusChoice.Lunas
            tagihan.save()

            pembayaran, created = Pembayaran.objects.get_or_create(
                pelanggan=tagihan.pelanggan,
                jenis_layanan=tagihan.jenis_layanan,
                bulan=tagihan.bulan,
                tahun=tagihan.tahun,
                defaults={
                    'status_bayar': StatusChoice.Lunas,
                    'kasir': request.user,
                    'tgl_pembayaran': timezone.now(),
                    'jumlah_bayar': tagihan.jenis_layanan.tarif
                }
            )

            if created:
                messages.success(request, f"Pembayaran {pelanggan.nama} dengan rumah {pelanggan.rumah.no_rumah} bulan {tagihan.bulan} berhasil")
            else:
                messages.success(request, f"Pembayaran {pelanggan.nama} dengan rumah {pelanggan.rumah.no_rumah} bulan {tagihan.bulan} sudah ada, tidak ditambahkan lagi.")

        except Tagihan.DoesNotExist:
            messages.error(request, f"Tagihan {layanan.layanan.nama_layanan} bulan {bulan} pada rumah dengan nomor {pelanggan.rumah.no_rumah} tidak ditemukan")

        except Rumah.DoesNotExist:
            messages.error(request, f"Rumah dengan nomor {pelanggan.rumah.no_rumah} tidak ditemukan")

        except Pembayaran.DoesNotExist:
            messages.error(request, f"Tagihan untuk rumah {pelanggan.rumah.no_rumah} belum ada atau sudah dibayar")

        return redirect("dashboard")


class DaftarKasir(LoginRequiredMixin, ListView):
    model = Kasir
    template_name = "users/daftar_users.html"
    context_object_name = "users_list"


class TambahKasir(LoginRequiredMixin, CreateView):
    model = Kasir
    form_class = PenggunaForm
    template_name = "users/form_users.html"
    success_url = reverse_lazy("daftar_users")


class UpdateKasir(LoginRequiredMixin, UpdateView):
    model = Kasir
    form_class = PenggunaForm
    template_name = "users/form_users.html"
    success_url = reverse_lazy("daftar_users")


class DeleteKasir(LoginRequiredMixin, DeleteView):
    model = Kasir
    template_name = "users/delete_users.html"
    success_url = reverse_lazy("daftar_users")


def hapus_tagihan(request, pk):
    if request.method == 'POST':
        data = get_object_or_404(Kasir, pk=pk)
        data.delete()
        return redirect('daftar_users')
    return redirect('daftar_users')

@login_required()
def get_layanan_by_rumah(request):
    no_rumah = request.GET.get("no_rumah")
    try:
        rumah = Rumah.objects.get(no_rumah=no_rumah)
        pelanggan = Pelanggan.objects.get(rumah=rumah)

        # ambil semua langganan aktif pelanggan tsb
        layanan = Langganan.objects.filter(pelanggan=pelanggan, aktif=True).select_related("jenis_layanan")

        data = [
            {"id": l.jenis_layanan.id, "nama": l.jenis_layanan.nama, "harga": str(l.jenis_layanan.harga)}
            for l in layanan
        ]
        return JsonResponse({"success": True, "layanan": data})

    except Rumah.DoesNotExist:
        return JsonResponse({"success": False, "message": "Rumah tidak ditemukan"})


User = get_user_model()


class UserLoginView(LoginView):
    template_name = "users/login.html"  # template login
    form_class = LoginForm
    redirect_authenticated_user = True  # kalau sudah login, langsung redirect
    next_page = reverse_lazy("dashboard")  # ke dashboard setelah login sukses


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("login")  # ke login setelah logout


class SignUpView(CreateView):
    model = User
    form_class = KasirCreationForm
    template_name = "users/signup.html"
    success_url = reverse_lazy("login")


@login_required()
def laporan_recent(request):
    from django.core.paginator import Paginator
    from django.template.loader import render_to_string

    bulan = timezone.now().month
    tahun = timezone.now().year

    pembayaran_list = (
        Pembayaran.objects.filter(status_bayar=StatusChoice.Lunas)
        .select_related("pelanggan", "pelanggan__rumah", "jenis_layanan", "jenis_layanan__layanan", "kasir")
        .order_by("-tgl_pembayaran", "-id_pembayaran")
    )
    first_payment = pembayaran_list.first()
    latest_id = first_payment.id_pembayaran if first_payment else 0

    paginator = Paginator(pembayaran_list, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    html = render_to_string("recent_table.html", {"recent": page_obj}, request=request)

    uang_bulan_ini = (
        Pembayaran.objects.filter(
            bulan=bulan,
            tahun=tahun,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total_uang=Sum("jumlah_bayar"))["total_uang"]
        or 0
    )
    uang_tahun_ini = (
        Pembayaran.objects.filter(
            tahun=tahun,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total_uang=Sum("jumlah_bayar"))["total_uang"]
        or 0
    )

    tunggakan_counts = {}
    for l_obj in Layanan.objects.all():
        tunggakan_counts[l_obj.nama_layanan] = Tagihan.objects.filter(
            jenis_layanan__layanan__nama_layanan=l_obj.nama_layanan,
            bulan=bulan,
            tahun=tahun,
            status_tagihan=StatusChoice.Belum,
        ).count()

    return JsonResponse(
        {
            "html": html,
            "latest_id": latest_id,
            "uang_bulan_ini": uang_bulan_ini,
            "uang_tahun_ini": uang_tahun_ini,
            "tunggakan_counts": tunggakan_counts,
        }
    )
