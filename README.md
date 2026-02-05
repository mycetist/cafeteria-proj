# Система управления школьной столовой

Веб-приложение для управления школьной столовой с тремя ролями: ученик, повар и администратор.

## Технологический стек

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.11+ / Flask |
| База данных | SQLite (разработка) / MySQL (продакшн) |
| ORM | SQLAlchemy + Flask-SQLAlchemy |
| Аутентификация | JWT (Flask-JWT-Extended) |
| Frontend | Bootstrap 5 + HTML/CSS/JS |
| Контейнеризация | Docker + Docker Compose |

## Функциональность

### Ученик
- Просмотр меню на текущий день
- Покупка разовых обедов
- Оформление абонементов (недельный/месячный)
- Подтверждение получения обеда
- Управление аллергиями
- Оставление отзывов о блюдах

### Повар
- Просмотр меню на сегодня
- Отслеживание выдачи обедов
- Управление инвентарём
- Создание заявок на закупку ингредиентов

### Администратор
- Просмотр статистики посещаемости
- Финансовая отчётность
- Управление пользователями
- Создание и редактирование меню
- Управление блюдами и ингредиентами
- Утверждение заявок на закупку
- Генерация отчётов (посещаемость, финансы)

## Быстрый старт

### Локальная разработка

```bash
# 1. Клонирование репозитория
git clone <repository-url>
cd cafeteria-proj

# 2. Установка зависимостей
pip3 install -r requirements.txt

# 3. Настройка окружения
cp .env.example .env

# 4. Инициализация базы данных
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# 5. Заполнение тестовыми данными
python3 seed_data.py

# 6. Запуск приложения
python3 run.py

# 7. Открыть в браузере
# http://localhost:5002
```

### Docker (опционально)

```bash
# Запуск с Docker Compose
docker-compose up -d

# Остановка
docker-compose down
```

## Данные для входа

| Роль | Email | Пароль |
|------|-------|--------|
| Администратор | admin@cafeteria.com | admin123 |
| Повар | cook@cafeteria.com | cook123 |
| Студент | student@school.com | student123 |

## API Endpoints

### Аутентификация
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход
- `POST /api/auth/logout` - Выход
- `POST /api/auth/refresh` - Обновление токена
- `GET /api/auth/me` - Информация о текущем пользователе

### Студент
- `GET /api/menu` - Меню на сегодня
- `GET /api/menu/<date>` - Меню на конкретную дату
- `POST /api/payment` - Создание платежа
- `GET /api/subscription` - Активный абонемент
- `POST /api/subscription` - Покупка абонемента
- `POST /api/meal/confirm` - Подтверждение получения обеда
- `GET /api/allergies` - Список аллергий
- `POST /api/allergies` - Добавление аллергии
- `DELETE /api/allergies/<id>` - Удаление аллергии
- `GET /api/reviews` - Отзывы пользователя
- `POST /api/reviews` - Создание отзыва
- `GET /api/notifications` - Уведомления

### Повар
- `GET /api/cook/meals/today` - Обеды на сегодня
- `POST /api/cook/meals/serve` - Выдача обеда
- `GET /api/cook/meals/search-student` - Поиск студента
- `GET /api/cook/inventory` - Инвентарь
- `PUT /api/cook/inventory/<id>` - Обновление инвентаря
- `POST /api/cook/inventory/<id>/adjust` - Корректировка запасов
- `GET /api/cook/purchase-requests` - Заявки на закупку
- `POST /api/cook/purchase-requests` - Создание заявки
- `DELETE /api/cook/purchase-requests/<id>` - Удаление заявки

### Администратор
- `GET /api/admin/statistics/dashboard` - Статистика дашборда
- `GET /api/admin/statistics/payments` - Статистика платежей
- `GET /api/admin/statistics/attendance` - Статистика посещаемости
- `GET /api/admin/purchase-requests` - Все заявки на закупку
- `PUT /api/admin/purchase-requests/<id>` - Утверждение/отклонение заявки
- `GET /api/admin/reports/meals` - Отчёт по питанию
- `GET /api/admin/reports/expenses` - Финансовый отчёт
- `GET /api/admin/users` - Список пользователей
- `PUT /api/admin/users/<id>` - Обновление пользователя
- `DELETE /api/admin/users/<id>` - Удаление пользователя
- `POST /api/admin/menu` - Создание меню
- `DELETE /api/admin/menu/<id>` - Удаление меню
- `POST /api/admin/ingredients` - Создание ингредиента
- `GET /api/admin/ingredients` - Список ингредиентов
- `PUT /api/admin/ingredients/<id>` - Обновление ингредиента
- `DELETE /api/admin/ingredients/<id>` - Удаление ингредиента
- `GET /api/admin/dishes` - Список блюд
- `POST /api/admin/dishes` - Создание блюда
- `PUT /api/admin/dishes/<id>` - Обновление блюда
- `DELETE /api/admin/dishes/<id>` - Удаление блюда

## Структура проекта

```
cafeteria-proj/
├── app/                    # Flask приложение
│   ├── __init__.py        # Фабрика приложения
│   ├── extensions.py      # Расширения Flask
│   ├── routes.py          # HTML маршруты
│   ├── api/               # API endpoints
│   │   ├── auth.py
│   │   ├── student.py
│   │   ├── cook.py
│   │   ├── admin.py
│   │   └── common.py
│   ├── models/            # SQLAlchemy модели
│   │   ├── user.py
│   │   ├── dish.py
│   │   ├── menu.py
│   │   ├── payment.py
│   │   ├── inventory.py
│   │   ├── meal_record.py
│   │   ├── purchase_request.py
│   │   ├── review.py
│   │   └── notification.py
│   └── utils/             # Утилиты
│       └── decorators.py
├── templates/             # Jinja2 шаблоны
│   ├── base.html
│   ├── auth/
│   ├── student/
│   ├── cook/
│   └── admin/
├── static/                # CSS, JS, изображения
│   ├── css/
│   └── js/
├── config.py              # Конфигурация
├── run.py                 # Точка входа
├── seed_data.py           # Начальные данные
├── requirements.txt       # Зависимости
├── docker-compose.yml     # Docker Compose
├── Dockerfile             # Docker образ
└── .env.example           # Пример переменных окружения
```

## Разработка

### Запуск в режиме разработки

```bash
export FLASK_ENV=development
python3 run.py
```

### Тестирование

```bash
# Установка pytest
pip3 install pytest pytest-flask

# Запуск тестов
pytest
```

### Миграции базы данных

```bash
# Инициализация миграций
flask db init

# Создание миграции
flask db migrate -m "Description"

# Применение миграций
flask db upgrade
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| FLASK_ENV | Режим Flask | development |
| SECRET_KEY | Секретный ключ Flask | - |
| JWT_SECRET_KEY | Секретный ключ JWT | - |
| APP_PORT | Порт приложения | 5002 |
| DB_HOST | Хост базы данных | localhost |
| DB_PORT | Порт базы данных | 3306 |
| DB_NAME | Имя базы данных | cafeteria_db |
| DB_USER | Пользователь БД | - |
| DB_PASSWORD | Пароль БД | - |

## Лицензия

MIT License

## Авторы

- Команда разработки школы

---

**Примечание:** Для продакшн-развёртывания используйте MySQL и настройте SSL/HTTPS.
