# 📁 Расшифровка структуры проекта RegionShop

Этот документ описывает назначение каждого файла и папки в проекте.

## 📦 Корневая директория

| Файл/Папка | Назначение |
|------------|------------|
| `README.md` | Основная документация проекта с описанием функционала, инструкциями по запуску и API |
| `docker-compose.yml` | Основной файл Docker Compose для локальной разработки |
| `docker-compose.prod.yml` | Дополнительные настройки для production окружения |
| `docker-compose.override.yml` | Переопределения для локальной разработки (volumes, порты и т.д.) |
| `.env.example` | Шаблон файла с переменными окружения (нужно скопировать в `.env` и заполнить) |
| `.gitignore` | Файл для игнорирования ненужных файлов в Git (python, node, docker) |
| `.editorconfig` | Конфигурация стилей кода для разных редакторов |
| `.prettierrc` | Настройки форматирования кода для Prettier |
| `PROJECT_STRUCTURE.md` | Этот файл - расшифровка структуры проекта |

### 🛠️ `.kiro/` - Kiro IDE настройки
| Файл/Папка | Назначение |
|------------|------------|
| `hooks/` | Папка для Kiro hooks (автоматизация на события IDE) |
| `steering/` | Папка для steering файлов Kiro (правила и инструкции) |
| `steering/project-rules.md` | Правила и стандарты проекта для Kiro |

### 🌐 `nginx/` - Веб-сервер Nginx
| Файл/Папка | Назначение |
|------------|------------|
| `nginx.conf` | Основной конфигурационный файл Nginx |
| `ssl/` | Папка для SSL сертификатов |

## 🐍 Backend (Django)

### 📁 `backend/` - Основная папка Django
| Файл/Папка | Назначение |
|------------|------------|
| `Dockerfile` | Конфигурация Docker образа для backend |
| `requirements.txt` | Зависимости Python проекта |
| `manage.py` | Основная утилита Django для управления проектом |

### ⚙️ `backend/config/` - Настройки Django
| Файл | Назначение |
|------|------------|
| `__init__.py` | Инициализация Python пакета |
| `settings.py` | Основные настройки Django проекта |
| `urls.py` | Маршруты (URL patterns) всего проекта |
| `wsgi.py` | WSGI конфигурация для production |
| `asgi.py` | ASGI конфигурация для async |

### 👤 `backend/accounts/` - Приложение пользователей
| Файл | Назначение |
|------|------------|
| `__init__.py` | Инициализация приложения |
| `admin.py` | Регистрация моделей в Django Admin |
| `apps.py` | Конфигурация приложения |
| `models.py` | Модели данных (User, ClientProfile) |
| `serializers.py` | Сериализаторы Django REST Framework |
| `urls.py` | Маршруты API для аутентификации и профилей |
| `views.py` | Views (контроллеры) для аутентификации |
| `permissions.py` | Кастомные permissions для ролей |

### 🛍️ `backend/catalog/` - Приложение каталога товаров
| Файл | Назначение |
|------|------------|
| `__init__.py` | Инициализация приложения |
| `admin.py` | Админка для товаров и категорий |
| `apps.py` | Конфигурация приложения |
| `models.py` | Модели товаров, категорий, цен |
| `serializers.py` | Сериализаторы для API каталога |
| `urls.py` | Маршруты API для каталога |
| `views.py` | Views для работы с товарами |
| `tasks.py` | Фоновые задачи (синхронизация с 1С через Celery) |
| `sync.py` | Логика синхронизации данных с 1С |

### 📦 `backend/orders/` - Приложение заказов
| Файл | Назначение |
|------|------------|
| `__init__.py` | Инициализация приложения |
| `admin.py` | Админка для заказов и корзины |
| `apps.py` | Конфигурация приложения |
| `models.py` | Модели заказов, корзины, позиций заказа |
| `serializers.py` | Сериализаторы для API заказов |
| `urls.py` | Маршруты API для заказов |
| `views.py` | Views для работы с заказами и корзиной |
| `cart.py` | Логика работы с корзиной покупок |
| `signals.py` | Django signals (обработчики событий) |

## ⚛️ Frontend (React)

### 📁 `frontend/` - Основная папка React
| Файл/Папка | Назначение |
|------------|------------|
| `Dockerfile` | Конфигурация Docker образа для frontend |
| `package.json` | Зависимости Node.js и скрипты |
| `vite.config.js` | Конфигурация сборщика Vite |

### 🌐 `frontend/public/` - Публичные файлы
| Файл | Назначение |
|------|------------|
| `index.html` | Основной HTML файл приложения |
| `favicon.ico` | Иконка сайта |
| `robots.txt` | Инструкции для поисковых роботов |

### 📝 `frontend/src/` - Исходный код React
| Файл | Назначение |
|------|------------|
| `main.jsx` | Точка входа React приложения |
| `App.jsx` | Корневой компонент приложения |
| `index.css` | Глобальные стили |
| `App.css` | Стили для App компонента |

