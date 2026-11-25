/**
 * Interactive Math Visuals & Confirmation Forms for Bàn làm việc (#51–#57):
 * - GraphFigure (#51, #52, #56, #57): server-sampled SVG plot, pan/zoom, hover (x; y), shaded area [a; b],
 *   and verified special points (Cực trị, Giao với trục, Tiệm cận) through Cổng toán.
 * - BbtFigure (#55): 3-row Bảng biến thiên (x, y', y) with 3-step progressive reveal in presentation mode.
 * - SpaceFigure (#53, #54): interactive 3D viewer for Khối đa diện (cube, square_pyramid_regular, square_pyramid_at_a
 *   with hidden dashed edges and Khai triển net) and Hình Oxyz (point, vector, line, plane, sphere with dashed projections).
 * - VisualConfirmForm & AddVisualForm (#51, #53, #54, #55, #56): confirmation forms bound to project_id + item_id.
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import MathText from '../../shared/math/MathText';
import { postJson } from '../../shared/api/client.js';
import { VISUAL_KIND_NAMES } from '../../shared/storage/lessonProject.js';

const graphCache = new Map();
const graphInflight = new Map();
const bbtCache = new Map();
const bbtInflight = new Map();
const sceneCache = new Map();
const sceneInflight = new Map();

export function formatVnCoord(num, digits = 2) {
  if (!Number.isFinite(num)) return '';
  const rounded = Math.abs(num - Math.round(num)) < 1e-6 ? String(Math.round(num)) : num.toFixed(digits).replace(/\.?0+$/, '').replace('.', ',');
  return rounded.replace('-', '−');
}

const SOLID_KIND_LABELS = {
  cube: "Hình lập phương ABCD.A'B'C'D'",
  square_pyramid_regular: 'Chóp tứ giác đều S.ABCD',
  square_pyramid_at_a: 'Chóp S.ABCD có SA ⊥ (ABCD)',
};

const BBT_FAMILY_NAMES = {
  cubic: 'Hàm bậc ba',
  rational_1_1: 'Phân thức bậc nhất trên bậc nhất',
  rational_2_1: 'Phân thức bậc hai trên bậc nhất',
};

export function detectClientBbtFamily(expression = '') {
  const s = String(expression || '').replace(/\s+/g, '');
  if (!s) return 'Chưa nhập biểu thức';
  if (s.includes('/')) {
    if (/x\^2|x\*\*2/.test(s.split('/')[0])) return BBT_FAMILY_NAMES.rational_2_1;
    return BBT_FAMILY_NAMES.rational_1_1;
  }
  if (/x\^3|x\*\*3/.test(s)) return BBT_FAMILY_NAMES.cubic;
  return 'Chưa hỗ trợ lập bảng';
}

/* ============================================================================
 * 1. ĐỒ THỊ HÀM SỐ TƯƠNG TÁC (#51, #52, #56, #57)
 * ========================================================================== */
