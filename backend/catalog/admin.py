from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import Category, Product, ProductImage, Price, Stock


class ProductImageInline(admin.TabularInline):
    """Inline для изображений товара"""
    model = ProductImage
    extra = 1
    fields = ['image', 'caption', 'order', 'is_main']
    readonly_fields = ['preview']
    
    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="50" />', obj.image.url)
        return "-"
    preview.short_description = _('Предпросмотр')


class PriceInline(admin.TabularInline):
    """Inline для цен товара"""
    model = Price
    extra = 1
    fields = ['value', 'old_value', 'currency', 'price_type', 'min_quantity', 'is_active', 'valid_from', 'valid_to']
    readonly_fields = ['discount_percent']


class StockInline(admin.TabularInline):
    """Inline для остатков товара"""
    model = Stock
    extra = 1
    fields = ['warehouse', 'quantity', 'reserved_quantity', 'available_quantity', 'is_active', 'last_updated']
    readonly_fields = ['available_quantity']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка для категорий"""
    
    list_display = ['name', 'slug', 'parent', 'is_active', 'order', 'products_count', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'slug', 'description', 'onec_code']
    prepopulated_fields = {'slug': ['name']}
    readonly_fields = ['created_at', 'updated_at', 'full_path', 'products_count']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'parent', 'image')
        }),
        (_('Настройки'), {
            'fields': ('order', 'is_active')
        }),
        (_('Интеграция с 1С'), {
            'fields': ('onec_ref_key', 'onec_code'),
            'classes': ('collapse',),
        }),
        (_('Дополнительно'), {
            'fields': ('full_path', 'products_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def full_path(self, obj):
        return obj.full_path
    full_path.short_description = _('Полный путь')
    
    def products_count(self, obj):
        return obj.products_count
    products_count.short_description = _('Товаров')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админка для товаров"""
    
    list_display = ['name', 'article', 'current_price', 'current_stock', 'status', 'is_active', 'is_featured', 'created_at']
    list_filter = ['status', 'is_active', 'is_featured', 'categories', 'created_at']
    search_fields = ['name', 'article', 'description', 'onec_code', 'manufacturer']
    prepopulated_fields = {'slug': ['name', 'article']}
    readonly_fields = ['created_at', 'updated_at', 'onec_synced_at', 'current_price', 'current_stock', 'is_available', 'main_category']
    filter_horizontal = ['categories']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'article', 'barcode')
        }),
        (_('Описание'), {
            'fields': ('short_description', 'description')
        }),
        (_('Категории'), {
            'fields': ('categories',)
        }),
        (_('Характеристики'), {
            'fields': ('manufacturer', 'country_of_origin', 'weight', 'dimensions'),
            'classes': ('collapse',),
        }),
        (_('Изображения'), {
            'fields': ('main_image',),
            'classes': ('collapse',),
        }),
        (_('Статус и настройки'), {
            'fields': ('status', 'is_active', 'is_featured', 'rating')
        }),
        (_('Интеграция с 1С'), {
            'fields': ('onec_ref_key', 'onec_code', 'onec_synced_at'),
            'classes': ('collapse',),
        }),
        (_('Дополнительно'), {
            'fields': ('current_price', 'current_stock', 'is_available', 'main_category', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [ProductImageInline, PriceInline, StockInline]
    
    def current_price(self, obj):
        price = obj.current_price
        return f"{price} RUB" if price else "-"
    current_price.short_description = _('Текущая цена')
    
    def current_stock(self, obj):
        return obj.current_stock
    current_stock.short_description = _('Остаток')
    
    def is_available(self, obj):
        return obj.is_available
    is_available.short_description = _('Доступен')
    is_available.boolean = True
    
    def main_category(self, obj):
        return obj.main_category
    main_category.short_description = _('Основная категория')


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    """Админка для цен"""
    
    list_display = ['product', 'value', 'currency', 'price_type', 'is_active', 'is_current', 'valid_from', 'valid_to']
    list_filter = ['price_type', 'is_active', 'currency', 'valid_from']
    search_fields = ['product__name', 'product__article']
    readonly_fields = ['discount_percent', 'is_current', 'created_at']
    raw_id_fields = ['product']
    
    fieldsets = (
        (None, {
            'fields': ('product', 'value', 'old_value', 'currency', 'price_type')
        }),
        (_('Количество и сроки'), {
            'fields': ('min_quantity', 'valid_from', 'valid_to')
        }),
        (_('Настройки'), {
            'fields': ('is_active',)
        }),
        (_('Интеграция с 1С'), {
            'fields': ('onec_price_type_ref',),
            'classes': ('collapse',),
        }),
        (_('Расчеты'), {
            'fields': ('discount_percent', 'is_current', 'created_at'),
            'classes': ('collapse',),
        }),
    )
    
    def discount_percent(self, obj):
        return f"{obj.discount_percent}%"
    discount_percent.short_description = _('Скидка')
    
    def is_current(self, obj):
        return obj.is_current
    is_current.short_description = _('Текущая')
    is_current.boolean = True


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    """Админка для остатков"""
    
    list_display = ['product', 'warehouse', 'quantity', 'reserved_quantity', 'available_quantity', 'is_low_stock', 'is_active', 'last_updated']
    list_filter = ['warehouse', 'is_active', 'is_low_stock', 'last_updated']
    search_fields = ['product__name', 'product__article', 'warehouse']
    readonly_fields = ['available_quantity', 'is_low_stock', 'last_updated', 'created_at', 'onec_synced_at']
    raw_id_fields = ['product']
    
    fieldsets = (
        (None, {
            'fields': ('product', 'warehouse', 'warehouse_ref')
        }),
        (_('Количества'), {
            'fields': ('quantity', 'reserved_quantity', 'available_quantity')
        }),
        (_('Настройки'), {
            'fields': ('is_active',)
        }),
        (_('Интеграция с 1С'), {
            'fields': ('onec_synced_at',),
            'classes': ('collapse',),
        }),
        (_('Статус'), {
            'fields': ('is_low_stock', 'last_updated', 'created_at'),
            'classes': ('collapse',),
        }),
    )
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.short_description = _('Низкий остаток')
    is_low_stock.boolean = True


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Админка для изображений товаров"""
    
    list_display = ['product', 'preview', 'caption', 'order', 'is_main', 'created_at']
    list_filter = ['is_main', 'created_at']
    search_fields = ['product__name', 'product__article', 'caption']
    readonly_fields = ['preview', 'created_at']
    raw_id_fields = ['product']
    
    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="100" />', obj.image.url)
        return "-"
    preview.short_description = _('Изображение')