[Репозиторий](https://github.com/Kexogg/webapi-parser) 

# Архитектура приложения

## Основные компоненты приложения

- `database.py`: настройка подключения к базе данных.
- `models.py`: определения моделей данных для категорий и продуктов.
- `parser.py`: функции для парсинга категорий и продуктов с внешнего сайта и сохранения их в базу данных.
- `main.py`: точки входа в приложение, определение маршрутов API и запуск сервера.
- `websocket_manager.py`: менеджер WebSocket соединений для real-time обновлений.

## Эндпоинты API

### Запуск парсинга данных

- **Метод**: `POST`
- **URL**: `/parse`
- **Описание**: Запускает фоновую задачу по парсингу данных с внешнего сайта и сохранению их в базе данных.

## Работа с продуктами

### Получить список продуктов

- **Метод**: `GET`
- **URL**: `/products`
- **Параметры запроса (опциональные)**:
  - `skip` (`int`): количество записей для пропуска (используется для пагинации).
  - `limit` (`int`): максимальное количество записей для возврата.
- **Описание**: Возвращает список продуктов из базы данных.

### Получить продукт по идентификатору

- **Метод**: `GET`
- **URL**: `/products/{product_id}`
- **Описание**: Возвращает информацию о конкретном продукте по его `product_id`.

### Создать новый продукт

- **Метод**: `POST`
- **URL**: `/products`
- **Query параметры**:
  - `name` (`str`): название продукта
  - `price` (`float`): цена продукта
  - `code` (`str`): код продукта
  - `category_id` (`str`): ID категории продукта
- **Описание**: Создает новый продукт в базе данных.

### Обновить продукт

- **Метод**: `PUT`
- **URL**: `/products/{product_id}`
- **Query параметры**:
  - `name` (`str`): новое название продукта
  - `price` (`float`): новая цена продукта
- **Описание**: Обновляет данные продукта с указанным `product_id`.

### Удалить продукт

- **Метод**: `DELETE`
- **URL**: `/products/{product_id}`
- **Описание**: Удаляет продукт из базы данных по его `product_id`.

## Работа с категориями

### Получить список категорий

- **Метод**: `GET`
- **URL**: `/categories`
- **Описание**: Возвращает список всех категорий из базы данных.

### Получить категорию по идентификатору

- **Метод**: `GET`
- **URL**: `/categories/{category_id}`
- **Описание**: Возвращает информацию о конкретной категории по её `category_id`.

### Создать новую категорию

- **Метод**: `POST`
- **URL**: `/categories`
- **Query параметры**:
  - `name` (`str`): название категории
  - `id` (`str`): идентификатор категории
  - `parent_id` (`str`, опционально): ID родительской категории
- **Описание**: Создает новую категорию в базе данных.

### Обновить категорию

- **Метод**: `PUT`
- **URL**: `/categories/{category_id}`
- **Query параметры**:
  - `name` (`str`): новое название категории
- **Описание**: Обновляет данные категории с указанным `category_id`.

### Удалить категорию

- **Метод**: `DELETE`
- **URL**: `/categories/{category_id}`
- **Описание**: Удаляет категорию из базы данных по её `category_id`.

### WebSocket соединение

- **URL**: `/ws`
- **Описание**: Устанавливает WebSocket соединение для получения real-time обновлений.
- **События**:
  - `parsing_started`: начало процесса парсинга
  - `categories_received`: получены новые категории
  - `parsing_finished`: завершение процесса парсинга
  - `product_updated`: обновление продукта
  - `product_deleted`: удаление продукта
  - `category_updated`: обновление категории
  - `category_deleted`: удаление категории

## Описание работы приложения

### Парсинг данных

- При вызове эндпоинта `/parse` запускается фоновая задача, которая парсит категории и продукты
- Парсер получает список категорий, сохраняет их в базу данных, а затем рекурсивно обрабатывает подкатегории.
- Для каждой категории собираются данные продуктов, которые также сохраняются в базу данных.

### Структура данных

- **Модель `Category`**:
  - Хранит информацию о категориях, включая идентификатор, название и родительскую категорию.
- **Модель `Product`**:
  - Хранит информацию о продуктах, включая код, название, цену и ссылку на категорию, к которой они принадлежат.

### Работа с базой данных

- Используется SQLite в качестве базы данных.
- Все операции с базой данных осуществляются через сессии SQLAlchemy.
- При запуске приложения создаются необходимые таблицы в базе данных, если они не существуют.

### Real-time обновления

- Приложение использует WebSocket для отправки уведомлений клиентам в реальном времени
- При изменении данных (обновление/удаление продуктов или категорий) все подключенные клиенты получают уведомления
- Во время парсинга клиенты получают уведомления о статусе процесса

### Запуск приложения

- Запускается с помощью `uvicorn` командой `python main.py`.
- Сервер будет доступен по адресу `http://127.0.0.1:8000/`.

### Использование API

- После запуска приложения и выполнения парсинга данных можно обращаться к эндпоинтам для работы с продуктами и категориями.