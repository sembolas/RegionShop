from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import uuid


class User(AbstractUser):
    """
    Кастомная модель пользователя с расширенными полями и ролями.
    Заменяет стандартную модель Django User.
    """
    
    class Role(models.TextChoices):
        CLIENT = 'client', _('Клиент')
        MANAGER = 'manager', _('Менеджер')
        ADMIN = 'admin', _('Администратор')
    
    # Основные поля
    role = models.CharField(
        _('Роль'),
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT,
        help_text=_('Роль пользователя в системе')
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Номер телефона должен быть в формате: '+79991234567'. Допускается до 15 цифр.")
    )
    
    phone = models.CharField(
        _('Телефон'),
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text=_('Контактный телефон пользователя')
    )
    
    email = models.EmailField(
        _('Email адрес'),
        unique=True,
        help_text=_('Уникальный email адрес пользователя')
    )
    
    is_verified = models.BooleanField(
        _('Подтвержден'),
        default=False,
        help_text=_('Пользователь подтвердил email/телефон')
    )
    
    # Методы для проверки ролей
    @property
    def is_client(self):
        return self.role == self.Role.CLIENT
    
    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def save(self, *args, **kwargs):
        # При создании администратора устанавливаем соответствующие флаги
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        elif self.role == self.Role.MANAGER:
            self.is_staff = True
            self.is_superuser = False
        else:  # CLIENT
            self.is_staff = False
            self.is_superuser = False
        
        # Email должен быть уникальным
        if not self.username:
            self.username = self.email
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['date_joined']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_role_display()})"


class ClientProfile(models.Model):
    """
    Расширенный профиль для клиентов компании.
    Содержит бизнес-информацию для интеграции с 1С.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile',
        verbose_name=_('Пользователь'),
        help_text=_('Связанный пользователь системы')
    )
    
    # Бизнес-информация
    company_name = models.CharField(
        _('Название компании'),
        max_length=255,
        blank=True,
        help_text=_('Официальное название компании клиента')
    )
    
    inn_regex = RegexValidator(
        regex=r'^\d{10}$|^\d{12}$',
        message=_("ИНН должен содержать 10 или 12 цифр")
    )
    
    inn = models.CharField(
        _('ИНН'),
        validators=[inn_regex],
        max_length=12,
        blank=True,
        help_text=_('Идентификационный номер налогоплательщика')
    )
    
    kpp = models.CharField(
        _('КПП'),
        max_length=9,
        blank=True,
        help_text=_('Код причины постановки на учет')
    )
    
    legal_address = models.TextField(
        _('Юридический адрес'),
        blank=True,
        help_text=_('Юридический адрес компании')
    )
    
    actual_address = models.TextField(
        _('Фактический адрес'),
        blank=True,
        help_text=_('Фактический адрес доставки')
    )
    
    contact_person = models.CharField(
        _('Контактное лицо'),
        max_length=255,
        blank=True,
        help_text=_('ФИО контактного лица для связи')
    )
    
    # Интеграция с 1С
    onec_ref_key = models.UUIDField(
        _('Ключ ссылки в 1С'),
        null=True,
        blank=True,
        help_text=_('Уникальный идентификатор контрагента в системе 1С (GUID)')
    )
    
    onec_synced_at = models.DateTimeField(
        _('Время синхронизации с 1С'),
        null=True,
        blank=True,
        help_text=_('Когда последний раз синхронизировались данные с 1С')
    )
    
    onec_sync_status = models.CharField(
        _('Статус синхронизации с 1С'),
        max_length=20,
        choices=[
            ('pending', _('Ожидает синхронизации')),
            ('synced', _('Синхронизировано')),
            ('failed', _('Ошибка синхронизации')),
            ('not_linked', _('Не привязан к 1С')),
        ],
        default='not_linked',
        help_text=_('Текущий статус привязки к системе 1С')
    )
    
    # Дополнительные поля
    notes = models.TextField(
        _('Заметки'),
        blank=True,
        help_text=_('Дополнительные заметки по клиенту')
    )
    
    is_active_client = models.BooleanField(
        _('Активный клиент'),
        default=True,
        help_text=_('Клиент активен и может делать заказы')
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
        verbose_name = _('Профиль клиента')
        verbose_name_plural = _('Профили клиентов')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['inn']),
            models.Index(fields=['onec_ref_key']),
            models.Index(fields=['onec_sync_status']),
            models.Index(fields=['is_active_client']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Профиль: {self.user.email} ({self.company_name or 'без названия'})"
    
    def save(self, *args, **kwargs):
        # Автоматически создаем профиль при создании клиента
        if not self.pk and self.user.is_client:
            super().save(*args, **kwargs)
        elif self.user.is_client:
            super().save(*args, **kwargs)
    
    @property
    def is_linked_to_1c(self):
        """Проверка привязки к 1С"""
        return bool(self.onec_ref_key) and self.onec_sync_status == 'synced'
    
    @property
    def display_name(self):
        """Отображаемое имя компании"""
        return self.company_name or f"Клиент #{self.user.id}"


class ManagerProfile(models.Model):
    """
    Профиль менеджера для дополнительной информации.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='manager_profile',
        verbose_name=_('Менеджер'),
        help_text=_('Связанный пользователь-менеджер')
    )
    
    department = models.CharField(
        _('Отдел'),
        max_length=100,
        blank=True,
        help_text=_('Отдел, в котором работает менеджер')
    )
    
    position = models.CharField(
        _('Должность'),
        max_length=100,
        blank=True,
        help_text=_('Должность менеджера')
    )
    
    work_phone = models.CharField(
        _('Рабочий телефон'),
        max_length=17,
        blank=True,
        help_text=_('Рабочий телефон менеджера')
    )
    
    internal_extension = models.CharField(
        _('Внутренний номер'),
        max_length=10,
        blank=True,
        help_text=_('Внутренний телефонный номер')
    )
    
    can_manage_orders = models.BooleanField(
        _('Может управлять заказами'),
        default=True,
        help_text=_('Разрешение на управление заказами')
    )
    
    can_manage_catalog = models.BooleanField(
        _('Может управлять каталогом'),
        default=True,
        help_text=_('Разрешение на управление каталогом товаров')
    )
    
    can_manage_clients = models.BooleanField(
        _('Может управлять клиентами'),
        default=True,
        help_text=_('Разрешение на управление клиентами')
    )
    
    notes = models.TextField(
        _('Заметки'),
        blank=True,
        help_text=_('Дополнительные заметки по менеджеру')
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
        verbose_name = _('Профиль менеджера')
        verbose_name_plural = _('Профили менеджеров')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Менеджер: {self.user.get_full_name() or self.user.email}"
    
    @property
    def permissions_list(self):
        """Список разрешений менеджера"""
        permissions = []
        if self.can_manage_orders:
            permissions.append('Управление заказами')
        if self.can_manage_catalog:
            permissions.append('Управление каталогом')
        if self.can_manage_clients:
            permissions.append('Управление клиентами')
        return permissions


# Сигналы для автоматического создания профилей
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Автоматически создаем соответствующий профиль при создании пользователя.
    """
    if created:
        if instance.is_client:
            ClientProfile.objects.create(user=instance)
        elif instance.is_manager:
            ManagerProfile.objects.create(user=instance)


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