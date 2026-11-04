import React,{useEffect,useRef,useState} from 'react';
import MathText from '../../shared/math/MathText';
import {postJson,ensureOwner} from '../../shared/api/client.js';
export default function TeacherChatDock({isOpen,onToggle,currentSlide,slideDeck,onApplyPatch}) {
  const [messages,setMessages]=useState([]),[input,setInput]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false),[proposal,setProposal]=useState(null),[ack,setAck]=useState(false);
  const session=useRef(null), epoch=useRef(0), current=useRef(slideDeck);current.current=slideDeck;
  useEffect(()=>{
    if(!slideDeck?.deck_id)return;
    const key='lessonai-chat-'+slideDeck.deck_id,stored=sessionStorage.getItem(key);let active=true;
    if(stored){setBusy(true);ensureOwner().then(()=>fetch(`/api/v1/chat/history/${stored}`)).then(async response=>{if(!response.ok){sessionStorage.removeItem(key);return;}const data=await response.json();if(active){session.current=stored;setMessages(data.history||[]);}}).catch(error=>{if(active)setError(error.message);}).finally(()=>{if(active)setBusy(false);});}
    return()=>{active=false;epoch.current++;};
  },[slideDeck?.deck_id]);
  const labels={title:'Tiêu đề',subtitle:'Phụ đề',bullet_points:'Nội dung',worked_solution_steps:'Các bước giải',main_definition_latex:'Công thức chính',math_formulas:'Công thức',teacher_note:'Ghi chú giáo viên',quiz_options:'Phương án trả lời',layout:'Bố cục'};
  const readable=value=>Array.isArray(value)?value.map(item=>typeof item==='string'?item:`${item.label||''}. ${item.text||''}${item.is_correct?' (được đánh dấu đúng)':''} ${item.distractor_rationale||''}`).join('\n'):String(value??'');
  const send=async()=>{
    if(!input.trim()||busy||!slideDeck?.slides?.[currentSlide])return;
    const version=epoch.current, base=structuredClone(slideDeck), text=input;setBusy(true);setError('');setInput('');setProposal(null);setAck(false);
    setMessages(v=>[...v,{role:'user',text}]);
    try{
      if(!session.current){const r=await postJson('/api/v1/chat/sessions',{slide_deck:base}),d=await r.json();if(!r.ok)throw new Error(d.detail?.message||d.detail);if(version!==epoch.current){await fetch(`/api/v1/chat/session/${d.session_id}`,{method:'DELETE'});return;}session.current=d.session_id;sessionStorage.setItem('lessonai-chat-'+base.deck_id,d.session_id);}
      const r=await postJson('/api/v1/chat/interact',{session_id:session.current,slide_id:base.slides[currentSlide].slide_id,slide_deck:base,user_message:text}),d=await r.json();
      if(!r.ok)throw new Error(d.detail?.message||d.detail||'Không nhận được phản hồi');
      if(version===epoch.current){setMessages(v=>[...v,{role:'assistant',text:d.ai_response}]);setProposal(d.suggested_patch?{...d.suggested_patch,base}:null);}
    }catch(e){if(version===epoch.current)setError(e.message);}finally{if(version===epoch.current)setBusy(false);}
  };
  const reset=async()=>{epoch.current++;setBusy(false);setError('');try{if(session.current){const r=await fetch(`/api/v1/chat/session/${session.current}`,{method:'DELETE'});if(!r.ok)throw new Error('Không xóa được phiên cũ');}session.current=null;sessionStorage.removeItem('lessonai-chat-'+slideDeck.deck_id);setMessages([]);setProposal(null);}catch(e){setError(e.message);}};
  const apply=async()=>{const version=epoch.current;setBusy(true);setError('');const base=structuredClone(current.current);try{const r=await postJson('/api/v1/chat/apply-patch',{proposal_id:proposal.proposal_id,slide_deck:base,acknowledged:ack}),d=await r.json();if(!r.ok)throw new Error(d.detail?.message||d.detail);if(version!==epoch.current)return;if(!onApplyPatch(d.slide_deck,base))throw new Error('Bài đã thay đổi trong khi áp dụng; giữ bản soạn hiện tại.');setProposal(null);}catch(e){setError(e.message);}finally{setBusy(false);}};
  if(!isOpen)return null;
  return <aside className="w-80 shrink-0 border-r p-3 flex flex-col gap-3 overflow-auto"><div className="flex justify-between"><strong>Trợ giảng</strong><button onClick={onToggle}>Đóng</button><button onClick={reset}>Làm mới</button></div>
    {!messages.length&&<p className="text-sm">Nhập yêu cầu về slide đang mở. Đề xuất cần được duyệt trước khi áp dụng.</p>}
    {messages.map((m,i)=><div key={i} className="border rounded p-2 text-sm"><strong>{m.role==='user'?'Giáo viên':'AI'}: </strong><MathText text={m.text}/></div>)}
    {error&&<p role="alert" className="text-red-700">{error}</p>}
    {proposal&&<div className="text-sm space-y-2"><p>Đề xuất cần rà soát:</p>{Object.keys(proposal.changes).map(k=><div key={k}><strong>{labels[k]||k}</strong><p className="whitespace-pre-wrap">Trước: <MathText text={readable(proposal.before[k])}/></p><p className="whitespace-pre-wrap">Sau: <MathText text={readable(proposal.changes[k])}/></p></div>)}<label><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/> Tôi đã đối chiếu nội dung trước/sau với yêu cầu.</label><button disabled={!ack||busy} onClick={apply}>Áp dụng đề xuất</button></div>}
    <textarea aria-label="Yêu cầu trợ giảng" value={input} onChange={e=>setInput(e.target.value)} className="border p-2 rounded"/><button onClick={send} disabled={busy||!input.trim()||!slideDeck}>Gửi</button>
  </aside>;
}
