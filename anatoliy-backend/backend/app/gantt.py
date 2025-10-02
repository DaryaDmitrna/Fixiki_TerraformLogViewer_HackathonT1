from collections import defaultdict
from dateutil import parser as dtp

def build_gantt_segments(items, tf_req_id=None):
    by_req = defaultdict(list)
    for it in items:
        rid = it.get('tf_req_id') or 'unknown'
        if tf_req_id and rid != tf_req_id:
            continue
        ts = it.get('ts')
        if ts:
            try:
                it['_ts'] = dtp.parse(ts)
            except:
                continue
            by_req[rid].append(it)

    segments = []
    for rid, logs in by_req.items():
        logs.sort(key=lambda x: x['_ts'])
        start = logs[0]['_ts']
        end = logs[-1]['_ts']
        parent = logs[0].get('parent_req_id')
        seg = {
            'tf_req_id': rid,
            'start_ts': start.isoformat(),
            'end_ts': end.isoformat(),
            'duration_ms': int((end - start).total_seconds() * 1000),
            'parent_req_id': parent,
            'sections': list({l.get('section') for l in logs}),
            'levels': list({l.get('level') for l in logs}),
        }
        segments.append(seg)
    return sorted(segments, key=lambda s: s['start_ts'])
