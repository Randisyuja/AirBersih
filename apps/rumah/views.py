from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from apps.rumah.models import Rumah
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.rumah.forms import RumahForm


class DaftarRumah(LoginRequiredMixin, ListView):
    model = Rumah
    template_name = "rumah/daftar_rumah.html"
    context_object_name = "rumah_list"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("penghuni")
        q = self.request.GET.get("q", "").strip()
        if q:
            import re
            from django.db.models import Q
            clean_q = q.strip()
            no_spaces_q = re.sub(r"\s+", "", clean_q)
            rt_stripped = re.sub(r"^(rt|no\.?)\s*", "", clean_q, flags=re.IGNORECASE).strip()
            rt_stripped_no_spaces = re.sub(r"^(rt|no\.?)\s*", "", no_spaces_q, flags=re.IGNORECASE).strip()

            candidates = {clean_q}
            if no_spaces_q:
                candidates.add(no_spaces_q)
            if rt_stripped:
                candidates.add(rt_stripped)
                if rt_stripped.isdigit():
                    candidates.add(rt_stripped.zfill(2))
                    candidates.add(rt_stripped.lstrip("0"))
            if rt_stripped_no_spaces:
                candidates.add(rt_stripped_no_spaces)

            query_filter = Q()
            for term in candidates:
                if term:
                    query_filter |= (
                        Q(rt__icontains=term)
                        | Q(no_rumah__icontains=term)
                        | Q(penghuni__nama__icontains=term)
                    )
            queryset = queryset.filter(query_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["total_count"] = self.get_queryset().count()
        return context


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


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

@login_required
@require_POST
def tambah_rumah_ajax(request):
    form = RumahForm(request.POST)
    if form.is_valid():
        rumah = form.save()
        return JsonResponse({
            "status": "success",
            "id": rumah.id_rumah,
            "rt": rumah.rt,
            "no_rumah": rumah.no_rumah,
            "text": str(rumah),
            "message": f"Kavling {rumah} berhasil ditambahkan!"
        })
    else:
        errors = {field: [str(err) for err in errs] for field, errs in form.errors.items()}
        return JsonResponse({
            "status": "error",
            "errors": errors,
            "message": "Validasi gagal. Pastikan RT dan nomor rumah belum pernah terdaftar."
        }, status=400)


