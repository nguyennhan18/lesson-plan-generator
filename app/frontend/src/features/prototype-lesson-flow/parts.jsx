/**
 * PROTOTYPE, wipe me. Mảnh giao diện nhỏ dùng chung giữa các biến thể.
 * Chỉ là nội dung, không phải bố cục: mỗi biến thể tự quyết định đặt chúng ở đâu.
 */
import React, { useState } from 'react';
import MathText from '../../shared/math/MathText';
import { ACTIVITIES, BBT_STUBS, LESSON_MINUTES, detectSgk } from './mockLessons.js';

export const KIND_NAME = { graph: 'Đồ thị hàm số', bbt: 'Bảng biến thiên', oxyz: 'Hình Oxyz' };
export const LEVELS = ['Cơ bản', 'Trung bình', 'Khá'];

export function groupByActivity(items) {
  return ACTIVITIES.map((activity) => ({
    activity,
    items: items.filter((i) => i.activity === activity),
    minutes: items.filter((i) => i.activity === activity).reduce((s, i) => s + i.minutes, 0)
  }));
}

export function lessonStats(lesson) {
  const visuals = lesson.items.flatMap((i) => i.visuals);
  return {
    visuals: visuals.length,
    confirmed: visuals.filter((v) => v.status === 'confirmed').length,
    minutes: lesson.items.reduce((s, i) => s + i.minutes, 0),
    plannedSlides: lesson.items.reduce((s, i) => s + i.slideCount, 0)
  };
}

export function presentIssues(lesson) {
  const used = new Set(lesson.slides.flatMap((s) => s.elements.map((e) => e.visualId).filter(Boolean)));
  const pending = lesson.items.flatMap((item) => item.visuals.filter((v) => used.has(v.id) && v.status !== 'confirmed'));
  return { pending, unapproved: !lesson.approved };
}

export function ThinkingDots({ label = 'Đang soạn' }) {
  return <span className="lf-thinking" role="status" aria-label={label}><span /><span /><span /></span>;
}

export function DraftTag({ lesson }) {
  return <span className={`lf-draft ${lesson.approved ? 'is-ok' : ''}`}>{lesson.approved ? 'Đã xác nhận chuyên môn' : 'Bản nháp'}</span>;
}

export function SourcesNote() {
  return <p className="lf-sources">Chưa có nguồn đã duyệt cho bài này. Dàn ý do AI soạn, bạn cần đối chiếu với SGK.</p>;
}

export function PromptForm({ onSubmit, size = 'large', autoFocus = true }) {
  const [prompt, setPrompt] = useState('');
  const [level, setLevel] = useState('Trung bình');
  const sgk = detectSgk(prompt);
  const ready = prompt.trim().length > 8;
  const submit = (e) => {
    e.preventDefault();
    if (ready) onSubmit({ prompt: prompt.trim(), level });
  };
  return (
    <form className={`lf-prompt lf-prompt--${size}`} onSubmit={submit}>
      <label className="lf-prompt-label" htmlFor={`lf-prompt-${size}`}>Bạn muốn soạn bài gì?</label>
      <textarea
        id={`lf-prompt-${size}`}
        className="lf-prompt-input"
        rows={size === 'compact' ? 2 : 3}
        autoFocus={autoFocus}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit(e); }}
        placeholder="Ví dụ: tiết khảo sát hàm số bậc ba cho lớp 12A3, lấy ví dụ y = x³ − 3x + 1, thêm một câu trắc nghiệm củng cố."
      />
      <div className="lf-prompt-row">
        <div className="lf-prompt-field">
          <span className="lf-meta">Bài trong SGK</span>
          <span className="lf-prompt-sgk">
            {sgk ? <>{sgk} <button type="button" className="lf-link">Đổi bài</button></> : <span className="lf-meta">Hệ thống nhận diện bài khi bạn gõ</span>}
          </span>
        </div>
        <div className="lf-prompt-field">
          <span className="lf-meta">Trình độ lớp</span>
          <span className="lf-seg" role="group" aria-label="Trình độ lớp">
            {LEVELS.map((l) => <button key={l} type="button" aria-pressed={level === l} onClick={() => setLevel(l)}>{l}</button>)}
          </span>
        </div>
        <button className="lf-btn lf-btn--primary lf-prompt-submit" type="submit" disabled={!ready}>Lập dàn ý</button>
      </div>
      <p className="lf-meta lf-prompt-hint">Một bài giảng là một tiết 45 phút. Bản prototype luôn trả về dàn ý mẫu.</p>
    </form>
  );
}

