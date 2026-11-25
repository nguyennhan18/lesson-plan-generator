/**
 * Basic fullscreen presentation for Bàn làm việc (#41):
 * - Progressive reveal: at step s, element reveals clamp(s - reveal + 1, 0, parts) parts.
 * - Keys: ArrowRight / Space / PageDown (next), ArrowLeft / PageUp (previous slide shows full),
 *   P (pen), W (grid-paper whiteboard), B (blackout), Escape (exit to active slide).
 * - Auto-hiding toolbar on mouse idle; no teacher notes or editing controls.
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import SlideCanvas, { totalSlideSteps } from './SlideCanvas.jsx';

const pointsToSvgPath = pts => pts.map((pt, i) => `${i ? 'L' : 'M'}${pt[0]},${pt[1]}`).join('');

export default function WorkbenchPresenter({ lesson, initialSlideId, onExit }) {
  const slides = lesson?.deck?.slides || [];
  const startIndex = Math.max(0, slides.findIndex(slide => slide.slide_id === initialSlideId));
  const [index, setIndex] = useState(startIndex);
  const [step, setStep] = useState(0);
  const [pen, setPen] = useState(false);
  const [board, setBoard] = useState(false);
  const [black, setBlack] = useState(false);
  const [ink, setInk] = useState({});
  const [barVisible, setBarVisible] = useState(true);
  const strokeRef = useRef(null);
  const idleTimer = useRef(null);

  const slide = slides[index] || slides[0];
  const lastStep = totalSlideSteps(lesson, slide);
  const inkKey = board ? 'board' : slide?.slide_id;

  const exitPresentation = useCallback(() => {
    if (document.fullscreenElement) {
      document.exitFullscreen?.().catch(() => {});
    }
    onExit(slide?.slide_id || initialSlideId);
  }, [onExit, slide, initialSlideId]);

  const next = useCallback(() => {
    if (step < lastStep) {
      setStep(s => s + 1);
    } else if (index < slides.length - 1) {
      setIndex(i => i + 1);
      setStep(0);
    }
  }, [step, lastStep, index, slides.length]);

  const prev = useCallback(() => {
    if (step > 0) {
      setStep(s => s - 1);
    } else if (index > 0) {
      const prevIndex = index - 1;
      setIndex(prevIndex);
      setStep(totalSlideSteps(lesson, slides[prevIndex]));
    }
  }, [step, index, lesson, slides]);

  useEffect(() => {
    document.body.dataset.wbPresenting = 'true';
    let enteredFullscreen = Boolean(document.fullscreenElement);
    const onFullscreenChange = () => {
      if (document.fullscreenElement) {
        enteredFullscreen = true;
      } else if (enteredFullscreen) {
        onExit(slide?.slide_id || initialSlideId);
      }
    };
    document.addEventListener('fullscreenchange', onFullscreenChange);
    return () => {
      delete document.body.dataset.wbPresenting;
      document.removeEventListener('fullscreenchange', onFullscreenChange);
    };
  }, [onExit, slide, initialSlideId]);

  useEffect(() => {
    const onKeyDown = event => {
      if (/INPUT|TEXTAREA|SELECT/.test(event.target?.tagName || '')) return;
      if (['ArrowRight', 'PageDown', ' '].includes(event.key)) {
        event.preventDefault();
        next();
      } else if (['ArrowLeft', 'PageUp'].includes(event.key)) {
        event.preventDefault();
        prev();
      } else if (event.key === 'p' || event.key === 'P') {
        event.preventDefault();
        setPen(v => !v);
      } else if (event.key === 'w' || event.key === 'W') {
        event.preventDefault();
        setBoard(v => !v);
      } else if (event.key === 'b' || event.key === 'B') {
        event.preventDefault();
        setBlack(v => !v);
      } else if (event.key === 'Escape') {
        event.preventDefault();
        exitPresentation();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [next, prev, exitPresentation]);

  const wakeToolbar = useCallback(() => {
    setBarVisible(true);
    clearTimeout(idleTimer.current);
    idleTimer.current = setTimeout(() => setBarVisible(false), 2400);
  }, []);

  useEffect(() => {
    wakeToolbar();
    return () => clearTimeout(idleTimer.current);
  }, [wakeToolbar]);

  const drawing = pen || board;
  const onInkDown = event => {
    if (!drawing) return;
    event.currentTarget.setPointerCapture?.(event.pointerId);
    strokeRef.current = [[event.clientX, event.clientY]];
    const first = strokeRef.current;
    setInk(prevInk => ({ ...prevInk, [inkKey]: [...(prevInk[inkKey] || []), first] }));
  };
  const onInkMove = event => {
    if (!strokeRef.current) return;
    strokeRef.current = [...strokeRef.current, [event.clientX, event.clientY]];
    const current = strokeRef.current;
    setInk(prevInk => {
      const list = [...(prevInk[inkKey] || [])];
      list[list.length - 1] = current;
      return { ...prevInk, [inkKey]: list };
    });
  };
  const onInkUp = () => {
    strokeRef.current = null;
  };

  if (!slide) return null;

  return (
    <div
      className="wb-present"
      role="region"
      aria-label="Màn trình chiếu"
      onMouseMove={wakeToolbar}
    >
      <div key={slide.slide_id} className="wb-present-stage">
        <SlideCanvas
          lesson={lesson}
          slide={slide}
          mode="present"
          fit="contain"
          step={step}
        />
      </div>

      {board && (
        <div className="wb-present-board" role="region" aria-label="Bảng phụ">
          <span className="wb-present-board-title">Bảng phụ</span>
        </div>
      )}

      <svg
        className={`wb-present-ink${drawing ? ' is-active' : ''}`}
        onPointerDown={onInkDown}
        onPointerMove={onInkMove}
        onPointerUp={onInkUp}
        aria-label="Lớp nét bút chú thích"
      >
        {(ink[inkKey] || []).map((pts, i) => (
          <path key={i} d={pointsToSvgPath(pts)} />
        ))}
      </svg>

      {black && (
        <button
          type="button"
          className="wb-present-blackout"
          onClick={() => setBlack(false)}
          aria-label="Mở lại màn hình"
        />
      )}

      <div
        className={`wb-present-bar${barVisible ? '' : ' is-hidden'}`}
        role="toolbar"
        aria-label="Thanh công cụ trình chiếu"
        onMouseEnter={() => clearTimeout(idleTimer.current)}
      >
        <button type="button" onClick={prev} aria-label="Trước">Trước</button>
        <span className="wb-present-count" aria-label="Số trang">{index + 1}/{slides.length}</span>
        <button type="button" onClick={next} aria-label="Sau">Sau</button>
        <span className="wb-present-sep" aria-hidden="true" />
        <button type="button" aria-pressed={pen} onClick={() => setPen(v => !v)}>Bút</button>
        <button type="button" aria-pressed={board} onClick={() => setBoard(v => !v)}>Bảng phụ</button>
        <button type="button" aria-pressed={black} onClick={() => setBlack(v => !v)}>Tối màn hình</button>
        <button type="button" onClick={() => setInk(prevInk => ({ ...prevInk, [inkKey]: [] }))}>Xóa nét</button>
        <span className="wb-present-sep" aria-hidden="true" />
        <button type="button" onClick={exitPresentation}>Thoát</button>
      </div>
    </div>
  );
}
