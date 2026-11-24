/**
 * PROTOTYPE, wipe me.
 * Câu hỏi: giao diện mới cho luồng Prompt → Dàn ý → Bộ slide → Trình chiếu nên trông thế nào?
 * Ba biến thể khác nhau về cấu trúc trên cùng một route, chuyển qua `?variant=A|B|C` hoặc thanh vàng ở dưới:
 *   A. Từng bước       bốn màn nối tiếp
 *   B. Bàn làm việc    Dàn ý luôn hiện cạnh canvas
 *   C. Bảng kể chuyện  Dàn ý là bảng theo Hoạt động, phóng vào slide để soạn
 * Chạy: `npm run prototype` trong app/frontend, mở /?prototype=lesson-flow. Không gọi backend, trạng thái chỉ nằm trong bộ nhớ.
 *
 * Kết luận (2026-11-24): chủ dự án chọn B "Bàn làm việc". A và C giữ lại làm tài liệu gốc, không đưa vào sản phẩm.
 * Nhánh này là nháp: code thật được viết lại theo spec, không merge nhánh này.
 */
import React, { useCallback, useMemo, useReducer, useRef, useState, useEffect } from 'react';
import './prototype.css';
import PrototypeSwitcher from '../../shared/components/PrototypeSwitcher.jsx';
import { TEMPLATES, buildLesson, buildSlidesForItem, detectTemplate } from './mockLessons.js';
import { PreflightDialog, lessonStats, presentIssues } from './parts.jsx';
import Presenter from './Presenter.jsx';
import VariantA from './VariantA.jsx';
import VariantB from './VariantB.jsx';
import VariantC from './VariantC.jsx';

const VARIANTS = [
  { key: 'A', name: 'Từng bước', Component: VariantA },
  { key: 'B', name: 'Bàn làm việc', Component: VariantB },
  { key: 'C', name: 'Bảng kể chuyện', Component: VariantC }
];

function initialState() {
  const ks = buildLesson('khao-sat', { id: 'ks', confirmed: ['v-bbt', 'v-graph'], updatedAt: 'Hôm qua, 21:40' });
  const ox = buildLesson('oxyz', { id: 'ox', confirmed: ['v-oxyz'], updatedAt: 'Thứ Hai, 15:05' });
  return { lessons: { ks, ox }, order: ['ks', 'ox'], activeId: null };
}

function reducer(state, action) {
  const patch = (fn) => ({ ...state, lessons: { ...state.lessons, [action.id]: fn(state.lessons[action.id]) } });
  switch (action.type) {
    case 'open':
      return { ...state, activeId: action.id };
    case 'home':
      return { ...state, activeId: null };
    case 'create': {
      const full = buildLesson(action.templateKey, { id: action.id, prompt: action.prompt, level: action.level, withSlides: false });
      const lesson = { ...full, items: [], queue: full.items, generating: 'outline' };
      return { ...state, lessons: { ...state.lessons, [action.id]: lesson }, order: [action.id, ...state.order], activeId: action.id };
    }
    case 'itemArrived':
      return patch((l) => {
        const [next, ...rest] = l.queue;
        if (!next) return { ...l, generating: null };
        return { ...l, items: [...l.items, { ...next, fresh: true }], queue: rest, generating: rest.length ? 'outline' : null };
      });
    case 'setItem':
      return patch((l) => ({
        ...l, approved: false,
        items: l.items.map((it) => (it.id === action.itemId ? { ...it, ...action.patch, stale: it.stale || ('slideCount' in action.patch && l.slides.length > 0) } : it))
      }));
    case 'confirmVisual':
      return patch((l) => ({
        ...l, approved: false,
        items: l.items.map((it) => (it.id !== action.itemId ? it : {
          ...it, visuals: it.visuals.map((v) => (v.id === action.visualId ? { ...v, status: 'confirmed', data: { ...v.data, ...action.data } } : v))
        }))
      }));
    case 'startSlides':
      return patch((l) => {
        const items = l.items.map((it) => ({ ...it, fresh: false, stale: false }));
        const queue = items.flatMap((it) => buildSlidesForItem(l.templateKey, l.id, it));
        return { ...l, items, slides: [], queue, generating: 'slides', approved: false };
      });
    case 'slideArrived':
      return patch((l) => {
        const [next, ...rest] = l.queue;
        if (!next) return { ...l, generating: null };
        return { ...l, slides: [...l.slides, { ...next, fresh: true }], queue: rest, generating: rest.length ? 'slides' : null };
      });
    case 'regenerateItem':
      return patch((l) => {
        const item = l.items.find((i) => i.id === action.itemId);
        const fresh = buildSlidesForItem(l.templateKey, l.id, item).map((s) => ({ ...s, fresh: true }));
        return {
          ...l, approved: false,
          slides: l.items.flatMap((it) => (it.id === item.id ? fresh : l.slides.filter((s) => s.itemId === it.id))),
          items: l.items.map((i) => (i.id === item.id ? { ...i, stale: false } : i))
        };
      });
    case 'moveElement':
      return patch((l) => ({
        ...l, approved: false,
        slides: l.slides.map((s) => (s.id !== action.slideId ? s : {
          ...s, edited: true, elements: s.elements.map((e) => (e.id === action.elId ? { ...e, ...action.rect } : e))
        }))
      }));
    case 'approve':
      return patch((l) => ({ ...l, approved: true }));
    default:
      return state;
  }
}

