/**
 * Bàn làm việc (spec #36, variant B): top bar, left column (saved Bài giảng, or the Dàn ý tree with
 * the time budget and expandable slide thumbnails), centre (the Phiếu Dàn ý or the 16:9 SlideCanvas + Dải slide)
 * and right column (properties of Mục, Slide, or selected Phần tử), plus Trình chiếu (#41) and Menu phụ (#46).
 */
import React, { useEffect, useRef, useState } from 'react';
import OutlineRequest from './OutlineRequest.jsx';
import SlideCanvas, { ELEMENT_TYPE_LABELS } from './SlideCanvas.jsx';
import WorkbenchPresenter from './WorkbenchPresenter.jsx';
import AnalyticsScreen from '../analytics/AnalyticsScreen.jsx';
import MathText from '../../shared/math/MathText';
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

function LessonList({ lessons, legacyCount, onOpen }) {
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
        <p className="wb-meta wb-legacy">
          Máy này còn {legacyCount} dự án bản 2 của giao diện cũ. Bàn làm việc chưa mở được dự án bản 2; tắt Bàn làm việc để mở chúng.
        </p>
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

function SlideProperties({ slide }) {
  return (
    <div className="wb-panel wb-fade" key={slide.slide_id}>
      <h3 className="wb-h3">Slide</h3>
      <dl className="wb-props">
        <dt>Bố cục mẫu</dt><dd>{slide.layout}</dd>
        <dt>Số phần tử</dt><dd>{slide.elements.length}</dd>
        {slide.edited && <><dt>Trạng thái</dt><dd>Đã sửa tay</dd></>}
      </dl>
      <p className="wb-meta">Chọn một phần tử trên canvas để xem vị trí, kích thước và cách hiện dần. Kéo để di chuyển, kéo góc để đổi cỡ theo lưới 20 đơn vị.</p>
    </div>
  );
}

function ElementProperties({ element }) {
  const fit = measureElementTextFit(element);
  const isOverflow = Boolean(element.overflow || fit.overflow);
  const typeLabel = ELEMENT_TYPE_LABELS[element.type] || element.type;
  const reveal = element.reveal ?? 0;
  const parts = element.parts ?? 1;
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
    </div>
  );
}

function ItemProperties({ lesson, itemId, actions, disabled }) {
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
      {item.visuals.length > 0 && (
        <>
          <h4 className="wb-label">Hình</h4>
          <ul className="wb-chips">{item.visuals.map(visual => <li key={visual.visual_id}><VisualChip visual={visual} /></li>)}</ul>
        </>
      )}
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

function FileMenu({ canExport, actions }) {
  const [open, setOpen] = useState(false);
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
    event.target.value = ''; // choosing the same file again must still import it
    setOpen(false);
    if (file) actions.importFile(file);
  };
  return (
    <div className="wb-menu" ref={box}>
      <button type="button" className="wb-btn" aria-expanded={open} aria-controls="wb-file-menu" onClick={() => setOpen(value => !value)}>Tệp</button>
      <input ref={picker} type="file" accept="application/json,.json" className="wb-hidden" aria-label="Nhập tệp JSON" tabIndex={-1} onChange={importChosen} />
      {open && (
        <div id="wb-file-menu" className="wb-menu-list" role="group" aria-label="Tệp">
          <button type="button" onClick={() => picker.current?.click()}>Nhập tệp JSON bản 3…</button>
          <button type="button" disabled={!canExport} onClick={() => { setOpen(false); actions.exportLesson(); }}>Xuất tệp JSON</button>
        </div>
      )}
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

export default function Workbench({ session, actions, onSwitchOff }) {
  const { lesson, notice } = session;
  const [modalOpen, setModalOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [buildingSlides, setBuildingSlides] = useState(false);
  const [buildError, setBuildError] = useState('');
  const [presentingSlideId, setPresentingSlideId] = useState(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);

  const dialog = useRef(null);
  const settingsDialog = useRef(null);
  const analyticsDialog = useRef(null);
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
    } catch (error) {
      setBuildError(error.message.startsWith('[') ? error.message : `[invalid_ai_output] ${error.message}`);
    } finally {
      setBuildingSlides(false);
    }
  };

  const handleStartPresentation = () => {
    if (!slides.length) return;
    document.documentElement.requestFullscreen?.().catch(() => {});
    setPresentingSlideId(activeSlide?.slide_id || slides[0].slide_id);
  };

  const handleExitPresentation = returnedSlideId => {
    setPresentingSlideId(null);
    if (returnedSlideId) {
      selectSlide(returnedSlideId);
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

  return (
    <div className="wb">
      {presentingSlideId && lesson?.deck?.slides?.length > 0 && (
        <WorkbenchPresenter
          lesson={lesson}
          initialSlideId={presentingSlideId}
          onExit={handleExitPresentation}
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
        <div className="wb-top-end">
          <button type="button" className="wb-btn" disabled={disabled || generating || buildingSlides} onClick={() => {
            setModalOpen(true);
            dialog.current.showModal();
          }}>Soạn bài mới</button>
          {slides.length > 0 && (
            <button
              type="button"
              className="wb-btn wb-btn--primary"
              disabled={disabled || generating || buildingSlides}
              onClick={handleStartPresentation}
            >
              Trình chiếu
            </button>
          )}
          <FileMenu canExport={Boolean(lesson)} actions={actions} />
          <SecondaryMenu onOpenSettings={openSettingsModal} onOpenAnalytics={openAnalyticsModal} />
          <label className="wb-switch">
            <input type="checkbox" role="switch" checked disabled={generating || buildingSlides} onChange={onSwitchOff} />
            <span>Bàn làm việc</span>
          </label>
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
            : <LessonList lessons={session.lessons} legacyCount={session.legacyCount} onOpen={actions.openLesson} />}
        </aside>
        <main className="wb-center">
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
          {lesson && slides.length === 0 && (
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
          {lesson && slides.length > 0 && activeSlide && (
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
          <h2 className="wb-column-title">Thuộc tính</h2>
          {selectedElement ? (
            <ElementProperties element={selectedElement} />
          ) : selectedId ? (
            <ItemProperties lesson={lesson} itemId={selectedId} actions={actions} disabled={disabled} />
          ) : activeSlide ? (
            <SlideProperties slide={activeSlide} />
          ) : (
            <ItemProperties lesson={lesson} itemId={selectedId} actions={actions} disabled={disabled} />
          )}
          {lesson && <AddItem key={lesson.project_id} actions={actions} onSelect={selectItem} disabled={disabled} />}
        </aside>
      </div>
    </div>
  );
}
