/**
 * PROTOTYPE, wipe me. Trình chiếu một màn hình (Q9, Q17): chuyển slide, hiện dần, thao tác Hình tương tác,
 * bút, bảng phụ, tối màn hình, bỏ phiếu trắc nghiệm. Không sửa nội dung, không hiện ghi chú giáo viên.
 * Phím: → hoặc Space tiếp, ← lùi, P bút, W bảng phụ, B tối màn hình, Esc thoát.
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Moon, Pencil, Square, X } from 'lucide-react';
import SlideCanvas, { totalSteps } from './SlideCanvas.jsx';

const toPath = (pts) => pts.map((p, i) => `${i ? 'L' : 'M'}${p[0]},${p[1]}`).join('');

export default function Presenter({ lesson, startIndex = 0, onExit }) {
  const slides = lesson.slides;
  const [index, setIndex] = useState(Math.min(startIndex, slides.length - 1));
  const [step, setStep] = useState(0);
  const [pen, setPen] = useState(false);
  const [board, setBoard] = useState(false);
  const [black, setBlack] = useState(false);
  const [ink, setInk] = useState({});
  const [barVisible, setBarVisible] = useState(true);
  const rootRef = useRef(null);
  const stroke = useRef(null);
  const idle = useRef(null);
  const slide = slides[index];
  const last = totalSteps(lesson, slide);
  const inkKey = board ? 'board' : slide?.id;

  const next = useCallback(() => {
    if (step < last) setStep(step + 1);
    else if (index < slides.length - 1) { setIndex(index + 1); setStep(0); }
  }, [step, last, index, slides.length]);
  const prev = useCallback(() => {
    if (step > 0) setStep(step - 1);
    else if (index > 0) { setIndex(index - 1); setStep(totalSteps(lesson, slides[index - 1])); }
  }, [step, index, slides, lesson]);

  useEffect(() => {
    document.body.dataset.presenting = 'true';
    // Toàn màn hình được bật ngay lúc bấm "Trình chiếu"; rời toàn màn hình (Esc của trình duyệt) là kết thúc trình chiếu.
    let wasFullscreen = !!document.fullscreenElement;
    const onChange = () => {
      if (document.fullscreenElement) wasFullscreen = true;
      else if (wasFullscreen) onExit();
    };
    document.addEventListener('fullscreenchange', onChange);
    return () => {
      delete document.body.dataset.presenting;
      document.removeEventListener('fullscreenchange', onChange);
      if (document.fullscreenElement) document.exitFullscreen?.().catch(() => {});
    };
  }, [onExit]);

  useEffect(() => {
    const onKey = (e) => {
      if (/INPUT|TEXTAREA|SELECT/.test(e.target?.tagName || '')) return;
      if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(e.key)) { e.preventDefault(); next(); }
      else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(e.key)) { e.preventDefault(); prev(); }
      else if (e.key === 'b' || e.key === 'B') setBlack((v) => !v);
      else if (e.key === 'w' || e.key === 'W') setBoard((v) => !v);
      else if (e.key === 'p' || e.key === 'P') setPen((v) => !v);
      else if (e.key === 'Escape') {
        if (black) setBlack(false);
        else if (board) setBoard(false);
        else if (pen) setPen(false);
        else onExit();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [next, prev, black, board, pen, onExit]);

  const wake = () => {
    setBarVisible(true);
    clearTimeout(idle.current);
    idle.current = setTimeout(() => setBarVisible(false), 2400);
  };
  useEffect(() => { wake(); return () => clearTimeout(idle.current); }, []);

  const drawing = pen || board;
  const onInkDown = (e) => {
    if (!drawing) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    stroke.current = [[e.clientX, e.clientY]];
    const first = stroke.current;
    setInk((m) => ({ ...m, [inkKey]: [...(m[inkKey] || []), first] }));
  };
  const onInkMove = (e) => {
    if (!stroke.current) return;
    stroke.current = [...stroke.current, [e.clientX, e.clientY]];
    const current = stroke.current;
    setInk((m) => {
      const list = [...(m[inkKey] || [])];
      list[list.length - 1] = current;
      return { ...m, [inkKey]: list };
    });
  };
  const onInkUp = () => { stroke.current = null; };

  if (!slide) return null;
  return (
    <div ref={rootRef} className="lf lf-present" onMouseMove={wake}>
      <div key={slide.id} className="lf-present-stage lf-fade">
        <SlideCanvas lesson={lesson} slide={slide} mode="present" fit="contain" step={step} style={{ width: '100%', height: '100%' }} />
      </div>
      {board && <div className="lf-board lf-desk"><span className="lf-board-title">Bảng phụ</span></div>}
      <svg className={`lf-inklayer ${drawing ? 'is-active' : ''}`} onPointerDown={onInkDown} onPointerMove={onInkMove} onPointerUp={onInkUp} aria-hidden>
        {(ink[inkKey] || []).map((s, i) => <path key={i} d={toPath(s)} />)}
      </svg>
      {black && <button type="button" className="lf-blackout" onClick={() => setBlack(false)} aria-label="Mở lại màn hình" />}
      <div className={`lf-present-bar ${barVisible || drawing ? '' : 'is-hidden'}`} onMouseEnter={() => clearTimeout(idle.current)}>
        <button type="button" onClick={prev} aria-label="Slide trước"><ChevronLeft size={18} /></button>
        <span className="lf-present-count">{index + 1}/{slides.length}</span>
        <button type="button" onClick={next} aria-label="Slide sau hoặc ý tiếp theo"><ChevronRight size={18} /></button>
        <span className="lf-present-sep" aria-hidden />
        <button type="button" aria-pressed={pen} onClick={() => setPen((v) => !v)}><Pencil size={15} />Bút</button>
        <button type="button" aria-pressed={board} onClick={() => setBoard((v) => !v)}><Square size={15} />Bảng phụ</button>
        <button type="button" onClick={() => setBlack(true)}><Moon size={15} />Tối màn hình</button>
        {drawing && <button type="button" onClick={() => setInk((m) => ({ ...m, [inkKey]: [] }))}>Xóa nét</button>}
        <span className="lf-present-sep" aria-hidden />
        <button type="button" onClick={onExit}><X size={15} />Thoát</button>
      </div>
    </div>
  );
}
