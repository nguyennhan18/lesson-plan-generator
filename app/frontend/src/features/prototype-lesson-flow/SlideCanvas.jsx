/**
 * PROTOTYPE, wipe me. Một Slide 16:9 (1600 x 900 đơn vị logic) co giãn theo khung chứa.
 * mode: 'thumb' (chỉ xem), 'edit' (kéo thả, đổi cỡ, bám lưới 20), 'present' (hiện dần theo step).
 */
import React, { useLayoutEffect, useRef, useState } from 'react';
import MathText from '../../shared/math/MathText';
import { STAGE_H, STAGE_W } from './mockLessons.js';
import { BbtWidget, GraphWidget, OxyzWidget, QuizWidget } from './mathWidgets.jsx';

const VISUAL_TYPES = new Set(['graph', 'bbt', 'oxyz']);
const KIND_NAME = { graph: 'Đồ thị hàm số', bbt: 'Bảng biến thiên', oxyz: 'Hình Oxyz' };
const SNAP = 20;

export function findVisual(lesson, slide, visualId) {
  const item = lesson.items.find((i) => i.id === slide.itemId);
  return item?.visuals.find((v) => v.id === visualId) || null;
}

function isShown(lesson, slide, el) {
  if (!VISUAL_TYPES.has(el.type)) return true;
  return findVisual(lesson, slide, el.visualId)?.status === 'confirmed';
}

/** Số bước hiện dần của một slide; hình chưa xác nhận bị ẩn nên không chiếm bước. */
export function totalSteps(lesson, slide) {
  if (!slide) return 0;
  return Math.max(0, ...slide.elements.filter((el) => isShown(lesson, slide, el)).map((el) => (el.reveal || 0) + (el.parts || 1) - 1));
}

function useFit(ref, fit) {
  const [box, setBox] = useState({ w: 0, h: 0 });
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const ro = new ResizeObserver(([entry]) => setBox({ w: entry.contentRect.width, h: entry.contentRect.height }));
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref]);
  if (!box.w) return { scale: 0, left: 0, top: 0 };
  if (fit === 'width') return { scale: box.w / STAGE_W, left: 0, top: 0 };
  const scale = Math.min(box.w / STAGE_W, box.h / STAGE_H);
  return { scale, left: (box.w - STAGE_W * scale) / 2, top: (box.h - STAGE_H * scale) / 2 };
}

function PendingVisual({ visual, slide, onRequestConfirm }) {
  return (
    <div className="lf-pending">
      <strong>{KIND_NAME[visual?.kind] || 'Hình'} chờ xác nhận</strong>
      {visual && <p><MathText text={visual.label} /></p>}
      <p>Khi trình chiếu, hình này bị ẩn.</p>
      {onRequestConfirm && visual && (
        <button type="button" className="lf-btn lf-btn--slide" onPointerDown={(e) => e.stopPropagation()} onClick={() => onRequestConfirm(slide.itemId, visual.id)}>
          Xác nhận dữ kiện
        </button>
      )}
    </div>
  );
}

