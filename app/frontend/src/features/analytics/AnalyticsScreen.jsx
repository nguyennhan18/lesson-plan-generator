import React, {useEffect,useState} from 'react';
export function gradeGroups(data) {
  const counts=data.counts;
  if (!counts) return null;
  return [['Dưới 5',counts.below_5],['Từ 5 đến dưới 8',counts.between_5_8],['Từ 8 trở lên',counts.above_8]];
}
export default function AnalyticsScreen({analyticsData,onClassificationSuccess,onApplyToLessonPlan}) {
  const [data,setData]=useState(analyticsData),[busy,setBusy]=useState(false),[error,setError]=useState('');
  useEffect(()=>setData(analyticsData),[analyticsData]);
  const upload=async e=>{
    const file=e.target.files?.[0];if(!file)return;setBusy(true);setError('');
    try{const form=new FormData();form.append('file',file);const response=await fetch('/api/v1/ingest/classify-grades',{method:'POST',body:form});const result=await response.json();
      if(!response.ok)throw new Error(result.detail?.message||result.detail||'Không phân tích được bảng điểm');
      setData(result);onClassificationSuccess?.(result);
    }catch(e){setError(e.message);}finally{setBusy(false);e.target.value='';}
  };
  return <div className="p-6 overflow-auto w-full space-y-5"><h1 className="text-2xl font-bold">Phân tích bảng điểm</h1>
    <label className="block">Nhập bảng điểm CSV hoặc Excel <input aria-label="Nhập bảng điểm" type="file" accept=".csv,.xlsx,.xlsm" onChange={upload} disabled={busy}/></label>
    {busy&&<p role="status">Đang phân tích…</p>}{error&&<p role="alert">{error}</p>}
    {!data?<p>Chưa có dữ liệu bảng điểm. Hãy nhập tệp của lớp để phân tích.</p>:<>
      <p>Đã phân tích {data.filename}: {data.total_students} học sinh.</p>
      <div className="grid grid-cols-3 gap-4"><p>Trung bình: {data.mean}</p><p>Độ lệch chuẩn: {data.std_dev}</p><p>CV: {data.cv==null?'Không xác định':`${(data.cv*100).toFixed(1)}%`}</p></div>
      {gradeGroups(data)?<table className="w-full text-left"><thead><tr><th>Nhóm điểm</th><th>Số học sinh</th><th>Tỷ lệ</th></tr></thead><tbody>{gradeGroups(data).map(([label,count])=><tr key={label}><td>{label}</td><td>{count}</td><td>{data.total_students?`${(count/data.total_students*100).toFixed(1)}%`:'—'}</td></tr>)}</tbody></table>:<p>Dữ liệu cũ chưa có số đếm chính xác; cần nhập lại tệp để đối chiếu.</p>}
      <p>{data.target_outcome}</p>{data.warning_notes?.map((v,i)=><p key={i}>{v}</p>)}
      <button className="border p-2 rounded" onClick={()=>onApplyToLessonPlan?.(data.class_label,data.target_outcome)}>Áp dụng phân hóa vào bài dạy</button>
      <table className="w-full text-left"><thead><tr><th>STT</th><th>Điểm</th><th>Z-score</th><th>Nhận xét</th></tr></thead><tbody>{data.student_evaluations?.map((s,i)=><tr key={i}><td>{i+1}</td><td>{s.score}</td><td>{s.z_score}</td><td>{s.recommendation}</td></tr>)}</tbody></table>
    </>}
  </div>;
}
