import React from 'react';

export default function LessonPlanEditor({plan,onChange}) {
  const update=changes=>onChange({...plan,...changes},plan);
  const activity=(index,changes)=>update({activities:plan.activities.map((item,i)=>i===index?{...item,...changes}:item)});
  return <details className="border rounded-xl p-3 text-sm">
    <summary>Chỉnh sửa nội dung giáo án</summary>
    <div className="space-y-3 mt-3">
      <label className="block">Tên bài dạy<input className="block w-full border p-2" aria-label="Tên giáo án" value={plan.lesson_title||''} onChange={e=>update({lesson_title:e.target.value})}/></label>
      {Object.entries({knowledge_goals:'Mục tiêu kiến thức',competency_goals:'Mục tiêu năng lực',skills_goals:'Mục tiêu kỹ năng',character_goals:'Mục tiêu phẩm chất',teaching_equipment:'Thiết bị và học liệu'}).map(([field,label])=><label className="block" key={field}>{label} (mỗi dòng một ý)<textarea className="block w-full border p-2" value={(plan[field]||[]).join('\n')} onChange={e=>update({[field]:e.target.value.split('\n')})}/></label>)}
      {(plan.activities||[]).map((item,index)=><fieldset key={index} className="border p-3 space-y-2">
        <legend>Hoạt động {item.activity_number}</legend>
        <label className="block">Thời lượng (phút)<input type="number" className="border p-2 ml-2" value={item.time_minutes} onChange={e=>activity(index,{time_minutes:Number(e.target.value)})}/></label>
        {Object.entries({goal:'Mục tiêu / đề bài',expected_product:'Đáp án / sản phẩm dự kiến'}).map(([field,label])=><label key={field} className="block">{label}<textarea className="block w-full border p-2" aria-label={`${label} hoạt động ${index+1}`} value={item[field]||''} onChange={e=>activity(index,{[field]:e.target.value})}/></label>)}
        {Object.entries({step_1_assign:'Chuyển giao nhiệm vụ',step_2_excute:'Thực hiện nhiệm vụ',step_3_report:'Báo cáo thảo luận',step_4_conclusion:'Kết luận'}).map(([field,label])=><label key={field} className="block">{label}<textarea className="block w-full border p-2" value={item.execution?.[field]||''} onChange={e=>activity(index,{execution:{...item.execution,[field]:e.target.value}})}/></label>)}
      </fieldset>)}
    </div>
  </details>;
}