function ElementBody({ el, lesson, slide, mode, step, onRequestConfirm }) {
  const parts = el.parts || 1;
  const visible = mode === 'present' ? Math.max(0, Math.min(parts, step - (el.reveal || 0) + 1)) : parts;
  if (visible === 0) return null;
  const live = mode === 'present';
  const enter = live ? 'lf-appear' : '';
  switch (el.type) {
    case 'title':
      return <h2 className={`lf-s-title ${el.hero ? 'lf-s-title--hero' : ''}`}><MathText text={el.text} /></h2>;
    case 'caption':
      return <p className={`lf-s-caption ${enter}`}><MathText text={el.text} /></p>;
    case 'paragraph':
      return <p className={`lf-s-para ${enter}`}><MathText text={el.text} /></p>;
    case 'text':
      return <ul className="lf-s-list">{el.items.slice(0, visible).map((t, i) => <li key={i} className={enter}><MathText text={t} /></li>)}</ul>;
    case 'steps':
      return <ol className="lf-s-steps">{el.items.slice(0, visible).map((t, i) => <li key={i} className={enter}><span><MathText text={t} /></span></li>)}</ol>;
    case 'formula':
      return <div className={`lf-s-formula ${enter}`}><MathText text={el.latex} block /></div>;
    case 'quiz':
      return <QuizWidget el={el} interactive={live} />;
    case 'graph':
    case 'bbt':
    case 'oxyz': {
      const visual = findVisual(lesson, slide, el.visualId);
      if (visual?.status !== 'confirmed') {
        return live ? null : <PendingVisual visual={visual} slide={slide} onRequestConfirm={mode === 'edit' ? onRequestConfirm : null} />;
      }
      if (el.type === 'graph') return <GraphWidget visual={visual} width={el.w} height={el.h} interactive={live} animate={live} />;
      if (el.type === 'bbt') return <BbtWidget visual={visual} width={el.w} height={el.h} rows={visible} animate={live} />;
      return <OxyzWidget visual={visual} width={el.w} height={el.h} interactive={live} />;
    }
    default:
      return null;
  }
}

export default function SlideCanvas({
  lesson, slide, mode = 'thumb', fit = 'width', selectedId = null, onSelect, onMoveElement,
  step = Infinity, onRequestConfirm, className = '', style
}) {
  const outer = useRef(null);
  const { scale, left, top } = useFit(outer, fit);
  const [dragging, setDragging] = useState(false);

  const begin = (e, el, kind) => {
    if (mode !== 'edit' || e.button !== 0) return;
    e.stopPropagation();
    onSelect?.(el.id);
    const start = { x: e.clientX, y: e.clientY };
    const orig = { x: el.x, y: el.y, w: el.w, h: el.h };
    const snap = (v) => Math.round(v / SNAP) * SNAP;
    setDragging(true);
    const move = (ev) => {
      const dx = (ev.clientX - start.x) / scale;
      const dy = (ev.clientY - start.y) / scale;
      const rect = kind === 'resize'
        ? { ...orig, w: Math.max(160, Math.min(STAGE_W - orig.x, snap(orig.w + dx))), h: Math.max(60, Math.min(STAGE_H - orig.y, snap(orig.h + dy))) }
        : { ...orig, x: Math.max(0, Math.min(STAGE_W - orig.w, snap(orig.x + dx))), y: Math.max(0, Math.min(STAGE_H - orig.h, snap(orig.y + dy))) };
      onMoveElement?.(el.id, rect);
    };
    const up = () => {
      setDragging(false);
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };

  return (
    <div ref={outer} className={`lf-stage-outer lf-stage-outer--${fit} ${className}`} style={style}>
      <div
        className={`lf-stage lf-stage--${mode} ${dragging ? 'is-dragging' : ''}`}
        style={{ width: STAGE_W, height: STAGE_H, transform: `translate(${left}px, ${top}px) scale(${scale})`, '--s': scale || 1, visibility: scale ? 'visible' : 'hidden' }}
        onPointerDown={mode === 'edit' ? () => onSelect?.(null) : undefined}
      >
        {slide.elements.map((el) => {
          const selected = mode === 'edit' && el.id === selectedId;
          return (
            <div
              key={el.id}
              className={`lf-el lf-el--${el.type} ${selected ? 'is-selected' : ''}`}
              style={{ left: el.x, top: el.y, width: el.w, height: el.h }}
              onPointerDown={mode === 'edit' ? (e) => begin(e, el, 'move') : undefined}
            >
              <ElementBody el={el} lesson={lesson} slide={slide} mode={mode} step={step} onRequestConfirm={onRequestConfirm} />
              {selected && <span className="lf-el-handle" onPointerDown={(e) => begin(e, el, 'resize')} aria-hidden />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
