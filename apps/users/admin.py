from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.users.models import Kasir


@admin.register(Kasir)
class UsersAdmin(UserAdmin):
    model = Kasir

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'first_name', 'last_name', 'no_hp')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'first_name',
                'last_name',
                'no_hp',
                'password1',
                'password2',
            ),
        }),
    )

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'no_hp',
        'is_staff',
        'is_active',
    )

    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'no_hp')
    ordering = ('username',)

    def get_fieldsets(self, request, obj=None):
        # Superuser: full access
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)

        # Edit existing user (non-superuser)
        if obj:
            return (
                (None, {'fields': ('username',)}),
                ('Personal info', {'fields': ('email', 'first_name', 'last_name', 'no_hp')}),
                ('Status', {'fields': ('is_active',)}),
                ('Important dates', {'fields': ('last_login',)}),
            )

        # Create new user (non-superuser)
        return (
            (None, {
                'fields': (
                    'username',
                    'email',
                    'first_name',
                    'last_name',
                    'no_hp',
                    'password1',
                    'password2',
                )
            }),
        )

    def save_model(self, request, obj, form, change):
        # Non-superuser tidak boleh ubah privilege
        if not request.user.is_superuser:
            obj.is_staff = False
            obj.is_superuser = False
        super().save_model(request, obj, form, change)
