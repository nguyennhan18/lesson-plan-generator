import React, { useEffect, useRef, useState } from 'react';
import { postJson } from '../api/client.js';

export default function FunctionPlotter({ spec = {}, defaultExpr = '', deckId, slideId, onSpecChange, sourceSlide }) {
  const [expression, setExpression] = useState(spec.expression || defaultExpr);
  const [operation, setOperation] = useState(spec.operation || 'function');
  const [xmin, setXmin] = useState(spec.x_min ?? -4);
  const [xmax, setXmax] = useState(spec.x_max ?? 4);
  const [ymin,setYmin]=useState(spec.y_min??'');
  const [ymax,setYmax]=useState(spec.y_max??'');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const request = useRef(0);
  const signature = JSON.stringify(spec);
  useEffect(() => {
    const controller = new AbortController();
    const sequence = ++request.current;
    let objectUrl;
    setResult(null); setError('');
    setExpression(spec.expression||'');setOperation(spec.operation||'function');setXmin(spec.x_min??-4);setXmax(spec.x_max??4);setYmin(spec.y_min??'');setYmax(spec.y_max??'');
    if (spec.requirement_token) {
      setBusy(true);
      postJson('/api/v1/chart/render', spec, { signal: controller.signal })
        .then(async response => {
          if (!response.ok || !response.headers.get('content-type')?.startsWith('image/png')) {
            const data = await response.json();
            throw new Error(data.detail?.message || data.message || 'Không dựng được đồ thị');
          }
          const blob = await response.blob();
          if (request.current === sequence && !controller.signal.aborted) {
            objectUrl = URL.createObjectURL(blob); setResult(objectUrl);
          }
        }).catch(e => { if (!controller.signal.aborted) setError(e.message); })
        .finally(() => { if (request.current === sequence) setBusy(false); });
    }
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [signature]);
  const confirm = async () => {
    const sequence=++request.current;
    setBusy(true); setError('');
    try {
      const source = { kind: 'function_plot', expression, operation, x_min: Number(xmin), x_max: Number(xmax), deck_id: deckId, slide_id: slideId, y_min:ymin===''?null:Number(ymin),y_max:ymax===''?null:Number(ymax) };
      const response = await postJson('/api/v1/visuals/confirm', {...source,source:sourceSlide});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail?.message || 'Dữ kiện chưa hợp lệ');
      if(sequence!==request.current)return;
      onSpecChange?.({ ...source, ...data.requirement.spec, requirement_token: data.requirement_token });
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  return <section className="space-y-3 p-3 border rounded-xl bg-white text-gray-900">
    <p className="text-sm">Đối chiếu công thức và yêu cầu với đề bài trước khi xác nhận.</p>
    <label className="block text-sm">Hàm gốc <input aria-label="Biểu thức hàm gốc" value={expression} onChange={e => {setExpression(e.target.value); setResult(null);request.current++;setBusy(false);}} className="border rounded p-2 w-full" /></label>
    <select aria-label="Đối tượng cần vẽ" value={operation} onChange={e => {setOperation(e.target.value); setResult(null);request.current++;setBusy(false);}} className="border p-2">
      <option value="function">Vẽ hàm gốc</option><option value="derivative">Vẽ đạo hàm</option>
    </select>
    <div className="flex gap-2"><label>Khoảng hiển thị từ <input aria-label="x nhỏ nhất" type="number" value={xmin} onChange={e => {setXmin(e.target.value); setResult(null);request.current++;setBusy(false);}} className="border w-20" /></label><label>đến <input aria-label="x lớn nhất" type="number" value={xmax} onChange={e => {setXmax(e.target.value); setResult(null);request.current++;setBusy(false);}} className="border w-20" /></label></div>
    <div className="flex gap-2"><label>y từ <input aria-label="y nhỏ nhất" type="number" value={ymin} onChange={e=>{setYmin(e.target.value);setResult(null);request.current++;setBusy(false);}} className="border w-20"/></label><label>đến <input aria-label="y lớn nhất" type="number" value={ymax} onChange={e=>{setYmax(e.target.value);setResult(null);request.current++;setBusy(false);}} className="border w-20"/></label></div>
    <p className="text-sm">Để trống cả hai giới hạn y để tự chọn cửa sổ nhìn rõ đồ thị; phần vượt cửa sổ sẽ bị cắt. Có thể nhập giới hạn để đối chiếu tiệm cận.</p>
    <button disabled={busy || !expression.trim() || !onSpecChange} onClick={confirm} className="border rounded px-3 py-2 disabled:opacity-40">Xác nhận dữ kiện và vẽ</button>
    {busy && <p role="status">Đang xử lý…</p>}{error && <p role="alert" className="text-red-700">{error}</p>}
    {!expression && <p>Chưa có công thức để vẽ.</p>}
    {result && <img src={result} alt={`Đồ thị ${operation === 'derivative' ? 'đạo hàm của ' : ''}${expression}`} className="w-full" />}
  </section>;
}
