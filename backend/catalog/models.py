from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import uuid


class Category(models.Model):
    """
    Категория товаров для каталога.
    Может быть синхронизирована с категориями из 1С.
    """
    
    name = models.CharField(
        _('Название категории'),
        max_length=200,
        help_text=_('Название категории товаров')
    )
    
    slug = models.SlugField(
        _('URL-идентификатор'),
        max_length=200,
        unique=True,
        help_text=_('Уникальный идентификатор для URL')
    )
    
    description = models.TextField(
        _('Описание'),
        blank=True,
        help_text=_('Подробное описание категории')
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
        verbose_name=_('Родительская категория'),
        help_text=_('Вышестоящая категория в иерархии')
    )
    
    image = models.ImageField(
        _('Изображение'),
        upload_to='categories/',
        null=True,
        blank=True,
        help_text=_('Изображение для категории')
    )
    
    # Интеграция с 1С
    onec_ref_key = models.UUIDField(
        _('Ключ ссылки в 1С'),
        null=True,
        blank=True,
        help_text=_('Уникальный идентификатор категории в системе 1С (GUID)')
    )
    
    onec_code = models.CharField(
        _('Код в 1С'),
        max_length=50,
        blank=True,
        help_text=_('Код категории в системе 1С')
    )
    
    is_active = models.BooleanField(
        _('Активна'),
        default=True,
        help_text=_('Категория отображается в каталоге')
    )
    
    order = models.PositiveIntegerField(
        _('Порядок сортировки'),
        default=0,
        help_text=_('Порядок отображения в списке категорий')
    )
    
    created_at = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('Дата обновления'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
            models.Index(fields=['onec_ref_key']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Автоматически генерируем slug из названия
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Гарантируем уникальность slug
        original_slug = self.slug
        counter = 1
        while Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
        super().save(*args, **kwargs)
    
    @property
    def full_path(self):
        """Полный путь категории в иерархии"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name
    
    @property
    def products_count(self):
        """Количество товаров в категории (включая подкатегории)"""
        from django.db.models import Count
        return self.get_all_products().count()
    
    def get_all_products(self):
        """Все товары в категории и её подкатегориях"""
        from django.db.models import Q
        
        # Получаем все подкатегории
        def get_child_categories(category):
            children = category.children.all()
            result = list(children)
            for child in children:
                result.extend(get_child_categories(child))
            return result
        
        all_categories = [self] + get_child_categories(self)
        category_ids = [cat.id for cat in all_categories]
        
        return Product.objects.filter(categories__id__in=category_ids, is_active=True)


class Product(models.Model):
    """
    Товар в каталоге.
    Основная модель для хранения информации о товарах.
    """
    
    class Status(models.TextChoices):
        AVAILABLE = 'available', _('В наличии')
        LIMITED = 'limited', _('Ограниченное количество')
        OUT_OF_STOCK = 'out_of_stock', _('Нет в наличии')
        DISCONTINUED = 'discontinued', _('Снят с производства')
    
    name = models.CharField(
        _('Название товара'),
        max_length=500,
        help_text=_('Полное название товара')
    )
    
    slug = models.SlugField(
        _('URL-идентификатор'),
        max_length=500,
        unique=True,
        help_text=_('Уникальный идентификатор для URL')
    )
    
    description = models.TextField(
        _('Описание'),
        blank=True,
        help_text=_('Подробное описание товара')
    )
    
    short_description = models.CharField(
        _('Краткое описание'),
        max_length=500,
        blank=True,
        help_text=_('Краткое описание для карточки товара')
    )
    
    categories = models.ManyToManyField(
        Category,
        related_name='products',
        verbose_name=_('Категории'),
        help_text=_('Категории, к которым относится товар')
    )
    
    article = models.CharField(
        _('Артикул'),
        max_length=100,
        unique=True,
        help_text=_('Уникальный артикул товара')
    )
    
    barcode = models.CharField(
        _('Штрих-код'),
        max_length=50,
        blank=True,
        help_text=_('Штрих-код товара (EAN-13, UPC и т.д.)')
    )
    
    manufacturer = models.CharField(
        _('Производитель'),
        max_length=200,
        blank=True,
        help_text=_('Название производителя')
    )
    
    country_of_origin = models.CharField(
        _('Страна производства'),
        max_length=100,
        blank=True,
        help_text=_('Страна-производитель товара')
    )
    
    weight = models.DecimalField(
        _('Вес'),
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('Вес товара в килограммах')
    )
    
    dimensions = models.CharField(
        _('Габариты'),
        max_length=100,
        blank=True,
        help_text=_('Габаритные размеры (Д×Ш×В)')
    )
    
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        help_text=_('Текущий статус товара')
    )
    
    # Изображения
    main_image = models.ImageField(
        _('Основное изображение'),
        upload_to='products/main/',
        null=True,
        blank=True,
        help_text=_('Основное изображение товара')
    )
    
    # Интеграция с 1С
    onec_ref_key = models.UUIDField(
        _('Ключ ссылки в 1С'),
        unique=True,
        help_text=_('Уникальный идентификатор товара в системе 1С (GUID)')
    )
    
    onec_code = models.CharField(
        _('Код в 1С'),
        max_length=50,
        unique=True,
        help_text=_('Код товара в системе 1С')
    )
    
    onec_synced_at = models.DateTimeField(
        _('Время синхронизации с 1С'),
        null=True,
        blank=True,
        help_text=_('Когда последний раз синхронизировались данные с 1С')
    )
    
    # Технические поля
    is_active = models.BooleanField(
        _('Активен'),
        default=True,
        help_text=_('Товар отображается в каталоге')
    )
    
    is_featured = models.BooleanField(
        _('Рекомендуемый'),
        default=False,
        help_text=_('Товар отображается в рекомендуемых')
    )
    
    rating = models.DecimalField(
        _('Рейтинг'),
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text=_('Средний рейтинг товара')
    )
    
    created_at = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('Дата обновления'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('Товар')
        verbose_name_plural = _('Товары')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['article']),
            models.Index(fields=['onec_ref_key']),
            models.Index(fields=['onec_code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.article})"
    
    def save(self, *args, **kwargs):
        # Автоматически генерируем slug из названия и артикула
        if not self.slug:
            slug_base = f"{self.name} {self.article}"
            self.slug = slugify(slug_base)
        
        # Гарантируем уникальность slug
        original_slug = self.slug
        counter = 1
        while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
        super().save(*args, **kwargs)
    
    @property
    def current_price(self):
        """Текущая цена товара"""
        latest_price = self.prices.filter(is_active=True).order_by('-created_at').first()
        return latest_price.value if latest_price else 0
    
    @property
    def current_stock(self):
        """Текущий остаток товара"""
        total_stock = self.stock_entries.aggregate(total=models.Sum('quantity'))['total']
        return total_stock or 0
    
    @property
    def is_available(self):
        """Доступен ли товар для заказа"""
        return self.is_active and self.status in [
            self.Status.AVAILABLE,
            self.Status.LIMITED
        ] and self.current_stock > 0
    
    @property
    def main_category(self):
        """Основная категория товара"""
        return self.categories.first()


class ProductImage(models.Model):
    """
    Дополнительные изображения товара.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='additional_images',
        verbose_name=_('Товар')
    )
    
    image = models.ImageField(
        _('Изображение'),
        upload_to='products/additional/'
    )
    
    caption = models.CharField(
        _('Подпись'),
        max_length=200,
        blank=True,
        help_text=_('Подпись к изображению')
    )
    
    order = models.PositiveIntegerField(
        _('Порядок'),
        default=0,
        help_text=_('Порядок отображения изображений')
    )
    
    is_main = models.BooleanField(
        _('Основное изображение'),
        default=False,
        help_text=_('Использовать как основное изображение товара')
    )
    
    created_at = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Изображение товара')
        verbose_name_plural = _('Изображения товаров')
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['product', 'order']),
            models.Index(fields=['is_main']),
        ]
    
    def __str__(self):
        return f"Изображение для {self.product.name}"


