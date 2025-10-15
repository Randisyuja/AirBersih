from django.views.generic import CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from users.models import Kasir
from django.utils import timezone
from pembayaran.models import Pembayaran
from django.contrib import messages
from django.shortcuts import redirect
from rumah.models import Rumah
from pelanggan.models import Langganan, Pelanggan
from django.http import JsonResponse
from pembayaran.forms import PembayaranUpdate
from pembayaran.choices import StatusChoice
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from users.forms import PenggunaForm, LoginForm


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bulan = timezone.now().month
        tahun = timezone.now().year

        context["status_wifi"] = Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan="WIFI",
            bulan=bulan, tahun=tahun, status_bayar=StatusChoice.Belum
        ).select_related("pelanggan", "pelanggan__rumah").count()

        context["status_air"] = Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan="AIR",
            bulan=bulan, tahun=tahun, status_bayar=StatusChoice.Belum
        ).select_related("pelanggan", "pelanggan__rumah").count()

        context["recent"] = Pembayaran.objects.filter(
            status_bayar=StatusChoice.Lunas
        ).select_related(
            "pelanggan", "pelanggan", "jenis_layanan"
        ).order_by("-tgl_pembayaran")[:10]

        context["bulan"] = bulan
        context["tahun"] = tahun
        context["form_pembayaran"] = PembayaranUpdate()

        return context

    def post(self, request):
        pelanggan = request.POST.get("pelanggan")  # input dari form
        id_layanan = request.POST.get("jenis_layanan")
        bulan = request.POST.get("bulan")
        tahun = timezone.now().year

        try:

            pelanggan = Pelanggan.objects.get(id_pelanggan=pelanggan)

            pembayaran = Pembayaran.objects.get(
                pelanggan=pelanggan,
                jenis_layanan=id_layanan,
                bulan=bulan,
                tahun=tahun,
                status_bayar=StatusChoice.Belum
            )

            # Update status pembayaran
            pembayaran.status_bayar = StatusChoice.Lunas
            pembayaran.tgl_pembayaran = timezone.now().date()
            pembayaran.kasir = request.user
            pembayaran.save()

            messages.success(request, f"Pembayaran {pelanggan.nama} dengan rumah {pelanggan.rumah.no_rumah} berhasil diperbarui")

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

    def form_valid(self, form):
        # pastikan password disimpan dengan benar (hash)
        kasir = form.save(commit=False)
        kasir.set_password(form.cleaned_data["password"])
        kasir.save()
        return super().form_valid(form)


class UpdateKasir(LoginRequiredMixin, UpdateView):
    model = Kasir
    form_class = PenggunaForm
    template_name = "users/form_users.html"
    success_url = reverse_lazy("daftar_users")


class DeleteKasir(LoginRequiredMixin, DeleteView):
    model = Kasir
    template_name = "users/delete_users.html"
    success_url = reverse_lazy("daftar_users")


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
    form_class = UserCreationForm  # bisa custom form kalau mau tambah field
    template_name = "users/signup.html"
    success_url = reverse_lazy("login")  # setelah daftar, ke login
