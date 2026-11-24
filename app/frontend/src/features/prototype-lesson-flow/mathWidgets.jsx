/**
 * PROTOTYPE, wipe me. Đồ thị, Bảng biến thiên, Hình Oxyz và Câu hỏi trắc nghiệm cho prototype giao diện.
 * Điểm của đồ thị lấy từ GRAPH_STUBS, đứng thay server (ADR 0006).
 */
import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import MathText from '../../shared/math/MathText';
import { BBT_STUBS, GRAPH_STUBS } from './mockLessons.js';

const vn = (n, digits = 2) => {
  const r = Math.round(n * 10 ** digits) / 10 ** digits;
  return String(Object.is(r, -0) ? 0 : r).replace('.', ',').replace('-', '−');
};

function niceStep(span) {
  const raw = span / 8;
  const p = 10 ** Math.floor(Math.log10(raw));
  const m = raw / p;
  return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p;
}

function ticks(min, max, step) {
  const out = [];
  for (let v = Math.ceil(min / step) * step; v <= max + 1e-9; v += step) out.push(Number(v.toFixed(10)));
  return out;
}

function useWheel(ref, enabled, onWheel) {
  useEffect(() => {
    const el = ref.current;
    if (!el || !enabled) return undefined;
    const handler = (e) => { e.preventDefault(); onWheel(e, el.getBoundingClientRect()); };
    el.addEventListener('wheel', handler, { passive: false });
    return () => el.removeEventListener('wheel', handler);
  }, [ref, enabled, onWheel]);
}

// Kích thước vùng vẽ theo đơn vị logic của slide (ResizeObserver không tính transform scale).
function useSize(ref, fallback) {
  const [size, setSize] = useState(fallback);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) setSize({ w: width, h: height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref]);
  return size;
}

function dragOnWindow(e, onMove, onEnd) {
  const start = { x: e.clientX, y: e.clientY };
  const move = (ev) => onMove(ev.clientX - start.x, ev.clientY - start.y);
  const up = () => {
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', up);
    onEnd?.();
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up);
}