class Price(models.Model):
    """
    Цена товара.
    Хранит историю изменения цен.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='prices',
        verbose_name=_('Товар')
    )
    
    value = models.DecimalField(
        _('Значение'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Цена в рублях')
    )
    
    old_value = models.DecimalField(
        _('Старая цена'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Предыдущая цена для отображения скидки')
    )
    
    currency = models.CharField(
        _('Валюта'),
        max_length=3,
        default='RUB',
        help_text=_('Код валюты (RUB, USD, EUR и т.д.)')
    )
    
    price_type = models.CharField(
        _('Тип цены'),
        max_length=50,
        choices=[
            ('retail', _('Розничная')),
            ('wholesale', _('Оптовая')),
            ('special', _('Специальная')),
            ('promo', _('Акционная')),
        ],
        default='retail',
        help_text=_('Тип цены')
    )
    
    min_quantity = models.PositiveIntegerField(
        _('Минимальное количество'),
        default=1,
        help_text=_('Минимальное количество для данной цены')
    )
    
    # Интеграция с 1С
    onec_price_type_ref = models.UUIDField(
        _('Ключ типа цены в 1С'),
        null=True,
        blank=True,
        help_text=_('Идентификатор типа цены в системе 1С')
    )
    
    is_active = models.BooleanField(
        _('Активна'),
        default=True,
        help_text=_('Цена активна и используется для расчётов')
    )
    
    valid_from = models.DateTimeField(
        _('Действует с'),
        auto_now_add=True
    )
    
    valid_to = models.DateTimeField(
        _('Действует до'),
        null=True,
        blank=True,
        help_text=_('Дата окончания действия цены')
    )
    
    created_at = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Цена')
        verbose_name_plural = _('Цены')
        ordering = ['-valid_from']
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['price_type']),
            models.Index(fields=['valid_from', 'valid_to']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.value} {self.currency}"
    
    @property
    def discount_percent(self):
        """Процент скидки относительно старой цены"""
        if self.old_value and self.old_value > 0:
            discount = ((self.old_value - self.value) / self.old_value) * 100
            return round(discount, 1)
        return 0
    
    @property
    def is_current(self):
        """Текущая ли это цена"""
        from django.utils.timezone import now
        current_time = now()
        
        if not self.is_active:
            return False
        
        if self.valid_to and self.valid_to < current_time:
            return False
        
        return True


class Stock(models.Model):
    """
    Остатки товаров на складах.
    Синхронизируется с 1С.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_entries',
        verbose_name=_('Товар')
    )
    
    warehouse = models.CharField(
        _('Склад'),
        max_length=100,
        help_text=_('Название или код склада')
    )
    
    warehouse_ref = models.UUIDField(
        _('Ключ склада в 1С'),
        null=True,
        blank=True,
        help_text=_('Идентификатор склада в системе 1С')
    )
    
    quantity = models.DecimalField(
        _('Количество'),
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Доступное количество товара')
    )
    
    reserved_quantity = models.DecimalField(
        _('Зарезервировано'),
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Количество зарезервированных товаров')
    )
    
    # Интеграция с 1С
    onec_synced_at = models.DateTimeField(
        _('Время синхронизации с 1С'),
        null=True,
        blank=True,
        help_text=_('Когда последний раз синхронизировались остатки с 1С')
    )
    
    is_active = models.BooleanField(
        _('Активен'),
        default=True,
        help_text=_('Запись об остатках активна')
    )
    
    last_updated = models.DateTimeField(
        _('Последнее обновление'),
        auto_now=True
    )
    
    created_at = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Остаток')
        verbose_name_plural = _('Остатки')
        unique_together = ['product', 'warehouse']
        ordering = ['warehouse', 'product']
        indexes = [
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['warehouse']),
            models.Index(fields=['is_active']),
            models.Index(fields=['onec_synced_at']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.warehouse}: {self.available_quantity}"
    
    @property
    def available_quantity(self):
        """Доступное для заказа количество"""
        return max(self.quantity - self.reserved_quantity, 0)
    
    @property
    def is_low_stock(self):
        """Низкий ли остаток"""
        return self.available_quantity <= 10  # Можно настроить порог
    
    def reserve(self, quantity):
        """Резервирование товара"""
        if quantity <= self.available_quantity:
            self.reserved_quantity += quantity
            self.save()
            return True
        return False
    
    def release(self, quantity):
        """Освобождение резерва"""
        if quantity <= self.reserved_quantity:
            self.reserved_quantity -= quantity
            self.save()
            return True
        return False
    
    def commit_reservation(self, quantity):
        """Подтверждение резерва (списание товара)"""
        if quantity <= self.reserved_quantity and quantity <= self.quantity:
            self.reserved_quantity -= quantity
            self.quantity -= quantity
            self.save()
            return True
        return False