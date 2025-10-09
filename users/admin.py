from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from users.models import Kasir


class UsersAdmin(DefaultUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email',)}),
        ('Role & Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'groups'),
        }),
    )

    # Fields displayed in the user list
    list_display = ['username', 'email', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['username']

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)
        if obj:
            return [
                (None, {'fields': ('username', 'password')}),
                ('Personal info', {'fields': ('email',)}),
                ('Role & Permissions', {'fields': ('is_active',)}),
                ('Important dates', {'fields': ('last_login', 'date_joined')}),
            ]
        else:
            return [
                (None, {'fields': ('username', 'password1', 'password2', 'email')}),
                ('Role & Permissions', {'fields': ('role',)}),
            ]

    def save_model(self, request, obj, form, change):
        if 'role' in form.changed_data and not request.user.is_superuser:
            raise PermissionError("You are not allowed to modify user roles.")
        super().save_model(request, obj, form, change)


# Register the customized UserAdmin
admin.site.register(Kasir, UsersAdmin)
