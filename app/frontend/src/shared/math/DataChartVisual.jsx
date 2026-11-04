import React,{useEffect,useRef,useState} from 'react';
import {postJson} from '../api/client.js';

export default function DataChartVisual({spec,deckId,slideId,sourceSlide,onSpecChange}) {
  const [draft,setDraft]=useState(spec),[image,setImage]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const epoch=useRef(0);
  useEffect(()=>{
    const serial=++epoch.current,controller=new AbortController();let url;
    setDraft(spec);setImage(null);setError('');
    if(spec.requirement_token){setBusy(true);postJson('/api/v1/chart/render',spec,{signal:controller.signal}).then(async response=>{
      if(!response.ok){const data=await response.json();throw new Error(data.detail?.message||'Không vẽ được dữ kiện');}
      const blob=await response.blob();if(serial===epoch.current&&!controller.signal.aborted){url=URL.createObjectURL(blob);setImage(url);}
    }).catch(error=>{if(serial===epoch.current&&!controller.signal.aborted)setError(error.message);}).finally(()=>{if(serial===epoch.current)setBusy(false);});}
    return()=>{controller.abort();if(url)URL.revokeObjectURL(url);};
  },[JSON.stringify(spec)]);
  const edit=change=>{epoch.current++;setBusy(false);setImage(null);setDraft({...draft,...change});};
  const confirm=async()=>{
    const serial=++epoch.current;setBusy(true);setError('');
    try{
      const source={...draft,deck_id:deckId,slide_id:slideId,source:sourceSlide};
      const response=await postJson('/api/v1/visuals/confirm',source),data=await response.json();
      if(!response.ok)throw new Error(data.detail?.message||'Thiếu dữ kiện');
      if(serial===epoch.current)onSpecChange({...data.requirement.spec,deck_id:deckId,slide_id:slideId,requirement_token:data.requirement_token});
    }catch(error){if(serial===epoch.current)setError(error.message);}finally{if(serial===epoch.current)setBusy(false);}
  };
  const input=(label,key)=><label className="block" key={key}>{label} <input aria-label={label} type="number" className="border p-1 w-24" value={draft[key]??''} onChange={e=>edit({[key]:e.target.value===''?null:Number(e.target.value)})}/></label>;
  return <section className="border rounded p-3 space-y-3 text-base">
    <p>Nhập và đối chiếu dữ kiện với đề bài trước khi vẽ.</p>
    {spec.kind==='arithmetic_sequence'?<>{input('Số hạng đầu u₁','first_term')}{input('Công sai d','common_difference')}{input('Số số hạng cần biểu diễn','count')}</>:<>
      <p>Mỗi dòng là bất phương trình ax + by so với c.</p>
      {(draft.constraints||[]).map((row,index)=><div className="flex gap-1 items-center flex-wrap" key={index}>{['a','b','c'].map(key=><label key={key}>{key}<input aria-label={`${key} dòng ${index+1}`} type="number" className="border w-16" value={row[key]??''} onChange={e=>edit({constraints:draft.constraints.map((item,i)=>i===index?{...item,[key]:e.target.value===''?null:Number(e.target.value)}:item)})}/></label>)}<select aria-label={`Quan hệ dòng ${index+1}`} value={row.relation||''} onChange={e=>edit({constraints:draft.constraints.map((item,i)=>i===index?{...item,relation:e.target.value}:item)})}><option value="">Quan hệ</option>{['<=','>=','<','>'].map(value=><option key={value}>{value}</option>)}</select><button onClick={()=>edit({constraints:draft.constraints.filter((_,i)=>i!==index)})}>Xóa dòng</button></div>)}
      <button onClick={()=>edit({constraints:[...(draft.constraints||[]),{a:null,b:null,c:null,relation:''}]})}>Thêm bất phương trình</button>
      <div className="grid grid-cols-2 gap-2">{input('x nhỏ nhất','x_min')}{input('x lớn nhất','x_max')}{input('y nhỏ nhất','y_min')}{input('y lớn nhất','y_max')}</div>
      <p className="text-sm">Miền tô chỉ nằm trong cửa sổ hiển thị. Biên nét đứt không thuộc miền nghiệm.</p>
    </>}
    <button disabled={busy} className="border rounded p-2" onClick={confirm}>Xác nhận dữ kiện và biểu diễn</button>
    {busy&&<p role="status">Đang vẽ…</p>}{error&&<p role="alert">{error}</p>}{image&&<img src={image} alt={spec.kind==='arithmetic_sequence'?'Các số hạng của cấp số cộng':'Miền nghiệm của hệ bất phương trình'}/>}
  </section>;
}
