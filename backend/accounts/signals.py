"""
Сигналы для автоматического создания профилей пользователей.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .models import User, ClientProfile, ManagerProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Автоматически создаем соответствующий профиль при создании пользователя.
    """
    if created:
        if instance.is_client:
            ClientProfile.objects.create(user=instance)
            instance.client_profile.save()
        elif instance.is_manager:
            ManagerProfile.objects.create(user=instance)
            instance.manager_profile.save()


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Автоматически сохраняем связанный профиль.
    """
    try:
        if instance.is_client:
            instance.client_profile.save()
        elif instance.is_manager:
            instance.manager_profile.save()
    except (ClientProfile.DoesNotExist, ManagerProfile.DoesNotExist):
        # Профиль еще не создан, будет создан при следующем сохранении
        pass


@receiver(post_save, sender=User)
def update_user_flags(sender, instance, **kwargs):
    """
    Обновляем флаги is_staff и is_superuser в зависимости от роли.
    """
    if instance.role == User.Role.ADMIN:
        User.objects.filter(pk=instance.pk).update(
            is_staff=True,
            is_superuser=True
        )
    elif instance.role == User.Role.MANAGER:
        User.objects.filter(pk=instance.pk).update(
            is_staff=True,
            is_superuser=False
        )
    else:  # CLIENT
        User.objects.filter(pk=instance.pk).update(
            is_staff=False,
            is_superuser=False
        )