export function GraphFigure({ lesson, slide, visual, mode }) {
  const initialXMin = Number(visual.data?.x_min ?? -4);
  const initialXMax = Number(visual.data?.x_max ?? 4);
  const initialYMin = visual.data?.y_min != null && visual.data?.y_min !== '' ? Number(visual.data.y_min) : null;
  const initialYMax = visual.data?.y_max != null && visual.data?.y_max !== '' ? Number(visual.data.y_max) : null;

  const [viewport, setViewport] = useState({
    xMin: initialXMin,
    xMax: initialXMax,
    yMin: initialYMin,
    yMax: initialYMax,
    isInitial: true,
  });
  const [sample, setSample] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [hoverPt, setHoverPt] = useState(null);
  const [showExtrema, setShowExtrema] = useState(false);
  const [showIntercepts, setShowIntercepts] = useState(false);
  const [showAsymptotes, setShowAsymptotes] = useState(false);

  const svgRef = useRef(null);
  const panRef = useRef(null);
  const debounceRef = useRef(null);
  const abortRef = useRef(null);

  const fetchSample = useCallback((vp, immediate = false) => {
    if (!visual?.requirement_token || !lesson?.project_id || !slide?.item_id) return;
    const cacheKey = JSON.stringify({
      token: visual.requirement_token,
      xMin: Number(vp.xMin.toFixed(4)),
      xMax: Number(vp.xMax.toFixed(4)),
      yMin: vp.yMin != null ? Number(vp.yMin.toFixed(4)) : null,
      yMax: vp.yMax != null ? Number(vp.yMax.toFixed(4)) : null,
    });
    if (graphCache.has(cacheKey)) {
      setSample(graphCache.get(cacheKey));
      setError('');
      return;
    }

    const runFetch = async () => {
      setLoading(true);
      try {
        let promise = graphInflight.get(cacheKey);
        if (!promise) {
          const payload = {
            ...visual.data,
            kind: 'graph',
            project_id: lesson.project_id,
            item_id: slide.item_id,
            requirement_token: visual.requirement_token,
            viewport_x_min: vp.xMin,
            viewport_x_max: vp.xMax,
            ...(vp.yMin != null && vp.yMax != null ? { viewport_y_min: vp.yMin, viewport_y_max: vp.yMax } : {}),
          };
          promise = postJson('/api/v1/visuals/graph/sample', payload).then(async res => {
            const data = await res.json();
            if (!res.ok) {
              throw new Error(data.detail?.message || 'Không lấy được mẫu đồ thị.');
            }
            graphCache.set(cacheKey, data);
            return data;
          }).finally(() => {
            graphInflight.delete(cacheKey);
          });
          graphInflight.set(cacheKey, promise);
        }
        const data = await promise;
        setSample(data);
        setError('');
      } catch (err) {
        if (err.name === 'AbortError') return;
        setError(err.message || 'Không kết nối được máy chủ để lấy mẫu đồ thị.');
      } finally {
        setLoading(false);
      }
    };

    clearTimeout(debounceRef.current);
    if (immediate) {
      runFetch();
    } else {
      debounceRef.current = setTimeout(runFetch, 110);
    }
  }, [visual, lesson?.project_id, slide?.item_id]);

  useEffect(() => {
    const initVp = {
      xMin: Number(visual.data?.x_min ?? -4),
      xMax: Number(visual.data?.x_max ?? 4),
      yMin: visual.data?.y_min != null && visual.data?.y_min !== '' ? Number(visual.data.y_min) : null,
      yMax: visual.data?.y_max != null && visual.data?.y_max !== '' ? Number(visual.data.y_max) : null,
      isInitial: true,
    };
    setViewport(initVp);
    fetchSample(initVp, true);
    return () => {
      clearTimeout(debounceRef.current);
      abortRef.current?.abort();
    };
  }, [visual.requirement_token, visual.data, fetchSample]);

  const W = 760;
  const H = 520;
  const PAD = 44;
  const plotW = W - PAD * 2;
  const plotH = H - PAD * 2;

  const xMin = sample?.x_min ?? viewport.xMin;
  const xMax = sample?.x_max ?? viewport.xMax;
  const yMin = sample?.y_min ?? viewport.yMin ?? -4;
  const yMax = sample?.y_max ?? viewport.yMax ?? 4;

  const toSvgX = x => PAD + ((x - xMin) / Math.max(1e-9, xMax - xMin)) * plotW;
  const toSvgY = y => PAD + plotH - ((y - yMin) / Math.max(1e-9, yMax - yMin)) * plotH;
  const fromSvgX = px => xMin + ((px - PAD) / plotW) * (xMax - xMin);
  const fromSvgY = py => yMin + ((PAD + plotH - py) / plotH) * (yMax - yMin);

  const zoom = factor => {
    const cx = (xMin + xMax) / 2;
    const cy = (yMin + yMax) / 2;
    const halfX = Math.max(0.25, ((xMax - xMin) / 2) * factor);
    const halfY = Math.max(0.25, ((yMax - yMin) / 2) * factor);
    const next = { xMin: cx - halfX, xMax: cx + halfX, yMin: cy - halfY, yMax: cy + halfY, isInitial: false };
    setViewport(next);
    fetchSample(next, false);
  };

  const resetViewport = () => {
    const initVp = {
      xMin: initialXMin,
      xMax: initialXMax,
      yMin: initialYMin,
      yMax: initialYMax,
      isInitial: true,
    };
    setViewport(initVp);
    fetchSample(initVp, true);
  };

  const onPointerDown = event => {
    if (mode !== 'present' || event.button !== 0) return;
    event.stopPropagation();
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    panRef.current = {
      startX: event.clientX,
      startY: event.clientY,
      rectW: rect.width,
      rectH: rect.height,
      origXMin: xMin,
      origXMax: xMax,
      origYMin: yMin,
      origYMax: yMax,
    };
  };

  const onPointerMove = event => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    const localX = ((event.clientX - rect.left) / Math.max(1, rect.width)) * W;
    const localY = ((event.clientY - rect.top) / Math.max(1, rect.height)) * H;
    if (localX >= PAD && localX <= W - PAD && localY >= PAD && localY <= H - PAD) {
      setHoverPt({ x: fromSvgX(localX), y: fromSvgY(localY), svgX: localX, svgY: localY });
    } else {
      setHoverPt(null);
    }
    if (!panRef.current || mode !== 'present') return;
    const dxPx = ((event.clientX - panRef.current.startX) / Math.max(1, panRef.current.rectW)) * W;
    const dyPx = ((event.clientY - panRef.current.startY) / Math.max(1, panRef.current.rectH)) * H;
    const spanX = panRef.current.origXMax - panRef.current.origXMin;
    const spanY = panRef.current.origYMax - panRef.current.origYMin;
    const shiftX = -(dxPx / plotW) * spanX;
    const shiftY = (dyPx / plotH) * spanY;
    const next = {
      xMin: panRef.current.origXMin + shiftX,
      xMax: panRef.current.origXMax + shiftX,
      yMin: panRef.current.origYMin + shiftY,
      yMax: panRef.current.origYMax + shiftY,
      isInitial: false,
    };
    setViewport(next);
    fetchSample(next, false);
  };

  const onPointerUp = () => {
    panRef.current = null;
  };

  const onWheel = event => {
    if (mode !== 'present') return;
    event.preventDefault();
    event.stopPropagation();
    zoom(event.deltaY > 0 ? 1.2 : 0.8);
  };

  const sp = sample?.special_points;
  const asympInfo = sp?.asymptotes;
  const asympDisabled = Boolean(asympInfo && asympInfo.supported && !asympInfo.has_asymptotes);

  const axisX0 = Math.max(PAD, Math.min(W - PAD, toSvgX(0)));
  const axisY0 = Math.max(PAD, Math.min(H - PAD, toSvgY(0)));

  return (
    <div className="wb-graph-widget" data-testid="wb-graph-widget">
      <div className="wb-graph-head">
        <span className="wb-s-figure-kind">Đồ thị hàm số</span>
        {visual.label ? <MathText text={visual.label} /> : <code className="wb-s-figure-expr">y = {visual.data?.expression}</code>}
        {hoverPt && mode === 'present' && (
          <span className="wb-graph-coords" data-testid="wb-graph-coords">
            ({formatVnCoord(hoverPt.x)}; {formatVnCoord(hoverPt.y)})
          </span>
        )}
      </div>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        className="wb-graph-svg"
        role="img"
        aria-label={`Đồ thị hàm số y = ${visual.data?.expression || ''}`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={() => { panRef.current = null; setHoverPt(null); }}
        onWheel={onWheel}
      >
        <defs>
          <clipPath id={`clip-${visual.visual_id}`}>
            <rect x={PAD} y={PAD} width={plotW} height={plotH} />
          </clipPath>
        </defs>

        {/* Lưới tọa độ */}
        {[-3, -2, -1, 0, 1, 2, 3].map(tick => {
          const tx = xMin + ((tick + 3) / 6) * (xMax - xMin);
          const ty = yMin + ((tick + 3) / 6) * (yMax - yMin);
          const sx = toSvgX(tx);
          const sy = toSvgY(ty);
          return (
            <g key={tick}>
              <line x1={sx} y1={PAD} x2={sx} y2={H - PAD} stroke="#e8e8e8" strokeWidth="1" />
              <line x1={PAD} y1={sy} x2={W - PAD} y2={sy} stroke="#e8e8e8" strokeWidth="1" />
              <text x={sx} y={H - PAD + 18} textAnchor="middle" fontSize="14" fill="#6e6e6e">{formatVnCoord(tx, 1)}</text>
              <text x={PAD - 8} y={sy + 4} textAnchor="end" fontSize="14" fill="#6e6e6e">{formatVnCoord(ty, 1)}</text>
            </g>
          );
        })}

        {/* Trục Ox, Oy */}
        <line x1={PAD} y1={axisY0} x2={W - PAD} y2={axisY0} stroke="#000000" strokeWidth="1.6" />
        <line x1={axisX0} y1={PAD} x2={axisX0} y2={H - PAD} stroke="#000000" strokeWidth="1.6" />
        <text x={W - PAD + 12} y={axisY0 + 5} fontSize="16" fontWeight="600">x</text>
        <text x={axisX0 + 8} y={PAD - 10} fontSize="16" fontWeight="600">y</text>
        <text x={axisX0 - 14} y={axisY0 + 18} fontSize="15" fill="#6e6e6e">O</text>

        <g clipPath={`url(#clip-${visual.visual_id})`}>
          {/* Miền tô diện tích (#56) */}
          {(sample?.area_polygons || []).map((poly, pIdx) => {
            const pts = poly.map(([px, py]) => `${toSvgX(px)},${toSvgY(py)}`).join(' ');
            return <polygon key={`area-${pIdx}`} points={pts} className="wb-graph-area" data-testid="wb-graph-area" />;
          })}

          {/* Đường cong thứ hai (nếu miền tô giới hạn bởi hai đồ thị #56) */}
          {(sample?.second_segments || []).map((seg, sIdx) => {
            if (seg.length < 2) return null;
            const d = seg.map(([px, py], i) => `${i === 0 ? 'M' : 'L'}${toSvgX(px)},${toSvgY(py)}`).join(' ');
            return <path key={`sec-${sIdx}`} d={d} fill="none" stroke="#111111" strokeWidth="2.2" strokeDasharray="6 4" />;
          })}

          {/* Đường tiệm cận đã chứng minh (#57) */}
          {showAsymptotes && asympInfo?.supported && (asympInfo.items || []).filter(it => it.status === 'verified').map(item => {
            if (item.kind === 'vertical') {
              const sx = toSvgX(item.x);
              return (
                <g key={item.id} data-testid="wb-graph-asymptote">
                  <line x1={sx} y1={PAD} x2={sx} y2={H - PAD} stroke="#4f2bd9" strokeWidth="1.8" strokeDasharray="7 5" />
                  <text x={sx + 8} y={PAD + 24} fontSize="15" fontWeight="600" fill="#4f2bd9">{item.equation}</text>
                </g>
              );
            }
            const y1 = item.slope * xMin + item.intercept;
            const y2 = item.slope * xMax + item.intercept;
            return (
              <g key={item.id} data-testid="wb-graph-asymptote">
                <line x1={toSvgX(xMin)} y1={toSvgY(y1)} x2={toSvgX(xMax)} y2={toSvgY(y2)} stroke="#4f2bd9" strokeWidth="1.8" strokeDasharray="7 5" />
                <text x={W - PAD - 120} y={toSvgY(y2) - 8} fontSize="15" fontWeight="600" fill="#4f2bd9">{item.equation}</text>
              </g>
            );
          })}

          {/* Các nhánh đồ thị hàm số (#51, #52) */}
          {(sample?.segments || []).map((seg, idx) => {
            if (seg.length < 2) return null;
            const d = seg.map(([px, py], i) => `${i === 0 ? 'M' : 'L'}${toSvgX(px)},${toSvgY(py)}`).join(' ');
            return <path key={idx} d={d} className="wb-graph-curve" data-testid="wb-graph-curve" />;
          })}

          {/* Điểm cực trị đã chứng minh qua Cổng toán (#57) */}
          {showExtrema && sp?.extrema?.supported && (sp.extrema.items || []).filter(pt => pt.status === 'verified').map(pt => {
            const sx = toSvgX(pt.x);
            const sy = toSvgY(pt.y);
            return (
              <g key={pt.id} data-testid="wb-graph-extremum">
                <line x1={sx} y1={sy} x2={sx} y2={axisY0} stroke="#6e6e6e" strokeWidth="1.3" strokeDasharray="4 4" />
                <line x1={sx} y1={sy} x2={axisX0} y2={sy} stroke="#6e6e6e" strokeWidth="1.3" strokeDasharray="4 4" />
                <circle cx={sx} cy={sy} r="5.5" fill="#4f2bd9" stroke="#ffffff" strokeWidth="1.5" />
                <text x={sx + 8} y={sy - 10} fontSize="16" fontWeight="600" fill="#000000">{pt.display}</text>
              </g>
            );
          })}

          {/* Giao điểm với trục đã chứng minh qua Cổng toán (#57) */}
          {showIntercepts && sp?.intercepts?.supported && (sp.intercepts.items || []).filter(pt => pt.status === 'verified').map(pt => {
            const sx = toSvgX(pt.x);
            const sy = toSvgY(pt.y);
            return (
              <g key={pt.id} data-testid="wb-graph-intercept">
                <circle cx={sx} cy={sy} r="5" fill="#000000" stroke="#ffffff" strokeWidth="1.5" />
                <text x={sx + 8} y={sy + 18} fontSize="15" fontWeight="600" fill="#000000">{pt.display}</text>
              </g>
            );
          })}
        </g>
      </svg>

      {error && <p role="alert" className="wb-error-text">{error}</p>}
      {showExtrema && sp?.extrema && !sp.extrema.supported && (
        <p role="status" className="wb-meta">Cực trị: chưa hỗ trợ ({sp.extrema.unsupported_reason})</p>
      )}
      {showIntercepts && sp?.intercepts && !sp.intercepts.supported && (
        <p role="status" className="wb-meta">Giao với trục: chưa hỗ trợ ({sp.intercepts.unsupported_reason})</p>
      )}
      {showAsymptotes && asympInfo && !asympInfo.supported && (
        <p role="status" className="wb-meta">Tiệm cận: chưa hỗ trợ ({asympInfo.unsupported_reason})</p>
      )}

      {mode === 'present' && (
        <div className="wb-graph-bar" role="toolbar" aria-label="Điều khiển đồ thị" onPointerDown={e => e.stopPropagation()}>
          <button type="button" className="wb-btn" onClick={() => zoom(0.8)} aria-label="Phóng to">+</button>
          <button type="button" className="wb-btn" onClick={() => zoom(1.25)} aria-label="Thu nhỏ">−</button>
          <button type="button" className="wb-btn" onClick={resetViewport}>Khung ban đầu</button>
          <button
            type="button"
            className="wb-btn"
            aria-pressed={showExtrema}
            onClick={() => setShowExtrema(v => !v)}
          >
            Cực trị
          </button>
          <button
            type="button"
            className="wb-btn"
            aria-pressed={showIntercepts}
            onClick={() => setShowIntercepts(v => !v)}
          >
            Giao với trục
          </button>
          <button
            type="button"
            className="wb-btn"
            aria-pressed={showAsymptotes}
            disabled={asympDisabled}
            title={asympDisabled ? asympInfo.disabled_reason : undefined}
            onClick={() => setShowAsymptotes(v => !v)}
          >
            Tiệm cận
          </button>
          {asympDisabled && <span className="wb-meta">{asympInfo.disabled_reason}</span>}
          {loading && <span className="wb-meta">Đang lấy mẫu…</span>}
        </div>
      )}
    </div>
  );
}

