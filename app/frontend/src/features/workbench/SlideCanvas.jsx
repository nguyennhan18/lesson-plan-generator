/**
 * SlideCanvas 16:9 (1600 × 900 logical units) for Bàn làm việc (#40, #41, #42).
 * Supports modes: 'thumb' (read-only miniature), 'edit' (selection, 20-unit grid drag & resize, overflow detection),
 * and 'present' (progressive reveal by step; unconfirmed visuals hidden).
 */
import React, { useLayoutEffect, useRef, useState } from 'react';
import MathText from '../../shared/math/MathText';
import { BbtFigure, GraphFigure, SpaceFigure } from './WorkbenchVisuals.jsx';
import {
  SNAP_GRID,
  STAGE_SIZE,
  VISUAL_KIND_NAMES,
  measureElementTextFit,
  snapToGrid,
} from '../../shared/storage/lessonProject.js';

const FIGURE_TYPES = new Set(Object.keys(VISUAL_KIND_NAMES));
const INLINE_EDITABLE_TYPES = new Set(['title', 'paragraph', 'caption', 'text', 'steps']);

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

function FigureBody({ element, lesson, slide, visual, mode, visibleParts }) {
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
  if (element.type === 'graph') {
    return <GraphFigure lesson={lesson} slide={slide} visual={visual} mode={mode} />;
  }
  if (element.type === 'bbt') {
    return <BbtFigure lesson={lesson} slide={slide} visual={visual} mode={mode} visibleParts={visibleParts} />;
  }
  if (element.type === 'solid' || element.type === 'oxyz') {
    return <SpaceFigure lesson={lesson} slide={slide} visual={visual} mode={mode} />;
  }
  return (
    <div className="wb-s-figure">
      <span className="wb-s-figure-kind">{kindLabel}</span>
      {visual.label && <span className="wb-s-figure-label"><MathText text={visual.label} /></span>}
      {visual.data?.expression && <code className="wb-s-figure-expr">y = {visual.data.expression}</code>}
    </div>
  );
}

