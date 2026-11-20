"""Management command to create/sync default Django Groups & Permissions for RBAC."""

from django.core.management.base import BaseCommand
from apps.core.permissions import sync_default_groups


class Command(BaseCommand):
    help = "Membuat dan menyinkronkan Group/Role default (Administrator, Kasir, Viewer) beserta hak akses fiturnya."

    def handle(self, *args, **options):
        groups = sync_default_groups()
        for name, group in groups.items():
            self.stdout.write(
                self.style.SUCCESS(
                    f"Group '{name}' tersinkronisasi ({group.permissions.count()} hak akses)."
                )
            )
