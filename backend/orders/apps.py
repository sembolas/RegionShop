from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    verbose_name = _('Заказы')
    
    def ready(self):
        """
        Импортируем сигналы при инициализации приложения.
        """
        import orders.signals