export function GraphWidget({ visual, width, height, interactive = false, animate = false }) {
  const stub = GRAPH_STUBS[visual.data.expression];
  const { xMin, xMax, yMin, yMax } = visual.data;
  const base = useMemo(() => ({ xMin, xMax, yMin, yMax }), [xMin, xMax, yMin, yMax]);
  const [view, setView] = useState(base);
  const [show, setShow] = useState({ extrema: false, intercepts: false });
  const [hover, setHover] = useState(null);
  const [panning, setPanning] = useState(false);
  const svgRef = useRef(null);
  const plotRef = useRef(null);
  const { w: W, h: H } = useSize(plotRef, { w: width, h: interactive ? height - 70 : height });
  useEffect(() => setView(base), [base]);

  const X = (x) => ((x - view.xMin) / (view.xMax - view.xMin)) * W;
  const Y = (y) => H - ((y - view.yMin) / (view.yMax - view.yMin)) * H;

  const path = useMemo(() => {
    if (!stub) return '';
    const n = 520;
    const span = view.yMax - view.yMin;
    let d = '';
    let pen = false;
    for (let i = 0; i <= n; i += 1) {
      const x = view.xMin + ((view.xMax - view.xMin) * i) / n;
      const y = stub.fn(x);
      if (!Number.isFinite(y) || y > view.yMax + span * 4 || y < view.yMin - span * 4) { pen = false; continue; }
      d += `${pen ? 'L' : 'M'}${X(x).toFixed(1)},${Y(y).toFixed(1)}`;
      pen = true;
    }
    return d;
  }, [stub, view, W, H]);

  const zoomAt = (px, py, f) => setView((v) => {
    const cx = v.xMin + px * (v.xMax - v.xMin);
    const cy = v.yMax - py * (v.yMax - v.yMin);
    return { xMin: cx - (cx - v.xMin) * f, xMax: cx + (v.xMax - cx) * f, yMin: cy - (cy - v.yMin) * f, yMax: cy + (v.yMax - cy) * f };
  });
  const onWheel = useMemo(() => (e, r) => zoomAt((e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height, e.deltaY > 0 ? 1.12 : 1 / 1.12), []);
  useWheel(svgRef, interactive, onWheel);

  if (!stub) {
    return <div className="lf-pending"><strong>Chưa có dữ liệu mẫu cho biểu thức này</strong></div>;
  }

  const onPointerDown = (e) => {
    if (!interactive) return;
    e.stopPropagation();
    e.preventDefault();
    const r = svgRef.current.getBoundingClientRect();
    const startView = view;
    setPanning(true);
    setHover(null);
    dragOnWindow(e, (dx, dy) => {
      const wx = (dx / r.width) * (startView.xMax - startView.xMin);
      const wy = (dy / r.height) * (startView.yMax - startView.yMin);
      setView({ xMin: startView.xMin - wx, xMax: startView.xMax - wx, yMin: startView.yMin + wy, yMax: startView.yMax + wy });
    }, () => setPanning(false));
  };
  const onPointerMove = (e) => {
    if (!interactive || panning) return;
    const r = svgRef.current.getBoundingClientRect();
    const x = view.xMin + ((e.clientX - r.left) / r.width) * (view.xMax - view.xMin);
    const y = stub.fn(x);
    setHover(Number.isFinite(y) && y <= view.yMax && y >= view.yMin ? { x, y } : null);
  };

  const sx = niceStep(view.xMax - view.xMin);
  const sy = niceStep(view.yMax - view.yMin);
  const xs = ticks(view.xMin, view.xMax, sx);
  const ys = ticks(view.yMin, view.yMax, sy);
  const x0 = X(0);
  const y0 = Y(0);
  const hasYAxis = view.xMin < 0 && view.xMax > 0;
  const hasXAxis = view.yMin < 0 && view.yMax > 0;
  const arrow = `lf-ah-${visual.id}`;
  const clip = `lf-clip-${visual.id}`;
  const pointMark = (p, label, key) => (
    <g key={key} className="lf-graph-pt lf-fade">
      {hasXAxis && <line className="lf-graph-guide" x1={X(p.x)} x2={X(p.x)} y1={Y(p.y)} y2={y0} />}
      {hasYAxis && <line className="lf-graph-guide" x1={X(p.x)} x2={x0} y1={Y(p.y)} y2={Y(p.y)} />}
      <circle cx={X(p.x)} cy={Y(p.y)} r={9} />
      <text x={X(p.x) + 16} y={Y(p.y) - 16}>{label}</text>
    </g>
  );

  return (
    <div className={`lf-graph ${interactive ? 'is-interactive' : ''} ${panning ? 'is-panning' : ''}`}>
      {interactive && (
        <div className="lf-widget-tools" onPointerDown={(e) => e.stopPropagation()}>
          <button type="button" aria-pressed={show.extrema} onClick={() => setShow((s) => ({ ...s, extrema: !s.extrema }))}>Cực trị</button>
          <button type="button" aria-pressed={show.intercepts} onClick={() => setShow((s) => ({ ...s, intercepts: !s.intercepts }))}>Giao với trục</button>
          <button type="button" disabled={!stub.asymptotes} title={stub.asymptotes ? undefined : 'Hàm bậc ba không có tiệm cận'}>Tiệm cận</button>
          <button type="button" aria-label="Phóng to" onClick={() => zoomAt(0.5, 0.5, 1 / 1.25)}>+</button>
          <button type="button" aria-label="Thu nhỏ" onClick={() => zoomAt(0.5, 0.5, 1.25)}>−</button>
          <button type="button" onClick={() => setView(base)}>Khung ban đầu</button>
        </div>
      )}
      <div ref={plotRef} className="lf-widget-plot">
      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerLeave={() => setHover(null)} role="img" aria-label={`Đồ thị hàm số y = ${visual.data.expression}`}>
        <defs>
          <marker id={arrow} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#000" /></marker>
          <clipPath id={clip}><rect width={W} height={H} /></clipPath>
        </defs>
        <g className="lf-graph-grid">
          {xs.map((x) => <line key={`gx${x}`} x1={X(x)} x2={X(x)} y1={0} y2={H} />)}
          {ys.map((y) => <line key={`gy${y}`} x1={0} x2={W} y1={Y(y)} y2={Y(y)} />)}
        </g>
        {hasXAxis && <line className="lf-graph-axis" x1={0} x2={W - 6} y1={y0} y2={y0} markerEnd={`url(#${arrow})`} />}
        {hasYAxis && <line className="lf-graph-axis" x1={x0} x2={x0} y1={H} y2={6} markerEnd={`url(#${arrow})`} />}
        {hasXAxis && xs.filter((x) => Math.abs(x) > 1e-9 && X(x) > 26 && X(x) < W - 40).map((x) => <text key={`tx${x}`} className="lf-graph-tick" x={X(x)} y={y0 + 32} textAnchor="middle">{vn(x)}</text>)}
        {hasYAxis && ys.filter((y) => Math.abs(y) > 1e-9 && Y(y) > 40 && Y(y) < H - 18).map((y) => <text key={`ty${y}`} className="lf-graph-tick" x={x0 - 12} y={Y(y) + 8} textAnchor="end">{vn(y)}</text>)}
        {hasXAxis && <text className="lf-graph-axislabel" x={W - 26} y={y0 - 18}>x</text>}
        {hasYAxis && <text className="lf-graph-axislabel" x={x0 + 16} y={34}>y</text>}
        {hasXAxis && hasYAxis && <text className="lf-graph-axislabel" x={x0 - 30} y={y0 + 34}>O</text>}
        <g clipPath={`url(#${clip})`}>
          <path d={path} className={`lf-graph-curve ${animate ? 'lf-draw' : ''}`} pathLength={animate ? 1 : undefined} />
          {show.extrema && stub.extrema.map((p, i) => pointMark(p, `${p.label} (${vn(p.x)}; ${vn(p.y)})`, `e${i}`))}
          {show.intercepts && stub.intercepts.map((p, i) => pointMark(p, `(${vn(p.x)}; ${vn(p.y)})`, `i${i}`))}
          {hover && (
            <g className="lf-graph-hover">
              <line x1={X(hover.x)} x2={X(hover.x)} y1={0} y2={H} />
              <circle cx={X(hover.x)} cy={Y(hover.y)} r={8} />
            </g>
          )}
        </g>
      </svg>
      {interactive && hover && <div className="lf-graph-readout">({vn(hover.x)}; {vn(hover.y)})</div>}
      </div>
    </div>
  );
}

export function BbtWidget({ visual, width: W, height: H, rows = 3, animate = false }) {
  const d = BBT_STUBS[visual.data.expression];
  if (!d) return <div className="lf-pending"><strong>Chưa hỗ trợ lập bảng cho hàm này</strong></div>;
  const labelW = 150;
  const h1 = H * 0.2;
  const h2 = H * 0.2;
  const n = d.xs.length;
  const left = labelW + 90;
  const right = W - 90;
  const colX = (i) => left + ((right - left) * i) / (n - 1);
  const signX = (k) => (k % 2 === 0 ? (colX(k / 2) + colX(k / 2 + 1)) / 2 : colX((k + 1) / 2));
  const valY = (at) => (at === 'high' ? h1 + h2 + 62 : H - 34);
  const arrow = `lf-bbt-ah-${visual.id}`;
  return (
    <svg className="lf-bbt" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Bảng biến thiên">
      <defs>
        <marker id={arrow} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#4f2bd9" /></marker>
      </defs>
      <rect x={1.5} y={1.5} width={W - 3} height={H - 3} className="lf-bbt-frame" />
      <line className="lf-bbt-line" x1={labelW} x2={labelW} y1={0} y2={H} />
      <line className="lf-bbt-line" x1={0} x2={W} y1={h1} y2={h1} />
      <line className="lf-bbt-line" x1={0} x2={W} y1={h1 + h2} y2={h1 + h2} />
      <text className="lf-bbt-label" x={labelW / 2} y={h1 / 2 + 13}>x</text>
      <text className="lf-bbt-label" x={labelW / 2} y={h1 + h2 / 2 + 13}>y′</text>
      <text className="lf-bbt-label" x={labelW / 2} y={h1 + h2 + (H - h1 - h2) / 2 + 13}>y</text>
      {rows >= 1 && (
        <g className={animate ? 'lf-fade' : ''}>
          {d.xs.map((x, i) => <text key={i} className="lf-bbt-val" x={colX(i)} y={h1 / 2 + 13}>{x}</text>)}
        </g>
      )}
      {rows >= 2 && (
        <g className={animate ? 'lf-fade' : ''}>
          {d.signs.map((s, k) => <text key={k} className={`lf-bbt-val ${s === '0' ? '' : 'lf-bbt-sign'}`} x={signX(k)} y={h1 + h2 / 2 + 13}>{s}</text>)}
        </g>
      )}
      {rows >= 3 && (
        <g>
          {d.values.map((v, i) => <text key={i} className={`lf-bbt-val ${animate ? 'lf-fade' : ''}`} x={colX(i)} y={valY(v.at)}>{v.v}</text>)}
          {d.values.slice(0, -1).map((v, i) => {
            const w = d.values[i + 1];
            const y1 = valY(v.at) + (v.at === 'high' ? 16 : -40);
            const y2 = valY(w.at) + (w.at === 'high' ? 16 : -40);
            return (
              <line
                key={i}
                className={`lf-bbt-arrow ${animate ? 'lf-draw' : ''}`}
                x1={colX(i) + 56} y1={y1} x2={colX(i + 1) - 56} y2={y2}
                pathLength={animate ? 1 : undefined}
                style={animate ? { animationDelay: `${0.15 + i * 0.4}s`, animationDuration: '0.6s' } : undefined}
                markerEnd={`url(#${arrow})`}
              />
            );
          })}
        </g>
      )}
    </svg>
  );
}

const PRESETS = {
  'Phối cảnh': { yaw: 4.36, pitch: 0.44 },
  'Từ trên': { yaw: 4.712, pitch: 1.55 },
  'Mặt trước': { yaw: 4.712, pitch: 0 }
};
const add = (a, b) => a.map((v, i) => v + b[i]);
const mul = (a, k) => a.map((v) => v * k);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unit = (a) => { const l = Math.hypot(...a); return a.map((v) => v / l); };

export function OxyzWidget({ visual, width, height, interactive = false }) {
  const [cam, setCam] = useState({ ...PRESETS['Phối cảnh'], zoom: 1 });
  const [hidden, setHidden] = useState({});
  const [labels, setLabels] = useState(true);
  const [proj, setProj] = useState(true);
  const svgRef = useRef(null);
  const plotRef = useRef(null);
  const { w: W, h: H } = useSize(plotRef, { w: width, h: interactive ? height - 130 : height });
  const onWheel = useMemo(() => (e) => setCam((c) => ({ ...c, zoom: Math.min(2.4, Math.max(0.5, c.zoom * (e.deltaY > 0 ? 0.92 : 1.08))) })), []);
  useWheel(svgRef, interactive, onWheel);

  const objects = visual.data.objects;
  const s = (Math.min(W, H) / 8.4) * cam.zoom;
  const cx = W * 0.42;
  const cy = H * 0.66;
  const P = ([x, y, z]) => {
    const c = Math.cos(cam.yaw);
    const sn = Math.sin(cam.yaw);
    const X1 = x * c - y * sn;
    const Y1 = x * sn + y * c;
    const up = Y1 * Math.sin(cam.pitch) + z * Math.cos(cam.pitch);
    return [cx + X1 * s, cy - up * s];
  };
  const seg = (a, b, className, extra = {}) => {
    const [x1, y1] = P(a);
    const [x2, y2] = P(b);
    return <line x1={x1} y1={y1} x2={x2} y2={y2} className={className} {...extra} />;
  };
  const onPointerDown = (e) => {
    if (!interactive) return;
    e.stopPropagation();
    e.preventDefault();
    const start = cam;
    dragOnWindow(e, (dx, dy) => setCam({ ...start, yaw: start.yaw - dx * 0.008, pitch: Math.min(1.55, Math.max(-0.1, start.pitch + dy * 0.006)) }));
  };

  const point = objects.find((o) => o.type === 'point');
  const vector = objects.find((o) => o.type === 'vector');
  const plane = objects.find((o) => o.type === 'plane');
  const axis = 4.6;
  const inkArrow = `lf-oxyz-ink-${visual.id}`;
  const violetArrow = `lf-oxyz-vio-${visual.id}`;

  let planeShape = null;
  if (plane && !hidden[plane.id]) {
    const n = unit(plane.n);
    const u = unit(cross(n, Math.abs(n[2]) < 0.9 ? [0, 0, 1] : [1, 0, 0]));
    const v = cross(n, u);
    const h = plane.size;
    const corner = (a, b) => add(plane.center, add(mul(u, a * h), mul(v, b * h)));
    const corners = [corner(1, 1), corner(1, -1), corner(-1, -1), corner(-1, 1)];
    const grid = [-0.5, 0, 0.5].map((t) => (
      <React.Fragment key={t}>
        {seg(corner(t, -1), corner(t, 1), 'lf-oxyz-planegrid')}
        {seg(corner(-1, t), corner(1, t), 'lf-oxyz-planegrid')}
      </React.Fragment>
    ));
    const [lx, ly] = P(corner(-1, 1));
    planeShape = (
      <g>
        <polygon className="lf-oxyz-plane" points={corners.map((c) => P(c).join(',')).join(' ')} />
        {grid}
        {labels && <text className="lf-oxyz-label lf-oxyz-label--violet" x={lx + 10} y={ly - 12}>{plane.svgLabel}</text>}
      </g>
    );
  }

  return (
    <div className={`lf-oxyz ${interactive ? 'is-interactive' : ''}`}>
      <div ref={plotRef} className="lf-widget-plot">
      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} onPointerDown={onPointerDown} role="img" aria-label="Hình Oxyz">
        <defs>
          <marker id={inkArrow} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#000" /></marker>
          <marker id={violetArrow} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#4f2bd9" /></marker>
        </defs>
        {planeShape}
        {seg([0, 0, 0], [axis, 0, 0], 'lf-oxyz-axis', { markerEnd: `url(#${inkArrow})` })}
        {seg([0, 0, 0], [0, axis, 0], 'lf-oxyz-axis', { markerEnd: `url(#${inkArrow})` })}
        {seg([0, 0, 0], [0, 0, axis], 'lf-oxyz-axis', { markerEnd: `url(#${inkArrow})` })}
        {[['x', [axis + 0.35, 0, 0]], ['y', [0, axis + 0.35, 0]], ['z', [0, 0, axis + 0.35]]].map(([name, p]) => {
          const [x, y] = P(p);
          return <text key={name} className="lf-oxyz-axislabel" x={x} y={y + 10} textAnchor="middle">{name}</text>;
        })}
        {(() => { const [x, y] = P([0, 0, 0]); return <text className="lf-oxyz-axislabel" x={x - 26} y={y + 30}>O</text>; })()}
        {point && proj && !hidden[point.id] && (
          <g className="lf-oxyz-proj">
            {seg(point.p, [point.p[0], point.p[1], 0])}
            {seg([point.p[0], point.p[1], 0], [point.p[0], 0, 0])}
            {seg([point.p[0], point.p[1], 0], [0, point.p[1], 0])}
            {seg(point.p, [0, 0, point.p[2]])}
          </g>
        )}
        {vector && !hidden[vector.id] && (() => {
          const tip = add(vector.from, mul(vector.d, 0.75));
          const [tx, ty] = P(tip);
          return (
            <g>
              {seg(vector.from, tip, 'lf-oxyz-vector', { markerEnd: `url(#${violetArrow})` })}
              {labels && (
                <g className="lf-oxyz-label lf-oxyz-label--violet">
                  <text x={tx + 14} y={ty + 6}>{vector.svgLabel}</text>
                  <text x={tx + 12} y={ty - 22} className="lf-oxyz-vecbar">→</text>
                </g>
              )}
            </g>
          );
        })()}
        {point && !hidden[point.id] && (() => {
          const [x, y] = P(point.p);
          return (
            <g>
              <circle className="lf-oxyz-point" cx={x} cy={y} r={9} />
              {labels && <text className="lf-oxyz-label" x={x + 18} y={y + 40}>{point.svgLabel}</text>}
            </g>
          );
        })()}
      </svg>
      </div>
      {interactive && (
        <div className="lf-widget-tools" onPointerDown={(e) => e.stopPropagation()}>
          {Object.keys(PRESETS).map((name) => <button key={name} type="button" onClick={() => setCam((c) => ({ ...c, ...PRESETS[name] }))}>{name}</button>)}
          {objects.map((o) => <button key={o.id} type="button" aria-pressed={!hidden[o.id]} onClick={() => setHidden((h) => ({ ...h, [o.id]: !h[o.id] }))}>{o.toggleLabel}</button>)}
          <button type="button" aria-pressed={proj} onClick={() => setProj((v) => !v)}>Hình chiếu</button>
          <button type="button" aria-pressed={labels} onClick={() => setLabels((v) => !v)}>Nhãn</button>
        </div>
      )}
    </div>
  );
}

