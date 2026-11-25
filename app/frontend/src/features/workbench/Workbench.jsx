/**
 * Bàn làm việc (spec #36, #37–#59): default and sole teaching studio interface.
 * - Top bar: breadcrumbs, expert confirmation status tag, Soạn bài mới, Bộ slide / Kế hoạch bài dạy tabs (#50),
 *   Kiểm tra bài & Xác nhận chuyên môn (#49), Trình chiếu with preflight (#41, #49), Tệp (JSON/PPTX/DOCX/ZIP #44, #50),
 *   Menu phụ (Cài đặt & Phân tích lớp học #46).
 * - Left column: saved Bài giảng bản 3 + one-click v2-to-v3 conversion (#58), or Dàn ý tree with 45-min budget & slide thumbnails.
 * - Centre: Phiếu Dàn ý, or 16:9 SlideCanvas + Dải slide (#40, #42, #48, #51–#57), or Kế hoạch bài dạy 5512 (#50).
 * - Right column: tabs Thuộc tính (Mục, Slide, Phần tử, Yêu cầu trực quan) and Trợ giảng AI (#45).
 */
import React, { useEffect, useRef, useState } from 'react';
import OutlineRequest from './OutlineRequest.jsx';
import SlideCanvas, { ELEMENT_TYPE_LABELS, findSlideVisual } from './SlideCanvas.jsx';
import WorkbenchPresenter from './WorkbenchPresenter.jsx';
import { AddVisualForm, VisualConfirmCard } from './WorkbenchVisuals.jsx';
import AnalyticsScreen from '../analytics/AnalyticsScreen.jsx';
import LessonPlanEditor from '../lesson-plan/LessonPlanEditor.jsx';
import MathText from '../../shared/math/MathText';
import MathLiveModal from '../../shared/math/MathLiveModal.jsx';
import {
  ACTIVITIES,
  ITEM_KINDS,
  KIND_ACTIVITY,
  LESSON_MINUTES,
  VISUAL_KIND_NAMES,
  isExpertConfirmed,
  measureElementTextFit,
} from '../../shared/storage/lessonProject.js';
import './workbench.css';

const UNTITLED = 'Bài giảng chưa đặt tên';
const isDataConfirmed = visual => visual.status === 'confirmed';
const plannedSlides = items => items.reduce((sum, item) => sum + item.slide_count, 0);

function groupByActivity(items) {
  return ACTIVITIES.map(activity => {
    const entries = items.map((item, index) => ({ item, number: index + 1 })).filter(({ item }) => item.activity === activity);
    return { activity, entries, minutes: entries.reduce((sum, { item }) => sum + item.minutes, 0) };
  });
}

export function validateImageFile(file) {
  return new Promise((resolve, reject) => {
    if (!file) {
      reject(new Error('Chưa chọn tệp ảnh.'));
      return;
    }
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('Không đọc được tệp ảnh đã chọn.'));
    reader.onload = () => {
      const dataUrl = String(reader.result || '');
      if (!/^data:image\/(png|jpeg|jpg|webp);base64,/i.test(dataUrl)) {
        reject(new Error('Tệp không phải định dạng ảnh PNG hoặc JPEG hợp lệ.'));
        return;
      }
      const b64 = dataUrl.split(',')[1] || '';
      try {
        const binary = atob(b64.slice(0, 32));
        const bytes = Array.from(binary, ch => ch.charCodeAt(0));
        const isPng = bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4e && bytes[3] === 0x47;
        const isJpeg = bytes[0] === 0xff && bytes[1] === 0xd8;
        const isWebp = bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46;
        if (!isPng && !isJpeg && !isWebp) {
          reject(new Error('Tệp ảnh bị hỏng hoặc không đúng định dạng PNG/JPEG.'));
          return;
        }
      } catch {
        reject(new Error('Tệp ảnh bị hỏng, không thể giải mã dữ liệu ảnh.'));
        return;
      }
      resolve(dataUrl);
    };
    reader.readAsDataURL(file);
  });
}

function StatusTag({ confirmed }) {
  const detail = confirmed
    ? 'Bộ slide có Xác nhận chuyên môn đã lưu. Máy chủ kiểm tra lại xác nhận này mỗi khi dùng tới.'
    : 'Bộ slide chưa có Xác nhận chuyên môn cho phiên bản hiện tại.';
  return <span className={`wb-tag${confirmed ? ' is-confirmed' : ''}`} title={detail}>{confirmed ? 'Đã xác nhận chuyên môn' : 'Bản nháp'}</span>;
}

function SlideGlyphs({ count }) {
  return (
    <span className="wb-glyphs" role="img" aria-label={`${count} slide`}>
      {Array.from({ length: count }, (_, index) => <i key={index} />)}
    </span>
  );
}

function VisualMark({ visual }) {
  const label = `${VISUAL_KIND_NAMES[visual.kind]}, ${isDataConfirmed(visual) ? 'đã xác nhận' : 'chờ xác nhận'}`;
  return <span className={`wb-vmark${isDataConfirmed(visual) ? ' is-confirmed' : ''}`} role="img" aria-label={label} title={label} />;
}

function VisualChip({ visual, number, onSelect }) {
  const confirmed = isDataConfirmed(visual);
  const state = confirmed ? 'đã xác nhận' : visual.origin === 'ai' ? 'AI đề xuất, chờ xác nhận' : 'chờ xác nhận';
  const Chip = onSelect ? 'button' : 'span';
  return (
    <Chip type={onSelect ? 'button' : undefined} className={`wb-chip${confirmed ? ' is-confirmed' : ''}`} onClick={onSelect}>
      <span className={`wb-vmark${confirmed ? ' is-confirmed' : ''}`} aria-hidden="true" />
      <span className="wb-chip-kind">{VISUAL_KIND_NAMES[visual.kind]}</span>
      {visual.label && <MathText text={visual.label} />}
      <span className="wb-chip-state">{number ? `Mục ${number}, ${state}` : state}</span>
    </Chip>
  );
}

