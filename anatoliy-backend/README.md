
# Terraform LogViewer — Backend (Анатолий)

FastAPI + SQLAlchemy сервис: импорт/парсинг, поиск/фильтрация, lazy JSON, экспорт, плагины (mock).

## Быстрый старт
Требуется БД PostgreSQL (см. переменную DATABASE_URL). Для локальной проверки можно использовать docker-compose ниже.

### Docker Compose (локально)
```yaml
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: logviewer
      POSTGRES_PASSWORD: logviewer
      POSTGRES_DB: logviewer
    ports: ["5432:5432"]
  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+psycopg://logviewer:logviewer@db:5432/logviewer
    depends_on: [db]
    ports: ["8000:8000"]
```
Запуск:
```bash
docker compose up --build
```
API: http://localhost:8000/docs
