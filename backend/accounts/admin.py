from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, ClientProfile, ManagerProfile


class ClientProfileInline(admin.StackedInline):
    """Inline для профиля клиента"""
    model = ClientProfile
    can_delete = False
    verbose_name_plural = _('Профиль клиента')
    fieldsets = (
        (None, {
            'fields': (
                'company_name', 'inn', 'kpp',
                'legal_address', 'actual_address',
                'contact_person',
            )
        }),
        (_('Интеграция с 1С'), {
            'fields': (
                'onec_ref_key', 'onec_synced_at',
                'onec_sync_status',
            ),
            'classes': ('collapse',),
        }),
        (_('Дополнительно'), {
            'fields': ('notes', 'is_active_client'),
            'classes': ('collapse',),
        }),
    )


class ManagerProfileInline(admin.StackedInline):
    """Inline для профиля менеджера"""
    model = ManagerProfile
    can_delete = False
    verbose_name_plural = _('Профиль менеджера')
    fieldsets = (
        (None, {
            'fields': ('department', 'position', 'work_phone', 'internal_extension')
        }),
        (_('Разрешения'), {
            'fields': (
                'can_manage_orders',
                'can_manage_catalog',
                'can_manage_clients',
            )
        }),
        (_('Дополнительно'), {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
    )


class UserAdmin(BaseUserAdmin):
    """Админка для кастомной модели User"""
    
    list_display = ('email', 'get_full_name', 'role', 'phone', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Персональная информация'), {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        (_('Роли и разрешения'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Важные даты'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )
    
    inlines = []
    
    def get_inlines(self, request, obj=None):
        """Возвращаем соответствующие inline в зависимости от роли пользователя"""
        if obj:
            if obj.is_client:
                return [ClientProfileInline]
            elif obj.is_manager:
                return [ManagerProfileInline]
        return []
    
    def get_form(self, request, obj=None, **kwargs):
        """Кастомизируем форму в админке"""
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.is_superuser:
            # Для суперпользователей скрываем поле role
            form.base_fields['role'].disabled = True
            form.base_fields['role'].help_text = _('Роль автоматически установлена как Администратор')
        return form
    
    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение модели"""
        if not change and not obj.username:
            obj.username = obj.email
        super().save_model(request, obj, form, change)
    
    def get_full_name(self, obj):
        """Отображаем полное имя в списке"""
        return obj.get_full_name() or obj.email
    get_full_name.short_description = _('Полное имя')
    get_full_name.admin_order_field = 'first_name'


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    """Админка для профилей клиентов"""
    
    list_display = ('user', 'company_name', 'inn', 'is_linked_to_1c', 'is_active_client', 'created_at')
    list_filter = ('onec_sync_status', 'is_active_client', 'created_at')
    search_fields = ('user__email', 'company_name', 'inn', 'contact_person')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at', 'onec_synced_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'company_name', 'inn', 'kpp')
        }),
        (_('Адреса'), {
            'fields': ('legal_address', 'actual_address', 'contact_person')
        }),
        (_('Интеграция с 1С'), {
            'fields': ('onec_ref_key', 'onec_sync_status', 'onec_synced_at')
        }),
        (_('Статус'), {
            'fields': ('is_active_client', 'notes')
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    """Админка для профилей менеджеров"""
    
    list_display = ('user', 'department', 'position', 'work_phone', 'created_at')
    list_filter = ('department', 'can_manage_orders', 'can_manage_catalog', 'can_manage_clients')
    search_fields = ('user__email', 'department', 'position', 'work_phone')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'department', 'position')
        }),
        (_('Контакты'), {
            'fields': ('work_phone', 'internal_extension')
        }),
        (_('Разрешения'), {
            'fields': (
                'can_manage_orders',
                'can_manage_catalog',
                'can_manage_clients',
            )
        }),
        (_('Дополнительно'), {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# Регистрируем кастомную админку для User
admin.site.register(User, UserAdmin)