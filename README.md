/pixelplayer
|
├── app/
│   ├── api/
│   │   └── routes.py         # Все эндпоинты API
│   ├── core/
│   │   ├── config.py         # Конфигурация из переменных окружения
│   │   └── security.py       # JWT, хеширование паролей
│   ├── crud/
│   │   └── actions.py        # Функции для работы с БД (Create, Read, Update, Delete)
│   ├── db/
│   │   ├── database.py       # Настройка сессии БД
│   │   └── models.py         # Модели SQLAlchemy
│   ├── schemas/
│   │   ├── file.py           # Схемы Pydantic для файлов
│   │   ├── token.py          # Схемы Pydantic для токенов
│   │   └── user.py           # Схемы Pydantic для пользователей
│   ├── services/
│   │   └── minio_client.py   # Клиент для работы с MinIO
│   ├── templates/
│   │   └── index.html        # Простой HTML-интерфейс
│   └── main.py               # Главный файл приложения
|
├── .env                      # Переменные окружения (СЕКРЕТЫ)
├── docker-compose.yml        # Файл для оркестрации контейнеров
├── Dockerfile                # Инструкции для сборки Docker-образа приложения
└── requirements.txt          # Зависимости Python
