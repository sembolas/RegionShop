from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse

from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory


class CartItemInline(admin.TabularInline):
    """Inline для позиций корзины"""
    model = CartItem
    extra = 0
    fields = ['product', 'quantity', 'price', 'total_price', 'is_available', 'added_at']
    readonly_fields = ['total_price', 'is_available']
    raw_id_fields = ['product']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Админка для корзин"""
    
    list_display = ['id', 'user', 'total_items', 'total_amount', 'items_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'total_items', 'total_amount', 'items_count']
    raw_id_fields = ['user']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'session_key', 'is_active')
        }),
        (_('Суммы'), {
            'fields': ('total_items', 'total_amount', 'items_count'),
            'classes': ('collapse',),
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [CartItemInline]
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = _('Всего товаров')
    
    def total_amount(self, obj):
        return f"{obj.total_amount} RUB"
    total_amount.short_description = _('Общая сумма')
    
    def items_count(self, obj):
        return obj.items_count
    items_count.short_description = _('Разных товаров')


class OrderItemInline(admin.TabularInline):
    """Inline для позиций заказа"""
    model = OrderItem
    extra = 0
    fields = ['product', 'quantity', 'price', 'total_price', 'price_difference', 'is_price_changed']
    readonly_fields = ['total_price', 'price_difference', 'is_price_changed']
    raw_id_fields = ['product']


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline для истории статусов заказа"""
    model = OrderStatusHistory
    extra = 0
    fields = ['old_status', 'new_status', 'changed_by', 'reason', 'changed_at']
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'changed_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Админка для заказов"""
    
    list_display = [
        'order_number', 'user', 'status', 'payment_status', 'total_amount', 
        'final_amount', 'items_count', 'is_paid', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'payment_method', 'is_urgent', 'created_at']
    search_fields = [
        'order_number', 'user__email', 'contact_person', 'phone', 'email',
        'delivery_address', 'delivery_city'
    ]
    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 'items_count', 
        'total_items_quantity', 'is_paid', 'can_be_cancelled', 'delivery_info',
        'onec_synced_at'
    ]
    raw_id_fields = ['user']
    
    fieldsets = (
        (None, {
            'fields': ('order_number', 'user', 'status', 'is_urgent')
        }),
        (_('Контактная информация'), {
            'fields': ('contact_person', 'phone', 'email')
        }),
        (_('Доставка'), {
            'fields': ('delivery_city', 'delivery_address', 'delivery_postal_code', 'delivery_notes')
        }),
        (_('Оплата'), {
            'fields': ('payment_status', 'payment_method')
        }),
        (_('Суммы'), {
            'fields': ('total_amount', 'discount_amount', 'tax_amount', 'final_amount'),
            'classes': ('collapse',),
        }),
        (_('Интеграция с 1С'), {
            'fields': ('onec_ref_key', 'onec_document_number', 'onec_sync_status', 'onec_synced_at'),
            'classes': ('collapse',),
        }),
        (_('Примечания'), {
            'fields': ('notes', 'manager_notes'),
            'classes': ('collapse',),
        }),
        (_('Дополнительно'), {
            'fields': (
                'items_count', 'total_items_quantity', 'is_paid', 
                'can_be_cancelled', 'delivery_info', 'created_at', 'updated_at'
            ),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    actions = ['mark_as_processing', 'mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered']
    
    def items_count(self, obj):
        return obj.items_count
    items_count.short_description = _('Позиций')
    
    def total_items_quantity(self, obj):
        return obj.total_items_quantity
    total_items_quantity.short_description = _('Всего товаров')
    
    def is_paid(self, obj):
        return obj.is_paid
    is_paid.short_description = _('Оплачен')
    is_paid.boolean = True
    
    def can_be_cancelled(self, obj):
        return obj.can_be_cancelled
    can_be_cancelled.short_description = _('Можно отменить')
    can_be_cancelled.boolean = True
    
    def delivery_info(self, obj):
        return obj.delivery_info
    delivery_info.short_description = _('Доставка')
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status=Order.Status.PROCESSING)
    mark_as_processing.short_description = _('Перевести в статус "В обработке"')
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status=Order.Status.CONFIRMED)
    mark_as_confirmed.short_description = _('Перевести в статус "Подтвержден"')
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status=Order.Status.SHIPPED)
    mark_as_shipped.short_description = _('Перевести в статус "Отгружен"')
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status=Order.Status.DELIVERED)
    mark_as_delivered.short_description = _('Перевести в статус "Доставлен"')
    
    def save_model(self, request, obj, form, change):
        # Сохраняем историю изменения статуса
        if change and 'status' in form.changed_data:
            OrderStatusHistory.objects.create(
                order=obj,
                old_status=form.initial.get('status'),
                new_status=obj.status,
                changed_by=request.user,
                reason='Изменено через админку'
            )
        
        super().save_model(request, obj, form, change)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Админка для позиций корзины"""
    
    list_display = ['cart', 'product', 'quantity', 'price', 'total_price', 'is_available', 'added_at']
    list_filter = ['added_at']
    search_fields = ['cart__user__email', 'product__name', 'product__article']
    readonly_fields = ['total_price', 'is_available', 'added_at', 'updated_at']
    raw_id_fields = ['cart', 'product']
    
    fieldsets = (
        (None, {
            'fields': ('cart', 'product', 'quantity', 'price')
        }),
        (_('Расчеты'), {
            'fields': ('total_price', 'is_available'),
            'classes': ('collapse',),
        }),
        (_('Даты'), {
            'fields': ('added_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = _('Общая стоимость')
    
    def is_available(self, obj):
        return obj.is_available
    is_available.short_description = _('Доступен')
    is_available.boolean = True


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Админка для позиций заказа"""
    
    list_display = ['order', 'product', 'quantity', 'price', 'total_price', 'price_difference', 'created_at']
    list_filter = ['created_at']
    search_fields = ['order__order_number', 'product__name', 'product__article']
    readonly_fields = ['total_price', 'price_difference', 'is_price_changed', 'created_at', 'updated_at']
    raw_id_fields = ['order', 'product']
    
    fieldsets = (
        (None, {
            'fields': ('order', 'product', 'quantity', 'price', 'cart_item_price')
        }),
        (_('Расчеты'), {
            'fields': ('total_price', 'price_difference', 'is_price_changed'),
            'classes': ('collapse',),
        }),
        (_('Интеграция с 1С'), {
            'fields': ('onec_ref_key',),
            'classes': ('collapse',),
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = _('Общая стоимость')
    
    def price_difference(self, obj):
        return obj.price_difference
    price_difference.short_description = _('Разница цены')
    
    def is_price_changed(self, obj):
        return obj.is_price_changed
    is_price_changed.short_description = _('Цена изменена')
    is_price_changed.boolean = True


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Админка для истории статусов заказов"""
    
    list_display = ['order', 'old_status_display', 'new_status_display', 'changed_by', 'changed_at']
    list_filter = ['new_status', 'changed_at']
    search_fields = ['order__order_number', 'changed_by__email', 'reason']
    readonly_fields = ['order', 'old_status', 'new_status', 'changed_by', 'reason', 'notes', 'changed_at']
    
    fieldsets = (
        (None, {
            'fields': ('order', 'old_status', 'new_status', 'changed_by')
        }),
        (_('Причины и примечания'), {
            'fields': ('reason', 'notes'),
            'classes': ('collapse',),
        }),
        (_('Дата'), {
            'fields': ('changed_at',),
            'classes': ('collapse',),
        }),
    )
    
    def old_status_display(self, obj):
        return obj.get_old_status_display() if obj.old_status else '-'
    old_status_display.short_description = _('Старый статус')
    
    def new_status_display(self, obj):
        return obj.get_new_status_display()
    new_status_display.short_description = _('Новый статус')