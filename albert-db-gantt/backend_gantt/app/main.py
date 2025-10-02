
from fastapi import FastAPI
from sqlalchemy import create_engine, text
import os

from .gantt import build_gantt_segments

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://logviewer:logviewer@db:5432/logviewer")
engine = create_engine(DATABASE_URL, future=True)

app = FastAPI(title="LogViewer Gantt API", version="0.1.0")

@app.get("/gantt/segments")
def gantt_segments(tf_req_id: str | None = None):
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, ts, level, section, tf_req_id, parent_req_id, raw FROM log_record"))
        items = [dict(r._mapping) for r in rows]
    return {"segments": build_gantt_segments(items, tf_req_id=tf_req_id)}
