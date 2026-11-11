"""
Сигналы для приложения каталога.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.timezone import now

from .models import Product, Stock, Price


@receiver(post_save, sender=Stock)
def update_product_status_on_stock_change(sender, instance, **kwargs):
    """
    Обновляем статус товара при изменении остатков.
    """
    product = instance.product
    
    # Получаем общий доступный остаток по всем складам
    from django.db.models import Sum
    total_available = Stock.objects.filter(
        product=product,
        is_active=True
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    # Определяем новый статус товара
    if total_available <= 0:
        product.status = Product.Status.OUT_OF_STOCK
    elif total_available <= 10:  # Порог для "ограниченного количества"
        product.status = Product.Status.LIMITED
    else:
        product.status = Product.Status.AVAILABLE
    
    # Сохраняем только если статус изменился
    if product.has_changed('status'):
        product.save()


@receiver(pre_save, sender=Price)
def deactivate_old_prices(sender, instance, **kwargs):
    """
    Деактивируем старые цены при создании новой активной цены.
    """
    if instance.is_active and instance.pk is None:  # Новая активная цена
        # Деактивируем все старые активные цены для этого товара
        Price.objects.filter(
            product=instance.product,
            price_type=instance.price_type,
            is_active=True
        ).update(is_active=False)


@receiver(post_save, sender=Product)
def create_default_price(sender, instance, created, **kwargs):
    """
    Создаем цену по умолчанию при создании товара.
    """
    if created:
        Price.objects.create(
            product=instance,
            value=0,
            currency='RUB',
            price_type='retail',
            is_active=True
        )