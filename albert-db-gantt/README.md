
# Terraform LogViewer — DB & Gantt API (Альберт)

Схема PostgreSQL и узкий API для данных диаграммы Ганта.

## Состав
- `db/init.sql` — таблица `log_record`, индексы, FTS-триггер.
- `backend_gantt/` — FastAPI сервис с единой ручкой `/gantt/segments`.

## Docker Compose
```yaml
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: logviewer
      POSTGRES_PASSWORD: logviewer
      POSTGRES_DB: logviewer
    volumes:
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports: ["5432:5432"]

  gantt:
    build: ./backend_gantt
    environment:
      DATABASE_URL: postgresql+psycopg://logviewer:logviewer@db:5432/logviewer
    depends_on: [db]
    ports: ["8001:8001"]
```
Запуск:
```bash
docker compose up --build
```
API: http://localhost:8001/gantt/segments
