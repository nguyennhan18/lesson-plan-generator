/**
 * SlideCanvas 16:9 (1600 × 900 logical units) for Bàn làm việc (#40, #41, #42).
 * Supports modes: 'thumb' (read-only miniature), 'edit' (selection, 20-unit grid drag & resize, overflow detection),
 * and 'present' (progressive reveal by step; unconfirmed visuals hidden).
 */
import React, { useLayoutEffect, useRef, useState } from 'react';
import MathText from '../../shared/math/MathText';
import {
  SNAP_GRID,
  STAGE_SIZE,
  VISUAL_KIND_NAMES,
  measureElementTextFit,
  snapToGrid,
} from '../../shared/storage/lessonProject.js';

const FIGURE_TYPES = new Set(Object.keys(VISUAL_KIND_NAMES));

export const ELEMENT_TYPE_LABELS = {
  title: 'Tiêu đề',
  paragraph: 'Đoạn văn',
  text: 'Danh sách ý',
  steps: 'Các bước giải',
  formula: 'Công thức',
  table: 'Bảng dữ liệu',
  image: 'Hình ảnh',
  caption: 'Chú thích',
  quiz: 'Câu hỏi trắc nghiệm',
  ...VISUAL_KIND_NAMES,
};

export function findSlideVisual(lesson, slide, visualId) {
  if (!lesson?.outline?.items || !slide || !visualId) return null;
  const item = lesson.outline.items.find(entry => entry.item_id === slide.item_id);
  return item?.visuals?.find(visual => visual.visual_id === visualId) || null;
}

export function isElementShownInPresentation(lesson, slide, element) {
  if (!FIGURE_TYPES.has(element.type)) return true;
  return findSlideVisual(lesson, slide, element.visual_id)?.status === 'confirmed';
}

/**
 * Maximum step index of a slide (#36, #41): max of (reveal + parts - 1) across shown elements.
 * Unconfirmed figures are hidden during presentation and take 0 steps.
 */
export function totalSlideSteps(lesson, slide) {
  if (!slide?.elements?.length) return 0;
  const shown = slide.elements.filter(el => isElementShownInPresentation(lesson, slide, el));
  if (!shown.length) return 0;
  return Math.max(0, ...shown.map(el => (el.reveal ?? 0) + (el.parts ?? 1) - 1));
}

/**
 * Number of parts visible for an element at presentation step `s`: clamp(s - reveal + 1, 0, parts).
 */
export function visibleElementParts(element, step) {
  const parts = element.parts ?? 1;
  const reveal = element.reveal ?? 0;
  return Math.max(0, Math.min(parts, step - reveal + 1));
}

