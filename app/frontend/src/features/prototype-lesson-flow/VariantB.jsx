/**
 * PROTOTYPE, wipe me. Biến thể B, "Bàn làm việc": một màn duy nhất.
 * Dàn ý luôn hiện ở cột trái dưới dạng cây Hoạt động → Mục → Slide; canvas và dải slide ở giữa;
 * cột phải là bảng thuộc tính đổi theo thứ đang chọn (Mục, hình, phần tử, trợ giảng).
 */
import React, { useState } from 'react';
import MathText from '../../shared/math/MathText';
import SlideCanvas from './SlideCanvas.jsx';
import {
  AddVisualButton, ApprovalControl, AssistantPanel, CheckButton, ConfirmForTarget, DraftTag, ElementPanel, KIND_NAME,
  LessonList, PromptForm, SourcesNote, Stepper, ThinkingDots, TimeBudget, VisualChip, groupByActivity, presentIssues
} from './parts.jsx';

export default function VariantB({ state, lesson, actions }) {
  const [composer, setComposer] = useState(false);
  const [slideId, setSlideId] = useState(null);
  const [elId, setElId] = useState(null);
  const [focus, setFocus] = useState(null); // { kind: 'item', itemId } | { kind: 'visual', itemId, visualId } | { kind: 'ai' }
  const [expanded, setExpanded] = useState({});

  const create = (v) => { actions.create(v); setComposer(false); setSlideId(null); setFocus(null); };
  const slide = lesson ? lesson.slides.find((s) => s.id === slideId) || lesson.slides[0] : null;
  const selectSlide = (s) => { setSlideId(s.id); setElId(null); };
  const focusItem = (item) => {
    setFocus({ kind: 'item', itemId: item.id });
    const first = lesson.slides.find((s) => s.itemId === item.id);
    if (first) selectSlide(first);
  };

  return (
    <div className="vb">
      <header className="vb-head">
        <span className="lf-wordmark">LessonAI</span>
        <span className="vb-head-title">
          {lesson ? <><button type="button" className="lf-link" onClick={actions.home}>Bài giảng</button><span aria-hidden>/</span><MathText text={lesson.title} /><DraftTag lesson={lesson} /></> : <span className="lf-meta">Chưa mở bài giảng nào</span>}
        </span>
        <span className="vb-head-actions">
          <button type="button" className="lf-btn" onClick={() => setComposer(true)}>Soạn bài mới</button>
          {lesson && lesson.slides.length > 0 && (
            <>
              <CheckButton lesson={lesson} />
              <ApprovalControl lesson={lesson} onApprove={actions.approve} />
              <button type="button" className="lf-btn lf-btn--primary" disabled={!!lesson.generating} onClick={() => actions.present(Math.max(0, lesson.slides.indexOf(slide)))}>Trình chiếu</button>
            </>
          )}
        </span>
      </header>

      <div className="vb-body">
        <aside className="vb-tree" aria-label={lesson ? 'Dàn ý' : 'Bài giảng đã soạn'}>
          {!lesson && <LessonList state={state} onOpen={(id) => { actions.open(id); setSlideId(null); setFocus(null); }} />}
          {lesson && (
            <>
              <div className="vb-tree-head">
                <TimeBudget lesson={lesson} compact />
              </div>
              {groupByActivity(lesson.items).map((g) => (
                <section key={g.activity} className="vb-act">
                  <h2 className="vb-act-title"><span>{g.activity}</span><span className="lf-meta">{g.minutes} phút</span></h2>
                  {g.items.length === 0 && lesson.generating === 'outline' && <p className="lf-meta vb-act-wait"><ThinkingDots /></p>}
                  {g.items.map((item) => {
                    const own = lesson.slides.filter((s) => s.itemId === item.id);
                    const isOpen = expanded[item.id] ?? own.some((s) => s.id === slide?.id);
                    const active = (focus?.itemId === item.id) || own.some((s) => s.id === slide?.id);
                    return (
                      <div key={item.id} className={`vb-item ${active ? 'is-active' : ''} ${item.fresh ? 'lf-ink' : ''}`}>
                        <div className="vb-item-row">
                          <button type="button" className="vb-item-toggle" aria-label={isOpen ? 'Thu gọn' : 'Mở rộng'} aria-expanded={isOpen} disabled={!own.length} onClick={() => setExpanded((m) => ({ ...m, [item.id]: !isOpen }))}>{own.length ? (isOpen ? '▾' : '▸') : ''}</button>
                          <button type="button" className="vb-item-main" onClick={() => focusItem(item)}>
                            <span className="vb-item-n">{lesson.items.indexOf(item) + 1}</span>
                            <span className="vb-item-text">
                              <span className="vb-item-title"><MathText text={item.title} /></span>
                              <span className="vb-item-meta">
                                <span className="lf-meta">{item.kind}</span>
                                <span className="lf-glyphs" aria-label={`${item.slideCount} slide`}>{Array.from({ length: item.slideCount }, (_, i) => <i key={i} />)}</span>
                                {item.visuals.map((v) => <span key={v.id} className={`vb-vmark ${v.status === 'confirmed' ? 'is-confirmed' : ''}`} title={`${KIND_NAME[v.kind]}: ${v.status === 'confirmed' ? 'đã xác nhận' : 'chờ xác nhận'}`} />)}
                                {item.stale && <span className="lf-meta">đã đổi</span>}
                              </span>
                            </span>
                          </button>
                        </div>
                        {isOpen && own.length > 0 && (
                          <div className="vb-item-slides">
                            {own.map((s) => (
                              <button key={s.id} type="button" className={`vb-mini ${s.id === slide?.id ? 'is-current' : ''}`} onClick={() => selectSlide(s)}>
                                <SlideCanvas lesson={lesson} slide={s} mode="thumb" className="lf-sheet" />
                                <span className="lf-meta">Slide {lesson.slides.indexOf(s) + 1}</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </section>
              ))}
            </>
          )}
        </aside>

        <main className="vb-center lf-desk">
          {!lesson && (
            <div className="vb-start lf-fade">
              <PromptForm onSubmit={create} />
            </div>
          )}
          {lesson && !lesson.slides.length && <ReviewB lesson={lesson} actions={actions} setFocus={setFocus} />}
          {lesson && lesson.slides.length > 0 && slide && (
            <div className="vb-work">
              <div className="vb-canvas">
                <SlideCanvas
                  key={slide.id} lesson={lesson} slide={slide} mode="edit" fit="contain" className="lf-sheet"
                  selectedId={elId} onSelect={(id) => { setElId(id); if (id) setFocus(null); }}
                  onMoveElement={(id, rect) => actions.moveElement(slide.id, id, rect)}
                  onRequestConfirm={(itemId, visualId) => setFocus({ kind: 'visual', itemId, visualId })}
                />
              </div>
              <div className="vb-strip" aria-label="Dải slide">
                {lesson.items.map((item) => {
                  const own = lesson.slides.filter((s) => s.itemId === item.id);
                  if (!own.length) return null;
                  return (
                    <div key={item.id} className="vb-strip-group" title={item.title}>
                      <span className="vb-strip-n">{lesson.items.indexOf(item) + 1}</span>
                      {own.map((s) => (
                        <button key={s.id} type="button" className={`vb-strip-slide ${s.id === slide.id ? 'is-current' : ''} ${s.fresh ? 'lf-appear' : ''}`} onClick={() => selectSlide(s)} aria-label={`Slide ${lesson.slides.indexOf(s) + 1}`}>
                          <SlideCanvas lesson={lesson} slide={s} mode="thumb" className="lf-sheet" />
                        </button>
                      ))}
                    </div>
                  );
                })}
                {lesson.generating === 'slides' && <span className="lf-meta vb-strip-wait"><ThinkingDots /></span>}
              </div>
            </div>
          )}
        </main>

        <aside className="vb-inspector">
          {lesson ? (
            <>
              <div className="lf-tabs" role="tablist">
                <button type="button" role="tab" aria-selected={focus?.kind !== 'ai'} onClick={() => setFocus(null)}>Thuộc tính</button>
                <button type="button" role="tab" aria-selected={focus?.kind === 'ai'} onClick={() => setFocus({ kind: 'ai' })}>Trợ giảng AI</button>
              </div>
              {focus?.kind === 'ai' && <AssistantPanel />}
              {focus?.kind === 'visual' && <div className="lf-panel-body"><ConfirmForTarget lesson={lesson} target={focus} actions={actions} onClose={() => setFocus(null)} /></div>}
              {focus?.kind === 'item' && <ItemInspectorB lesson={lesson} itemId={focus.itemId} actions={actions} setFocus={setFocus} />}
              {!focus && (slide ? <ElementPanel slide={slide} el={slide.elements.find((e) => e.id === elId)} /> : <p className="lf-panel-body lf-meta">Chọn một mục ở cột trái để chỉnh số slide, số phút và hình của mục đó.</p>)}
            </>
          ) : (
            <p className="lf-panel-body lf-meta">Nhập yêu cầu ở giữa, hoặc mở một bài giảng đã soạn ở cột trái.</p>
          )}
        </aside>
      </div>

      {composer && (
        <div className="lf-dialog-backdrop" onPointerDown={(e) => { if (e.target === e.currentTarget) setComposer(false); }}>
          <div className="lf-dialog lf-dialog--wide lf-appear" role="dialog" aria-modal="true" aria-label="Soạn bài mới">
            <PromptForm onSubmit={create} size="compact" />
            <div className="lf-dialog-actions"><button type="button" className="lf-btn lf-btn--quiet" onClick={() => setComposer(false)}>Đóng</button></div>
          </div>
        </div>
      )}
    </div>
  );
}

function ReviewB({ lesson, actions, setFocus }) {
  const generating = lesson.generating === 'outline';
  const proposals = lesson.items.flatMap((item) => item.visuals.map((v) => ({ item, v })));
  const pendingCount = proposals.filter(({ v }) => v.status !== 'confirmed').length;
  return (
    <div className="vb-review lf-fade">
      <h1 className="lf-h1"><MathText text={lesson.title} /></h1>
      <p className="lf-meta">{lesson.sgk}. Trình độ lớp: {lesson.level.toLowerCase()}.</p>
      {generating ? (
        <p className="vb-review-wait"><ThinkingDots /> AI đang lập dàn ý. Các mục hiện dần ở cột bên trái.</p>
      ) : (
        <>
          <SourcesNote />
          <TimeBudget lesson={lesson} />
          <section className="vb-review-visuals">
            <h2 className="lf-h3">Hình AI đề xuất</h2>
            <p className="lf-meta">Hình chỉ được dựng khi bạn xác nhận dữ kiện. {pendingCount ? `Còn ${pendingCount} hình chờ xác nhận.` : 'Mọi hình đã được xác nhận.'}</p>
            <div className="vb-review-chips">
              {proposals.map(({ item, v }) => <VisualChip key={v.id} visual={v} onClick={() => setFocus({ kind: 'visual', itemId: item.id, visualId: v.id })} />)}
            </div>
          </section>
          <div className="vb-review-actions">
            <button type="button" className="lf-btn lf-btn--primary" onClick={actions.startSlides} disabled={lesson.generating === 'slides'}>Dựng bộ slide</button>
            {lesson.generating === 'slides' && <span className="lf-meta"><ThinkingDots /> Đang dựng slide</span>}
          </div>
        </>
      )}
    </div>
  );
}

function ItemInspectorB({ lesson, itemId, actions, setFocus }) {
  const item = lesson.items.find((i) => i.id === itemId);
  if (!item) return null;
  return (
    <div className="lf-panel-body vb-item-inspector lf-fade">
      <p className="lf-meta">Mục {lesson.items.indexOf(item) + 1}. {item.activity}, {item.kind.toLowerCase()}</p>
      <h3 className="lf-h3"><MathText text={item.title} /></h3>
      <ul className="vb-points">{item.points.map((p, i) => <li key={i}><MathText text={p} /></li>)}</ul>
      <dl className="lf-props">
        <dt>Số slide</dt><dd><Stepper label="số slide" value={item.slideCount} min={1} max={4} glyphs onChange={(v) => actions.setItem(item.id, { slideCount: v })} /></dd>
        <dt>Số phút</dt><dd><Stepper label="số phút" value={item.minutes} min={1} max={30} onChange={(v) => actions.setItem(item.id, { minutes: v })} /></dd>
      </dl>
      {item.visuals.length > 0 && (
        <div className="vb-item-visuals">
          {item.visuals.map((v) => <VisualChip compact key={v.id} visual={v} onClick={() => setFocus({ kind: 'visual', itemId: item.id, visualId: v.id })} />)}
        </div>
      )}
      <AddVisualButton />
      {item.stale && <p className="lf-stale">Mục đã đổi sau khi dựng slide. <button type="button" className="lf-link" onClick={() => actions.regenerateItem(item.id)}>Sinh lại slide của mục này</button></p>}
      {presentIssues(lesson).pending.some((v) => item.visuals.includes(v)) && <p className="lf-small">Hình chưa xác nhận của mục này sẽ bị ẩn khi trình chiếu.</p>}
    </div>
  );
}
