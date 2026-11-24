/**
 * PROTOTYPE, wipe me. Biến thể C, "Bảng kể chuyện": Dàn ý là một bảng ngang, mỗi Hoạt động một cột.
 * Dưới mỗi Mục là hàng khung slide (nét đứt khi chưa dựng); bấm một slide để phóng vào trình soạn toàn màn hình.
 */
import React, { useState } from 'react';
import MathText from '../../shared/math/MathText';
import SlideCanvas from './SlideCanvas.jsx';
import {
  AddVisualButton, ApprovalControl, AssistantPanel, CheckButton, ConfirmForTarget, DraftTag, ElementPanel,
  PromptForm, SourcesNote, Stepper, ThinkingDots, TimeBudget, VisualChip, groupByActivity
} from './parts.jsx';

export default function VariantC({ state, lesson, actions }) {
  const [zoomed, setZoomed] = useState(null);
  const [drawer, setDrawer] = useState(null);
  if (!lesson) return <LandingC state={state} actions={actions} />;
  const zoomSlide = zoomed && lesson.slides.find((s) => s.id === zoomed);
  if (zoomSlide) return <EditorC lesson={lesson} slide={zoomSlide} actions={actions} onBack={() => setZoomed(null)} onGo={setZoomed} />;
  return <BoardC lesson={lesson} actions={actions} onZoom={setZoomed} drawer={drawer} setDrawer={setDrawer} />;
}

