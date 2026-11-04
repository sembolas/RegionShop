from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = _('Учетные записи')
    
    def ready(self):
        """
        Импортируем сигналы при инициализации приложения.
        """
        import accounts.signals