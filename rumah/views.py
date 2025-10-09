from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from rumah.models import Rumah
from django.contrib.auth.mixins import LoginRequiredMixin


class DaftarRumah(LoginRequiredMixin, ListView):
    model = Rumah
    template_name = "rumah/daftar_rumah.html"
    context_object_name = "rumah_list"


class TambahRumah(LoginRequiredMixin, CreateView):
    model = Rumah
    fields = ["rt", "no_rumah"]
    template_name = "rumah/form_rumah.html"
    success_url = reverse_lazy("daftar_rumah")


class UpdateRumah(LoginRequiredMixin, UpdateView):
    model = Rumah
    fields = ["rt", "no_rumah"]
    template_name = "rumah/form_rumah.html"
    success_url = reverse_lazy("daftar_rumah")


class DeleteRumah(LoginRequiredMixin, DeleteView):
    model = Rumah
    template_name = "rumah/delete_rumah.html"
    success_url = reverse_lazy("daftar_rumah")

