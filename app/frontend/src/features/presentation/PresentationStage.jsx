import React, {useEffect,useRef,useState} from 'react';
import MathText from '../../shared/math/MathText';
import FunctionPlotter from '../../shared/math/FunctionPlotter';
import DataChartVisual from '../../shared/math/DataChartVisual';
import GeometryVisual from '../geometry/GeometryVisual';
import AnnotationCanvas from './AnnotationCanvas';
import WhiteboardOverlay from './WhiteboardOverlay';
import MathLiveModal from '../../shared/math/MathLiveModal';
import {postJson} from '../../shared/api/client.js';

export default function PresentationStage({slideDeck,setSlideDeck,currentSlide,setCurrentSlide,isPresentationMode,onExitPresentation,isBlackout,onToggleBlackout,onNavigateScreen}) {
  const slide=slideDeck?.slides?.[currentSlide];
  const deckRef=useRef(slideDeck);deckRef.current=slideDeck;
  const [mathOpen,setMathOpen]=useState(false),[recentlyUpdatedFormula,setRecentlyUpdatedFormula]=useState(false);
  const [whiteboard,setWhiteboard]=useState(false),[undo,setUndo]=useState({}),[redo,setRedo]=useState({});
  useEffect(()=>{setUndo({});setRedo({});setWhiteboard(false);},[slideDeck?.deck_id,slideDeck?.project_id]);
  const [color,setColor]=useState('#2563eb');
  useEffect(()=>{setMathOpen(false);setRecentlyUpdatedFormula(false);},[slide?.slide_id]);
  useEffect(()=>{if(!recentlyUpdatedFormula)return;const timer=setTimeout(()=>setRecentlyUpdatedFormula(false),2000);return()=>clearTimeout(timer);},[recentlyUpdatedFormula]);
  useEffect(()=>{const handler=e=>{if(/INPUT|TEXTAREA|MATH-FIELD|SELECT/.test(e.target?.tagName)||e.target?.isContentEditable)return;if(e.key==='w'||e.key==='W')setWhiteboard(v=>!v);if(e.key==='p'||e.key==='P')setPen(v=>!v);};window.addEventListener('keydown',handler);return()=>window.removeEventListener('keydown',handler);},[]);
  const [reveal,setReveal]=useState(0),[selected,setSelected]=useState(null),[pen,setPen]=useState(false),[tool,setTool]=useState('pen');
  const [reviewedIssues,setReviewedIssues]=useState({});
  const [report,setReport]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[ack,setAck]=useState(false);
  useEffect(()=>{setReveal(0);setSelected(null);setPen(false);},[slide?.slide_id]);
  useEffect(()=>{setReport(null);setAck(false);setReviewedIssues({});},[slideDeck?.revision,slideDeck?.deck_id]);
  if(!slide)return <div className="p-8"><p>Chưa có slide để trình chiếu.</p><button onClick={()=>onNavigateScreen?.('dashboard')}>Về màn hình soạn bài</button></div>;
  const sid=slide.slide_id;
  const updateSlide=changes=>setSlideDeck(previous=>previous?.deck_id===slideDeck.deck_id?{...previous,slides:previous.slides.map(s=>s.slide_id===sid?{...s,...changes}:s)}:previous);
  const drawings=slideDeck.annotations?.[sid]||[];
  const writeDrawings=(key,strokes)=>setSlideDeck(previous=>previous?.deck_id===slideDeck.deck_id?({...previous,annotations:{...previous.annotations,[key]:strokes}}):previous);
  const recordDrawings=(key,strokes)=>{setUndo(previous=>({...previous,[key]:[...(previous[key]||[]),deckRef.current.annotations?.[key]||[]].slice(-50)}));setRedo(previous=>({...previous,[key]:[]}));writeDrawings(key,strokes);};
  const setDrawings=strokes=>recordDrawings(sid,strokes);
  const undoDrawing=key=>{const stack=undo[key]||[];if(!stack.length)return;setRedo(previous=>({...previous,[key]:[...(previous[key]||[]),deckRef.current.annotations?.[key]||[]]}));setUndo(previous=>({...previous,[key]:stack.slice(0,-1)}));writeDrawings(key,stack.at(-1));};
  const redoDrawing=key=>{const stack=redo[key]||[];if(!stack.length)return;setUndo(previous=>({...previous,[key]:[...(previous[key]||[]),deckRef.current.annotations?.[key]||[]]}));setRedo(previous=>({...previous,[key]:stack.slice(0,-1)}));writeDrawings(key,stack.at(-1));};
  const votes=slideDeck.polls?.[sid]||{};
  const setVotes=value=>setSlideDeck(previous=>({...previous,polls:{...previous.polls,[sid]:value}}));
  const audit=async(approve=false)=>{
    setBusy(true);setError(''); const base=slideDeck;
    try{const response=await postJson(`/api/v1/quality/${approve?'approve':'check'}`,approve?{deck:base,acknowledged:true,content_fingerprint:report?.content_fingerprint,reviewed_issue_ids:Object.keys(reviewedIssues).filter(id=>reviewedIssues[id])}:base);const data=await response.json();if(!response.ok)throw new Error(data.detail?.message||'Không kiểm tra được bài');
      if(deckRef.current?.deck_id!==base.deck_id||deckRef.current?.revision!==base.revision){setError('Bài đã thay đổi trong khi kiểm tra. Vui lòng kiểm tra lại.');return;}
      if(approve)setSlideDeck(previous=>previous.deck_id===base.deck_id&&previous.revision===base.revision?{...previous,review_token:data.review_token,quality_report:data.report}:previous);
      if(!approve){setReviewedIssues({});setAck(false);}
      setReport(data.report||data);
    }catch(e){setError(e.message);}finally{setBusy(false);}
  };
  return <section className={`flex-1 min-w-0 overflow-auto p-4 space-y-4 ${isPresentationMode?'bg-white text-gray-900':''}`}>
    {isBlackout&&<div className="fixed inset-0 bg-black z-50" onClick={()=>onToggleBlackout?.(false)} role="button" aria-label="Mở lại trình chiếu"/>}
    <nav className="flex flex-wrap gap-2 items-center text-sm">
      <button className="border rounded p-2" disabled={currentSlide===0} onClick={()=>setCurrentSlide(currentSlide-1)}>Trang trước</button>
      <span>{currentSlide+1}/{slideDeck.slides.length}</span><button className="border rounded p-2" disabled={currentSlide+1>=slideDeck.slides.length} onClick={()=>setCurrentSlide(currentSlide+1)}>Trang sau</button>
      <button className="border rounded p-2" onClick={()=>setPen(!pen)}>{pen?'Tắt bút':'Chú thích'}</button>
      <button className="border rounded p-2" onClick={()=>setWhiteboard(true)}>Bảng phụ</button>
      {pen&&<><input type="color" aria-label="Màu bút" value={color} onChange={e=>setColor(e.target.value)}/><button disabled={!undo[sid]?.length} onClick={()=>undoDrawing(sid)}>Hoàn tác</button><button disabled={!redo[sid]?.length} onClick={()=>redoDrawing(sid)}>Làm lại</button><select value={tool} onChange={e=>setTool(e.target.value)}><option value="pen">Bút</option><option value="highlighter">Đánh dấu</option><option value="eraser">Tẩy</option></select><button onClick={()=>setDrawings([])}>Xóa nét vẽ trang này</button></>}
      <button className="border rounded p-2" disabled={busy} onClick={()=>audit()}>Kiểm tra bài</button>
      {isPresentationMode&&<><button onClick={()=>onToggleBlackout?.(true)}>Tối màn hình</button><button onClick={onExitPresentation}>Thoát trình chiếu</button></>}
      <span className="ml-auto text-amber-800">{slideDeck.review_token?'Đã lưu xác nhận duyệt; kiểm tra lại khi xuất':'BẢN NHÁP — cần duyệt nội dung'}</span>
    </nav>
    {error&&<p role="alert">{error}</p>}
    {report&&<div className="border rounded p-3 text-sm space-y-2"><p>Trạng thái: {report.status}</p><ul>{report.issues?.map((v,i)=><li key={v.issue_id||i}>{v.severity==='warning'?<label><input type="checkbox" checked={!!reviewedIssues[v.issue_id]} onChange={e=>setReviewedIssues(previous=>({...previous,[v.issue_id]:e.target.checked}))}/> Đã đối chiếu trang {v.slide_index||'—'} — {v.field}: {v.message}</label>:<>Trang {v.slide_index||'—'} — {v.field}: {v.message}</>}</li>)}</ul>
      {report.status!=='blocked'&&<><label><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/> Tôi đã đối chiếu đề, điều kiện, lời giải, nguồn và tiến trình bài dạy của phiên bản này.</label><button className="border p-2 ml-2" disabled={!ack||busy||report.issues.some(v=>v.severity==='warning'&&!reviewedIssues[v.issue_id])} onClick={()=>audit(true)}>Lưu xác nhận chuyên môn</button></>}
    </div>}
    <article className="relative border rounded-2xl p-6 min-h-[520px] bg-white text-gray-900">
      <h1 className="text-3xl font-semibold mb-4"><MathText text={slide.title}/></h1>
      {slide.subtitle&&<MathText text={slide.subtitle}/>}
      <div className={`grid gap-6 ${slide.has_3d||slide.chart_spec?.kind==='function_plot'||slide.worked_solution_steps?.length?'lg:grid-cols-2':''}`}>
        <div className="space-y-4 text-xl"><ul className="list-disc pl-6 space-y-3">{slide.bullet_points?.map((b,i)=><li key={i}><MathText text={b}/></li>)}</ul>
          {slide.main_definition_latex&&<div className={recentlyUpdatedFormula?'bg-green-50':''} onDoubleClick={()=>setMathOpen(true)}><MathText text={slide.main_definition_latex} block/><button className="text-sm border p-1" onClick={()=>setMathOpen(true)}>Sửa công thức</button></div>}
          {slide.math_formulas?.map((v,i)=><MathText key={i} text={v} block/>)}
          {slide.question&&<MathText text={slide.question}/>}
          {slide.blocks?.map((b,i)=><div key={b.id||i}>{b.type==='image'?<img className="max-h-80 object-contain" src={b.data_url} alt={b.alt||'Hình trong tài liệu'}/>:b.type==='table'?<ContentTable data={b.rows||b.data}/>:<MathText text={b.text||b.latex||''} block={b.type==='formula'}/>}</div>)}
          {slide.table_data&&<ContentTable data={slide.table_data}/>}
          {slide.source_refs?.length>0&&<details className="text-sm"><summary>Nguồn nội dung</summary>{slide.source_refs.map((ref,i)=><pre className="whitespace-pre-wrap" key={i}>{JSON.stringify(ref,null,2)}</pre>)}</details>}
        </div>
        {slide.worked_solution_steps?.length>0&&<div className="space-y-3"><h2 className="font-semibold text-lg">Lời giải</h2>{slide.worked_solution_steps.slice(0,reveal).map((v,i)=><div className="border-l-2 pl-3" key={i}><MathText text={typeof v==='string'?v:v.text||v.explanation||''}/></div>)}<button className="border rounded p-2" onClick={()=>setReveal(Math.min(reveal+1,slide.worked_solution_steps.length))} disabled={reveal>=slide.worked_solution_steps.length}>Hiện bước tiếp theo</button></div>}
        {slide.chart_spec?.kind==='function_plot'&&<FunctionPlotter key={`${sid}-chart`} spec={slide.chart_spec} deckId={slideDeck.deck_id} slideId={sid} sourceSlide={slide} onSpecChange={chart_spec=>updateSlide({chart_spec})}/>}
        {['arithmetic_sequence','inequality_system'].includes(slide.chart_spec?.kind)&&<DataChartVisual spec={slide.chart_spec} deckId={slideDeck.deck_id} slideId={sid} sourceSlide={slide} onSpecChange={chart_spec=>updateSlide({chart_spec})}/>}
        {slide.has_3d&&<GeometryVisual key={`${sid}-scene`} spec={slide.scene_spec||{}} deckId={slideDeck.deck_id} slideId={sid} sourceSlide={slide} onSpecChange={scene_spec=>updateSlide({scene_spec})}/>}
      </div>
      {slide.quiz_options?.length>0&&<div className="mt-6 space-y-3"><p>Ghi nhận lựa chọn tại máy giáo viên</p>{slide.quiz_options.map(o=><button className={`block w-full text-left border p-3 rounded ${selected===o.label?'bg-blue-50':''}`} key={o.label} onClick={()=>{setSelected(o.label);setVotes({...votes,[o.label]:(votes[o.label]||0)+1});}}><strong>{o.label}. </strong><MathText text={o.text}/> — {votes[o.label]||0} lượt</button>)}<button onClick={()=>{setVotes({});setSelected(null);}}>Đặt lại số lượt của câu hỏi</button>{selected&&<p>{slide.quiz_options.find(o=>o.label===selected)?.is_correct?'Đáp án được đánh dấu đúng trong bản soạn.':slide.quiz_options.find(o=>o.label===selected)?.distractor_rationale}</p>}</div>}
      <AnnotationCanvas isActive={pen} tool={tool} slideIndex={sid} color={color} strokes={drawings} onStrokesChange={setDrawings} isPresentationMode={isPresentationMode}/>
    </article>
    <MathLiveModal isOpen={mathOpen} initialLatex={slide.main_definition_latex||''} onClose={()=>setMathOpen(false)} onSave={value=>{updateSlide({main_definition_latex:value});setRecentlyUpdatedFormula(true);}}/>
    <WhiteboardOverlay isOpen={whiteboard} onClose={()=>setWhiteboard(false)} tool={tool} color={color} onSelectTool={setTool} onSelectColor={setColor} strokes={slideDeck.annotations?.whiteboard||[]} onStrokesChange={strokes=>recordDrawings('whiteboard',strokes)} canUndo={!!undo.whiteboard?.length} canRedo={!!redo.whiteboard?.length} onUndo={()=>undoDrawing('whiteboard')} onRedo={()=>redoDrawing('whiteboard')} onClear={()=>recordDrawings('whiteboard',[])}/>
    {slide.teacher_note&&<details><summary>Ghi chú giáo viên</summary><MathText text={slide.teacher_note}/></details>}
  </section>;
}

function ContentTable({data}) {
  const rows=Array.isArray(data)?data:data?.rows||[];
  return <div className="overflow-auto"><table className="border-collapse text-base"><tbody>{rows.map((row,i)=><tr key={i}>{(Array.isArray(row)?row:Object.values(row)).map((cell,j)=><td className="border p-2" key={j}><MathText text={typeof cell==='object'?cell.text||JSON.stringify(cell):String(cell)}/></td>)}</tr>)}</tbody></table></div>;
}
