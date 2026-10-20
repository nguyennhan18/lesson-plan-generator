import React, { useState, useEffect, useRef } from 'react';
import MathText from './MathText';

/**
 * FunctionPlotter - 2D Cartesian Coordinate & Parabola Analyzer
 * Bộ vẽ đồ thị 2D trên hệ trục Oxy chuyên sâu cho Đại số & Giải tích.
 * Hỗ trợ tự động phân tích nghiệm, đỉnh, trục đối xứng và biệt thức Delta cho Phương trình bậc hai.
 */
export default function FunctionPlotter({
  defaultExpr = 'x**2 - 4',
  title = 'Đồ thị Parabol y = f(x)',
  pedagogicalPurpose = null,
  compact = false,
  allowEdit = true
}) {
  const [expr, setExpr] = useState(defaultExpr);
  const [xMin, setXMin] = useState(-5);
  const [xMax, setXMax] = useState(5);
  const [analysis, setAnalysis] = useState(null);
  const canvasRef = useRef(null);

  // Cập nhật khi prop defaultExpr thay đổi
  useEffect(() => {
    if (defaultExpr) {
      setExpr(defaultExpr);
    }
  }, [defaultExpr]);

  const presets = [
    { label: 'Parabol bậc 2 (2 nghiệm): y = x² - 4', val: 'x**2 - 4' },
    { label: 'Parabol bậc 2 (Nghiệm kép): y = x² - 2x + 1', val: 'x**2 - 2*x + 1' },
    { label: 'Parabol bậc 2 (Vô nghiệm): y = x² + 2', val: 'x**2 + 2' },
    { label: 'Quỹ đạo ném bóng: y = -0.5x² + 2x + 2.5', val: '-0.5*x**2 + 2*x + 2.5' },
    { label: 'Bậc nhất: y = 2x - 1', val: '2*x - 1' },
    { label: 'Lượng giác: y = 2sin(x)', val: '2*sin(x)' }
  ];

  // Phân tích đặc trưng hàm số bậc hai y = ax^2 + bx + c
  const analyzeQuadratic = (expression) => {
    try {
      const clean = expression.replace(/\s+/g, '');
      // Mẫu tổng quát: a*x**2 + b*x + c
      let a = 0, b = 0, c = 0;

      // Phân tích sơ bộ các dạng phổ biến của bậc hai
      if (clean === 'x**2-4') { a = 1; b = 0; c = -4; }
      else if (clean === 'x**2-2*x+1') { a = 1; b = -2; c = 1; }
      else if (clean === 'x**2+2') { a = 1; b = 0; c = 2; }
      else if (clean === '-0.5*x**2+2*x+2.5') { a = -0.5; b = 2; c = 2.5; }
      else if (clean === 'x**2-2*x-3') { a = 1; b = -2; c = -3; }
      else {
        // Parse cơ bản
        const matchA = clean.match(/([+-]?\d*\.?\d*)\*?x\*\*2/);
        if (matchA) {
          const valA = matchA[1];
          a = valA === '' || valA === '+' ? 1 : valA === '-' ? -1 : parseFloat(valA);
        }
        const matchB = clean.match(/([+-]?\d*\.?\d*)\*?x(?!\*)/);
        if (matchB) {
          const valB = matchB[1];
          b = valB === '' || valB === '+' ? 1 : valB === '-' ? -1 : parseFloat(valB);
        }
        const matchC = clean.match(/([+-]\d+\.?\d*)$/);
        if (matchC) {
          c = parseFloat(matchC[1]);
        }
      }

      if (a !== 0) {
        const delta = b * b - 4 * a * c;
        const vx = -b / (2 * a);
        const vy = a * vx * vx + b * vx + c;
        let roots = [];
        if (delta > 0) {
          roots = [
            (-b - Math.sqrt(delta)) / (2 * a),
            (-b + Math.sqrt(delta)) / (2 * a)
          ].sort((r1, r2) => r1 - r2);
        } else if (Math.abs(delta) < 1e-9) {
          roots = [vx];
        }

        return { isQuadratic: true, a, b, c, delta, vx, vy, roots };
      }
    } catch (e) {
      // bỏ qua lỗi parse
    }
    return { isQuadratic: false };
  };

  const plot = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    // 1. Phông nền tối tương phản cao
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#050a18';
    ctx.fillRect(0, 0, w, h);

    // 2. Lưới tọa độ Grid
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.08)';
    ctx.lineWidth = 1;
    const step = 28;
    for (let x = 0; x < w; x += step) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }
    for (let y = 0; y < h; y += step) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // 3. Hệ trục tọa độ Oxy
    const cx = w / 2;
    const cy = h / 2 + 10;
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.6)';
    ctx.lineWidth = 1.6;

    // Trục Ox
    ctx.beginPath(); ctx.moveTo(10, cy); ctx.lineTo(w - 10, cy); ctx.stroke();
    // Mũi tên Ox
    ctx.beginPath();
    ctx.moveTo(w - 10, cy); ctx.lineTo(w - 18, cy - 4); ctx.lineTo(w - 18, cy + 4);
    ctx.fillStyle = 'rgba(56, 189, 248, 0.8)';
    ctx.fill();

    // Trục Oy
    ctx.beginPath(); ctx.moveTo(cx, h - 10); ctx.lineTo(cx, 10); ctx.stroke();
    // Mũi tên Oy
    ctx.beginPath();
    ctx.moveTo(cx, 10); ctx.lineTo(cx - 4, 18); ctx.lineTo(cx + 4, 18);
    ctx.fill();

    // Nhãn trục
    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 11px sans-serif';
    ctx.fillText('x', w - 16, cy - 8);
    ctx.fillText('y', cx + 8, 16);
    ctx.fillText('O', cx - 12, cy + 14);

    // 4. Vẽ đường cong hàm số
    const quadInfo = analyzeQuadratic(expr);
    setAnalysis(quadInfo);

    const scaleX = (w * 0.42) / Math.max(Math.abs(xMin), Math.abs(xMax));
    const scaleY = 20;

    // Trục đối xứng nếu là hàm bậc 2
    if (quadInfo.isQuadratic) {
      const symmPx = cx + quadInfo.vx * scaleX;
      ctx.strokeStyle = 'rgba(234, 179, 8, 0.4)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(symmPx, 10);
      ctx.lineTo(symmPx, h - 10);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Đường cong chính
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 3;
    ctx.beginPath();

    let first = true;
    for (let px = 10; px < w - 10; px += 2) {
      const x = (px - cx) / scaleX;
      let y = 0;
      try {
        const evalExpr = expr
          .replace(/\bsin\b/g, 'Math.sin')
          .replace(/\bcos\b/g, 'Math.cos')
          .replace(/\btan\b/g, 'Math.tan')
          .replace(/\bsqrt\b/g, 'Math.sqrt')
          .replace(/\babs\b/g, 'Math.abs')
          .replace(/\bpi\b/g, 'Math.PI')
          .replace(/\^/g, '**');

        const fn = new Function('x', `return ${evalExpr};`);
        y = fn(x);
      } catch (e) {
        y = 0;
      }

      if (isNaN(y) || !isFinite(y)) {
        first = true;
        continue;
      }

      const py = cy - y * scaleY;
      if (py < -80 || py > h + 80) {
        first = true;
        continue;
      }

      if (first) {
        ctx.moveTo(px, py);
        first = false;
      } else {
        ctx.lineTo(px, py);
      }
    }
    ctx.stroke();

    // 5. Đánh dấu các điểm đặc trưng của Parabol (Đỉnh và Các nghiệm)
    if (quadInfo.isQuadratic) {
      // Đỉnh I
      const vPx = cx + quadInfo.vx * scaleX;
      const vPy = cy - quadInfo.vy * scaleY;
      if (vPx >= 10 && vPx <= w - 10 && vPy >= 10 && vPy <= h - 10) {
        ctx.fillStyle = '#eab308';
        ctx.beginPath();
        ctx.arc(vPx, vPy, 5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.fillStyle = '#fde047';
        ctx.font = 'bold 10px sans-serif';
        ctx.fillText(`Đỉnh I(${quadInfo.vx.toFixed(1)}, ${quadInfo.vy.toFixed(1)})`, vPx + 8, vPy - 4);
      }

      // Các nghiệm (Giao điểm với Ox)
      quadInfo.roots.forEach((rx, idx) => {
        const rPx = cx + rx * scaleX;
        const rPy = cy;
        if (rPx >= 10 && rPx <= w - 10) {
          ctx.fillStyle = '#10b981';
          ctx.beginPath();
          ctx.arc(rPx, rPy, 5, 0, 2 * Math.PI);
          ctx.fill();
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1.5;
          ctx.stroke();

          ctx.fillStyle = '#34d399';
          ctx.font = 'bold 10px sans-serif';
          ctx.fillText(`x${idx + 1}=${rx.toFixed(1)}`, rPx - 10, rPy + 16);
        }
      });
    }
  };

  useEffect(() => {
    plot();
  }, [expr, xMin, xMax]);

  return (
    <div className="w-full h-full flex flex-col justify-between text-xs space-y-2">
      {/* Tiêu đề đồ thị */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5 shrink-0">
        <div>
          <span className="font-bold text-cyan-300 flex items-center gap-1.5 text-xs">
            {title}
          </span>
          {pedagogicalPurpose && (
            <p className="text-[10px] text-slate-400 mt-0.5">{pedagogicalPurpose}</p>
          )}
        </div>
        {analysis?.isQuadratic && (
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
            analysis.delta > 0
              ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
              : analysis.delta === 0
              ? 'bg-amber-950/80 text-amber-300 border-amber-800'
              : 'bg-rose-950/80 text-rose-300 border-rose-800'
          }`}>
            {analysis.delta > 0
              ? `Δ = ${analysis.delta.toFixed(1)} > 0 (2 nghiệm)`
              : analysis.delta === 0
              ? 'Δ = 0 (Nghiệm kép)'
              : `Δ = ${analysis.delta.toFixed(1)} < 0 (Vô nghiệm)`}
          </span>
        )}
      </div>

      {/* Canvas vẽ đồ thị */}
      <div className="flex-1 w-full min-h-[190px] bg-[#050a18] rounded-xl border border-slate-800 flex items-center justify-center relative overflow-hidden shadow-inner">
        <canvas
          ref={canvasRef}
          width={440}
          height={240}
          className="w-full h-full object-contain rounded"
        />
        <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-slate-900/80 backdrop-blur text-[10px] text-cyan-400 font-mono border border-slate-800">
          y = {expr}
        </div>
      </div>

      {/* Thông tin giải thích sư phạm & Biện luận nghiệm */}
      {analysis?.isQuadratic && (
        <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 flex items-center justify-between text-[11px] shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-amber-400 font-semibold">
              Đỉnh: <strong className="text-white">I({analysis.vx.toFixed(1)}, {analysis.vy.toFixed(1)})</strong>
            </span>
            <span className="text-emerald-400 font-semibold">
              Nghiệm Ox: <strong className="text-white">{analysis.roots.length > 0 ? analysis.roots.map(r => r.toFixed(1)).join(', ') : 'Không giao Ox'}</strong>
            </span>
          </div>
          <span className="text-[10px] text-slate-400 italic">
            *Nghiệm chính là hoành độ giao điểm với Ox
          </span>
        </div>
      )}

      {/* Bảng chọn hàm nhanh (chỉ hiện khi bật allowEdit) */}
      {allowEdit && !compact && (
        <div className="flex items-center gap-2 pt-1 border-t border-slate-800/80 shrink-0">
          <span className="text-[10px] text-slate-400 shrink-0">Đổi hàm số:</span>
          <select
            value={expr}
            onChange={(e) => setExpr(e.target.value)}
            className="flex-1 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-[11px] text-white focus:outline-none focus:border-cyan-500 font-mono"
          >
            {presets.map((p) => (
              <option key={p.val} value={p.val}>{p.label}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
