from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.conf import settings
import uuid


class Cart(models.Model):
    """
    Корзина покупок пользователя.
    Временное хранилище товаров перед оформлением заказа.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name=_('Пользователь'),
        help_text=_('Владелец корзины')
    )
    
    session_key = models.CharField(
        _('Ключ сессии'),
        max_length=40,
        blank=True,
        help_text=_('Ключ сессии для анонимных пользователей')
    )
    
    is_active = models.BooleanField(
        _('Активна'),
        default=True,
        help_text=_('Корзина активна и используется')
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
        verbose_name = _('Корзина')
        verbose_name_plural = _('Корзины')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Корзина #{self.id} - {self.user.email}"
    
    @property
    def total_items(self):
        """Общее количество позиций в корзине"""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def total_amount(self):
        """Общая сумма корзины"""
        total = 0
        for item in self.items.all():
            total += item.total_price
        return total
    
    @property
    def items_count(self):
        """Количество различных товаров в корзине"""
        return self.items.count()
    
    def add_item(self, product, quantity=1):
        """Добавление товара в корзину"""
        from catalog.models import Product
        
        if not isinstance(product, Product):
            product = Product.objects.get(pk=product)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return cart_item
    
    def remove_item(self, product):
        """Удаление товара из корзины"""
        self.items.filter(product=product).delete()
    
    def update_item_quantity(self, product, quantity):
        """Обновление количества товара в корзине"""
        cart_item = self.items.filter(product=product).first()
        if cart_item:
            if quantity <= 0:
                cart_item.delete()
            else:
                cart_item.quantity = quantity
                cart_item.save()
    
    def clear(self):
        """Очистка корзины"""
        self.items.all().delete()
    
    def merge_with(self, other_cart):
        """Слияние с другой корзиной"""
        for item in other_cart.items.all():
            self.add_item(item.product, item.quantity)
        other_cart.clear()
        other_cart.is_active = False
        other_cart.save()


class CartItem(models.Model):
    """
    Позиция в корзине покупок.
    """
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Корзина')
    )
    
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        verbose_name=_('Товар')
    )
    
    quantity = models.PositiveIntegerField(
        _('Количество'),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_('Количество товара в корзине')
    )
    
    price = models.DecimalField(
        _('Цена'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Цена товара на момент добавления в корзину')
    )
    
    added_at = models.DateTimeField(
        _('Дата добавления'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('Дата обновления'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('Позиция корзины')
        verbose_name_plural = _('Позиции корзины')
        unique_together = ['cart', 'product']
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['cart', 'product']),
            models.Index(fields=['added_at']),
        ]
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity} в корзине #{self.cart.id}"
    
    def save(self, *args, **kwargs):
        # Сохраняем текущую цену товара при добавлении в корзину
        if not self.price:
            self.price = self.product.current_price
        super().save(*args, **kwargs)
    
    @property
    def total_price(self):
        """Общая стоимость позиции"""
        return self.quantity * (self.price or self.product.current_price)
    
    @property
    def is_available(self):
        """Доступен ли товар в нужном количестве"""
        return self.product.is_available and self.product.current_stock >= self.quantity


class Order(models.Model):
    """
    Заказ клиента.
    """
    
    class Status(models.TextChoices):
        NEW = 'new', _('Новый')
        PROCESSING = 'processing', _('В обработке')
        CONFIRMED = 'confirmed', _('Подтвержден')
        ASSEMBLING = 'assembling', _('Комплектуется')
        SHIPPED = 'shipped', _('Отгружен')
        DELIVERED = 'delivered', _('Доставлен')
        CANCELLED = 'cancelled', _('Отменен')
        RETURNED = 'returned', _('Возвращен')
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Ожидает оплаты')
        PARTIAL = 'partial', _('Частично оплачен')
        PAID = 'paid', _('Оплачен')
        REFUNDED = 'refunded', _('Возврат')
        FAILED = 'failed', _('Ошибка оплаты')
    
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Наличные')
        CARD = 'card', _('Банковская карта')
        TRANSFER = 'transfer', _('Банковский перевод')
        ONLINE = 'online', _('Онлайн-оплата')
    
    # Основная информация
    order_number = models.CharField(
        _('Номер заказа'),
        max_length=20,
        unique=True,
        help_text=_('Уникальный номер заказа')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('Клиент'),
        help_text=_('Клиент, оформивший заказ')
    )
    
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        help_text=_('Текущий статус заказа')
    )
    
    # Контактная информация
    contact_person = models.CharField(
        _('Контактное лицо'),
        max_length=255,
        help_text=_('ФИО контактного лица')
    )
    
    phone = models.CharField(
        _('Телефон'),
        max_length=20,
        help_text=_('Контактный телефон')
    )
    
    email = models.EmailField(
        _('Email'),
        help_text=_('Email для уведомлений')
    )
    
    # Адрес доставки
    delivery_address = models.TextField(
        _('Адрес доставки'),
        help_text=_('Полный адрес доставки')
    )
    
    delivery_city = models.CharField(
        _('Город'),
        max_length=100,
        help_text=_('Город доставки')
    )
    
    delivery_postal_code = models.CharField(
        _('Почтовый индекс'),
        max_length=20,
        blank=True,
        help_text=_('Почтовый индекс')
    )
    
    delivery_notes = models.TextField(
        _('Примечания к доставке'),
        blank=True,
        help_text=_('Дополнительные указания по доставке')
    )
    
    # Оплата
    payment_status = models.CharField(
        _('Статус оплаты'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        help_text=_('Текущий статус оплаты')
    )
    
    payment_method = models.CharField(
        _('Способ оплаты'),
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        help_text=_('Выбранный способ оплаты')
    )
    
    total_amount = models.DecimalField(
        _('Общая сумма'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Общая сумма заказа')
    )
    
    # Скидки и налоги
    discount_amount = models.DecimalField(
        _('Сумма скидки'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Общая сумма скидки')
    )
    
    tax_amount = models.DecimalField(
        _('Сумма налога'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Сумма налога')
    )
    
    final_amount = models.DecimalField(
        _('Итоговая сумма'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Итоговая сумма к оплате')
    )
    
    # Интеграция с 1С
    onec_ref_key = models.UUIDField(
        _('Ключ ссылки в 1С'),
        null=True,
        blank=True,
        help_text=_('Уникальный идентификатор заказа в системе 1С')
    )
    
    onec_document_number = models.CharField(
        _('Номер документа в 1С'),
        max_length=50,
        blank=True,
        help_text=_('Номер документа "Заказ клиента" в 1С')
    )
    
    onec_synced_at = models.DateTimeField(
        _('Время синхронизации с 1С'),
        null=True,
        blank=True,
        help_text=_('Когда заказ был синхронизирован с 1С')
    )
    
    onec_sync_status = models.CharField(
        _('Статус синхронизации с 1С'),
        max_length=20,
        choices=[
            ('pending', _('Ожидает синхронизации')),
            ('synced', _('Синхронизирован')),
            ('failed', _('Ошибка синхронизации')),
            ('not_needed', _('Синхронизация не требуется')),
        ],
        default='pending',
        help_text=_('Статус синхронизации заказа с 1С')
    )
    
    # Технические поля
    notes = models.TextField(
        _('Примечания'),
        blank=True,
        help_text=_('Внутренние примечания по заказу')
    )
    
    manager_notes = models.TextField(
        _('Примечания менеджера'),
        blank=True,
        help_text=_('Примечания менеджера по обработке заказа')
    )
    
    is_urgent = models.BooleanField(
        _('Срочный заказ'),
        default=False,
        help_text=_('Заказ требует срочной обработки')
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
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['onec_ref_key']),
            models.Index(fields=['onec_sync_status']),
        ]
    
    def __str__(self):
        return f"Заказ #{self.order_number} - {self.user.email} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Автоматически генерируем номер заказа
        if not self.order_number:
            import datetime
            date_prefix = datetime.datetime.now().strftime('%Y%m%d')
            last_order = Order.objects.filter(order_number__startswith=date_prefix).order_by('order_number').last()
            
            if last_order:
                last_number = int(last_order.order_number[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.order_number = f"{date_prefix}{new_number:04d}"
        
        # Автоматически рассчитываем итоговую сумму
        if not self.final_amount:
            self.final_amount = self.total_amount - self.discount_amount + self.tax_amount
        
        super().save(*args, **kwargs)
    
    @property
    def items_count(self):
        """Количество позиций в заказе"""
        return self.items.count()
    
    @property
    def total_items_quantity(self):
        """Общее количество товаров в заказе"""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def is_paid(self):
        """Оплачен ли заказ"""
        return self.payment_status == self.PaymentStatus.PAID
    
    @property
    def can_be_cancelled(self):
        """Может ли заказ быть отменен"""
        return self.status in [
            self.Status.NEW,
            self.Status.PROCESSING,
            self.Status.CONFIRMED,
        ]
    
    @property
    def delivery_info(self):
        """Информация о доставке"""
        return f"{self.delivery_city}, {self.delivery_address}"
    
    def calculate_totals(self):
        """Перерасчет всех сумм заказа"""
        items = self.items.all()
        
        total_amount = sum(item.total_price for item in items)
        total_quantity = sum(item.quantity for item in items)
        
        # Здесь можно добавить логику расчета скидок и налогов
        discount_amount = 0
        tax_amount = total_amount * 0.20  # Пример: 20% НДС
        
        self.total_amount = total_amount
        self.discount_amount = discount_amount
        self.tax_amount = tax_amount
        self.final_amount = total_amount - discount_amount + tax_amount
        
        self.save()
    
    def create_from_cart(self, cart):
        """Создание заказа из корзины"""
        self.user = cart.user
        
        # Копируем контактную информацию из профиля пользователя
        if hasattr(self.user, 'client_profile'):
            profile = self.user.client_profile
            self.contact_person = profile.contact_person or f"{self.user.first_name} {self.user.last_name}"
            self.phone = self.user.phone
            self.email = self.user.email
            self.delivery_address = profile.actual_address or profile.legal_address
            # Можно добавить логику для определения города из адреса
        
        self.save()
        
        # Переносим товары из корзины в заказ
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=self,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.current_price,
                cart_item_price=cart_item.price
            )
        
        # Пересчитываем суммы
        self.calculate_totals()
        
        # Очищаем корзину
        cart.clear()
        cart.is_active = False
        cart.save()
        
        return self


class OrderItem(models.Model):
    """
    Позиция в заказе.
    Сохраняет информацию о товаре на момент оформления заказа.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Заказ')
    )
    
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.PROTECT,
        verbose_name=_('Товар')
    )
    
    quantity = models.PositiveIntegerField(
        _('Количество'),
        validators=[MinValueValidator(1)],
        help_text=_('Количество товара в заказе')
    )
    
    price = models.DecimalField(
        _('Цена'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Цена товара на момент оформления заказа')
    )
    
    cart_item_price = models.DecimalField(
        _('Цена в корзине'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Цена товара на момент добавления в корзину')
    )
    
    # Интеграция с 1С
    onec_ref_key = models.UUIDField(
        _('Ключ ссылки в 1С'),
        null=True,
        blank=True,
        help_text=_('Уникальный идентификатор позиции в системе 1С')
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
        verbose_name = _('Позиция заказа')
        verbose_name_plural = _('Позиции заказа')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order', 'product']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity} в заказе #{self.order.order_number}"
    
    @property
    def total_price(self):
        """Общая стоимость позиции"""
        return self.quantity * self.price
    
    @property
    def price_difference(self):
        """Разница между ценой в корзине и ценой в заказе"""
        if self.cart_item_price:
            return self.price - self.cart_item_price
        return 0
    
    @property
    def is_price_changed(self):
        """Изменялась ли цена с момента добавления в корзину"""
        return bool(self.cart_item_price and self.price != self.cart_item_price)


class OrderStatusHistory(models.Model):
    """
    История изменения статусов заказа.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('Заказ')
    )
    
    old_status = models.CharField(
        _('Старый статус'),
        max_length=20,
        choices=Order.Status.choices,
        null=True,
        blank=True
    )
    
    new_status = models.CharField(
        _('Новый статус'),
        max_length=20,
        choices=Order.Status.choices
    )
    
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Изменен пользователем')
    )
    
    reason = models.TextField(
        _('Причина изменения'),
        blank=True,
        help_text=_('Причина изменения статуса')
    )
    
    notes = models.TextField(
        _('Примечания'),
        blank=True,
        help_text=_('Дополнительные примечания')
    )
    
    changed_at = models.DateTimeField(
        _('Время изменения'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('История статуса заказа')
        verbose_name_plural = _('История статусов заказов')
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['order', 'changed_at']),
            models.Index(fields=['changed_by']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number}: {self.get_old_status_display() or 'Нет'} → {self.get_new_status_display()}"