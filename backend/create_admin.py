#!/usr/bin/env python
"""
Скрипт для создания суперпользователя.
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_simple')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Проверяем существующих пользователей
print("Существующие пользователи:")
users = User.objects.all()
if users:
    for user in users:
        print(f"- {user.username} ({user.email})")
        print(f"  is_staff: {user.is_staff}, is_superuser: {user.is_superuser}, role: {user.role}")
else:
    print("Нет пользователей")

print("\nСоздаю нового суперпользователя...")

# Удаляем старого пользователя если есть
User.objects.filter(email='admin@regionshop.ru').delete()

# Создаем нового
try:
    user = User.objects.create_user(
        email='admin@regionshop.ru',
        password='admin123',
        role='admin',
        is_staff=True,
        is_superuser=True
    )
    print(f"Успешно создан пользователь:")
    print(f"- Email: {user.email}")
    print(f"- Username: {user.username}")
    print(f"- Role: {user.role}")
    print(f"- is_staff: {user.is_staff}")
    print(f"- is_superuser: {user.is_superuser}")
    
    # Проверяем аутентификацию
    from django.contrib.auth import authenticate
    auth_user = authenticate(username=user.email, password='admin123')
    if auth_user:
        print(f"\nАутентификация успешна! Можно войти с:")
        print(f"- Email: {user.email}")
        print(f"- Пароль: admin123")
    else:
        print("\nОшибка аутентификации!")
        
except Exception as e:
    print(f"Ошибка при создании пользователя: {e}")
    import traceback
    traceback.print_exc()