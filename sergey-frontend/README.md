
# Terraform LogViewer — Frontend (Сергей)

React + Vite UI: фильтры, полнотекстовый поиск, группировка по tf_req_id, lazy JSON.

## Настройка
По умолчанию UI стучится на `http://localhost:8000` (см. `const API = (path) => ...` в `src/main.jsx`).

## Запуск (Docker)
```bash
docker build -t logviewer-frontend ./frontend
docker run --rm -p 5173:5173 logviewer-frontend
```
UI: http://localhost:5173