export function QuizWidget({ el, interactive = false }) {
  const [counts, setCounts] = useState({});
  const [revealed, setRevealed] = useState(false);
  const total = Object.values(counts).reduce((s, v) => s + v, 0);
  const bump = (label, delta) => setCounts((c) => ({ ...c, [label]: Math.max(0, (c[label] || 0) + delta) }));
  return (
    <div className="lf-quiz" onPointerDown={(e) => interactive && e.stopPropagation()}>
      <p className="lf-quiz-q"><MathText text={el.question} /></p>
      <ol className="lf-quiz-opts">
        {el.options.map((o) => (
          <li key={o.label} className={`lf-quiz-opt ${revealed ? (o.correct ? 'is-correct' : 'is-wrong') : ''}`}>
            <span className="lf-quiz-letter">{o.label}</span>
            <span className="lf-quiz-text"><MathText text={o.text} /></span>
            {interactive && (
              <span className="lf-quiz-count">
                <button type="button" aria-label={`Bớt một phiếu cho ${o.label}`} onClick={() => bump(o.label, -1)}>−</button>
                <output>{counts[o.label] || 0}</output>
                <button type="button" aria-label={`Thêm một phiếu cho ${o.label}`} onClick={() => bump(o.label, 1)}>+</button>
              </span>
            )}
            {revealed && <span className="lf-quiz-why"><MathText text={o.why} /></span>}
            {revealed && <span className="lf-quiz-bar" style={{ '--share': total ? (counts[o.label] || 0) / total : 0 }} />}
          </li>
        ))}
      </ol>
      {interactive && (
        <div className="lf-quiz-actions">
          <button type="button" className="lf-btn lf-btn--primary lf-btn--slide" onClick={() => setRevealed((v) => !v)}>{revealed ? 'Ẩn đáp án' : 'Hiện đáp án'}</button>
          <span className="lf-quiz-total">{total} phiếu</span>
        </div>
      )}
    </div>
  );
}
