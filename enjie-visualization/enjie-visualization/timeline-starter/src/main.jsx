import React, {useEffect,useState} from 'react'; import {createRoot} from 'react-dom/client'; import dayjs from 'dayjs';
const API = (p)=>`http://localhost:8001${p}`; // ожидается сервис Альберта
function App(){ const [seg,setSeg]=useState([]); useEffect(()=>{fetch(API('/gantt/segments')).then(r=>r.json()).then(d=>setSeg(d.segments||[]))},[]);
return (<div style={{padding:16,fontFamily:'system-ui'}}><h2>Timeline (Энже)</h2><div>{seg.map(s=>(<div key={s.tf_req_id} style={{margin:'8px 0',border:'1px solid #ddd',padding:8}}>
<b>{s.tf_req_id}</b> — {dayjs(s.start_ts).format('HH:mm:ss.SSS')} → {dayjs(s.end_ts).format('HH:mm:ss.SSS')} ({s.duration_ms} ms)
</div>))}</div></div>);} createRoot(document.getElementById('root')).render(<App/>);