function useStageScale(containerRef, fit) {
  const [size, setSize] = useState({ w: 0, h: 0 });
  useLayoutEffect(() => {
    const node = containerRef.current;
    if (!node) return undefined;
    const update = widthAndHeight => setSize(widthAndHeight);
    const rect = node.getBoundingClientRect();
    if (rect.width > 0 || rect.height > 0) {
      update({ w: rect.width, h: rect.height });
    }
    if (typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver(([entry]) => {
      update({ w: entry.contentRect.width, h: entry.contentRect.height });
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, [containerRef]);

  const fallbackW = fit === 'width' ? 160 : 800;
  const fallbackH = fit === 'width' ? 90 : 450;
  const w = size.w || fallbackW;
  const h = size.h || fallbackH;
  if (fit === 'width') {
    return { scale: w / STAGE_SIZE.width, left: 0, top: 0 };
  }
  const scale = Math.min(w / STAGE_SIZE.width, h / STAGE_SIZE.height);
  return {
    scale,
    left: (w - STAGE_SIZE.width * scale) / 2,
    top: (h - STAGE_SIZE.height * scale) / 2,
  };
}

function FigureBody({ element, visual, mode }) {
  const kindLabel = VISUAL_KIND_NAMES[element.type] || 'Hình';
  if (visual?.status !== 'confirmed') {
    if (mode === 'present') return null;
    return (
      <div className="wb-s-pending">
        <strong>{kindLabel} chờ xác nhận</strong>
        {visual?.label && <p><MathText text={visual.label} /></p>}
        <p className="wb-s-pending-note">Khi trình chiếu, hình chưa xác nhận sẽ bị ẩn.</p>
      </div>
    );
  }
  return (
    <div className="wb-s-figure">
      <span className="wb-s-figure-kind">{kindLabel}</span>
      {visual.label && <span className="wb-s-figure-label"><MathText text={visual.label} /></span>}
      {visual.data?.expression && <code className="wb-s-figure-expr">y = {visual.data.expression}</code>}
    </div>
  );
}

function ElementContent({ element, lesson, slide, mode, step, fontSize }) {
  const parts = element.parts ?? 1;
  const visible = mode === 'present' ? visibleElementParts(element, step) : parts;
  if (visible <= 0) return null;
  const style = fontSize ? { fontSize: `${fontSize}px` } : undefined;

  switch (element.type) {
    case 'title':
      return (
        <h2 className={`wb-s-title${element.hero ? ' wb-s-title--hero' : ''}`} style={style}>
          <MathText text={element.text || ''} />
        </h2>
      );
    case 'paragraph':
      return (
        <p className="wb-s-para" style={style}>
          <MathText text={element.text || ''} />
        </p>
      );
    case 'caption':
      return (
        <p className="wb-s-caption" style={style}>
          <MathText text={element.text || ''} />
        </p>
      );
    case 'text': {
      const items = Array.isArray(element.items) ? element.items.slice(0, visible) : [];
      return (
        <ul className="wb-s-list" style={style}>
          {items.map((item, idx) => (
            <li key={idx}><MathText text={item} /></li>
          ))}
        </ul>
      );
    }
    case 'steps': {
      const items = Array.isArray(element.items) ? element.items.slice(0, visible) : [];
      return (
        <ol className="wb-s-steps" style={style}>
          {items.map((item, idx) => (
            <li key={idx}><span><MathText text={item} /></span></li>
          ))}
        </ol>
      );
    }
    case 'formula':
      return (
        <div className="wb-s-formula">
          <MathText text={element.latex || element.text || ''} block />
        </div>
      );
    case 'table': {
      const headers = Array.isArray(element.headers) ? element.headers : [];
      const rows = Array.isArray(element.rows) ? element.rows : [];
      return (
        <table className="wb-s-table">
          {headers.length > 0 && (
            <thead>
              <tr>{headers.map((header, idx) => <th key={idx}><MathText text={header} /></th>)}</tr>
            </thead>
          )}
          <tbody>
            {rows.map((row, rIdx) => (
              <tr key={rIdx}>
                {(Array.isArray(row) ? row : []).map((cell, cIdx) => (
                  <td key={cIdx}><MathText text={String(cell)} /></td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    }
    case 'image':
      return <img className="wb-s-image" src={element.src} alt={element.alt || 'Hình ảnh trên slide'} />;
    case 'quiz': {
      const options = Array.isArray(element.options) ? element.options : [];
      return (
        <div className="wb-s-quiz">
          <p className="wb-s-quiz-q"><MathText text={element.question || ''} /></p>
          <ul className="wb-s-quiz-opts">
            {options.map((opt, idx) => (
              <li key={opt.label || idx} className="wb-s-quiz-opt">
                <span className="wb-s-quiz-letter">{opt.label}</span>
                <span className="wb-s-quiz-text"><MathText text={opt.text || ''} /></span>
              </li>
            ))}
          </ul>
        </div>
      );
    }
    case 'graph':
    case 'bbt':
    case 'oxyz':
    case 'solid': {
      const visual = findSlideVisual(lesson, slide, element.visual_id);
      return <FigureBody element={element} visual={visual} mode={mode} />;
    }
    default:
      return null;
  }
}

export default function SlideCanvas({
  lesson,
  slide,
  mode = 'thumb',
  fit = 'width',
  selectedElementId = null,
  onSelectElement,
  onChangeElement,
  step = Infinity,
  className = '',
}) {
  const outerRef = useRef(null);
  const { scale, left, top } = useStageScale(outerRef, fit);
  const [dragRects, setDragRects] = useState(null);

  if (!slide) return null;

  const startDrag = (event, element, kind) => {
    if (mode !== 'edit' || event.button !== 0) return;
    event.stopPropagation();
    onSelectElement?.(element.element_id);
    const startX = event.clientX;
    const startY = event.clientY;
    const origin = { x: element.x, y: element.y, w: element.w, h: element.h };
    const effectiveScale = scale || 0.5;
    let latest = null;
    setDragRects({ id: element.element_id, rect: origin });

    const onMove = moveEvent => {
      const dx = (moveEvent.clientX - startX) / effectiveScale;
      const dy = (moveEvent.clientY - startY) / effectiveScale;
      if (kind === 'resize') {
        latest = {
          x: origin.x,
          y: origin.y,
          w: Math.max(160, Math.min(STAGE_SIZE.width - origin.x, snapToGrid(origin.w + dx, SNAP_GRID))),
          h: Math.max(60, Math.min(STAGE_SIZE.height - origin.y, snapToGrid(origin.h + dy, SNAP_GRID))),
        };
      } else {
        latest = {
          x: Math.max(0, Math.min(STAGE_SIZE.width - origin.w, snapToGrid(origin.x + dx, SNAP_GRID))),
          y: Math.max(0, Math.min(STAGE_SIZE.height - origin.h, snapToGrid(origin.y + dy, SNAP_GRID))),
          w: origin.w,
          h: origin.h,
        };
      }
      setDragRects({ id: element.element_id, rect: latest });
    };

    const onUp = () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      setDragRects(null);
      if (latest && (latest.x !== origin.x || latest.y !== origin.y || latest.w !== origin.w || latest.h !== origin.h)) {
        onChangeElement?.(slide.slide_id, element.element_id, latest);
      }
    };

    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  };

  const isDragging = Boolean(dragRects);

  return (
    <div
      ref={outerRef}
      className={`wb-stage-outer wb-stage-outer--${fit}${className ? ` ${className}` : ''}`}
      data-testid={mode === 'edit' ? 'wb-canvas' : undefined}
    >
      <div
        className={`wb-stage wb-stage--${mode}${isDragging ? ' is-dragging' : ''}`}
        style={{
          width: STAGE_SIZE.width,
          height: STAGE_SIZE.height,
          transform: `translate(${left}px, ${top}px) scale(${scale})`,
          '--s': scale || 1,
        }}
        onPointerDown={mode === 'edit' ? () => onSelectElement?.(null) : undefined}
      >
        {slide.elements.map(rawEl => {
          const el = dragRects?.id === rawEl.element_id ? { ...rawEl, ...dragRects.rect } : rawEl;
          if (mode === 'present' && !isElementShownInPresentation(lesson, slide, el)) {
            return null;
          }
          if (mode === 'present' && visibleElementParts(el, step) <= 0) {
            return null;
          }
          const fitInfo = measureElementTextFit(el);
          const isOverflow = Boolean(el.overflow || fitInfo.overflow);
          const selected = mode === 'edit' && el.element_id === selectedElementId;
          return (
            <div
              key={el.element_id}
              data-element-id={el.element_id}
              data-element-type={el.type}
              data-overflow={isOverflow ? 'true' : undefined}
              className={`wb-el wb-el--${el.type}${selected ? ' is-selected' : ''}${isOverflow ? ' is-overflow' : ''}`}
              style={{ left: el.x, top: el.y, width: el.w, height: el.h }}
              onPointerDown={mode === 'edit' ? event => startDrag(event, el, 'move') : undefined}
            >
              <ElementContent
                element={el}
                lesson={lesson}
                slide={slide}
                mode={mode}
                step={step}
                fontSize={fitInfo.fontSize}
              />
              {isOverflow && mode !== 'present' && (
                <span className="wb-el-overflow-badge" title="Chữ tràn khung sau khi đã thu nhỏ tới cỡ tối thiểu">
                  Tràn chữ
                </span>
              )}
              {selected && (
                <span
                  role="button"
                  aria-label="Đổi cỡ phần tử"
                  className="wb-el-handle"
                  onPointerDown={event => startDrag(event, el, 'resize')}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