function QuizBody({ element, lesson, slide, mode, onUpdatePoll }) {
  const [showAnswer, setShowAnswer] = useState(false);
  const options = Array.isArray(element.options) ? element.options : [];
  const poll = lesson?.polls?.[slide.slide_id] || { A: 0, B: 0, C: 0, D: 0 };
  const totalVotes = ['A', 'B', 'C', 'D'].reduce((sum, k) => sum + Number(poll[k] || 0), 0);

  const changeVote = (label, delta) => {
    const nextCount = Math.max(0, Number(poll[label] || 0) + delta);
    onUpdatePoll?.(slide.slide_id, { ...poll, [label]: nextCount });
  };

  return (
    <div className="wb-s-quiz" onPointerDown={mode === 'present' ? e => e.stopPropagation() : undefined}>
      <div className="wb-s-quiz-head">
        <p className="wb-s-quiz-q"><MathText text={element.question || ''} /></p>
        {mode === 'present' && (
          <div className="wb-s-quiz-bar">
            <span className="wb-s-quiz-total" data-testid="wb-quiz-total">{totalVotes} phiếu</span>
            <button
              type="button"
              className="wb-btn"
              aria-pressed={showAnswer}
              onClick={() => setShowAnswer(v => !v)}
            >
              {showAnswer ? 'Ẩn đáp án' : 'Hiện đáp án'}
            </button>
          </div>
        )}
      </div>
      <ul className="wb-s-quiz-opts">
        {options.map((opt, idx) => {
          const label = opt.label || ['A', 'B', 'C', 'D'][idx] || 'A';
          const count = Number(poll[label] || 0);
          const sharePct = totalVotes > 0 ? Math.round((count / totalVotes) * 100) : 0;
          const isCorrect = Boolean(opt.correct ?? opt.is_correct);
          const highlightCorrect = mode === 'present' && showAnswer && isCorrect;
          const whyText = opt.why || opt.distractor_rationale || '';
          return (
            <li
              key={label}
              data-quiz-option={label}
              className={`wb-s-quiz-opt${highlightCorrect ? ' is-correct' : ''}`}
              style={mode === 'present' && showAnswer ? { '--share': `${sharePct}%` } : undefined}
            >
              <span className="wb-s-quiz-letter">{label}</span>
              <div className="wb-s-quiz-main">
                <span className="wb-s-quiz-text"><MathText text={opt.text || ''} /></span>
                {mode === 'present' && showAnswer && whyText && (
                  <p className="wb-s-quiz-why" data-testid={`wb-quiz-why-${label}`}>
                    <MathText text={whyText} /> ({sharePct}%)
                  </p>
                )}
              </div>
              {mode === 'present' && (
                <div className="wb-s-quiz-tally" aria-label={`Phiếu phương án ${label}`}>
                  <button
                    type="button"
                    className="wb-btn"
                    aria-label={`Giảm phiếu ${label}`}
                    onClick={() => changeVote(label, -1)}
                  >
                    −
                  </button>
                  <span className="wb-s-quiz-count" data-testid={`wb-quiz-count-${label}`}>{count}</span>
                  <button
                    type="button"
                    className="wb-btn"
                    aria-label={`Tăng phiếu ${label}`}
                    onClick={() => changeVote(label, 1)}
                  >
                    +
                  </button>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function ElementContent({ element, lesson, slide, mode, step, fontSize, onUpdatePoll }) {
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
    case 'quiz':
      return <QuizBody element={element} lesson={lesson} slide={slide} mode={mode} onUpdatePoll={onUpdatePoll} />;
    case 'graph':
    case 'bbt':
    case 'oxyz':
    case 'solid': {
      const visual = findSlideVisual(lesson, slide, element.visual_id);
      return <FigureBody element={element} lesson={lesson} slide={slide} visual={visual} mode={mode} visibleParts={visible} />;
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
  onEditFormula,
  onUpdatePoll,
  step = Infinity,
  className = '',
}) {
  const outerRef = useRef(null);
  const { scale, left, top } = useStageScale(outerRef, fit);
  const [dragRects, setDragRects] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editingText, setEditingText] = useState('');

  if (!slide) return null;

  const commitInlineEdit = el => {
    setEditingId(null);
    if (!el) return;
    if (el.type === 'text' || el.type === 'steps') {
      const nextItems = editingText.split('\n').map(s => s.trim()).filter(Boolean);
      if (nextItems.length > 0 && JSON.stringify(nextItems) !== JSON.stringify(el.items)) {
        onChangeElement?.(slide.slide_id, el.element_id, { items: nextItems, parts: nextItems.length });
      }
    } else {
      const trimmed = editingText.trim();
      if (trimmed && trimmed !== el.text) {
        onChangeElement?.(slide.slide_id, el.element_id, { text: trimmed });
      }
    }
  };

  const handleDoubleClick = (event, el) => {
    if (mode !== 'edit') return;
    event.stopPropagation();
    if (el.type === 'formula') {
      onEditFormula?.(el);
      return;
    }
    if (INLINE_EDITABLE_TYPES.has(el.type)) {
      const initVal = Array.isArray(el.items) ? el.items.join('\n') : (el.text || '');
      setEditingId(el.element_id);
      setEditingText(initVal);
    }
  };

  const startDrag = (event, element, kind) => {
    if (mode !== 'edit' || event.button !== 0 || editingId === element.element_id) return;
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
          const isEditingThis = mode === 'edit' && editingId === el.element_id;
          return (
            <div
              key={el.element_id}
              data-element-id={el.element_id}
              data-element-type={el.type}
              data-overflow={isOverflow ? 'true' : undefined}
              className={`wb-el wb-el--${el.type}${selected ? ' is-selected' : ''}${isOverflow ? ' is-overflow' : ''}`}
              style={{ left: el.x, top: el.y, width: el.w, height: el.h }}
              onPointerDown={mode === 'edit' ? event => startDrag(event, el, 'move') : undefined}
              onDoubleClick={mode === 'edit' ? event => handleDoubleClick(event, el) : undefined}
            >
              {isEditingThis ? (
                <textarea
                  autoFocus
                  aria-label="Sửa nội dung phần tử trên canvas"
                  className="wb-el-inline-input"
                  value={editingText}
                  onChange={e => setEditingText(e.target.value)}
                  onPointerDown={e => e.stopPropagation()}
                  onBlur={() => commitInlineEdit(el)}
                  onKeyDown={e => {
                    if (e.key === 'Escape') {
                      e.stopPropagation();
                      setEditingId(null);
                    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey || el.type === 'title' || el.type === 'caption')) {
                      e.preventDefault();
                      commitInlineEdit(el);
                    }
                  }}
                />
              ) : (
                <ElementContent
                  element={el}
                  lesson={lesson}
                  slide={slide}
                  mode={mode}
                  step={step}
                  fontSize={fitInfo.fontSize}
                  onUpdatePoll={onUpdatePoll}
                />
              )}
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
