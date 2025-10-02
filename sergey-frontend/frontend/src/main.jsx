import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import dayjs from 'dayjs'

const API = (path) => `http://localhost:8000${path}`

function Row({item, onToggleSelect, onLoadJson}) {
  const color = {
    ERROR:'#ff6b6b', WARN:'#ffd166', INFO:'#a8dadc', DEBUG:'#caffbf', TRACE:'#e0fbfc'
  }[item.level] || '#e0e0e0'
  return (
    <div style={{border:'1px solid #ddd', margin:'6px 0', padding:'8px', background: color}}>
      <div style={{display:'flex', gap:12, alignItems:'center'}}>
        <input type="checkbox" onChange={(e)=>onToggleSelect(item.id, e.target.checked)} />
        <b>{item.level}</b>
        <span>{item.section}</span>
        <span>{item.tf_req_id}</span>
        <span>{item.tf_resource_type||''}</span>
        <span>{item.ts ? dayjs(item.ts).format('YYYY-MM-DD HH:mm:ss') : ''}</span>
        <span style={{opacity:.8}}>{item.message||''}</span>
        {item.has_req_body && <button onClick={()=>onLoadJson(item.id,'req')}>req JSON</button>}
        {item.has_res_body && <button onClick={()=>onLoadJson(item.id,'res')}>res JSON</button>}
        <button onClick={()=>onLoadJson(item.id,'raw')}>raw</button>
      </div>
    </div>
  )
}

function App(){
  const [items,setItems]=useState([])
  const [filters,setFilters]=useState({level:'',rtype:'',from:'',to:'',q:'',req:''})
  const [selected,setSelected]=useState([])
  const [jsonView,setJsonView]=useState(null)

  const search = async ()=>{
    const body = {
      level: filters.level? [filters.level]: null,
      tf_resource_type: filters.rtype || null,
      ts_from: filters.from || null,
      ts_to: filters.to || null,
      tf_req_id: filters.req || null,
      q: filters.q || null,
      limit: 500, offset: 0
    }
    const r = await fetch(API('/search'), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)})
    const data = await r.json()
    setItems(data.items||[])
  }

  useEffect(()=>{search()},[])

  const onToggleSelect = (id,checked)=>{
    setSelected(s=> checked? [...s,id]: s.filter(x=>x!==id))
  }

  const markRead = async ()=>{
    await fetch(API('/mark-read'), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(selected)})
    await search()
    setSelected([])
  }

  const onLoadJson = async (id,kind)=>{
    const r = await fetch(API(`/record/${id}/json/${kind}`))
    const data = await r.json()
    setJsonView(JSON.stringify(data,null,2))
  }

  const importLogs = async (file)=>{
    const txt = await file.text()
    const r = await fetch(API('/import'), {method:'POST', body: txt, headers:{'Content-Type':'application/x-ndjson'}})
    await r.json()
    await search()
  }

  return (
    <div style={{padding:16, fontFamily:'system-ui, sans-serif'}}>
      <h2>Terraform LogViewer</h2>
      <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
        <select value={filters.level} onChange={e=>setFilters({...filters, level:e.target.value})}>
          <option value="">level</option>
          <option>ERROR</option><option>WARN</option><option>INFO</option><option>DEBUG</option><option>TRACE</option>
        </select>
        <input placeholder="tf_resource_type" value={filters.rtype} onChange={e=>setFilters({...filters, rtype:e.target.value})}/>
        <input placeholder="from (ISO)" value={filters.from} onChange={e=>setFilters({...filters, from:e.target.value})}/>
        <input placeholder="to (ISO)" value={filters.to} onChange={e=>setFilters({...filters, to:e.target.value})}/>
        <input placeholder="tf_req_id" value={filters.req} onChange={e=>setFilters({...filters, req:e.target.value})}/>
        <input placeholder="full-text" value={filters.q} onChange={e=>setFilters({...filters, q:e.target.value})}/>
        <button onClick={search}>Search</button>
        <button onClick={markRead} disabled={!selected.length}>Mark as read ({selected.length})</button>
        <label style={{marginLeft:12}}>
          <input type="file" accept=".json,.ndjson,.log" onChange={e=>e.target.files[0] && importLogs(e.target.files[0])} style={{display:'none'}}/>
          <span style={{border:'1px solid #999', padding:'4px 8px', cursor:'pointer'}}>Import Logs</span>
        </label>
      </div>

      <div style={{marginTop:12}}>
        {items.map(it=> <Row key={it.id} item={it} onToggleSelect={onToggleSelect} onLoadJson={onLoadJson}/>)}
      </div>

      <div style={{marginTop:12}}>
        <h3>JSON viewer</h3>
        <pre style={{whiteSpace:'pre-wrap', background:'#111', color:'#ddd', padding:12, minHeight:120}}>{jsonView||'—'}</pre>
      </div>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App/>)
