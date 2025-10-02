
FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi==0.115.0 uvicorn[standard]==0.30.6 SQLAlchemy==2.0.36 psycopg[binary]==3.2.1 python-dateutil==2.9.0.post0
COPY app ./app
EXPOSE 8001
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8001"]
