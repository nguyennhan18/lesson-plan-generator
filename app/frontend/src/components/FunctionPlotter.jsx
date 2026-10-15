import React, { useState, useEffect, useRef } from 'react';

/**
 * FunctionPlotter - 2D Cartesian Function Plotter
 * Real-time math curve evaluator and renderer on Cartesian coordinate system (Oxy).
 */
export default function FunctionPlotter({ defaultExpr = 'x**3 - 3*x' }) {
  const [expr, setExpr] = useState(defaultExpr);
  const [xMin, setXMin] = useState(-4);
  const [xMax, setXMax] = useState(4);
  const canvasRef = useRef(null);

  const presets = [
    { label: 'Bậc ba: y = x³ - 3x', val: 'x**3 - 3*x' },
    { label: 'Bậc hai: y = x² - 4', val: 'x**2 - 4' },
    { label: 'Bậc nhất: y = 2x', val: '2*x' },
    { label: 'Lượng giác: y = sin(x)', val: 'sin(x)' },
    { label: 'Phân thức: y = 1/x', val: '1/x' }
  ];

  const plot = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    // 1. Clear & Background
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#060a14';
    ctx.fillRect(0, 0, w, h);

    // 2. Grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.lineWidth = 1;
    const step = 24;
    for (let x = 0; x < w; x += step) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }
    for (let y = 0; y < h; y += step) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // 3. Axes
    const cx = w / 2;
    const cy = h / 2;
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(w, cy); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(cx, 0); ctx.lineTo(cx, h); ctx.stroke();

    // Axis labels
    ctx.fillStyle = '#38bdf8';
    ctx.font = '10px monospace';
    ctx.fillText('x', w - 12, cy - 6);
    ctx.fillText('y', cx + 6, 12);
    ctx.fillText('O', cx - 12, cy + 12);

    // 4. Plot expression
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 2.5;
    ctx.beginPath();

    const scaleX = (w * 0.45) / Math.max(Math.abs(xMin), Math.abs(xMax));
    const scaleY = 22;
    let first = true;

    for (let px = 0; px < w; px += 2) {
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
      if (py < -50 || py > h + 50) {
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
  };

  useEffect(() => {
    plot();
  }, [expr, xMin, xMax]);

  return (
    <div className="space-y-2 text-xs">
      <div>
        <label className="text-slate-400 block mb-1">Hàm số mẫu:</label>
        <select
          value={expr}
          onChange={(e) => setExpr(e.target.value)}
          className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5 text-white focus:outline-none focus:border-cyan-500"
        >
          {presets.map((p) => (
            <option key={p.val} value={p.val}>{p.label}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="text-slate-400 block mb-1">Biểu thức f(x):</label>
        <input
          type="text"
          value={expr}
          onChange={(e) => setExpr(e.target.value)}
          className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-white font-mono focus:outline-none focus:border-cyan-500"
          placeholder="x**3 - 3*x"
        />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="text-slate-400 block mb-0.5">x min:</label>
          <input
            type="number"
            value={xMin}
            onChange={(e) => setXMin(parseFloat(e.target.value) || -4)}
            className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white"
          />
        </div>
        <div>
          <label className="text-slate-400 block mb-0.5">x max:</label>
          <input
            type="number"
            value={xMax}
            onChange={(e) => setXMax(parseFloat(e.target.value) || 4)}
            className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white"
          />
        </div>
      </div>

      <div className="bg-[#060a14] p-1.5 rounded-lg border border-slate-800 flex justify-center">
        <canvas ref={canvasRef} width={270} height={150} className="rounded" />
      </div>

      <button
        type="button"
        onClick={plot}
        className="w-full py-1.5 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white rounded font-medium shadow-md shadow-cyan-900/20"
      >
        🎨 Vẽ Lại Đồ Thị Tức Thì
      </button>
    </div>
  );
}
