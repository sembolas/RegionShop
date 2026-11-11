"""
Сигналы для приложения заказов.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.timezone import now

from .models import Order, OrderStatusHistory, Cart, CartItem


@receiver(post_save, sender=Order)
def create_status_history(sender, instance, created, **kwargs):
    """
    Создаем запись в истории статусов при создании заказа.
    """
    if created:
        OrderStatusHistory.objects.create(
            order=instance,
            new_status=instance.status,
            reason='Заказ создан'
        )
    elif 'status' in instance.changed_fields:
        OrderStatusHistory.objects.create(
            order=instance,
            old_status=instance.initial_status,
            new_status=instance.status,
            reason='Статус изменен'
        )


@receiver(pre_save, sender=Order)
def track_status_changes(sender, instance, **kwargs):
    """
    Отслеживаем изменения статуса заказа.
    """
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance.initial_status = old_instance.status
            instance.changed_fields = []
            
            for field in ['status', 'payment_status']:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    instance.changed_fields.append(field)
        except Order.DoesNotExist:
            instance.initial_status = None
            instance.changed_fields = []
    else:
        instance.initial_status = None
        instance.changed_fields = []


@receiver(post_save, sender=Order)
def update_stock_on_order_status_change(sender, instance, **kwargs):
    """
    Обновляем остатки товаров при изменении статуса заказа.
    """
    if 'status' in instance.changed_fields:
        from catalog.models import Stock
        
        if instance.status == Order.Status.CONFIRMED:
            # Резервируем товары при подтверждении заказа
            for item in instance.items.all():
                # Находим основной склад
                stock = Stock.objects.filter(
                    product=item.product,
                    is_active=True
                ).first()
                
                if stock:
                    stock.reserve(item.quantity)
        
        elif instance.status in [Order.Status.CANCELLED, Order.Status.RETURNED]:
            # Освобождаем резерв при отмене или возврате
            for item in instance.items.all():
                stock = Stock.objects.filter(
                    product=item.product,
                    is_active=True
                ).first()
                
                if stock:
                    stock.release(item.quantity)
        
        elif instance.status == Order.Status.SHIPPED:
            # Списываем товары при отгрузке
            for item in instance.items.all():
                stock = Stock.objects.filter(
                    product=item.product,
                    is_active=True
                ).first()
                
                if stock:
                    stock.commit_reservation(item.quantity)


@receiver(post_save, sender=CartItem)
def update_cart_timestamp(sender, instance, **kwargs):
    """
    Обновляем timestamp корзины при изменении позиций.
    """
    instance.cart.save()  # Это вызовет auto_now в updated_at


@receiver(post_save, sender=Cart)
def cleanup_old_carts(sender, instance, **kwargs):
    """
    Очищаем старые неактивные корзины.
    """
    from django.utils.timezone import now
    from datetime import timedelta
    
    # Удаляем неактивные корзины старше 30 дней
    if not instance.is_active:
        cutoff_date = now() - timedelta(days=30)
        Cart.objects.filter(
            is_active=False,
            updated_at__lt=cutoff_date
        ).delete()