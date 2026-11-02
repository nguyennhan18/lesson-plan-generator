import React from 'react';

/** M0: preserve the draft expression while expression processing is unavailable. */
export default function FunctionPlotter({
  defaultExpr = '',
  title = 'Đồ thị y = f(x)',
  pedagogicalPurpose = null
}) {
  return (
    <div className="w-full h-full flex flex-col justify-center gap-3 p-3 text-sm text-[#141414]"
      data-render-status="temporarily_unavailable">
      <strong>{title}</strong>
      {pedagogicalPurpose && <p>{pedagogicalPurpose}</p>}
      {defaultExpr && <code className="break-all">y = {defaultExpr}</code>}
      <p role="status">{defaultExpr
        ? 'Vẽ đồ thị đang tạm ngắt để nâng cấp bộ xử lý an toàn. Biểu thức được giữ trong bản nháp.'
        : 'Chưa có công thức để vẽ. Cần bổ sung biểu thức đúng yêu cầu của bài.'}</p>
    </div>
  );
}