function TimeBudget({ items, compact = false }) {
  const groups = groupByActivity(items);
  const total = groups.reduce((sum, group) => sum + group.minutes, 0);
  const slides = plannedSlides(items);
  const free = LESSON_MINUTES - total;
  const summary = `Thời lượng: ${groups.map(group => `${group.activity} ${group.minutes} phút`).join(', ')}; tổng ${total} trên ${LESSON_MINUTES} phút.`;
  return (
    <div className={`wb-budget${compact ? ' is-compact' : ''}`}>
      <span className="wb-budget-bar" role="img" aria-label={summary}>
        {groups.map((group, index) => group.minutes > 0 && (
          <span key={group.activity} className={`wb-budget-seg wb-budget-seg--${index}`} style={{ flexGrow: group.minutes }} title={`${group.activity}: ${group.minutes} phút`} />
        ))}
        {free > 0 && <span className="wb-budget-free" style={{ flexGrow: free }} title={`Còn ${free} phút`} />}
      </span>
      <span className="wb-budget-text">
        <strong>{total}</strong>/{LESSON_MINUTES} phút, {slides} slide{free < 0 ? `, vượt ${-free} phút` : ''}
      </span>
      {!compact && (
        <ul className="wb-budget-legend">
          {groups.map((group, index) => (
            <li key={group.activity}><span className={`wb-budget-seg wb-budget-seg--${index}`} aria-hidden="true" />{group.activity}: {group.minutes} phút</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function LessonList({ lessons, legacyCount, legacyProjects = [], onOpen }) {
  return (
    <div className="wb-panel">
      {lessons === null && <p className="wb-meta">Đang đọc các Bài giảng đã lưu…</p>}
      {lessons?.length === 0 && <p className="wb-meta">Chưa có Bài giảng bản 3 nào trên máy này. Nhập tệp JSON từ menu Tệp.</p>}
      {lessons?.length > 0 && (
        <ul className="wb-lessons">
          {lessons.map(lesson => (
            <li key={lesson.project_id}>
              <button type="button" className="wb-lesson" onClick={() => onOpen(lesson.project_id)}>
                <span className="wb-lesson-title"><MathText text={lesson.title || UNTITLED} /></span>
                {lesson.sgk && <span className="wb-meta">{lesson.sgk}</span>}
                <span className="wb-lesson-meta">
                  <span className="wb-meta">{lesson.items} Mục, {lesson.slides ? `${lesson.slides} slide` : 'chưa có slide'}</span>
                  <StatusTag confirmed={lesson.expert_confirmed} />
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {legacyCount > 0 && (
        <div className="wb-legacy">
          <p className="wb-meta">
            Máy này có {legacyCount} dự án bản 2. Chọn để chuyển sang Bài giảng bản 3 (bản 2 gốc vẫn được giữ nguyên):
          </p>
          {legacyProjects.length > 0 && (
            <ul className="wb-lessons">
              {legacyProjects.map(proj => (
                <li key={proj.project_id}>
                  <button type="button" className="wb-lesson" onClick={() => onOpen(proj.project_id)}>
                    <span className="wb-lesson-title">{proj.title}</span>
                    <span className="wb-meta">Dự án bản 2 ({proj.slides} slide) — bấm để chuyển sang bản 3</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function OutlineTree({ lesson, selectedId, activeSlideId, expandedItems, onSelectItem, onSelectSlide, animate }) {
  const items = lesson.outline.items;
  const allSlides = lesson.deck?.slides || [];
  return (
    <>
      <div className="wb-tree-head"><TimeBudget items={items} compact /></div>
      {groupByActivity(items).map(group => (
        <section key={group.activity} className="wb-act" aria-label={group.activity}>
          <h3 className="wb-act-title"><span>{group.activity}</span><span>{group.minutes} phút</span></h3>
          {group.entries.length === 0 ? <p className="wb-meta wb-act-empty">Chưa có Mục.</p> : (
            <ol className="wb-items">
              {group.entries.map(({ item, number }) => {
                const ownSlides = allSlides.filter(s => s.item_id === item.item_id);
                const isExpanded = Boolean(expandedItems?.[item.item_id]);
                return (
                  <li key={item.item_id} className={animate ? 'wb-ink' : undefined} style={animate ? { animationDelay: `${Math.min(number - 1, 24) * 65}ms` } : undefined}>
                    <button
                      type="button"
                      className="wb-item"
                      aria-current={item.item_id === selectedId ? 'true' : undefined}
                      onClick={() => onSelectItem(item.item_id)}
                    >
                      <span className="wb-item-n">{number}</span>
                      <span className="wb-item-body">
                        <span className="wb-item-title"><MathText text={item.title} /></span>
                        <span className="wb-item-meta">
                          <span className="wb-meta">{item.kind}</span>
                          <SlideGlyphs count={item.slide_count} />
                          {item.visuals.map(visual => <VisualMark key={visual.visual_id} visual={visual} />)}
                          {item.needs_review && <span className="wb-review-mark">Cần xem lại</span>}
                        </span>
                      </span>
                    </button>
                    {isExpanded && ownSlides.length > 0 && (
                      <div className="wb-item-slides" role="group" aria-label={`Slide của Mục ${number}`}>
                        {ownSlides.map(slide => {
                          const globalIndex = allSlides.indexOf(slide) + 1;
                          const isCurrent = slide.slide_id === activeSlideId;
                          return (
                            <button
                              key={slide.slide_id}
                              type="button"
                              className={`wb-mini${isCurrent ? ' is-current' : ''}`}
                              aria-label={`Mục ${number}, Slide ${globalIndex}`}
                              aria-current={isCurrent ? 'true' : undefined}
                              onClick={() => onSelectSlide(slide.slide_id)}
                            >
                              <SlideCanvas lesson={lesson} slide={slide} mode="thumb" fit="width" className="wb-sheet-thumb" />
                              <span className="wb-meta">Slide {globalIndex}</span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </li>
                );
              })}
            </ol>
          )}
        </section>
      ))}
    </>
  );
}

function OutlineSheet({ lesson, onSelect, onBuildSlides, buildingSlides, buildError, disabled }) {
  const items = lesson.outline.items;
  const visuals = items.flatMap((item, index) => item.visuals.map(visual => ({ item, number: index + 1, visual })));
  const sources = Array.isArray(lesson.source_refs)
    ? lesson.source_refs.filter(source => typeof source?.id === 'string' && typeof source?.source_type === 'string')
    : [];
  const pending = visuals.filter(({ visual }) => !isDataConfirmed(visual)).length;
  const planned = plannedSlides(items);
  const about = [lesson.sgk, lesson.level && `Trình độ lớp: ${lesson.level.toLowerCase()}`].filter(Boolean).join('. ');
  return (
    <article className="wb-sheet wb-fade" aria-labelledby="wb-sheet-title">
      <p className="wb-label">Phiếu Dàn ý, chỉ xem</p>
      <h1 id="wb-sheet-title" className="wb-sheet-title"><MathText text={lesson.title || UNTITLED} /></h1>
      {about && <p className="wb-meta">{about}</p>}
      <dl className="wb-facts">
        <div><dt>Mục dàn ý</dt><dd>{items.length}</dd></div>
        <div><dt>Slide dự kiến</dt><dd>{planned}</dd></div>
        <div><dt>Bộ slide</dt><dd>{lesson.deck ? `${lesson.deck.slides.length} slide` : 'chưa dựng'}</dd></div>
      </dl>
      <TimeBudget items={items} />
      {items.reduce((total, item) => total + item.minutes, 0) !== LESSON_MINUTES &&
        <p className="wb-meta" role="status">Thời lượng dự kiến khác {LESSON_MINUTES} phút.</p>}
      <section aria-label="Nguồn đã duyệt">
        {sources.length > 0 ? <>
          <h2 className="wb-h3">Nguồn đã duyệt đã dùng</h2>
          <ul>{sources.map((source, index) => <li key={index}>{source.id} · {source.source_type}</li>)}</ul>
        </> : <p className="wb-meta">Chưa có nguồn đã duyệt cho bài này</p>}
      </section>
      <section className="wb-visuals" aria-labelledby="wb-sheet-visuals">
        <h2 id="wb-sheet-visuals" className="wb-h3">Yêu cầu trực quan</h2>
        {visuals.length === 0 ? <p className="wb-meta">Dàn ý chưa có Yêu cầu trực quan nào.</p> : (
          <>
            <p className="wb-meta">
              {pending ? `${pending} hình chờ xác nhận dữ kiện. Hình chỉ được dựng sau khi dữ kiện được xác nhận.` : 'Mọi hình đã được xác nhận dữ kiện.'}
            </p>
            <ul className="wb-chips">
              {visuals.map(({ item, number, visual }) => (
                <li key={visual.visual_id}><VisualChip visual={visual} number={number} onSelect={() => onSelect(item.item_id)} /></li>
              ))}
            </ul>
          </>
        )}
      </section>
      {buildError && <p role="alert" className="wb-error-text">{buildError}</p>}
      <div className="wb-form-row">
        <button
          type="button"
          className="wb-btn wb-btn--primary"
          disabled={disabled || buildingSlides || items.length === 0}
          onClick={onBuildSlides}
        >
          {buildingSlides ? 'Đang dựng bộ slide…' : 'Dựng bộ slide'}
        </button>
      </div>
    </article>
  );
}

function SlideProperties({ lesson, slide, actions, disabled, showDetails = false }) {
  const imgInput = useRef(null);
  const [imgError, setImgError] = useState('');

  const handleImagePicked = async event => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setImgError('');
    try {
      const dataUrl = await validateImageFile(file);
      await actions.addElement(slide.slide_id, { type: 'image', src: dataUrl, alt: file.name });
    } catch (err) {
      setImgError(err.message);
    }
  };

  return (
    <div className="wb-panel wb-fade" key={`slide-tools-${slide.slide_id}`}>
      {showDetails && (
        <>
          <h3 className="wb-h3">Slide</h3>
          <dl className="wb-props">
            <dt>Bố cục mẫu</dt><dd>{slide.layout}</dd>
            <dt>Số phần tử</dt><dd>{slide.elements.length}</dd>
            {slide.edited && <><dt>Trạng thái</dt><dd>Đã sửa tay</dd></>}
          </dl>
          <p className="wb-meta">Chọn một phần tử trên canvas để xem vị trí, kích thước và sửa nội dung. Nhấp đúp vào chữ hoặc công thức để sửa nhanh.</p>
        </>
      )}

      <h4 className="wb-label">Thêm phần tử vào slide (#48)</h4>
      <div className="wb-form-row">
        <button type="button" className="wb-btn" disabled={disabled} onClick={() => actions.addElement(slide.slide_id, { type: 'paragraph', text: 'Đoạn văn mới' })}>
          + Đoạn văn
        </button>
        <button type="button" className="wb-btn" disabled={disabled} onClick={() => actions.addElement(slide.slide_id, { type: 'formula', latex: "f'(x) = 0" })}>
          + Công thức
        </button>
        <button type="button" className="wb-btn" disabled={disabled} onClick={() => actions.addElement(slide.slide_id, { type: 'table', headers: ['x', 'y'], rows: [['0', '1']] })}>
          + Bảng
        </button>
        <button type="button" className="wb-btn" disabled={disabled} onClick={() => imgInput.current?.click()}>
          + Hình ảnh
        </button>
        <input ref={imgInput} type="file" accept="image/png,image/jpeg,.png,.jpg,.jpeg" className="wb-hidden" aria-label="Tải ảnh lên slide" onChange={handleImagePicked} />
      </div>
      {imgError && <p role="alert" className="wb-error-text">{imgError}</p>}
    </div>
  );
}

function ElementProperties({ lesson, slide, element, actions, onOpenMathModal, disabled }) {
  const fit = measureElementTextFit(element);
  const isOverflow = Boolean(element.overflow || fit.overflow);
  const typeLabel = ELEMENT_TYPE_LABELS[element.type] || element.type;
  const reveal = element.reveal ?? 0;
  const parts = element.parts ?? 1;
  const visual = findSlideVisual(lesson, slide, element.visual_id);
  const ownerItem = lesson?.outline?.items.find(it => it.item_id === slide?.item_id);

  const saveElementContent = event => {
    event.preventDefault();
    const fd = new FormData(event.currentTarget);
    if (element.type === 'title' || element.type === 'paragraph' || element.type === 'caption') {
      actions.changeElement(slide.slide_id, element.element_id, { text: String(fd.get('text') || '').trim() });
    } else if (element.type === 'text' || element.type === 'steps') {
      const items = String(fd.get('items') || '').split('\n').map(s => s.trim()).filter(Boolean);
      if (items.length > 0) {
        actions.changeElement(slide.slide_id, element.element_id, { items, parts: items.length });
      }
    } else if (element.type === 'formula') {
      actions.changeElement(slide.slide_id, element.element_id, { latex: String(fd.get('latex') || '').trim() });
    } else if (element.type === 'table') {
      const headers = String(fd.get('headers') || '').split('|').map(s => s.trim()).filter(Boolean);
      const rows = String(fd.get('rows') || '').split('\n').map(line => line.split('|').map(c => c.trim())).filter(r => r.some(Boolean));
      if (headers.length > 0 && rows.length > 0) {
        actions.changeElement(slide.slide_id, element.element_id, { headers, rows });
      }
    } else if (element.type === 'quiz') {
      const question = String(fd.get('question') || '').trim();
      const nextOpts = (element.options || []).map((opt, idx) => ({
        ...opt,
        text: String(fd.get(`opt_${idx}`) ?? opt.text).trim(),
      }));
      actions.changeElement(slide.slide_id, element.element_id, { question, options: nextOpts });
    }
  };

  return (
    <div className="wb-panel wb-fade" key={element.element_id}>
      <h3 className="wb-h3">{typeLabel}</h3>
      <dl className="wb-props">
        <dt>Loại phần tử</dt><dd>{typeLabel}</dd>
        <dt>Vị trí</dt><dd>{element.x}, {element.y}</dd>
        <dt>Kích thước</dt><dd>{element.w} × {element.h}</dd>
        <dt>Hiện dần</dt><dd>Bước {reveal}, {parts} phần</dd>
        {isOverflow && <><dt>Cảnh báo</dt><dd><span className="wb-review-mark">Tràn chữ</span></dd></>}
      </dl>

      {visual && ownerItem ? (
        <VisualConfirmCard lesson={lesson} item={ownerItem} visual={visual} actions={actions} disabled={disabled} />
      ) : (
        <form className="wb-form" onSubmit={saveElementContent}>
          <fieldset disabled={disabled}>
            {(element.type === 'title' || element.type === 'paragraph' || element.type === 'caption') && (
              <label>Nội dung chữ
                <textarea name="text" rows={3} defaultValue={element.text || ''} required />
              </label>
            )}
            {(element.type === 'text' || element.type === 'steps') && (
              <label>Các dòng (mỗi dòng một ý)
                <textarea name="items" rows={4} defaultValue={(element.items || []).join('\n')} required />
              </label>
            )}
            {element.type === 'formula' && (
              <>
                <label>Công thức LaTeX
                  <input name="latex" defaultValue={element.latex || element.text || ''} required />
                </label>
                <button type="button" className="wb-btn" onClick={() => onOpenMathModal(element)}>
                  Mở bộ gõ công thức
                </button>
              </>
            )}
            {element.type === 'table' && (
              <>
                <label>Tiêu đề cột (ngăn cách bằng |)
                  <input name="headers" defaultValue={(element.headers || []).join(' | ')} required />
                </label>
                <label>Các dòng dữ liệu (mỗi dòng một hàng, ngăn cách ô bằng |)
                  <textarea name="rows" rows={3} defaultValue={(element.rows || []).map(r => r.join(' | ')).join('\n')} required />
                </label>
              </>
            )}
            {element.type === 'quiz' && (
              <>
                <label>Câu hỏi trắc nghiệm
                  <textarea name="question" rows={2} defaultValue={element.question || ''} required />
                </label>
                {(element.options || []).map((opt, idx) => (
                  <label key={opt.label || idx}>Phương án {opt.label}
                    <input name={`opt_${idx}`} defaultValue={opt.text || ''} required />
                  </label>
                ))}
              </>
            )}
            {element.type !== 'image' && (
              <button type="submit" className="wb-btn wb-btn--primary">Lưu nội dung phần tử</button>
            )}
          </fieldset>
        </form>
      )}

      <div className="wb-form-row">
        <button
          type="button"
          className="wb-btn"
          disabled={disabled}
          onClick={() => actions.removeElement(slide.slide_id, element.element_id)}
        >
          Xóa phần tử
        </button>
      </div>
    </div>
  );
}

function ItemProperties({ lesson, itemId, activeSlideId, actions, disabled }) {
  const [confirmRegen, setConfirmRegen] = useState(false);
  const [regenBusy, setRegenBusy] = useState(false);
  const [regenError, setRegenError] = useState('');

  if (!lesson) return <p className="wb-panel wb-meta">Mở một Bài giảng để xem Dàn ý và thuộc tính của từng Mục.</p>;
  const index = lesson.outline.items.findIndex(item => item.item_id === itemId);
  if (index < 0) return <p className="wb-panel wb-meta">Chọn một Mục ở cột trái để xem Loại mục, số slide, số phút và hình của Mục đó.</p>;
  const item = lesson.outline.items[index];
  const ownSlides = lesson.deck ? lesson.deck.slides.filter(slide => slide.item_id === item.item_id) : [];
  const built = ownSlides.length;
  const hasEditedSlides = ownSlides.some(slide => Boolean(slide.edited));

  const runRegenerate = async () => {
    setRegenError('');
    setRegenBusy(true);
    try {
      await actions.regenerateItemSlides(item.item_id);
      setConfirmRegen(false);
    } catch (error) {
      setRegenError(error.message);
    } finally {
      setRegenBusy(false);
    }
  };

  const handleRegenClick = () => {
    if (hasEditedSlides && !confirmRegen) {
      setConfirmRegen(true);
      return;
    }
    runRegenerate();
  };

  return (
    <div className="wb-panel wb-fade" key={item.item_id}>
      <p className="wb-meta">Mục {index + 1}, {item.activity}</p>
      <h3 className="wb-h3"><MathText text={item.title} /></h3>
      <dl className="wb-props">
        <dt>Loại mục</dt><dd>{item.kind}</dd>
        <dt>Số slide</dt><dd>{item.slide_count} <SlideGlyphs count={item.slide_count} /></dd>
        <dt>Số phút</dt><dd>{item.minutes}</dd>
        <dt>Slide đã dựng</dt><dd>{built}</dd>
        {item.needs_review && <><dt>Trạng thái</dt><dd><span className="wb-review-mark">Cần xem lại</span></dd></>}
      </dl>
      {item.needs_review && lesson.deck && (
        <div className="wb-regen-box">
          <button
            type="button"
            className="wb-btn"
            disabled={disabled || regenBusy}
            onClick={handleRegenClick}
          >
            {regenBusy ? 'Đang sinh lại…' : 'Sinh lại slide của mục này'}
          </button>
          {confirmRegen && (
            <div className="wb-regen-warn" role="alert">
              <p className="wb-meta">Các slide của Mục này đã được sửa tay. Sinh lại sẽ thay thế các chỉnh sửa đó.</p>
              <div className="wb-form-row">
                <button type="button" className="wb-btn wb-btn--primary" disabled={regenBusy} onClick={runRegenerate}>
                  Xác nhận sinh lại
                </button>
                <button type="button" className="wb-btn" disabled={regenBusy} onClick={() => setConfirmRegen(false)}>
                  Hủy
                </button>
              </div>
            </div>
          )}
          {regenError && <p role="alert" className="wb-error-text">{regenError}</p>}
        </div>
      )}
      {item.points.length > 0 && (
        <>
          <h4 className="wb-label">Các ý</h4>
          <ul className="wb-points">{item.points.map((point, i) => <li key={i}><MathText text={point} /></li>)}</ul>
        </>
      )}
      <ItemEditor key={JSON.stringify(item)} item={item} index={index} items={lesson.outline.items}
        built={built} actions={actions} disabled={disabled} />
      <h4 className="wb-label">Hình</h4>
      {item.visuals.length > 0 && (
        <>
          <ul className="wb-chips">{item.visuals.map(visual => <li key={visual.visual_id}><VisualChip visual={visual} /></li>)}</ul>
          {item.visuals.map(visual => (
            <VisualConfirmCard key={visual.visual_id} lesson={lesson} item={item} visual={visual} actions={actions} disabled={disabled} />
          ))}
        </>
      )}
      <AddVisualForm item={item} activeSlideId={activeSlideId} actions={actions} disabled={disabled} />
    </div>
  );
}

function ItemEditor({ item, index, items, built, actions, disabled }) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const apply = async action => {
    setError('');
    setBusy(true);
    try { await action(); }
    catch (error) { setError(error.message); }
    finally { setBusy(false); }
  };
  const initialPoints = item.points.join('\n');
  const save = event => {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const title = fields.get('title');
    const points = fields.get('points');
    if (!title.trim()) { setError('Hãy nhập tiêu đề Mục.'); return; }
    apply(() => actions.editItem(item.item_id, {
      title: title === item.title ? item.title : title.trim(),
      points: points === initialPoints ? item.points : points.split('\n').map(point => point.trim()).filter(Boolean),
      slide_count: Number(fields.get('slide_count')), minutes: Number(fields.get('minutes'))
    }));
  };
  return <form className="wb-form" onSubmit={save}>
    <fieldset disabled={disabled || busy}>
      <label>Tiêu đề Mục<input name="title" defaultValue={item.title} required /></label>
      <label>Các ý (mỗi dòng một ý)<textarea name="points" rows={4} defaultValue={initialPoints} /></label>
      <label>Số slide dự kiến<input type="number" name="slide_count" min="1" max="4" required defaultValue={item.slide_count} /></label>
      <label>Số phút dự kiến<input type="number" name="minutes" min="1" max={LESSON_MINUTES} required defaultValue={item.minutes} /></label>
      <button className="wb-btn wb-btn--primary" type="submit">Lưu Mục</button>
      <div className="wb-form-row">
        {[-1, 1].map(direction => <button key={direction} type="button" className="wb-btn"
          disabled={items[index + direction]?.activity !== item.activity}
          onClick={() => apply(() => actions.moveItem(item.item_id, direction))}>{direction < 0 ? 'Lên' : 'Xuống'}</button>)}
        <button type="button" className="wb-btn" onClick={() => setConfirmDelete(value => !value)}>Xóa Mục</button>
      </div>
      {confirmDelete && <div className="wb-form-row">
        <p className="wb-meta">{built ? `Xóa cả ${built} slide đã dựng từ Mục này?` : 'Xóa Mục này khỏi Dàn ý?'}</p>
        <button type="button" className="wb-btn" onClick={() => apply(() => actions.removeItem(item.item_id))}>Xác nhận xóa</button>
      </div>}
    </fieldset>
    {error && <p role="alert">{error}</p>}
  </form>;
}

function AddItem({ actions, onSelect, disabled }) {
  const [activity, setActivity] = useState(ACTIVITIES[0]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const kinds = ITEM_KINDS.filter(kind => !KIND_ACTIVITY[kind] || KIND_ACTIVITY[kind] === activity);

  async function add(event) {
    event.preventDefault();
    const kind = new FormData(event.currentTarget).get('kind');
    setBusy(true);
    setError('');
    try {
      const id = await actions.addItem(activity, kind);
      if (id) onSelect(id);
    } catch (error) { setError(error.message); }
    finally { setBusy(false); }
  }

  return <form className="wb-panel wb-form" onSubmit={add}>
    <fieldset disabled={disabled || busy}>
      <label>Hoạt động của Mục mới
        <select value={activity} onChange={event => setActivity(event.target.value)}>
          {ACTIVITIES.map(value => <option key={value}>{value}</option>)}
        </select>
      </label>
      <label>Loại mục mới
        <select key={activity} name="kind">{kinds.map(kind => <option key={kind}>{kind}</option>)}</select>
      </label>
      <button className="wb-btn" type="submit">Thêm Mục</button>
    </fieldset>
    {error && <p role="alert">{error}</p>}
  </form>;
}

function AssistantPanel({ activeSlide, actions, disabled }) {
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [proposal, setProposal] = useState(null);

  if (!activeSlide) {
    return <p className="wb-panel wb-meta">Hãy dựng và chọn một slide trên canvas để dùng Trợ giảng AI.</p>;
  }

  const handleSubmit = async event => {
    event.preventDefault();
    if (!message.trim()) return;
    setBusy(true);
    setError('');
    try {
      const result = await actions.askAssistant(activeSlide.slide_id, message.trim());
      setProposal(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleApply = async () => {
    if (!proposal?.patched_slide) return;
    await actions.applyAssistantPatch(proposal.patched_slide);
    setProposal(null);
    setMessage('');
  };

  return (
    <div className="wb-panel wb-fade">
      <h3 className="wb-h3">Trợ giảng AI</h3>
      <p className="wb-meta">Chỉ đề xuất sửa phần tử chữ cho slide đang chọn. Không tự thêm hay sửa Hình tương tác.</p>
      <form className="wb-form" onSubmit={handleSubmit}>
        <fieldset disabled={disabled || busy}>
          <label>Yêu cầu cho slide đang chọn
            <textarea
              rows={3}
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="Ví dụ: Rút gọn tiêu đề hoặc làm rõ bước giải thứ hai"
              required
            />
          </label>
          <button type="submit" className="wb-btn wb-btn--primary">
            {busy ? 'Đang hỏi Trợ giảng AI…' : 'Gửi yêu cầu'}
          </button>
        </fieldset>
      </form>
      {error && <p role="alert" className="wb-error-text">{error}</p>}
      {proposal && (
        <div className="wb-assistant-proposal" data-testid="wb-assistant-proposal">
          <p><strong>Phản hồi AI:</strong> {proposal.ai_response}</p>
          {proposal.diffs?.length > 0 ? (
            <ul className="wb-points">
              {proposal.diffs.map(diff => (
                <li key={diff.element_id}>
                  <strong>{ELEMENT_TYPE_LABELS[diff.type] || diff.type}:</strong>{' '}
                  <code>{JSON.stringify(diff.before)}</code> → <code>{JSON.stringify(diff.after)}</code>
                </li>
              ))}
            </ul>
          ) : (
            <p className="wb-meta">Không có thay đổi phần tử nào được đề xuất.</p>
          )}
          <div className="wb-form-row">
            <button type="button" className="wb-btn wb-btn--primary" onClick={handleApply}>
              Áp dụng
            </button>
            <button type="button" className="wb-btn" onClick={() => setProposal(null)}>
              Bỏ qua
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function LessonPlanWorkbench({ lesson, actions, disabled }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [exportErr, setExportErr] = useState('');

  const handleGenerate = async () => {
    setBusy(true);
    setError('');
    try {
      await actions.generateLessonPlan();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleExport = async fn => {
    setExportErr('');
    try {
      await fn();
    } catch (err) {
      setExportErr(err.message);
    }
  };

  return (
    <article className="wb-sheet wb-fade" aria-label="Kế hoạch bài dạy">
      <div className="wb-form-row" style={{ justifyContent: 'space-between' }}>
        <div>
          <p className="wb-label">Kế hoạch bài dạy theo Công văn 5512 (#50)</p>
          <h1 className="wb-sheet-title"><MathText text={lesson.title || UNTITLED} /></h1>
        </div>
        {lesson.plan?.needs_review && (
          <span className="wb-tag" data-testid="wb-plan-stale-badge">Lệch Dàn ý</span>
        )}
      </div>

      {lesson.plan?.needs_review && (
        <p role="status" className="wb-meta">
          Dàn ý đã thay đổi sau khi soạn Kế hoạch bài dạy này. Bạn có thể bấm «Soạn Kế hoạch bài dạy» để sinh lại theo Dàn ý mới.
        </p>
      )}

      <div className="wb-form-row">
        <button
          type="button"
          className="wb-btn wb-btn--primary"
          disabled={disabled || busy}
          onClick={handleGenerate}
        >
          {busy ? 'Đang soạn Kế hoạch bài dạy…' : 'Soạn Kế hoạch bài dạy'}
        </button>
        {lesson.plan && (
          <>
            <button type="button" className="wb-btn" disabled={disabled} onClick={() => handleExport(actions.exportDocx)}>
              Xuất Word (.docx)
            </button>
            <button type="button" className="wb-btn" disabled={disabled} onClick={() => handleExport(actions.exportZip)}>
              Xuất gói ZIP
            </button>
          </>
        )}
      </div>

      {error && <p role="alert" className="wb-error-text">{error}</p>}
      {exportErr && <p role="alert" className="wb-error-text">{exportErr}</p>}

      {lesson.plan ? (
        <div className="wb-plan-content">
          <LessonPlanEditor
            plan={lesson.plan}
            onChange={next => actions.updateLessonPlan(next)}
          />
          <section className="wb-plan-activities">
            {(lesson.plan.activities || []).map(act => (
              <div key={act.activity_number} className="wb-visual-card">
                <h3 className="wb-h3">
                  Hoạt động {act.activity_number}: <MathText text={act.goal || ''} /> ({act.time_minutes} phút)
                </h3>
                <p><strong>Sản phẩm dự kiến:</strong> <MathText text={act.expected_product || ''} /></p>
              </div>
            ))}
          </section>
        </div>
      ) : (
        <p className="wb-meta">Chưa có Kế hoạch bài dạy cho Bài giảng này. Bấm «Soạn Kế hoạch bài dạy» để sinh trực tiếp từ Dàn ý đã duyệt.</p>
      )}
    </article>
  );
}

function FileMenu({ lesson, actions }) {
  const [open, setOpen] = useState(false);
  const [exportErr, setExportErr] = useState('');
  const box = useRef(null), picker = useRef(null);
  useEffect(() => {
    if (!open) return undefined;
    const close = event => {
      if (event.type === 'keydown' ? event.key === 'Escape' : !box.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener('pointerdown', close);
    document.addEventListener('keydown', close);
    return () => {
      document.removeEventListener('pointerdown', close);
      document.removeEventListener('keydown', close);
    };
  }, [open]);
  const importChosen = event => {
    const file = event.target.files?.[0];
    event.target.value = '';
    setOpen(false);
    if (file) actions.importFile(file);
  };
  const runExport = async fn => {
    setOpen(false);
    setExportErr('');
    try {
      await fn();
    } catch (err) {
      setExportErr(err.message);
    }
  };
  const canExport = Boolean(lesson);
  const hasSlides = Boolean(lesson?.deck?.slides?.length);
  const hasPlan = Boolean(lesson?.plan);
  return (
    <div className="wb-menu" ref={box}>
      <button type="button" className="wb-btn" aria-expanded={open} aria-controls="wb-file-menu" onClick={() => setOpen(value => !value)}>Tệp</button>
      <input ref={picker} type="file" accept="application/json,.json" className="wb-hidden" aria-label="Nhập tệp JSON" tabIndex={-1} onChange={importChosen} />
      {open && (
        <div id="wb-file-menu" className="wb-menu-list" role="group" aria-label="Tệp">
          <button type="button" onClick={() => picker.current?.click()}>Nhập tệp JSON bản 3…</button>
          <button type="button" disabled={!canExport} onClick={() => { setOpen(false); actions.exportLesson(); }}>Xuất tệp JSON</button>
          <button type="button" disabled={!hasSlides} onClick={() => runExport(actions.exportPptx)}>Xuất PPTX</button>
          <button type="button" disabled={!hasPlan} onClick={() => runExport(actions.exportDocx)}>Xuất Word (.docx)</button>
          <button type="button" disabled={!hasSlides && !hasPlan} onClick={() => runExport(actions.exportZip)}>Xuất gói ZIP</button>
        </div>
      )}
      {exportErr && <span role="alert" className="wb-error-text">{exportErr}</span>}
    </div>
  );
}

function SecondaryMenu({ onOpenSettings, onOpenAnalytics }) {
  const [open, setOpen] = useState(false);
  const box = useRef(null);
  useEffect(() => {
    if (!open) return undefined;
    const close = event => {
      if (event.type === 'keydown' ? event.key === 'Escape' : !box.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener('pointerdown', close);
    document.addEventListener('keydown', close);
    return () => {
      document.removeEventListener('pointerdown', close);
      document.removeEventListener('keydown', close);
    };
  }, [open]);
  return (
    <div className="wb-menu" ref={box}>
      <button type="button" className="wb-btn" aria-expanded={open} aria-controls="wb-aux-menu" onClick={() => setOpen(v => !v)}>
        Menu phụ
      </button>
      {open && (
        <div id="wb-aux-menu" className="wb-menu-list" role="group" aria-label="Menu phụ">
          <button type="button" onClick={() => { setOpen(false); onOpenSettings(); }}>Cài đặt</button>
          <button type="button" onClick={() => { setOpen(false); onOpenAnalytics(); }}>Phân tích lớp học</button>
        </div>
      )}
    </div>
  );
}

function Notice({ notice, actions }) {
  return (
    <div className="wb-notice" role="alert">
      <p>{notice.message}</p>
      <div className="wb-notice-actions">
        {notice.kind === 'save-failed' && (
          <>
            <button type="button" className="wb-btn wb-btn--primary" onClick={actions.retrySave}>Lưu lại</button>
            <button type="button" className="wb-btn" onClick={actions.exportLesson}>Xuất tệp JSON dự phòng</button>
          </>
        )}
        {notice.kind === 'conflict' ? (
          <>
            <button type="button" className="wb-btn wb-btn--primary" onClick={actions.replaceStored}>Thay bằng bản trong tệp</button>
            <button type="button" className="wb-btn" onClick={actions.keepStored}>Giữ bản trên máy</button>
          </>
        ) : <button type="button" className="wb-btn wb-btn--quiet" onClick={actions.dismissNotice}>Đóng</button>}
      </div>
    </div>
  );
}

export default function Workbench({ session, actions }) {
  const { lesson, notice } = session;
  const [modalOpen, setModalOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [buildingSlides, setBuildingSlides] = useState(false);
  const [buildError, setBuildError] = useState('');
  const [presentingSlideId, setPresentingSlideId] = useState(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [qualityOpen, setQualityOpen] = useState(false);
  const [qualityReport, setQualityReport] = useState(null);
  const [qualityAck, setQualityAck] = useState(false);
  const [qualityBusy, setQualityBusy] = useState(false);
  const [qualityError, setQualityError] = useState('');
  const [preflightOpen, setPreflightOpen] = useState(false);
  const [centreTab, setCentreTab] = useState('slides'); // 'slides' | 'plan'
  const [rightTab, setRightTab] = useState('props');   // 'props' | 'assistant'
  const [mathModalEl, setMathModalEl] = useState(null);
  const [dropError, setDropError] = useState('');

  const dialog = useRef(null);
  const settingsDialog = useRef(null);
  const analyticsDialog = useRef(null);
  const qualityDialog = useRef(null);
  const preflightDialog = useRef(null);
  const disabled = session.saveState !== 'saved';

  const created = () => {
    if (dialog.current?.open) dialog.current.close();
  };

  const [selection, setSelection] = useState({
    lessonId: null,
    itemId: null,
    slideId: null,
    elementId: null,
    expanded: {},
  });

  const isSameLesson = Boolean(lesson && selection.lessonId === lesson.project_id);
  const selectedId = isSameLesson ? selection.itemId : null;
  const slides = lesson?.deck?.slides || [];
  const activeSlide = (isSameLesson && slides.find(s => s.slide_id === selection.slideId)) || slides[0] || null;
  const selectedElementId = isSameLesson ? selection.elementId : null;
  const selectedElement = activeSlide?.elements.find(el => el.element_id === selectedElementId) || null;
  const expandedItems = isSameLesson ? selection.expanded : {};

  const selectItem = itemId => {
    if (!lesson) return;
    const firstSlideOfItem = (lesson.deck?.slides || []).find(s => s.item_id === itemId);
    setSelection(prev => {
      const prevExpanded = prev.lessonId === lesson.project_id ? prev.expanded : {};
      return {
        lessonId: lesson.project_id,
        itemId,
        slideId: firstSlideOfItem ? firstSlideOfItem.slide_id : (prev.lessonId === lesson.project_id ? prev.slideId : null),
        elementId: null,
        expanded: { ...prevExpanded, [itemId]: true },
      };
    });
  };

  const selectSlide = slideId => {
    if (!lesson) return;
    const targetSlide = (lesson.deck?.slides || []).find(s => s.slide_id === slideId);
    setSelection(prev => {
      const prevExpanded = prev.lessonId === lesson.project_id ? prev.expanded : {};
      return {
        lessonId: lesson.project_id,
        itemId: targetSlide ? targetSlide.item_id : null,
        slideId,
        elementId: null,
        expanded: targetSlide ? { ...prevExpanded, [targetSlide.item_id]: true } : prevExpanded,
      };
    });
  };

  const selectElement = elementId => {
    if (!lesson) return;
    setSelection(prev => ({
      lessonId: lesson.project_id,
      itemId: elementId ? null : prev.itemId,
      slideId: activeSlide?.slide_id || null,
      elementId,
      expanded: prev.lessonId === lesson.project_id ? prev.expanded : {},
    }));
  };

  const handleBuildSlides = async () => {
    setBuildError('');
    setBuildingSlides(true);
    try {
      await actions.buildSlides();
      setCentreTab('slides');
    } catch (error) {
      setBuildError(error.message.startsWith('[') ? error.message : `[invalid_ai_output] ${error.message}`);
    } finally {
      setBuildingSlides(false);
    }
  };

  const launchPresentationNow = () => {
    if (!slides.length) return;
    if (preflightDialog.current?.open) preflightDialog.current.close();
    setPreflightOpen(false);
    document.documentElement.requestFullscreen?.().catch(() => {});
    setPresentingSlideId(activeSlide?.slide_id || slides[0].slide_id);
  };

  const placedVisualIds = new Set(
    slides.flatMap(s => (s.elements || []).map(el => el.visual_id).filter(Boolean))
  );
  const unconfirmedVisualsOnSlides = (lesson?.outline?.items || []).flatMap((item, idx) =>
    (item.visuals || []).filter(v => v.status !== 'confirmed' && placedVisualIds.has(v.visual_id)).map(v => ({
      ...v,
      item_number: idx + 1,
      item_title: item.title,
    }))
  );

  const handleStartPresentation = () => {
    if (!slides.length) return;
    if (unconfirmedVisualsOnSlides.length > 0) {
      setPreflightOpen(true);
      preflightDialog.current?.showModal?.();
      return;
    }
    launchPresentationNow();
  };

  const handleExitPresentation = returnedSlideId => {
    setPresentingSlideId(null);
    if (returnedSlideId) {
      selectSlide(returnedSlideId);
    }
  };

  const openQualityModal = async () => {
    setQualityOpen(true);
    setQualityAck(false);
    setQualityError('');
    qualityDialog.current?.showModal?.();
    setQualityBusy(true);
    try {
      const rep = await actions.checkDeckQuality();
      setQualityReport(rep);
    } catch (err) {
      setQualityError(err.message);
    } finally {
      setQualityBusy(false);
    }
  };

  const handleApproveQuality = async event => {
    event.preventDefault();
    if (!qualityAck || !qualityReport) return;
    setQualityBusy(true);
    setQualityError('');
    try {
      const warningIds = (qualityReport.issues || []).filter(i => i.severity === 'warning').map(i => i.issue_id);
      const res = await actions.approveDeckQuality(qualityReport.content_fingerprint, warningIds);
      setQualityReport(res.report);
      qualityDialog.current?.close?.();
      setQualityOpen(false);
    } catch (err) {
      setQualityError(err.message);
    } finally {
      setQualityBusy(false);
    }
  };

  const openSettingsModal = () => {
    setSettingsOpen(true);
    settingsDialog.current?.showModal?.();
  };

  const openAnalyticsModal = () => {
    setAnalyticsOpen(true);
    analyticsDialog.current?.showModal?.();
  };

  const saveSettingsForm = event => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    actions.updateSettings({
      model_provider: formData.get('model_provider') || '',
      model_id: formData.get('model_id') || '',
    });
    settingsDialog.current?.close?.();
    setSettingsOpen(false);
  };

  const handleCanvasDrop = async event => {
    if (!activeSlide || disabled) return;
    const files = event.dataTransfer?.files;
    if (!files?.length) return;
    event.preventDefault();
    setDropError('');
    try {
      const dataUrl = await validateImageFile(files[0]);
      await actions.addElement(activeSlide.slide_id, { type: 'image', src: dataUrl, alt: files[0].name });
    } catch (err) {
      setDropError(err.message);
    }
  };

  return (
    <div className="wb">
      {presentingSlideId && lesson?.deck?.slides?.length > 0 && (
        <WorkbenchPresenter
          lesson={lesson}
          initialSlideId={presentingSlideId}
          onUpdatePoll={actions.updatePoll}
          onExit={handleExitPresentation}
        />
      )}

      {mathModalEl && activeSlide && (
        <MathLiveModal
          isOpen={Boolean(mathModalEl)}
          initialLatex={mathModalEl.latex || mathModalEl.text || ''}
          fieldLabel="Công thức trên Slide"
          onClose={() => setMathModalEl(null)}
          onSave={(_, expandedLatex) => {
            actions.changeElement(activeSlide.slide_id, mathModalEl.element_id, { latex: expandedLatex });
            setMathModalEl(null);
          }}
        />
      )}

      <header className="wb-top">
        <span className="wb-wordmark">LessonAI</span>
        <nav className="wb-crumbs" aria-label="Đường dẫn">
          {lesson ? (
            <>
              <button type="button" className="wb-link" onClick={actions.closeLesson}>Bài giảng</button>
              <span className="wb-crumb-sep" aria-hidden="true">/</span>
              <span className="wb-crumb-title" aria-current="page"><MathText text={lesson.title || UNTITLED} /></span>
            </>
          ) : <span aria-current="page">Bài giảng</span>}
        </nav>
        {lesson && <StatusTag confirmed={isExpertConfirmed(lesson)} />}
        {session.saveState === 'unsaved' && <span className="wb-unsaved">Chưa lưu</span>}

        {lesson && (
          <div className="wb-mode-tabs" role="tablist" aria-label="Chế độ soạn">
            <button
              type="button"
              role="tab"
              aria-selected={centreTab === 'slides'}
              className={`wb-btn${centreTab === 'slides' ? ' wb-btn--primary' : ''}`}
              onClick={() => setCentreTab('slides')}
            >
              Bộ slide
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={centreTab === 'plan'}
              className={`wb-btn${centreTab === 'plan' ? ' wb-btn--primary' : ''}`}
              onClick={() => setCentreTab('plan')}
            >
              Kế hoạch bài dạy{lesson.plan?.needs_review ? ' (lệch Dàn ý)' : ''}
            </button>
          </div>
        )}

        <div className="wb-top-end">
          <button type="button" className="wb-btn" disabled={disabled || generating || buildingSlides} onClick={() => {
            setModalOpen(true);
            dialog.current.showModal();
          }}>Soạn bài mới</button>
          {slides.length > 0 && (
            <>
              <button
                type="button"
                className="wb-btn"
                disabled={disabled || generating || buildingSlides}
                onClick={openQualityModal}
              >
                Kiểm tra bài
              </button>
              <button
                type="button"
                className="wb-btn wb-btn--primary"
                disabled={disabled || generating || buildingSlides}
                onClick={handleStartPresentation}
              >
                Trình chiếu
              </button>
            </>
          )}
          <FileMenu lesson={lesson} actions={actions} />
          <SecondaryMenu onOpenSettings={openSettingsModal} onOpenAnalytics={openAnalyticsModal} />
        </div>
      </header>

      <dialog ref={dialog} className="wb-dialog" aria-labelledby="wb-new-title" onClose={() => setModalOpen(false)}
        onCancel={event => {
          if (generating) event.preventDefault();
        }}>
        <h2 id="wb-new-title" className="wb-h3">Soạn bài mới</h2>
        {modalOpen && (
          <OutlineRequest
            actions={actions}
            onCreated={created}
            onBusyChange={setGenerating}
            disabled={disabled}
            defaultLevel={session.preferredLevel}
          />
        )}
        <button type="button" className="wb-btn" disabled={generating} onClick={() => dialog.current.close()}>Đóng hộp soạn bài</button>
      </dialog>

      <dialog ref={qualityDialog} className="wb-dialog wb-dialog--wide" aria-labelledby="wb-quality-title" onClose={() => setQualityOpen(false)}>
        <h2 id="wb-quality-title" className="wb-h3">Kiểm tra bài & Xác nhận chuyên môn</h2>
        {qualityOpen && (
          <div className="wb-form">
            {qualityBusy && <p className="wb-meta">Đang kiểm tra Bộ slide…</p>}
            {qualityError && <p role="alert" className="wb-error-text">{qualityError}</p>}
            {qualityReport && (
              <>
                <section aria-label="Hình chưa xác nhận dữ kiện">
                  <h3 className="wb-label">Hình chưa xác nhận dữ kiện ({qualityReport.unconfirmed_visuals?.length || 0})</h3>
                  {qualityReport.unconfirmed_visuals?.length > 0 ? (
                    <ul className="wb-points">
                      {qualityReport.unconfirmed_visuals.map(v => (
                        <li key={v.visual_id}>Mục {v.item_number} ({VISUAL_KIND_NAMES[v.kind] || v.kind}): {v.reason}</li>
                      ))}
                    </ul>
                  ) : <p className="wb-meta">Không có hình chờ xác nhận.</p>}
                </section>
                <section aria-label="Phần tử tràn chữ">
                  <h3 className="wb-label">Phần tử tràn chữ ({qualityReport.overflow_elements?.length || 0})</h3>
                  {qualityReport.overflow_elements?.length > 0 ? (
                    <ul className="wb-points">
                      {qualityReport.overflow_elements.map(el => (
                        <li key={el.element_id}>{el.message}</li>
                      ))}
                    </ul>
                  ) : <p className="wb-meta">Không có phần tử tràn chữ.</p>}
                </section>
                <section aria-label="Slide đã sửa tay">
                  <h3 className="wb-label">Slide đã sửa tay ({qualityReport.edited_slides?.length || 0})</h3>
                  {qualityReport.edited_slides?.length > 0 ? (
                    <ul className="wb-points">
                      {qualityReport.edited_slides.map(s => (
                        <li key={s.slide_id}>Slide {s.slide_number} ({s.layout})</li>
                      ))}
                    </ul>
                  ) : <p className="wb-meta">Chưa có slide nào sửa tay.</p>}
                </section>
                {qualityReport.issues?.some(i => i.code === 'confirmation_key_changed') && (
                  <p role="alert" className="wb-error-text">
                    {qualityReport.issues.find(i => i.code === 'confirmation_key_changed').message}
                  </p>
                )}
                <form className="wb-form" onSubmit={handleApproveQuality}>
                  <label className="wb-check-label">
                    <input
                      type="checkbox"
                      checked={qualityAck}
                      onChange={e => setQualityAck(e.target.checked)}
                    />
                    <span>Tôi đã đối chiếu đề, điều kiện, lời giải, nguồn và tiến trình của phiên bản này</span>
                  </label>
                  <div className="wb-form-row">
                    <button
                      type="submit"
                      className="wb-btn wb-btn--primary"
                      disabled={!qualityAck || qualityBusy || qualityReport.status === 'blocked'}
                    >
                      Lưu Xác nhận chuyên môn
                    </button>
                    <button type="button" className="wb-btn" onClick={() => { qualityDialog.current?.close?.(); setQualityOpen(false); }}>
                      Đóng kiểm tra
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        )}
      </dialog>

      <dialog ref={preflightDialog} className="wb-dialog" aria-labelledby="wb-preflight-title" onClose={() => setPreflightOpen(false)}>
        <h2 id="wb-preflight-title" className="wb-h3">Trước khi trình chiếu</h2>
        {preflightOpen && (
          <div className="wb-form">
            <p className="wb-meta">
              Bài giảng còn {unconfirmedVisualsOnSlides.length} hình chưa xác nhận dữ kiện (sẽ bị ẩn khi trình chiếu):
            </p>
            <ul className="wb-points">
              {unconfirmedVisualsOnSlides.map(v => (
                <li key={v.visual_id}>Mục {v.item_number}: {VISUAL_KIND_NAMES[v.kind] || v.kind}</li>
              ))}
            </ul>
            <div className="wb-form-row">
              <button
                type="button"
                className="wb-btn"
                onClick={() => {
                  preflightDialog.current?.close?.();
                  setPreflightOpen(false);
                  openQualityModal();
                }}
              >
                Quay lại kiểm tra
              </button>
              <button type="button" className="wb-btn wb-btn--primary" onClick={launchPresentationNow}>
                Vẫn trình chiếu
              </button>
            </div>
          </div>
        )}
      </dialog>

      <dialog ref={settingsDialog} className="wb-dialog" aria-labelledby="wb-settings-title" onClose={() => setSettingsOpen(false)}>
        <h2 id="wb-settings-title" className="wb-h3">Cài đặt</h2>
        {settingsOpen && (
          <form className="wb-form" onSubmit={saveSettingsForm}>
            <label>Nhà cung cấp AI
              <select name="model_provider" defaultValue={session.settings?.model_provider || ''}>
                <option value="">Tự động theo hệ thống</option>
                <option value="google">Google Gemini</option>
                <option value="groq">Groq</option>
                <option value="openrouter">OpenRouter</option>
              </select>
            </label>
            <label>Model AI
              <input name="model_id" defaultValue={session.settings?.model_id || ''} placeholder="Ví dụ: llama-3.3-70b-versatile" />
            </label>
            <div className="wb-form-row">
              <button type="submit" className="wb-btn wb-btn--primary">Lưu cài đặt</button>
              <button type="button" className="wb-btn" onClick={() => { settingsDialog.current?.close?.(); setSettingsOpen(false); }}>Đóng cài đặt</button>
            </div>
          </form>
        )}
      </dialog>

      <dialog ref={analyticsDialog} className="wb-dialog wb-dialog--wide" aria-labelledby="wb-analytics-title" onClose={() => setAnalyticsOpen(false)}>
        <h2 id="wb-analytics-title" className="wb-h3">Phân tích lớp học</h2>
        {analyticsOpen && (
          <AnalyticsScreen
            analyticsData={session.analyticsData}
            onClassificationSuccess={actions.setAnalyticsResult}
            onApplyToLessonPlan={proficiencyLabel => {
              actions.applyClassLevel(proficiencyLabel);
              analyticsDialog.current?.close?.();
              setAnalyticsOpen(false);
            }}
          />
        )}
        <button type="button" className="wb-btn" onClick={() => { analyticsDialog.current?.close?.(); setAnalyticsOpen(false); }}>Đóng phân tích lớp học</button>
      </dialog>

      {notice && <Notice key={notice.message} notice={notice} actions={actions} />}
      <div className="wb-body">
        <aside className="wb-left" aria-label={lesson ? 'Dàn ý' : 'Bài giảng đã lưu'}>
          <h2 className="wb-column-title">{lesson ? 'Dàn ý' : 'Bài giảng đã lưu'}</h2>
          {lesson
            ? (
              <OutlineTree
                lesson={lesson}
                selectedId={selectedId}
                activeSlideId={activeSlide?.slide_id || null}
                expandedItems={expandedItems}
                onSelectItem={selectItem}
                onSelectSlide={selectSlide}
                animate={session.introducedId === lesson.project_id}
              />
            )
            : (
              <LessonList
                lessons={session.lessons}
                legacyCount={session.legacyCount}
                legacyProjects={session.legacyProjects}
                onOpen={actions.openLesson}
              />
            )}
        </aside>
        <main
          className="wb-center"
          onDragOver={e => e.preventDefault()}
          onDrop={handleCanvasDrop}
        >
          {dropError && (
            <div className="wb-notice" role="alert">
              <p>{dropError}</p>
              <button type="button" className="wb-btn wb-btn--quiet" onClick={() => setDropError('')}>Đóng</button>
            </div>
          )}
          {!lesson && (
            <div className="wb-empty wb-fade">
              <h1 className="wb-sheet-title">Soạn bài mới</h1>
              <OutlineRequest
                actions={actions}
                onCreated={created}
                onBusyChange={setGenerating}
                disabled={disabled || modalOpen}
                defaultLevel={session.preferredLevel}
              />
            </div>
          )}
          {lesson && centreTab === 'plan' && (
            <LessonPlanWorkbench lesson={lesson} actions={actions} disabled={disabled} />
          )}
          {lesson && centreTab === 'slides' && slides.length === 0 && (
            <OutlineSheet
              key={lesson.project_id}
              lesson={lesson}
              onSelect={selectItem}
              onBuildSlides={handleBuildSlides}
              buildingSlides={buildingSlides}
              buildError={buildError}
              disabled={disabled}
            />
          )}
          {lesson && centreTab === 'slides' && slides.length > 0 && activeSlide && (
            <div className="wb-work">
              <div className="wb-canvas-wrap">
                <SlideCanvas
                  key={activeSlide.slide_id}
                  lesson={lesson}
                  slide={activeSlide}
                  mode="edit"
                  fit="contain"
                  selectedElementId={selectedElementId}
                  onSelectElement={selectElement}
                  onChangeElement={actions.changeElement}
                  onEditFormula={el => setMathModalEl(el)}
                  className="wb-sheet-canvas"
                />
              </div>
              <div className="wb-strip" role="region" aria-label="Dải slide">
                {lesson.outline.items.map((item, idx) => {
                  const own = slides.filter(s => s.item_id === item.item_id);
                  if (!own.length) return null;
                  return (
                    <div key={item.item_id} className="wb-strip-group" title={item.title}>
                      <span className="wb-strip-n">{idx + 1}</span>
                      {own.map(s => {
                        const globalNumber = slides.indexOf(s) + 1;
                        const isCurrent = s.slide_id === activeSlide.slide_id;
                        return (
                          <button
                            key={s.slide_id}
                            type="button"
                            className={`wb-strip-slide wb-fade${isCurrent ? ' is-current' : ''}`}
                            aria-label={`Slide ${globalNumber}`}
                            aria-current={isCurrent ? 'true' : undefined}
                            onClick={() => selectSlide(s.slide_id)}
                          >
                            <SlideCanvas lesson={lesson} slide={s} mode="thumb" fit="width" className="wb-sheet-thumb" />
                          </button>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </main>
        <aside className="wb-right" aria-label="Thuộc tính">
          <div className="wb-right-head">
            <h2 className="wb-column-title">Thuộc tính</h2>
            {activeSlide && (
              <div className="wb-right-tabs" role="tablist" aria-label="Bảng bên phải">
                <button
                  type="button"
                  role="tab"
                  aria-selected={rightTab === 'props'}
                  className={`wb-btn${rightTab === 'props' ? ' wb-btn--primary' : ''}`}
                  onClick={() => setRightTab('props')}
                >
                  Thuộc tính
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={rightTab === 'assistant'}
                  className={`wb-btn${rightTab === 'assistant' ? ' wb-btn--primary' : ''}`}
                  onClick={() => setRightTab('assistant')}
                >
                  Trợ giảng AI
                </button>
              </div>
            )}
          </div>
          {rightTab === 'assistant' && activeSlide ? (
            <AssistantPanel activeSlide={activeSlide} actions={actions} disabled={disabled} />
          ) : (
            <>
              {selectedElement ? (
                <ElementProperties
                  lesson={lesson}
                  slide={activeSlide}
                  element={selectedElement}
                  actions={actions}
                  onOpenMathModal={el => setMathModalEl(el)}
                  disabled={disabled}
                />
              ) : (
                <ItemProperties lesson={lesson} itemId={selectedId} activeSlideId={activeSlide?.slide_id || null} actions={actions} disabled={disabled} />
              )}
              {activeSlide && centreTab === 'slides' && (
                <SlideProperties
                  lesson={lesson}
                  slide={activeSlide}
                  actions={actions}
                  disabled={disabled}
                  showDetails={!selectedElement && !selectedId}
                />
              )}
              {lesson && <AddItem key={lesson.project_id} actions={actions} onSelect={selectItem} disabled={disabled} />}
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