### 📄 `frontend/src/pages/` - Страницы приложения
| Файл | Назначение |
|------|------------|
| `CatalogPage.jsx` | Страница каталога товаров |
| `CartPage.jsx` | Страница корзины покупок |
| `LoginPage.jsx` | Страница входа в систему |
| `RegisterPage.jsx` | Страница регистрации |
| `OrderPage.jsx` | Страница оформления заказа |
| `ProfilePage.jsx` | Страница личного кабинета |
| `OrdersPage.jsx` | Страница истории заказов |

### 🧩 `frontend/src/components/` - React компоненты
| Файл | Назначение |
|------|------------|
| `ProductCard.jsx` | Карточка товара для каталога |
| `CartItem.jsx` | Элемент корзины покупок |
| `PrivateRoute.jsx` | Защищённый маршрут (требует авторизации) |
| `Navbar.jsx` | Навигационная панель |
| `Footer.jsx` | Подвал сайта |
| `LoadingSpinner.jsx` | Компонент загрузки |

### 🗃️ `frontend/src/store/` - Zustand сторы (состояние)
| Файл | Назначение |
|------|------------|
| `authStore.js` | Хранилище для данных аутентификации |
| `cartStore.js` | Хранилище для данных корзины |
| `productStore.js` | Хранилище для данных товаров |

### 🔌 `frontend/src/api/` - API клиенты
| Файл | Назначение |
|------|------------|
| `axiosClient.js` | Настроенный экземпляр Axios с интерсепторами |
| `authApi.js` | Методы для работы с API аутентификации |
| `productApi.js` | Методы для работы с API товаров |
| `orderApi.js` | Методы для работы с API заказов |

## 🐳 Docker файлы

| Файл | Назначение |
|------|------------|
| `docker-compose.yml` | Основная конфигурация сервисов (PostgreSQL, Redis, Backend, Frontend, Nginx) |
| `docker-compose.prod.yml` | Production настройки (без volumes для разработки, другие порты) |
| `docker-compose.override.yml` | Локальные переопределения (volumes для hot-reload) |
| `backend/Dockerfile` | Сборка Python/Django приложения |
| `frontend/Dockerfile` | Сборка React приложения |

## 🔧 Конфигурационные файлы

| Файл | Назначение |
|------|------------|
| `.env.example` → `.env` | Переменные окружения (секреты, URL БД, ключи 1С) |
| `.gitignore` | Игнорируемые файлы в Git |
| `.editorconfig` | Настройки форматирования для редакторов |
| `.prettierrc` | Конфигурация Prettier для форматирования кода |
| `nginx/nginx.conf` | Конфигурация веб-сервера Nginx |

## 📊 Типы файлов и их назначение

### Python/Django файлы:
- `*.py` - Python модули и пакеты
- `models.py` - Определение моделей данных (аналог таблиц БД)
- `views.py` - Контроллеры (обработка запросов)
- `serializers.py` - Преобразование данных для API
- `urls.py` - Маршрутизация URL → views
- `admin.py` - Настройки Django Admin
- `apps.py` - Конфигурация Django приложения

### React файлы:
- `*.jsx` - React компоненты с JSX синтаксисом
- `*.js` - JavaScript модули (хранилища, API клиенты)
- `*.css` - Стили CSS
- `package.json` - Метаданные и зависимости Node.js

### Конфигурационные файлы:
- `*.yml` / `*.yaml` - Docker Compose конфигурация
- `Dockerfile` - Инструкции сборки Docker образа
- `*.conf` - Конфигурация сервисов (Nginx)
- `*.rc` / `*config.*` - Конфигурация инструментов

### Документация:
- `*.md` - Документация в формате Markdown
- `README.md` - Основная документация
- `PROJECT_STRUCTURE.md` - Расшифровка структуры (этот файл)

## 🗺️ Структура данных

```
RegionShop/
├── .kiro/                    # Kiro IDE настройки
├── backend/                  # Django backend
│   ├── config/              # Настройки Django
│   ├── accounts/           # Пользователи и аутентификация
│   ├── catalog/            # Товары и интеграция с 1С
│   ├── orders/             # Заказы и корзина
│   ├── Dockerfile
│   ├── manage.py
│   └── requirements.txt
├── frontend/                # React frontend
│   ├── src/
│   │   ├── pages/          # Страницы приложения
│   │   ├── components/     # Компоненты UI
│   │   ├── store/          # Zustand хранилища
│   │   ├── api/           # API клиенты
│   │   ├── main.jsx
│   │   └── App.jsx
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── nginx/                   # Веб-сервер
├── docker-compose.yml      # Docker Compose
└── README.md              # Документация
```

## 📝 Примечания

1. **Пустые файлы** созданы как заготовки - их нужно заполнить кодом
2. **`.env` файл** нужно создать из `.env.example` и заполнить своими значениями
3. **Папка `migrations/`** будет создана автоматически при выполнении `python manage.py makemigrations`
4. **Папка `node_modules/`** будет создана при выполнении `npm install`
5. **Docker volumes** указаны в docker-compose для hot-reload разработки

Эта структура соответствует best practices для Django + React проектов и готова к разработке.