function LandingC({ state, actions }) {
  return (
    <div className="vc-landing lf-desk">
      <span className="lf-wordmark vc-landing-mark">LessonAI</span>
      <div className="vc-hero lf-fade"><PromptForm size="hero" onSubmit={actions.create} /></div>
      <section className="vc-shelf" aria-labelledby="vc-shelf-title">
        <h2 id="vc-shelf-title" className="lf-h3">Bài giảng đã soạn</h2>
        <div className="vc-slips">
          {state.order.map((id) => {
            const l = state.lessons[id];
            return (
              <button key={id} type="button" className="vc-slip" onClick={() => actions.open(id)}>
                {l.slides[0] ? <SlideCanvas lesson={l} slide={l.slides[0]} mode="thumb" className="lf-sheet" /> : <span className="vc-frame vc-frame--slip" />}
                <span className="vc-slip-title"><MathText text={l.title} /></span>
                <span className="vc-slip-meta"><span className="lf-meta">{l.slides.length ? `${l.slides.length} slide` : 'Chưa có slide'}</span><DraftTag lesson={l} /></span>
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function BoardC({ lesson, actions, onZoom, drawer, setDrawer }) {
  const generatingOutline = lesson.generating === 'outline';
  const hasSlides = lesson.slides.length > 0;
  return (
    <div className="vc">
      <header className="vc-bar">
        <button type="button" className="lf-link" onClick={actions.home}>Tất cả bài giảng</button>
        <h1 className="vc-title"><MathText text={lesson.title} /></h1>
        <TimeBudget lesson={lesson} compact />
        <span className="vc-bar-actions">
          {hasSlides ? (
            <>
              <CheckButton lesson={lesson} />
              <ApprovalControl lesson={lesson} onApprove={actions.approve} />
              <button type="button" className="lf-btn lf-btn--primary" disabled={!!lesson.generating} onClick={() => actions.present(0)}>Trình chiếu</button>
            </>
          ) : (
            <button type="button" className="lf-btn lf-btn--primary" disabled={!!lesson.generating} onClick={actions.startSlides}>Dựng bộ slide</button>
          )}
        </span>
      </header>
      <div className="vc-sub"><SourcesNote />{generatingOutline && <span className="lf-meta"><ThinkingDots /> AI đang lập dàn ý</span>}{lesson.generating === 'slides' && <span className="lf-meta"><ThinkingDots /> Đang dựng slide vào từng khung</span>}</div>
      <div className="vc-board lf-desk">
        {groupByActivity(lesson.items).map((g) => (
          <section key={g.activity} className="vc-col">
            <h2 className="vc-col-title"><span>{g.activity}</span><span className="lf-meta">{g.minutes} phút</span></h2>
            {g.items.length === 0 && generatingOutline && <span className="vc-card vc-card--ghost" aria-hidden />}
            {g.items.map((item) => {
              const own = lesson.slides.filter((s) => s.itemId === item.id);
              return (
                <article key={item.id} className={`vc-card ${item.fresh ? 'lf-ink' : ''}`}>
                  <header className="vc-card-head"><span className="vc-card-n">{lesson.items.indexOf(item) + 1}</span><span className="lf-meta">{item.kind}</span></header>
                  <h3 className="vc-card-title"><MathText text={item.title} /></h3>
                  {item.visuals.length > 0 && (
                    <div className="vc-card-visuals">
                      {item.visuals.map((v) => <VisualChip compact key={v.id} visual={v} active={drawer?.visualId === v.id} onClick={() => setDrawer({ itemId: item.id, visualId: v.id })} />)}
                    </div>
                  )}
                  <div className="vc-frames">
                    {Array.from({ length: Math.max(item.slideCount, own.length) }, (_, i) => (own[i] ? (
                      <button key={own[i].id} type="button" className={`vc-frame is-filled ${own[i].fresh ? 'lf-appear' : ''}`} onClick={() => onZoom(own[i].id)} aria-label={`Mở slide ${lesson.slides.indexOf(own[i]) + 1}`}>
                        <SlideCanvas lesson={lesson} slide={own[i]} mode="thumb" />
                      </button>
                    ) : <span key={`e${i}`} className="vc-frame" aria-hidden />))}
                  </div>
                  <footer className="vc-card-foot">
                    <span className="vc-card-ctl"><span className="lf-meta">Slide</span><Stepper label="số slide" value={item.slideCount} min={1} max={4} onChange={(v) => actions.setItem(item.id, { slideCount: v })} /></span>
                    <span className="vc-card-ctl"><span className="lf-meta">Phút</span><Stepper label="số phút" value={item.minutes} min={1} max={30} onChange={(v) => actions.setItem(item.id, { minutes: v })} /></span>
                  </footer>
                  {!generatingOutline && <AddVisualButton />}
                  {item.stale && <p className="lf-stale">Mục đã đổi. <button type="button" className="lf-link" onClick={() => actions.regenerateItem(item.id)}>Sinh lại slide của mục này</button></p>}
                </article>
              );
            })}
          </section>
        ))}
      </div>
      {drawer && (
        <aside className="vc-drawer lf-appear" aria-label="Xác nhận dữ kiện">
          <ConfirmForTarget lesson={lesson} target={drawer} actions={actions} onClose={() => setDrawer(null)} />
        </aside>
      )}
    </div>
  );
}

function EditorC({ lesson, slide, actions, onBack, onGo }) {
  const [elId, setElId] = useState(null);
  const [tab, setTab] = useState('el');
  const [confirmTarget, setConfirmTarget] = useState(null);
  const [panelOpen, setPanelOpen] = useState(true);
  const index = lesson.slides.indexOf(slide);
  const item = lesson.items.find((i) => i.id === slide.itemId);
  const go = (d) => { const s = lesson.slides[index + d]; if (s) { onGo(s.id); setElId(null); setConfirmTarget(null); } };
  return (
    <div className="vc-editor lf-desk lf-zoom">
      <div className="vc-float vc-float--top">
        <button type="button" className="lf-btn" onClick={onBack}>Về bảng</button>
        <span className="vc-crumb"><span className="lf-meta">Mục {lesson.items.indexOf(item) + 1}</span><MathText text={item.title} /></span>
        <span className="lf-meta">Slide {index + 1}/{lesson.slides.length}</span>
      </div>
      <button type="button" className="vc-nav vc-nav--prev" disabled={index === 0} onClick={() => go(-1)} aria-label="Slide trước">‹</button>
      <div className="vc-editor-canvas">
        <SlideCanvas
          key={slide.id} lesson={lesson} slide={slide} mode="edit" fit="contain" className="lf-sheet"
          selectedId={elId} onSelect={setElId}
          onMoveElement={(id, rect) => actions.moveElement(slide.id, id, rect)}
          onRequestConfirm={(itemId, visualId) => { setConfirmTarget({ itemId, visualId }); setTab('el'); setPanelOpen(true); }}
        />
      </div>
      <button type="button" className="vc-nav vc-nav--next" disabled={index === lesson.slides.length - 1} onClick={() => go(1)} aria-label="Slide sau">›</button>
      <aside className={`vc-float vc-float--side ${panelOpen ? '' : 'is-collapsed'}`}>
        <div className="lf-tabs" role="tablist">
          <button type="button" role="tab" aria-selected={tab === 'el'} onClick={() => { setTab('el'); setPanelOpen(true); }}>Phần tử</button>
          <button type="button" role="tab" aria-selected={tab === 'ai'} onClick={() => { setTab('ai'); setPanelOpen(true); }}>Trợ giảng AI</button>
          <button type="button" className="vc-collapse" aria-label={panelOpen ? 'Thu gọn bảng' : 'Mở bảng'} onClick={() => setPanelOpen((v) => !v)}>{panelOpen ? '–' : '+'}</button>
        </div>
        {panelOpen && tab === 'el' && (confirmTarget
          ? <div className="lf-panel-body"><ConfirmForTarget lesson={lesson} target={confirmTarget} actions={actions} onClose={() => setConfirmTarget(null)} /></div>
          : <ElementPanel slide={slide} el={slide.elements.find((e) => e.id === elId)} />)}
        {panelOpen && tab === 'ai' && <AssistantPanel />}
      </aside>
      <div className="vc-float vc-float--bottom">
        <CheckButton lesson={lesson} align="up" />
        <ApprovalControl lesson={lesson} onApprove={actions.approve} align="up" />
        <button type="button" className="lf-btn lf-btn--primary" onClick={() => actions.present(index)}>Trình chiếu từ slide này</button>
      </div>
    </div>
  );
}
