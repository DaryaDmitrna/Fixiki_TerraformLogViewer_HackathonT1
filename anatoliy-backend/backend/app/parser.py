import re, json
from datetime import datetime
from dateutil import parser as dtp

LEVELS = ["DEBUG","INFO","WARN","ERROR","TRACE"]
TS_PATTERNS = [
    r"(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)",
    r"(?P<ts>\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}:\d{2})",
    r"(?P<ts>\d{2}:\d{2}:\d{2})",
    r"(?P<ts>\d{4}-\d{2}-\d{2})",
]

def _guess_ts(obj):
    for k in ("@timestamp","timestamp","time","ts","_ts"):
        if k in obj:
            try:
                return dtp.parse(str(obj[k]))
            except:
                pass
    for v in obj.values():
        if isinstance(v,str):
            for p in TS_PATTERNS:
                m = re.search(p, v)
                if m:
                    try:
                        return dtp.parse(m.group("ts"))
                    except:
                        pass
    return None

def _guess_level(obj):
    for k in ("level","lvl","severity","log.level"):
        if k in obj:
            lv = str(obj[k]).upper()
            for L in LEVELS:
                if L in lv:
                    return L
    for k in ("msg","message","log","@message"):
        if k in obj and isinstance(obj[k], str):
            for L in LEVELS:
                import re as _re
                if _re.search(fr"\b{L}\b", obj[k], _re.I):
                    return L
    return None

def _section(obj):
    text = (obj.get("message") or obj.get("msg") or "") + " " + json.dumps(obj, ensure_ascii=False)
    import re as _re
    if _re.search(r"terraform\s+plan", text, _re.I):
        return "plan"
    if _re.search(r"terraform\s+apply", text, _re.I):
        return "apply"
    if ("tf_http_req_body" in obj) or ("tf_http_res_body" in obj) or _re.search(r"http/1|http/2|https://|http://", text, _re.I):
        return "http"
    return "other"

def parse_record(obj: dict) -> dict:
    ts = _guess_ts(obj)
    level = _guess_level(obj) or "INFO"
    section = _section(obj)
    tf_req_id = obj.get("tf_req_id") or obj.get("request_id") or obj.get("reqId") or obj.get("x-request-id")
    parent_req_id = obj.get("parent_req_id") or None
    tf_resource_type = obj.get("tf_resource_type") or obj.get("resource") or None
    message = obj.get("message") or obj.get("msg") or None

    has_req_body = bool(obj.get("tf_http_req_body"))
    has_res_body = bool(obj.get("tf_http_res_body"))

    return {
        "ts": ts.isoformat() if ts else None,
        "level": level,
        "section": section,
        "tf_req_id": tf_req_id,
        "parent_req_id": parent_req_id,
        "tf_resource_type": tf_resource_type,
        "is_read": False,
        "has_req_body": has_req_body,
        "has_res_body": has_res_body,
        "message": message,
    }
