# cashApp/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AdminProfile, Project, Transaction, AuditLog


# ── CustomUser ─────────────────────────────────────────────────────────────────

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username', 'email', 'full_name', 'user_type', 'is_frozen', 'date_joined')
    list_filter   = ('user_type', 'is_frozen', 'is_active')
    search_fields = ('username', 'email', 'full_name', 'phone')
    ordering      = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {
            'fields': ('full_name', 'phone', 'user_type', 'is_frozen')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Extra Info', {
            'fields': ('full_name', 'phone', 'email', 'user_type')
        }),
    )


# ── AdminProfile ───────────────────────────────────────────────────────────────

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)


# ── Project ────────────────────────────────────────────────────────────────────

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display  = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username')
    list_filter   = ('created_at',)
    readonly_fields = ('created_at',)
    filter_horizontal = ('members',)


# ── Transaction ────────────────────────────────────────────────────────────────

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = (
        'title', 'amount', 'type', 'user', 'project',
        'date', 'is_deleted', 'delete_requested'
    )
    list_filter   = ('type', 'is_deleted', 'delete_requested', 'date')
    search_fields = ('title', 'user__username', 'project__name')
    ordering      = ('-date',)
    readonly_fields = ('delete_requested_at', 'deleted_at')

    actions = ['mark_deleted', 'restore_transactions']

    @admin.action(description='Soft-delete selected transactions')
    def mark_deleted(self, request, queryset):
        queryset.update(is_deleted=True)

    @admin.action(description='Restore selected transactions')
    def restore_transactions(self, request, queryset):
        queryset.update(is_deleted=False, delete_requested=False,
                        delete_requested_at=None, deleted_at=None)


# ── AuditLog ───────────────────────────────────────────────────────────────────

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ('timestamp', 'actor', 'action', 'target_type', 'target_repr', 'ip_address')
    list_filter   = ('action', 'timestamp')
    search_fields = ('actor__username', 'target_repr', 'detail', 'ip_address')
    ordering      = ('-timestamp',)
    readonly_fields = (
        'actor', 'action', 'target_type', 'target_id',
        'target_repr', 'detail', 'timestamp', 'ip_address'
    )

    def has_add_permission(self, request):
        return False  

    def has_change_permission(self, request, obj=None):
        return False  