// Trình duyệt chỉ cho vào toàn màn hình ngay trong thao tác bấm của người dùng.
function enterFullscreen() {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen?.().catch(() => {});
}

function readVariant() {
  const key = new URLSearchParams(window.location.search).get('variant');
  return VARIANTS.some((v) => v.key === key) ? key : 'B';
}

export default function LessonFlowPrototype() {
  const [variant, setVariant] = useState(readVariant);
  const [state, dispatch] = useReducer(reducer, undefined, initialState);
  const [preflight, setPreflight] = useState(null);
  const [presenting, setPresenting] = useState(null);
  const stateRef = useRef(state);
  stateRef.current = state;
  const timers = useRef([]);
  const created = useRef(0);
  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const actions = useMemo(() => {
    const activeId = () => stateRef.current.activeId;
    const later = (ms, fn) => timers.current.push(setTimeout(fn, ms));
    const on = (type, extra = {}) => dispatch({ type, id: activeId(), ...extra });
    return {
      open: (id) => dispatch({ type: 'open', id }),
      home: () => dispatch({ type: 'home' }),
      create: ({ prompt, level }) => {
        created.current += 1;
        const id = `moi${created.current}`;
        const templateKey = detectTemplate(prompt);
        dispatch({ type: 'create', id, prompt, level, templateKey });
        // AI giả lập: nghĩ một lúc rồi trả từng mục, mỗi mục được "viết" ra.
        TEMPLATES[templateKey].items.forEach((_, i) => later(900 + i * 420, () => dispatch({ type: 'itemArrived', id })));
      },
      setItem: (itemId, patchValue) => on('setItem', { itemId, patch: patchValue }),
      confirmVisual: (itemId, visualId, data) => on('confirmVisual', { itemId, visualId, data }),
      startSlides: () => {
        const id = activeId();
        const lesson = stateRef.current.lessons[id];
        const count = lesson.items.reduce((s, i) => s + i.slideCount, 0);
        dispatch({ type: 'startSlides', id });
        for (let i = 0; i < count; i += 1) later(700 + i * 260, () => dispatch({ type: 'slideArrived', id }));
      },
      regenerateItem: (itemId) => on('regenerateItem', { itemId }),
      moveElement: (slideId, elId, rect) => on('moveElement', { slideId, elId, rect }),
      approve: () => on('approve'),
      present: (index = 0) => {
        const lesson = stateRef.current.lessons[activeId()];
        if (!lesson?.slides.length) return;
        const issues = presentIssues(lesson);
        if (issues.pending.length || issues.unapproved) setPreflight({ index, issues });
        else { enterFullscreen(); setPresenting({ index }); }
      }
    };
  }, []);

  const exitPresenter = useCallback(() => setPresenting(null), []);
  const changeVariant = useCallback((key) => {
    const url = new URL(window.location.href);
    url.searchParams.set('variant', key);
    window.history.replaceState(null, '', url);
    setVariant(key);
  }, []);

  const lesson = state.activeId ? state.lessons[state.activeId] : null;
  const current = VARIANTS.find((v) => v.key === variant) || VARIANTS[0];
  const View = current.Component;
  const summary = useMemo(() => {
    if (!lesson) return `Chưa mở bài giảng. Có ${state.order.length} bài giảng trong bộ nhớ.`;
    const s = lessonStats(lesson);
    const phase = lesson.generating === 'outline' ? 'AI đang lập dàn ý' : lesson.generating === 'slides' ? 'đang dựng slide' : lesson.slides.length ? `${lesson.slides.length} slide` : 'chưa dựng slide';
    return `${lesson.items.length} mục, ${s.plannedSlides} slide dự kiến, ${s.minutes} phút, ${phase}; hình đã xác nhận ${s.confirmed}/${s.visuals}; ${lesson.approved ? 'đã xác nhận chuyên môn' : 'bản nháp'}`;
  }, [lesson, state.order.length]);

  return (
    <div className="lf" data-variant={variant}>
      <View key={variant} state={state} lesson={lesson} actions={actions} />
      {preflight && lesson && (
        <PreflightDialog
          issues={preflight.issues}
          onBack={() => setPreflight(null)}
          onContinue={() => { enterFullscreen(); setPresenting({ index: preflight.index }); setPreflight(null); }}
        />
      )}
      {presenting && lesson && <Presenter lesson={lesson} startIndex={presenting.index} onExit={exitPresenter} />}
      <PrototypeSwitcher variants={VARIANTS} current={variant} onChange={changeVariant} summary={summary} hidden={!!presenting} />
    </div>
  );
}
