import React, { useEffect, useState, useRef } from 'react';
import ThreeCanvas from './ThreeCanvas';
import UnfoldedNetViewer from './UnfoldedNetViewer';
import { postJson } from '../../shared/api/client.js';

export default function GeometryVisual({ spec = {}, deckId, slideId, onSpecChange, sourceSlide }) {
  const request=useRef(0);
  const [cameraPreset,setCameraPreset]=useState('iso'),[labels,setLabels]=useState(true),[axes,setAxes]=useState(false),[net,setNet]=useState(false);
  const [kind,setKind]=useState(spec.polyhedron_type || '');
  const [edge,setEdge]=useState(spec.base_edge ?? '');
  const [height,setHeight]=useState(spec.height ?? '');
  const [scene,setScene]=useState(null), [error,setError]=useState(''), [busy,setBusy]=useState(false);
  useEffect(() => {
    const sequence=++request.current;
    const controller=new AbortController(); setScene(null); setError('');
    setKind(spec.polyhedron_type||'');setEdge(spec.base_edge??'');setHeight(spec.height??'');
    if(spec.requirement_token) {
      setBusy(true);
      postJson('/api/v1/visuals/scene',spec,{signal:controller.signal}).then(async response => {
        const data=await response.json(); if(!response.ok) throw new Error(data.detail?.message || 'Không dựng được hình');
        if(!controller.signal.aborted&&sequence===request.current) setScene(data);
      }).catch(e=>{if(!controller.signal.aborted)setError(e.message);}).finally(()=>{if(!controller.signal.aborted)setBusy(false);});
    }
    return ()=>controller.abort();
  },[JSON.stringify(spec)]);
  const confirm=async()=>{
    const sequence=++request.current;
    setBusy(true);setError('');
    try {
      const source={kind:'geometry',polyhedron_type:kind,base_edge:Number(edge),height:kind==='cube'?Number(edge):Number(height),deck_id:deckId,slide_id:slideId};
      const response=await postJson('/api/v1/visuals/confirm',{...source,source:sourceSlide}), data=await response.json();
      if(!response.ok)throw new Error(data.detail?.message || 'Dữ kiện không hợp lệ');
      if(sequence!==request.current)return;
      onSpecChange({...source,...data.requirement.spec,requirement_token:data.requirement_token});
    }catch(e){setError(e.message);}finally{setBusy(false);}
  };
  return <section className="p-3 border rounded-xl space-y-3 bg-white text-gray-900">
    <p className="text-sm">Chọn đúng giả thiết và nhập số đo từ đề bài. Hình chỉ dựng sau khi xác nhận.</p>
    <select aria-label="Giả thiết hình học" value={kind} onChange={e=>{setKind(e.target.value);setScene(null);request.current++;setBusy(false);}} className="border p-2 w-full">
      <option value="">Chọn loại hình</option><option value="cube">Hình lập phương</option><option value="square_pyramid_regular">Chóp đều đáy vuông</option><option value="square_pyramid_at_a">Chóp đáy vuông, SA vuông góc đáy</option>
    </select>
    <label>Cạnh đáy <input aria-label="Cạnh đáy" type="number" value={edge} onChange={e=>{setEdge(e.target.value);setScene(null);request.current++;setBusy(false);}} className="border w-24 p-1" /></label>
    {kind!=='cube'&&<label> Chiều cao <input aria-label="Chiều cao" type="number" value={height} onChange={e=>{setHeight(e.target.value);setScene(null);request.current++;setBusy(false);}} className="border w-24 p-1" /></label>}
    <button disabled={busy||!kind||!edge||(kind!=='cube'&&!height)} onClick={confirm} className="block border rounded p-2 disabled:opacity-40">Xác nhận dữ kiện và dựng hình</button>
    {busy&&<p role="status">Đang dựng hình…</p>}{error&&<p role="alert" className="text-red-700">{error}</p>}
    {scene&&<><div className="flex flex-wrap gap-2 text-sm"><select aria-label="Góc nhìn" value={cameraPreset} onChange={e=>setCameraPreset(e.target.value)}><option value="iso">Phối cảnh</option><option value="top">Từ trên</option><option value="front">Mặt trước</option></select><label><input type="checkbox" checked={labels} onChange={e=>setLabels(e.target.checked)}/>Tên đỉnh</label><label><input type="checkbox" checked={axes} onChange={e=>setAxes(e.target.checked)}/>Trục tọa độ</label><label><input type="checkbox" checked={net} onChange={e=>setNet(e.target.checked)}/>Khai triển</label></div><ThreeCanvas scene={scene} cameraPreset={cameraPreset} showLabels={labels} showAxes={axes}/>{net&&<UnfoldedNetViewer scene={scene}/>}<p>Thể tích: {Number(scene.measurements.volume.toPrecision(6))} (đơn vị khối)</p></>}
  </section>;
}
