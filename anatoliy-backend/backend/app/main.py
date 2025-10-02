from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os, json, orjson

from .parser import parse_record
from .gantt import build_gantt_segments
from .plugins.manager import run_plugins_export

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://logviewer:logviewer@localhost:5432/logviewer")
engine = create_engine(DATABASE_URL, future=True)
Session = sessionmaker(bind=engine, future=True)

app = FastAPI(title="Terraform LogViewer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchQuery(BaseModel):
    level: Optional[List[str]] = None
    tf_resource_type: Optional[str] = None
    ts_from: Optional[str] = None
    ts_to: Optional[str] = None
    tf_req_id: Optional[str] = None
    q: Optional[str] = None
    limit: int = 200
    offset: int = 0

def insert_record(conn, rec):
    sql = text("""
        INSERT INTO log_record (raw, ts, level, section, tf_req_id, parent_req_id,
                                tf_resource_type, is_read, has_req_body, has_res_body, message)
        VALUES (:raw::jsonb, :ts, :level, :section, :tf_req_id, :parent_req_id,
                :tf_resource_type, :is_read, :has_req_body, :has_res_body, :message)
        RETURNING id
    """)
    return conn.execute(sql, rec).scalar()

@app.post("/import")
async def import_logs(raw_body: bytes = Body(...)):
    """
    Принимает NDJSON или JSON массив.
    """
    inserted = 0
    lines = []
    body = raw_body.strip()
    try:
        if body.startswith(b"["):
            items = json.loads(body.decode("utf-8", errors="ignore"))
            lines = [orjson.dumps(i) for i in items]
        else:
            lines = [l for l in body.splitlines() if l.strip()]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    with engine.begin() as conn:
        for l in lines:
            try:
                obj = json.loads(l.decode("utf-8", errors="ignore"))
                rec = parse_record(obj)
                rec["raw"] = json.dumps(obj, ensure_ascii=False)
                insert_record(conn, rec)
                inserted += 1
            except Exception:
                continue

    return {"inserted": inserted}

@app.post("/search")
def search(q: SearchQuery):
    clauses = ["1=1"]
    params = {}
    if q.level:
        clauses.append("level = ANY(:levels)")
        params["levels"] = q.level
    if q.tf_resource_type:
        clauses.append("tf_resource_type = :rtype")
        params["rtype"] = q.tf_resource_type
    if q.ts_from:
        clauses.append("ts >= :ts_from")
        params["ts_from"] = q.ts_from
    if q.ts_to:
        clauses.append("ts <= :ts_to")
        params["ts_to"] = q.ts_to
    if q.tf_req_id:
        clauses.append("tf_req_id = :rid")
        params["rid"] = q.tf_req_id
    if q.q:
        clauses.append("fts @@ plainto_tsquery('simple', :q)")
        params["q"] = q.q

    sql = text(f"""
        SELECT id, ts, level, section, tf_req_id, parent_req_id, tf_resource_type, is_read,
               has_req_body, has_res_body, message
        FROM log_record
        WHERE {' AND '.join(clauses)}
        ORDER BY ts NULLS LAST
        LIMIT :limit OFFSET :offset
    """)
    params["limit"] = q.limit
    params["offset"] = q.offset
    with engine.begin() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return {"items": list(rows)}

@app.get("/record/{id}/json/{kind}")
def load_json(id: str, kind: str):
    if kind not in ("req", "res", "raw"):
        raise HTTPException(400, "kind must be req|res|raw")
    with engine.begin() as conn:
        row = conn.execute(text("SELECT raw FROM log_record WHERE id=:id"), {"id": id}).first()
    if not row:
        raise HTTPException(404, "not found")
    raw = row[0]
    try:
        obj = json.loads(raw)
    except:
        raise HTTPException(500, "bad raw json")
    if kind == "raw":
        return obj
    key = "tf_http_req_body" if kind == "req" else "tf_http_res_body"
    return obj.get(key, {})

@app.post("/mark-read")
def mark_read(ids: List[str] = Body(...)):
    with engine.begin() as conn:
        conn.execute(text("UPDATE log_record SET is_read=true WHERE id = ANY(:ids)"), {"ids": ids})
    return {"updated": len(ids)}

@app.get("/gantt/segments")
def gantt_segments(tf_req_id: Optional[str] = None):
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, ts, level, section, tf_req_id, parent_req_id, raw FROM log_record"))
        items = [dict(r._mapping) for r in rows]
    segments = build_gantt_segments(items, tf_req_id=tf_req_id)
    return {"segments": segments}

@app.get("/export")
def export(query: str = "", fmt: str = "ndjson"):
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT ts, level, section, tf_req_id, tf_resource_type, message, raw::text as raw
            FROM log_record
            ORDER BY ts NULLS LAST
        """))
        items = [dict(r._mapping) for r in rows]
    if fmt == "csv":
        import io, csv
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(items[0].keys()) if items else [])
        writer.writeheader()
        for it in items:
            writer.writerow(it)
        return buf.getvalue()
    return "\n".join(json.dumps(it, ensure_ascii=False) for it in items)

@app.get("/plugins/run")
def plugins_run():
    return run_plugins_export(engine)
