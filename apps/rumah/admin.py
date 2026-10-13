from django.contrib import admin
from .models import Rumah


@admin.register(Rumah)
class RumahAdmin(admin.ModelAdmin):
    list_display = ('rt', 'no_rumah', 'status')
    list_filter = ('rt',)
    search_fields = ('rt', 'no_rumah')
    ordering = ('rt', 'no_rumah')

    readonly_fields = ('status',)

    def status(self, obj):
        return obj.status

    status.short_description = "Status Rumah"
