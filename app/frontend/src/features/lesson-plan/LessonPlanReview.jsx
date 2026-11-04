import React, {useEffect, useRef, useState} from 'react';
import {postJson} from '../../shared/api/client.js';

export default function LessonPlanReview({plan, onChange}) {
  const current = useRef(plan);current.current = plan;
  const active = useRef(true);
  const [report,setReport] = useState(null), [reviewed,setReviewed] = useState({});
  const [ack,setAck] = useState(false), [busy,setBusy] = useState(false), [error,setError] = useState('');
  useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
  const {review_token,quality_report,...authored}=plan;
  const contentVersion=JSON.stringify(authored);
  useEffect(()=>{setReport(null);setReviewed({});setAck(false);setError('');},[contentVersion]);
  async function audit(approve=false) {
    const base=structuredClone(plan);
    setBusy(true);setError('');
    try {
      const payload=approve?{plan:base,acknowledged:ack,content_fingerprint:report.content_fingerprint,
        reviewed_issue_ids:Object.keys(reviewed).filter(id=>reviewed[id])}:base;
      const response=await postJson(`/api/v1/quality/lesson-plan/${approve?'approve':'check'}`,payload);
      const data=await response.json();
      if(!active.current)return;
      if(JSON.stringify(current.current)!==JSON.stringify(base))throw new Error('Giáo án đã đổi trong khi kiểm tra. Hãy kiểm tra lại.');
      if(!response.ok)throw new Error(data.detail?.message||'Không kiểm tra được giáo án');
      if(approve)onChange({...base,review_token:data.review_token,quality_report:data.report},base);
      setReviewed({});setAck(false);setReport(data.report||data);
    } catch(error) {if(active.current)setError(error.message);}
    finally {if(active.current)setBusy(false);}
  }
  const visibleReport=report;
  return <section aria-label="Duyệt giáo án" className="border rounded-xl p-3 space-y-2 text-sm">
    <p>{plan.review_token?'Đã lưu xác nhận giáo án; kiểm tra hiệu lực khi xuất.':'BẢN NHÁP — giáo án cần được duyệt riêng.'}</p>
    <button className="border rounded p-2" disabled={busy} onClick={()=>audit()}>Kiểm tra giáo án</button>
    {error&&<p role="alert">{error}</p>}
    {visibleReport&&<p>Trạng thái giáo án: {visibleReport.status}</p>}
    {report&&<>
      <ul>{report.issues.map(issue=><li key={issue.issue_id}>
        {issue.severity==='warning'?<label><input type="checkbox" checked={!!reviewed[issue.issue_id]} onChange={e=>setReviewed(previous=>({...previous,[issue.issue_id]:e.target.checked}))}/> Đã đối chiếu giáo án — {issue.field}: {issue.message}</label>:<span>{issue.field}: {issue.message}</span>}
      </li>)}</ul>
      {report.status!=='blocked'&&<>
        <label className="block"><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/> Tôi xác nhận đã đối chiếu toàn bộ giáo án của phiên bản này.</label>
        <button className="border rounded p-2" disabled={busy||!ack||report.issues.some(issue=>issue.severity==='warning'&&!reviewed[issue.issue_id])} onClick={()=>audit(true)}>Lưu xác nhận giáo án</button>
      </>}
    </>}
  </section>;
}