/* ============================================================================
 * 2. BẢNG BIẾN THIÊN (#55) — 3 bước hiện dần khi Trình chiếu (x -> y' -> y)
 * ========================================================================== */
export function BbtFigure({ lesson, slide, visual, mode, visibleParts = 3 }) {
  const [bbt, setBbt] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!visual?.requirement_token || !lesson?.project_id || !slide?.item_id) return;
    const key = visual.requirement_token;
    if (bbtCache.has(key)) {
      setBbt(bbtCache.get(key));
      setError('');
      return;
    }
    let active = true;
    let promise = bbtInflight.get(key);
    if (!promise) {
      promise = postJson('/api/v1/visuals/bbt', {
        ...visual.data,
        kind: 'bbt',
        project_id: lesson.project_id,
        item_id: slide.item_id,
        requirement_token: visual.requirement_token,
      }).then(async res => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail?.message || 'Không tính được Bảng biến thiên.');
        bbtCache.set(key, data);
        return data;
      }).finally(() => {
        bbtInflight.delete(key);
      });
      bbtInflight.set(key, promise);
    }
    promise
      .then(data => {
        if (active) {
          setBbt(data);
          setError('');
        }
      })
      .catch(err => {
        if (active) setError(err.message);
      });
    return () => { active = false; };
  }, [visual, lesson?.project_id, slide?.item_id]);

  if (error) return <p role="alert" className="wb-error-text">{error}</p>;
  if (!bbt) return <div className="wb-s-figure"><span className="wb-meta">Đang dựng Bảng biến thiên…</span></div>;

  const showX = visibleParts >= 1;
  const showYp = mode !== 'present' || visibleParts >= 2;
  const showY = mode !== 'present' || visibleParts >= 3;

  return (
    <div className="wb-bbt" data-testid="wb-bbt-widget">
      <div className="wb-graph-head">
        <span className="wb-s-figure-kind">Bảng biến thiên ({bbt.family_label})</span>
        {visual.label ? <MathText text={visual.label} /> : <MathText text={`$y = ${bbt.expression}$`} />}
      </div>
      <table className="wb-bbt-table" aria-label="Bảng biến thiên">
        <tbody>
          {showX && (
            <tr data-testid="wb-bbt-row-x">
              <th scope="row"><MathText text="$x$" /></th>
              {bbt.x_row.map((cell, idx) => (
                <React.Fragment key={idx}>
                  <td className="wb-bbt-cell"><MathText text={`$${cell}$`} /></td>
                  {idx < bbt.x_row.length - 1 && <td className="wb-bbt-spacer" />}
                </React.Fragment>
              ))}
            </tr>
          )}
          {showYp && (
            <tr data-testid="wb-bbt-row-yp">
              <th scope="row"><MathText text="$y'$" /></th>
              <td className="wb-bbt-cell" />
              {bbt.yp_row.map((cell, idx) => (
                <td key={idx} className={`wb-bbt-cell${cell === '||' ? ' wb-bbt-doublebar' : ''}`}>
                  {cell === '||' ? <span aria-label="Không xác định">||</span> : <strong>{cell}</strong>}
                </td>
              ))}
              <td className="wb-bbt-cell" />
            </tr>
          )}
          {showY && (
            <tr data-testid="wb-bbt-row-y" className="wb-bbt-yrow">
              <th scope="row"><MathText text="$y$" /></th>
              {bbt.intervals.map((interval, idx) => {
                const ev = bbt.events[idx];
                return (
                  <React.Fragment key={idx}>
                    {idx === 0 && (
                      <td className="wb-bbt-cell">
                        <MathText text={`$${interval.from}$`} />
                      </td>
                    )}
                    <td className="wb-bbt-arrow-cell">
                      <span className={`wb-bbt-arrow wb-bbt-arrow--${interval.direction}`} aria-label={interval.direction === 'up' ? 'Đồng biến' : 'Nghịch biến'}>
                        {interval.direction === 'up' ? '↗' : '↘'}
                      </span>
                    </td>
                    {ev ? (
                      ev.kind === 'pole' ? (
                        <td className="wb-bbt-cell wb-bbt-doublebar">
                          <span className="wb-bbt-lim-left"><MathText text={`$${ev.left_limit}$`} /></span>
                          <span aria-label="Tiệm cận đứng">||</span>
                          <span className="wb-bbt-lim-right"><MathText text={`$${ev.right_limit}$`} /></span>
                        </td>
                      ) : (
                        <td className="wb-bbt-cell">
                          <MathText text={`$${ev.y_label}$`} />
                        </td>
                      )
                    ) : (
                      <td className="wb-bbt-cell">
                        <MathText text={`$${interval.to}$`} />
                      </td>
                    )}
                  </React.Fragment>
                );
              })}
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

/* ============================================================================
 * 3. KHỐI ĐA DIỆN (#53) & HÌNH OXYZ (#54) — 3D Tương tác
 * ========================================================================== */
function project3D([x, y, z], yaw, pitch, scale, cx, cy) {
  const cosY = Math.cos(yaw), sinY = Math.sin(yaw);
  const cosP = Math.cos(pitch), sinP = Math.sin(pitch);
  const x1 = x * cosY - y * sinY;
  const y1 = x * sinY + y * cosY;
  const z1 = z;
  const screenX = cx + x1 * scale;
  const screenY = cy - (z1 * cosP - y1 * sinP) * scale;
  const depth = y1 * cosP + z1 * sinP;
  return [screenX, screenY, depth];
}

export function SpaceFigure({ lesson, slide, visual, mode }) {
  const [scene, setScene] = useState(null);
  const [error, setError] = useState('');
  const [angles, setAngles] = useState({ yaw: -0.65, pitch: 0.42, zoom: 1.0 });
  const [showHidden, setShowHidden] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [showProjections, setShowProjections] = useState(true);
  const [showUnfolded, setShowUnfolded] = useState(false);
  const [hiddenObjects, setHiddenObjects] = useState({});
  const dragRef = useRef(null);

  useEffect(() => {
    if (!visual?.requirement_token || !lesson?.project_id || !slide?.item_id) return;
    const key = visual.requirement_token;
    if (sceneCache.has(key)) {
      setScene(sceneCache.get(key));
      setError('');
      return;
    }
    let active = true;
    postJson('/api/v1/visuals/scene', {
      ...visual.data,
      kind: visual.kind === 'oxyz' ? 'oxyz' : 'solid',
      project_id: lesson.project_id,
      item_id: slide.item_id,
      requirement_token: visual.requirement_token,
    })
      .then(async res => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail?.message || 'Không dựng được mô hình 3D.');
        if (active) {
          sceneCache.set(key, data);
          setScene(data);
          setError('');
        }
      })
      .catch(err => {
        if (active) setError(err.message);
      });
    return () => { active = false; };
  }, [visual, lesson?.project_id, slide?.item_id]);

  const setPreset = preset => {
    if (preset === 'top') setAngles(a => ({ ...a, yaw: 0, pitch: 1.48 }));
    else if (preset === 'front') setAngles(a => ({ ...a, yaw: 0, pitch: 0.08 }));
    else setAngles({ yaw: -0.65, pitch: 0.42, zoom: 1.0 });
  };

  const onPointerDown = event => {
    if (event.button !== 0) return;
    if (mode === 'present') event.stopPropagation();
    dragRef.current = { x: event.clientX, y: event.clientY, yaw: angles.yaw, pitch: angles.pitch };
  };

  const onPointerMove = event => {
    if (!dragRef.current) return;
    const dx = (event.clientX - dragRef.current.x) * 0.01;
    const dy = (event.clientY - dragRef.current.y) * 0.01;
    setAngles(a => ({
      ...a,
      yaw: dragRef.current.yaw + dx,
      pitch: Math.max(-1.4, Math.min(1.4, dragRef.current.pitch + dy)),
    }));
  };

  const onPointerUp = () => { dragRef.current = null; };

  if (error) return <p role="alert" className="wb-error-text">{error}</p>;
  if (!scene) return <div className="wb-s-figure"><span className="wb-meta">Đang dựng hình không gian…</span></div>;

  const W = 740, H = 480;
  const isOxyz = visual.kind === 'oxyz' || scene.kind === 'oxyz';

  return (
    <div className="wb-space-widget" data-testid={`wb-${visual.kind}-widget`}>
      <div className="wb-graph-head">
        <span className="wb-s-figure-kind">{VISUAL_KIND_NAMES[visual.kind]}</span>
        {visual.label && <MathText text={visual.label} />}
        {!isOxyz && scene.spec && (
          <span className="wb-meta">
            {SOLID_KIND_LABELS[scene.spec.polyhedron_type] || scene.spec.polyhedron_type} · a = {formatVnCoord(scene.spec.base_edge)}, h = {formatVnCoord(scene.spec.height)}
          </span>
        )}
      </div>

      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="wb-space-svg"
        role="img"
        aria-label={VISUAL_KIND_NAMES[visual.kind]}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
      >
        {!isOxyz && showUnfolded ? (
          /* Khai triển 2D của khối đa diện (#53) */
          <g data-testid="wb-solid-unfolded">
            <rect x="270" y="170" width="140" height="140" fill="rgba(79,43,217,0.12)" stroke="#4f2bd9" strokeWidth="2" />
            <rect x="130" y="170" width="140" height="140" fill="rgba(79,43,217,0.08)" stroke="#4f2bd9" strokeWidth="2" strokeDasharray="4 3" />
            <rect x="410" y="170" width="140" height="140" fill="rgba(79,43,217,0.08)" stroke="#4f2bd9" strokeWidth="2" strokeDasharray="4 3" />
            <rect x="270" y="30" width="140" height="140" fill="rgba(79,43,217,0.08)" stroke="#4f2bd9" strokeWidth="2" strokeDasharray="4 3" />
            <rect x="270" y="310" width="140" height="140" fill="rgba(79,43,217,0.08)" stroke="#4f2bd9" strokeWidth="2" strokeDasharray="4 3" />
            {scene.spec?.polyhedron_type === 'cube' && (
              <rect x="550" y="170" width="140" height="140" fill="rgba(79,43,217,0.08)" stroke="#4f2bd9" strokeWidth="2" strokeDasharray="4 3" />
            )}
            <text x="340" y="245" textAnchor="middle" fontSize="16" fontWeight="600">Đáy ABCD</text>
          </g>
        ) : !isOxyz ? (
          /* Khối đa diện 3D với nét liền và nét đứt cho cạnh khuất (#53) */
          (() => {
            const a = scene.spec.base_edge;
            const h = scene.spec.height;
            const maxDim = Math.max(a, h, 1);
            const scale = (155 / maxDim) * angles.zoom;
            const cx = W / 2, cy = H / 2 + 30;
            const center = [a / 2, a / 2, h / 2];
            const proj = {};
            for (const [name, pt] of Object.entries(scene.vertices)) {
              proj[name] = project3D([pt[0] - center[0], pt[1] - center[1], pt[2] - center[2]], angles.yaw, angles.pitch, scale, cx, cy);
            }
            const backVertex = Object.entries(proj).reduce((best, cur) => (cur[1][2] > best[1][2] ? cur : best))[0];
            return (
              <g data-testid="wb-solid-3d">
                {scene.edges.map(([u, v], idx) => {
                  const isHiddenEdge = u === backVertex || v === backVertex;
                  if (isHiddenEdge && !showHidden) return null;
                  const p1 = proj[u], p2 = proj[v];
                  return (
                    <line
                      key={idx}
                      x1={p1[0]}
                      y1={p1[1]}
                      x2={p2[0]}
                      y2={p2[1]}
                      stroke="#4f2bd9"
                      strokeWidth="2.4"
                      strokeDasharray={isHiddenEdge ? '7 5' : undefined}
                    />
                  );
                })}
                {showLabels && Object.entries(proj).map(([name, [px, py]]) => (
                  <g key={name}>
                    <circle cx={px} cy={py} r="4" fill="#000000" />
                    <text x={px + 8} y={py - 8} fontSize="16" fontWeight="600">{name}</text>
                  </g>
                ))}
              </g>
            );
          })()
        ) : (
          /* Hệ trục tọa độ Oxyz và 5 loại đối tượng (#54) */
          (() => {
            const scale = 38 * angles.zoom;
            const cx = W / 2, cy = H / 2 + 20;
            const pO = project3D([0, 0, 0], angles.yaw, angles.pitch, scale, cx, cy);
            const pX = project3D([4.5, 0, 0], angles.yaw, angles.pitch, scale, cx, cy);
            const pY = project3D([0, 4.5, 0], angles.yaw, angles.pitch, scale, cx, cy);
            const pZ = project3D([0, 0, 4.2], angles.yaw, angles.pitch, scale, cx, cy);
            return (
              <g data-testid="wb-oxyz-3d">
                {/* 3 trục Ox, Oy, Oz */}
                <line x1={pO[0]} y1={pO[1]} x2={pX[0]} y2={pX[1]} stroke="#000000" strokeWidth="1.8" />
                <line x1={pO[0]} y1={pO[1]} x2={pY[0]} y2={pY[1]} stroke="#000000" strokeWidth="1.8" />
                <line x1={pO[0]} y1={pO[1]} x2={pZ[0]} y2={pZ[1]} stroke="#000000" strokeWidth="1.8" />
                <text x={pX[0] + 8} y={pX[1]} fontSize="15" fontWeight="600">x</text>
                <text x={pY[0] + 8} y={pY[1]} fontSize="15" fontWeight="600">y</text>
                <text x={pZ[0] + 8} y={pZ[1]} fontSize="15" fontWeight="600">z</text>
                <text x={pO[0] - 14} y={pO[1] + 14} fontSize="14" fill="#6e6e6e">O</text>

                {(scene.objects || []).map(obj => {
                  if (hiddenObjects[obj.id]) return null;
                  if (obj.type === 'point') {
                    const [x, y, z] = obj.coords;
                    const p = project3D([x, y, z], angles.yaw, angles.pitch, scale, cx, cy);
                    const pxy = project3D([x, y, 0], angles.yaw, angles.pitch, scale, cx, cy);
                    const px0 = project3D([x, 0, 0], angles.yaw, angles.pitch, scale, cx, cy);
                    const py0 = project3D([0, y, 0], angles.yaw, angles.pitch, scale, cx, cy);
                    return (
                      <g key={obj.id} data-testid={`wb-oxyz-point-${obj.label}`}>
                        {showProjections && (
                          <>
                            <line x1={p[0]} y1={p[1]} x2={pxy[0]} y2={pxy[1]} stroke="#6e6e6e" strokeWidth="1.2" strokeDasharray="4 4" />
                            <line x1={pxy[0]} y1={pxy[1]} x2={px0[0]} y2={px0[1]} stroke="#6e6e6e" strokeWidth="1.2" strokeDasharray="4 4" />
                            <line x1={pxy[0]} y1={pxy[1]} x2={py0[0]} y2={py0[1]} stroke="#6e6e6e" strokeWidth="1.2" strokeDasharray="4 4" />
                          </>
                        )}
                        <circle cx={p[0]} cy={p[1]} r="5" fill="#4f2bd9" />
                        {showLabels && (
                          <text x={p[0] + 8} y={p[1] - 8} fontSize="15" fontWeight="600">
                            {obj.label}({formatVnCoord(x)}; {formatVnCoord(y)}; {formatVnCoord(z)})
                          </text>
                        )}
                      </g>
                    );
                  }
                  if (obj.type === 'vector') {
                    const orig = obj.origin || [0, 0, 0];
                    const end = [orig[0] + obj.coords[0], orig[1] + obj.coords[1], orig[2] + obj.coords[2]];
                    const p1 = project3D(orig, angles.yaw, angles.pitch, scale, cx, cy);
                    const p2 = project3D(end, angles.yaw, angles.pitch, scale, cx, cy);
                    return (
                      <g key={obj.id} data-testid={`wb-oxyz-vector-${obj.label}`}>
                        <line x1={p1[0]} y1={p1[1]} x2={p2[0]} y2={p2[1]} stroke="#4f2bd9" strokeWidth="2.5" />
                        <circle cx={p2[0]} cy={p2[1]} r="4" fill="#4f2bd9" />
                        {showLabels && <text x={p2[0] + 8} y={p2[1] - 6} fontSize="15" fontWeight="600" fill="#4f2bd9">{obj.label}</text>}
                      </g>
                    );
                  }
                  if (obj.type === 'line') {
                    const [x0, y0, z0] = obj.point;
                    const [u1, u2, u3] = obj.direction;
                    const p1 = project3D([x0 - 2.5 * u1, y0 - 2.5 * u2, z0 - 2.5 * u3], angles.yaw, angles.pitch, scale, cx, cy);
                    const p2 = project3D([x0 + 2.5 * u1, y0 + 2.5 * u2, z0 + 2.5 * u3], angles.yaw, angles.pitch, scale, cx, cy);
                    return (
                      <g key={obj.id} data-testid={`wb-oxyz-line-${obj.label}`}>
                        <line x1={p1[0]} y1={p1[1]} x2={p2[0]} y2={p2[1]} stroke="#4f2bd9" strokeWidth="2" />
                        {showLabels && <text x={p2[0] + 6} y={p2[1]} fontSize="15" fontWeight="600" fill="#4f2bd9">{obj.label}</text>}
                      </g>
                    );
                  }
                  if (obj.type === 'plane') {
                    const [A, B, C, D] = obj.coeffs;
                    const corners = [[-2, -2], [2, -2], [2, 2], [-2, 2]].map(([u, v]) => {
                      if (Math.abs(C) > 1e-6) return [u, v, (-A * u - B * v - D) / C];
                      if (Math.abs(B) > 1e-6) return [u, (-A * u - C * v - D) / B, v];
                      return [(-B * u - C * v - D) / A, u, v];
                    });
                    const pts = corners.map(c => project3D(c, angles.yaw, angles.pitch, scale, cx, cy));
                    return (
                      <g key={obj.id} data-testid={`wb-oxyz-plane-${obj.label}`}>
                        <polygon
                          points={pts.map(p => `${p[0]},${p[1]}`).join(' ')}
                          fill="rgba(79, 43, 217, 0.14)"
                          stroke="#4f2bd9"
                          strokeWidth="1.5"
                        />
                        {showLabels && <text x={pts[0][0] + 8} y={pts[0][1] - 6} fontSize="15" fontWeight="600" fill="#4f2bd9">{obj.label}</text>}
                      </g>
                    );
                  }
                  if (obj.type === 'sphere') {
                    const pC = project3D(obj.center, angles.yaw, angles.pitch, scale, cx, cy);
                    const rPx = obj.radius * scale;
                    return (
                      <g key={obj.id} data-testid={`wb-oxyz-sphere-${obj.label}`}>
                        <circle cx={pC[0]} cy={pC[1]} r={rPx} fill="rgba(79, 43, 217, 0.10)" stroke="#4f2bd9" strokeWidth="1.8" />
                        <ellipse cx={pC[0]} cy={pC[1]} rx={rPx} ry={rPx * 0.35} fill="none" stroke="#4f2bd9" strokeWidth="1.2" strokeDasharray="5 4" />
                        {showLabels && <text x={pC[0] + 6} y={pC[1] - rPx - 6} fontSize="15" fontWeight="600" fill="#4f2bd9">{obj.label}</text>}
                      </g>
                    );
                  }
                  return null;
                })}
              </g>
            );
          })()
        )}
      </svg>

      {(mode === 'present' || mode === 'edit') && (
        <div className="wb-graph-bar" role="toolbar" aria-label="Điều khiển hình không gian" onPointerDown={e => e.stopPropagation()}>
          <button type="button" className="wb-btn" onClick={() => setPreset('iso')}>Phối cảnh</button>
          <button type="button" className="wb-btn" onClick={() => setPreset('top')}>Từ trên</button>
          <button type="button" className="wb-btn" onClick={() => setPreset('front')}>Mặt trước</button>
          <button type="button" className="wb-btn" aria-pressed={showLabels} onClick={() => setShowLabels(v => !v)}>Nhãn</button>
          {!isOxyz ? (
            <>
              <button type="button" className="wb-btn" aria-pressed={showHidden} onClick={() => setShowHidden(v => !v)}>Nét khuất</button>
              <button type="button" className="wb-btn" aria-pressed={showUnfolded} onClick={() => setShowUnfolded(v => !v)}>Khai triển</button>
            </>
          ) : (
            <>
              <button type="button" className="wb-btn" aria-pressed={showProjections} onClick={() => setShowProjections(v => !v)}>Hình chiếu</button>
              {(scene.objects || []).map(obj => (
                <button
                  key={obj.id}
                  type="button"
                  className="wb-btn"
                  aria-pressed={!hiddenObjects[obj.id]}
                  onClick={() => setHiddenObjects(prev => ({ ...prev, [obj.id]: !prev[obj.id] }))}
                >
                  {obj.label}
                </button>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}

/* ============================================================================
 * 4. BIỂU MẪU XÁC NHẬN DỮ KIỆN & THÊM YÊU CẦU TRỰC QUAN (#51, #53, #54, #55, #56)
 * ========================================================================== */
export function VisualConfirmCard({ lesson, item, visual, actions, disabled }) {
  const [acknowledged, setAcknowledged] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [enableArea, setEnableArea] = useState(Boolean(visual.data?.area));
  const [oxyzJson, setOxyzJson] = useState(() => JSON.stringify(visual.data?.objects || [
    { id: 'A', type: 'point', label: 'A', coords: [1, 2, 3] },
  ], null, 2));

  const ownSlides = useMemo(
    () => (lesson?.deck?.slides || []).filter(s => s.item_id === item.item_id),
    [lesson?.deck?.slides, item.item_id],
  );

  const handleConfirm = async event => {
    event.preventDefault();
    if (!acknowledged) {
      setError('Hãy tích xác nhận «Dữ kiện khớp đề bài» trước khi xác nhận.');
      return;
    }
    const fd = new FormData(event.currentTarget);
    let nextData = { ...visual.data };

    if (visual.kind === 'graph') {
      nextData = {
        expression: String(fd.get('expression') || visual.data?.expression || '').trim(),
        x_min: Number(fd.get('x_min')),
        x_max: Number(fd.get('x_max')),
      };
      const yMinRaw = fd.get('y_min');
      const yMaxRaw = fd.get('y_max');
      if (yMinRaw !== '' && yMinRaw != null && yMaxRaw !== '' && yMaxRaw != null) {
        nextData.y_min = Number(yMinRaw);
        nextData.y_max = Number(yMaxRaw);
      }
      if (enableArea) {
        nextData.area = {
          target: String(fd.get('area_target') || 'ox').trim() || 'ox',
          a: Number(fd.get('area_a')),
          b: Number(fd.get('area_b')),
        };
      }
    } else if (visual.kind === 'bbt') {
      nextData = {
        expression: String(fd.get('expression') || visual.data?.expression || '').trim(),
      };
    } else if (visual.kind === 'solid') {
      const polyType = String(fd.get('polyhedron_type') || visual.data?.polyhedron_type || 'cube');
      const baseEdge = Number(fd.get('base_edge'));
      const height = polyType === 'cube' ? baseEdge : Number(fd.get('height'));
      nextData = { polyhedron_type: polyType, base_edge: baseEdge, height };
    } else if (visual.kind === 'oxyz') {
      try {
        nextData = { objects: JSON.parse(oxyzJson) };
      } catch {
        setError('Danh sách đối tượng Oxyz không phải JSON hợp lệ.');
        return;
      }
    }

    setBusy(true);
    setError('');
    try {
      await actions.confirmVisual(item.item_id, visual.visual_id, nextData);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="wb-form wb-visual-card" onSubmit={handleConfirm} data-testid={`wb-confirm-${visual.visual_id}`}>
      <div className="wb-form-row">
        <span className={`wb-vmark${visual.status === 'confirmed' ? ' is-confirmed' : ''}`} />
        <strong>{VISUAL_KIND_NAMES[visual.kind]}</strong>
        <span className="wb-meta">({visual.status === 'confirmed' ? 'đã xác nhận' : 'chờ xác nhận'})</span>
      </div>

      <fieldset disabled={disabled || busy}>
        {visual.kind === 'graph' && (
          <>
            <label>Biểu thức hàm số y = f(x)
              <input name="expression" defaultValue={visual.data?.expression || ''} required />
            </label>
            <div className="wb-form-row">
              <label>x_min<input type="number" step="any" name="x_min" defaultValue={visual.data?.x_min ?? -4} required /></label>
              <label>x_max<input type="number" step="any" name="x_max" defaultValue={visual.data?.x_max ?? 4} required /></label>
            </div>
            <div className="wb-form-row">
              <label>y_min (tùy chọn)<input type="number" step="any" name="y_min" defaultValue={visual.data?.y_min ?? ''} /></label>
              <label>y_max (tùy chọn)<input type="number" step="any" name="y_max" defaultValue={visual.data?.y_max ?? ''} /></label>
            </div>
            <label className="wb-check-label">
              <input type="checkbox" checked={enableArea} onChange={e => setEnableArea(e.target.checked)} />
              <span>Tô miền diện tích trên đoạn [a; b]</span>
            </label>
            {enableArea && (
              <div className="wb-area-fields">
                <label>Giới hạn thứ hai (nhập ox hoặc biểu thức g(x))
                  <input name="area_target" defaultValue={visual.data?.area?.target || 'ox'} required />
                </label>
                <div className="wb-form-row">
                  <label>Cận a<input type="number" step="any" name="area_a" defaultValue={visual.data?.area?.a ?? -1} required /></label>
                  <label>Cận b<input type="number" step="any" name="area_b" defaultValue={visual.data?.area?.b ?? 1} required /></label>
                </div>
              </div>
            )}
          </>
        )}

        {visual.kind === 'bbt' && (
          <>
            <label>Biểu thức hàm số y = f(x)
              <input name="expression" defaultValue={visual.data?.expression || ''} required />
            </label>
            <p className="wb-meta">Dạng hàm nhận diện: <strong>{visual.data?.family_label || detectClientBbtFamily(visual.data?.expression)}</strong></p>
          </>
        )}

        {visual.kind === 'solid' && (
          <>
            <label>Loại khối đa diện
              <select name="polyhedron_type" defaultValue={visual.data?.polyhedron_type || 'cube'}>
                <option value="cube">Hình lập phương</option>
                <option value="square_pyramid_regular">Chóp tứ giác đều S.ABCD</option>
                <option value="square_pyramid_at_a">Chóp S.ABCD có SA ⊥ đáy</option>
              </select>
            </label>
            <div className="wb-form-row">
              <label>Cạnh đáy a<input type="number" step="any" name="base_edge" defaultValue={visual.data?.base_edge ?? 2} required /></label>
              <label>Chiều cao h<input type="number" step="any" name="height" defaultValue={visual.data?.height ?? 2} required /></label>
            </div>
          </>
        )}

        {visual.kind === 'oxyz' && (
          <label>Các đối tượng Oxyz (JSON: point, vector, line, plane, sphere)
            <textarea rows={4} value={oxyzJson} onChange={e => setOxyzJson(e.target.value)} />
          </label>
        )}

        <label className="wb-check-label">
          <input
            type="checkbox"
            checked={acknowledged}
            onChange={e => setAcknowledged(e.target.checked)}
          />
          <span>Dữ kiện khớp đề bài</span>
        </label>

        <div className="wb-form-row">
          <button type="submit" className="wb-btn wb-btn--primary">
            {busy ? 'Đang xác nhận…' : 'Xác nhận dữ kiện'}
          </button>
          {ownSlides.length > 1 && (
            <select
              aria-label="Đặt hình lên slide trong cùng Mục"
              defaultValue=""
              onChange={e => {
                if (e.target.value) {
                  actions.placeVisualOnSlide(visual.visual_id, e.target.value);
                  e.target.value = '';
                }
              }}
            >
              <option value="">Đặt thêm lên slide trong Mục…</option>
              {ownSlides.map((s, idx) => (
                <option key={s.slide_id} value={s.slide_id}>Slide {idx + 1} của Mục</option>
              ))}
            </select>
          )}
        </div>
      </fieldset>
      {error && <p role="alert" className="wb-error-text">{error}</p>}
    </form>
  );
}

export function AddVisualForm({ item, activeSlideId, actions, disabled }) {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState('graph');
  const [error, setError] = useState('');

  if (!open) {
    return (
      <button type="button" className="wb-btn" disabled={disabled} onClick={() => setOpen(true)}>
        + Thêm hình vào Mục
      </button>
    );
  }

  const handleAdd = async event => {
    event.preventDefault();
    const fd = new FormData(event.currentTarget);
    let data = {};
    let label = '';
    if (kind === 'graph') {
      const expr = String(fd.get('expression') || 'x^3 - 3*x + 1').trim();
      data = { expression: expr, x_min: Number(fd.get('x_min') || -4), x_max: Number(fd.get('x_max') || 4) };
      label = `$y = ${expr}$`;
    } else if (kind === 'bbt') {
      const expr = String(fd.get('expression') || 'x^3 - 3*x + 1').trim();
      data = { expression: expr };
      label = `$y = ${expr}$`;
    } else if (kind === 'solid') {
      const ptype = String(fd.get('polyhedron_type') || 'cube');
      const a = Number(fd.get('base_edge') || 2);
      const h = ptype === 'cube' ? a : Number(fd.get('height') || 3);
      data = { polyhedron_type: ptype, base_edge: a, height: h };
      label = SOLID_KIND_LABELS[ptype];
    } else if (kind === 'oxyz') {
      data = {
        objects: [
          { id: 'A', type: 'point', label: String(fd.get('point_label') || 'A'), coords: [Number(fd.get('px') || 1), Number(fd.get('py') || 2), Number(fd.get('pz') || 3)] },
        ],
      };
      label = 'Hệ trục Oxyz';
    }
    setError('');
    try {
      await actions.addVisualToItem(item.item_id, { kind, label, data }, activeSlideId);
      setOpen(false);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form className="wb-form wb-visual-card" onSubmit={handleAdd}>
      <label>Loại hình cần thêm
        <select value={kind} onChange={e => setKind(e.target.value)}>
          {Object.entries(VISUAL_KIND_NAMES).map(([k, name]) => (
            <option key={k} value={k}>{name}</option>
          ))}
        </select>
      </label>
      {(kind === 'graph' || kind === 'bbt') && (
        <label>Biểu thức hàm số y = f(x)
          <input name="expression" defaultValue="x^3 - 3*x + 1" required />
        </label>
      )}
      {kind === 'graph' && (
        <div className="wb-form-row">
          <label>x_min<input type="number" step="any" name="x_min" defaultValue={-4} required /></label>
          <label>x_max<input type="number" step="any" name="x_max" defaultValue={4} required /></label>
        </div>
      )}
      {kind === 'solid' && (
        <>
          <label>Loại khối đa diện
            <select name="polyhedron_type" defaultValue="cube">
              <option value="cube">Hình lập phương</option>
              <option value="square_pyramid_regular">Chóp tứ giác đều S.ABCD</option>
              <option value="square_pyramid_at_a">Chóp S.ABCD có SA ⊥ đáy</option>
            </select>
          </label>
          <div className="wb-form-row">
            <label>Cạnh đáy a<input type="number" step="any" name="base_edge" defaultValue={2} required /></label>
            <label>Chiều cao h<input type="number" step="any" name="height" defaultValue={2} required /></label>
          </div>
        </>
      )}
      {kind === 'oxyz' && (
        <div className="wb-form-row">
          <label>Nhãn điểm<input name="point_label" defaultValue="A" required /></label>
          <label>x<input type="number" step="any" name="px" defaultValue={1} required /></label>
          <label>y<input type="number" step="any" name="py" defaultValue={2} required /></label>
          <label>z<input type="number" step="any" name="pz" defaultValue={3} required /></label>
        </div>
      )}
      <div className="wb-form-row">
        <button type="submit" className="wb-btn wb-btn--primary">Tạo yêu cầu trực quan</button>
        <button type="button" className="wb-btn" onClick={() => setOpen(false)}>Hủy</button>
      </div>
      {error && <p role="alert" className="wb-error-text">{error}</p>}
    </form>
  );
}
