from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from rumah.models import Rumah
from django.contrib.auth.mixins import LoginRequiredMixin
from rumah.forms import RumahForm


class DaftarRumah(LoginRequiredMixin, ListView):
    model = Rumah
    template_name = "rumah/daftar_rumah.html"
    context_object_name = "rumah_list"


class TambahRumah(LoginRequiredMixin, CreateView):
    model = Rumah
    form_class = RumahForm
    template_name = "rumah/form_rumah.html"
    success_url = reverse_lazy("daftar_rumah")


class UpdateRumah(LoginRequiredMixin, UpdateView):
    model = Rumah
    form_class = RumahForm
    template_name = "rumah/form_rumah.html"
    success_url = reverse_lazy("daftar_rumah")


def hapus_rumah(request, pk):
    if request.method == 'POST':
        data = get_object_or_404(Rumah, pk=pk)
        data.delete()
        return redirect('daftar_rumah')
    return redirect('daftar_rumah')