export function LessonList({ state, onOpen }) {
  return (
    <ul className="lf-lessons">
      {state.order.map((id) => {
        const l = state.lessons[id];
        return (
          <li key={id}>
            <button type="button" className="lf-lesson" onClick={() => onOpen(id)}>
              <span className="lf-lesson-title"><MathText text={l.title} /></span>
              <span className="lf-meta">{l.sgk}</span>
              <span className="lf-meta">{l.slides.length ? `${l.slides.length} slide` : 'Chưa có slide'}</span>
              <DraftTag lesson={l} />
              <span className="lf-meta">{l.updatedAt}</span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

export function VisualChip({ visual, onClick, active, compact = false }) {
  const ok = visual.status === 'confirmed';
  const state = ok ? 'đã xác nhận' : visual.origin === 'ai' ? 'AI đề xuất, chờ xác nhận' : 'chờ xác nhận';
  return (
    <button type="button" className={`lf-chip ${ok ? 'is-confirmed' : ''} ${active ? 'is-active' : ''}`} onClick={onClick} aria-expanded={active} title={compact ? state : undefined}>
      <span className="lf-chip-mark" aria-hidden />
      <span className="lf-chip-kind">{KIND_NAME[visual.kind]}</span>
      <span className="lf-chip-label"><MathText text={visual.label} /></span>
      <span className={`lf-chip-state ${compact ? 'lf-sr' : ''}`}>{state}</span>
    </button>
  );
}

export function VisualConfirmForm({ item, visual, onConfirm, onClose }) {
  const [data, setData] = useState(visual.data);
  const [checked, setChecked] = useState(false);
  const ok = visual.status === 'confirmed';
  const num = (key) => ({
    type: 'number', className: 'lf-input', value: data[key], disabled: ok,
    onChange: (e) => setData((d) => ({ ...d, [key]: Number(e.target.value) }))
  });
  return (
    <div className="lf-confirm">
      <div className="lf-confirm-head">
        <h3 className="lf-h3">{KIND_NAME[visual.kind]}</h3>
        {onClose && <button type="button" className="lf-btn lf-btn--quiet lf-btn--sm" onClick={onClose}>Đóng</button>}
      </div>
      <p className="lf-meta">Thuộc mục: <MathText text={item.title} /></p>
      {visual.kind !== 'oxyz' && (
        <label className="lf-field">
          <span>Biểu thức</span>
          <span className="lf-input lf-input--math" aria-readonly><MathText text={`$y = ${data.expression}$`} /></span>
        </label>
      )}
      {visual.kind === 'graph' && (
        <div className="lf-field-grid">
          <label className="lf-field"><span>x từ</span><input {...num('xMin')} /></label>
          <label className="lf-field"><span>x đến</span><input {...num('xMax')} /></label>
          <label className="lf-field"><span>y từ</span><input {...num('yMin')} /></label>
          <label className="lf-field"><span>y đến</span><input {...num('yMax')} /></label>
        </div>
      )}
      {visual.kind === 'bbt' && (
        <p className="lf-small">
          Dạng hàm: {BBT_STUBS[data.expression]?.family || 'chưa hỗ trợ'}. Hệ thống tự tính bảng từ biểu thức này, AI không tự viết bảng.
        </p>
      )}
      {visual.kind === 'oxyz' && (
        <ul className="lf-confirm-objects">{data.objects.map((o) => <li key={o.id}><MathText text={o.label} /></li>)}</ul>
      )}
      {ok ? (
        <p className="lf-small lf-confirm-done">Đã xác nhận. Nếu dữ kiện hoặc đề bài thay đổi, hình cần được xác nhận lại.</p>
      ) : (
        <>
          <label className="lf-check">
            <input type="checkbox" checked={checked} onChange={(e) => setChecked(e.target.checked)} />
            <span>Dữ kiện trên khớp với đề bài của mục này.</span>
          </label>
          <button type="button" className="lf-btn lf-btn--primary" disabled={!checked} onClick={() => onConfirm(data)}>Xác nhận dữ kiện</button>
        </>
      )}
    </div>
  );
}

export function ConfirmForTarget({ lesson, target, actions, onClose }) {
  const item = lesson.items.find((i) => i.id === target.itemId);
  const visual = item?.visuals.find((v) => v.id === target.visualId);
  if (!item || !visual) return null;
  return <VisualConfirmForm key={visual.id + visual.status} item={item} visual={visual} onClose={onClose} onConfirm={(data) => actions.confirmVisual(item.id, visual.id, data)} />;
}

export function TimeBudget({ lesson, compact = false }) {
  const groups = groupByActivity(lesson.items);
  const total = groups.reduce((s, g) => s + g.minutes, 0);
  const slides = lesson.items.reduce((s, i) => s + i.slideCount, 0);
  return (
    <div className={`lf-budget ${compact ? 'is-compact' : ''}`}>
      <span className="lf-budget-bar" role="img" aria-label={`${total} trên ${LESSON_MINUTES} phút`}>
        {groups.map((g, idx) => g.minutes > 0 && <span key={g.activity} className={`lf-budget-seg lf-budget-seg--${idx}`} style={{ flexGrow: g.minutes }} title={`${g.activity}: ${g.minutes} phút`} />)}
        {total < LESSON_MINUTES && <span className="lf-budget-free" style={{ flexGrow: LESSON_MINUTES - total }} />}
      </span>
      <span className="lf-budget-text">
        <strong>{total}</strong>/{LESSON_MINUTES} phút, {slides} slide{total > LESSON_MINUTES ? ', vượt thời lượng tiết' : ''}
      </span>
    </div>
  );
}

export function Stepper({ label, value, min = 1, max = 99, onChange, glyphs = false }) {
  return (
    <span className="lf-stepper">
      <button type="button" aria-label={`Giảm ${label}`} disabled={value <= min} onClick={() => onChange(value - 1)}>−</button>
      <output aria-label={label}>{value}</output>
      <button type="button" aria-label={`Tăng ${label}`} disabled={value >= max} onClick={() => onChange(value + 1)}>+</button>
      {glyphs && <span className="lf-glyphs" aria-hidden>{Array.from({ length: value }, (_, i) => <i key={i} />)}</span>}
    </span>
  );
}

export function ApprovalControl({ lesson, onApprove, align = 'right' }) {
  const [open, setOpen] = useState(false);
  const [ack, setAck] = useState(false);
  if (lesson.approved) return <span className="lf-draft is-ok">Đã xác nhận chuyên môn</span>;
  return (
    <div className="lf-pop-anchor">
      <button type="button" className="lf-btn" aria-expanded={open} onClick={() => setOpen((v) => !v)}>Xác nhận chuyên môn</button>
      {open && (
        <div className={`lf-popover lf-popover--${align} lf-appear`} role="dialog" aria-label="Xác nhận chuyên môn">
          <span className="lf-small">Bộ slide đang là Bản nháp.</span>
          <label className="lf-check">
            <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} />
            <span>Tôi đã đối chiếu đề, điều kiện, lời giải, nguồn và tiến trình của phiên bản này.</span>
          </label>
          <button type="button" className="lf-btn lf-btn--primary" disabled={!ack} onClick={() => { onApprove(); setOpen(false); }}>Lưu xác nhận chuyên môn</button>
        </div>
      )}
    </div>
  );
}

export function CheckButton({ lesson, align = 'right' }) {
  const [open, setOpen] = useState(false);
  const { pending } = presentIssues(lesson);
  const edited = lesson.slides.filter((s) => s.edited).length;
  return (
    <div className="lf-pop-anchor">
      <button type="button" className="lf-btn" aria-expanded={open} onClick={() => setOpen((v) => !v)}>Kiểm tra bài</button>
      {open && (
        <div className={`lf-popover lf-popover--${align} lf-appear`} role="dialog" aria-label="Kết quả kiểm tra">
          <span className="lf-h3">Kết quả kiểm tra</span>
          <ul className="lf-report">
            {pending.map((v) => <li key={v.id}>{KIND_NAME[v.kind]} <MathText text={v.label} /> chưa xác nhận dữ kiện, sẽ bị ẩn khi trình chiếu.</li>)}
            {edited > 0 && <li>{edited} slide đã được sửa tay sau khi dựng.</li>}
            <li>Không có chữ tràn khung.</li>
          </ul>
        </div>
      )}
    </div>
  );
}

export function ElementPanel({ slide, el }) {
  if (!slide) return null;
  if (!el) {
    return (
      <div className="lf-panel-body">
        <p className="lf-h3">Slide</p>
        <dl className="lf-props"><dt>Bố cục mẫu</dt><dd>{slide.template}</dd><dt>Số phần tử</dt><dd>{slide.elements.length}</dd></dl>
        <p className="lf-meta">Chọn một phần tử trên slide để xem vị trí và kích thước. Kéo để di chuyển, kéo góc dưới bên phải để đổi cỡ. Phần tử bám theo lưới ô li.</p>
      </div>
    );
  }
  const name = { title: 'Tiêu đề', caption: 'Chú thích', paragraph: 'Đoạn văn', text: 'Danh sách ý', steps: 'Các bước giải', formula: 'Công thức', graph: 'Đồ thị hàm số', bbt: 'Bảng biến thiên', oxyz: 'Hình Oxyz', quiz: 'Câu hỏi trắc nghiệm' }[el.type];
  return (
    <div className="lf-panel-body">
      <p className="lf-h3">{name}</p>
      <dl className="lf-props">
        <dt>Vị trí</dt><dd>{el.x}, {el.y}</dd>
        <dt>Kích thước</dt><dd>{el.w} × {el.h}</dd>
        {el.parts > 1 && <><dt>Hiện dần</dt><dd>{el.parts} bước khi chiếu</dd></>}
        {el.reveal > 0 && el.parts === 1 && <><dt>Hiện dần</dt><dd>ở bước {el.reveal}</dd></>}
      </dl>
    </div>
  );
}

export function AssistantPanel() {
  return (
    <div className="lf-panel-body lf-assistant">
      <p className="lf-meta">Trợ giảng AI chỉ đề xuất sửa chữ. Nó không thêm, bỏ hay đổi hình.</p>
      <div className="lf-msg lf-msg--me">Viết lại tình huống khởi động cho ngắn hơn.</div>
      <div className="lf-msg">
        Đề xuất cho slide 2: “An nối vài điểm, Bình xét dấu đạo hàm trước. Ai vẽ đúng hình dạng?”
        <span className="lf-msg-actions">
          <button type="button" className="lf-btn lf-btn--sm">Áp dụng</button>
          <button type="button" className="lf-btn lf-btn--quiet lf-btn--sm">Bỏ qua</button>
        </span>
      </div>
      <input className="lf-input" placeholder="Nhờ trợ giảng sửa slide đang chọn" disabled />
    </div>
  );
}

export function PreflightDialog({ issues, onBack, onContinue }) {
  return (
    <div className="lf-dialog-backdrop">
      <div className="lf-dialog lf-appear" role="alertdialog" aria-modal="true" aria-labelledby="lf-preflight-title">
        <h2 id="lf-preflight-title" className="lf-h2">Trước khi trình chiếu</h2>
        {issues.pending.length > 0 && (
          <div className="lf-dialog-block">
            <p>{issues.pending.length} hình chưa xác nhận dữ kiện. Khi chiếu, các hình này bị ẩn khỏi slide.</p>
            <ul>{issues.pending.map((v) => <li key={v.id}>{KIND_NAME[v.kind]} <MathText text={v.label} /></li>)}</ul>
          </div>
        )}
        {issues.unapproved && <p className="lf-dialog-block">Bộ slide chưa có Xác nhận chuyên môn.</p>}
        <div className="lf-dialog-actions">
          <button type="button" className="lf-btn" onClick={onBack} autoFocus>Quay lại kiểm tra</button>
          <button type="button" className="lf-btn lf-btn--primary" onClick={onContinue}>Vẫn trình chiếu</button>
        </div>
      </div>
    </div>
  );
}

export function AddVisualButton() {
  const [open, setOpen] = useState(false);
  return (
    <div className="lf-pop-anchor">
      <button type="button" className="lf-link lf-link--quiet" aria-expanded={open} onClick={() => setOpen((v) => !v)}>+ Thêm hình</button>
      {open && <div className="lf-popover lf-popover--left lf-appear lf-small">Giáo viên chọn đồ thị, bảng biến thiên hoặc Hình Oxyz rồi nhập dữ kiện. Bản prototype chưa làm phần này.</div>}
    </div>
  );
}
