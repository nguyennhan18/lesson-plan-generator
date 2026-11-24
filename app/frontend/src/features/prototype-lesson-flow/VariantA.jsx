/**
 * PROTOTYPE, wipe me. Biến thể A, "Từng bước": bốn màn nối tiếp nhau (Yêu cầu, Dàn ý, Bộ slide, Trình chiếu).
 * Dàn ý là một văn bản đọc từ trên xuống; xác nhận hình mở ngay dưới mục; Bộ slide là trình soạn ba cột.
 */
import React, { useEffect, useState } from 'react';
import MathText from '../../shared/math/MathText';
import SlideCanvas from './SlideCanvas.jsx';
import {
  AddVisualButton, ApprovalControl, AssistantPanel, CheckButton, ConfirmForTarget, DraftTag, ElementPanel,
  LessonList, PromptForm, SourcesNote, Stepper, ThinkingDots, TimeBudget, VisualChip, VisualConfirmForm, groupByActivity
} from './parts.jsx';

export default function VariantA({ state, lesson, actions }) {
  const initial = !lesson ? 'prompt' : lesson.slides.length || lesson.generating === 'slides' ? 'slides' : 'outline';
  const [screen, setScreen] = useState(initial);
  useEffect(() => { if (!lesson) setScreen('prompt'); }, [lesson]);

  const canSlides = !!lesson && (lesson.slides.length > 0 || lesson.generating === 'slides');
  const canPresent = !!lesson && lesson.slides.length > 0 && !lesson.generating;
  const steps = [
    { key: 'prompt', label: 'Yêu cầu', enabled: true },
    { key: 'outline', label: 'Dàn ý', enabled: !!lesson },
    { key: 'slides', label: 'Bộ slide', enabled: canSlides },
    { key: 'present', label: 'Trình chiếu', enabled: canPresent }
  ];
  const goStep = (key) => {
    if (key === 'present') return actions.present(0);
    if (key === 'prompt') { actions.home(); return setScreen('prompt'); }
    return setScreen(key);
  };

  return (
    <div className="va">
      <header className="va-head">
        <span className="lf-wordmark">LessonAI</span>
        <nav className="va-steps" aria-label="Các bước soạn bài">
          {steps.map((s, i) => (
            <button key={s.key} type="button" className={`va-step ${screen === s.key ? 'is-current' : ''}`} disabled={!s.enabled} aria-current={screen === s.key ? 'step' : undefined} onClick={() => goStep(s.key)}>
              <span className="va-step-n">{i + 1}</span>{s.label}
            </button>
          ))}
        </nav>
        <span className="va-head-side">{lesson && <DraftTag lesson={lesson} />}</span>
      </header>
      <main className="va-main">
        {screen === 'prompt' && (
          <div key="prompt" className="va-prompt lf-fade">
            <PromptForm onSubmit={(v) => { actions.create(v); setScreen('outline'); }} />
            <section className="va-recent" aria-labelledby="va-recent-title">
              <h2 id="va-recent-title" className="lf-h3">Bài giảng đã soạn</h2>
              <LessonList state={state} onOpen={(id) => { actions.open(id); setScreen(state.lessons[id].slides.length ? 'slides' : 'outline'); }} />
            </section>
          </div>
        )}
        {screen === 'outline' && lesson && (
          <OutlineA key={`o-${lesson.id}`} lesson={lesson} actions={actions} onBuild={() => { actions.startSlides(); setScreen('slides'); }} onOpenSlides={() => setScreen('slides')} />
        )}
        {screen === 'slides' && lesson && <SlidesA key={`s-${lesson.id}`} lesson={lesson} actions={actions} />}
      </main>
    </div>
  );
}

function OutlineA({ lesson, actions, onBuild, onOpenSlides }) {
  const [openVisual, setOpenVisual] = useState(null);
  const generating = lesson.generating === 'outline';
  return (
    <div className="va-outline lf-fade">
      <div className="va-doc">
        <header className="va-doc-head">
          <h1 className="lf-h1"><MathText text={lesson.title} /></h1>
          <p className="lf-meta">{lesson.sgk}. Trình độ lớp: {lesson.level.toLowerCase()}.</p>
          <p className="va-doc-prompt">“{lesson.prompt}”</p>
          <SourcesNote />
        </header>
        {groupByActivity(lesson.items).map((g) => (
          <section key={g.activity} className="va-act">
            <h2 className="va-act-title"><span>{g.activity}</span><span className="lf-meta">{g.minutes} phút</span></h2>
            {g.items.length === 0 && generating && <p className="lf-meta va-act-wait"><ThinkingDots /> AI đang soạn</p>}
            <ol className="va-items">
              {g.items.map((item) => (
                <li key={item.id} className={`va-item ${item.fresh ? 'lf-ink' : ''}`}>
                  <span className="va-item-n">{lesson.items.indexOf(item) + 1}</span>
                  <div className="va-item-body">
                    <h3 className="va-item-title"><span className="va-item-kind">{item.kind}</span><MathText text={item.title} /></h3>
                    <ul className="va-item-points">{item.points.map((p, i) => <li key={i}><MathText text={p} /></li>)}</ul>
                    {item.visuals.length > 0 && (
                      <div className="va-item-visuals">
                        {item.visuals.map((v) => <VisualChip key={v.id} visual={v} active={openVisual === v.id} onClick={() => setOpenVisual(openVisual === v.id ? null : v.id)} />)}
                      </div>
                    )}
                    {item.visuals.filter((v) => v.id === openVisual).map((v) => (
                      <div key={v.id} className="va-item-confirm lf-appear">
                        <VisualConfirmForm item={item} visual={v} onClose={() => setOpenVisual(null)} onConfirm={(data) => { actions.confirmVisual(item.id, v.id, data); setOpenVisual(null); }} />
                      </div>
                    ))}
                    {!generating && <AddVisualButton />}
                    {item.stale && (
                      <p className="lf-stale">Mục đã đổi sau khi dựng slide. <button type="button" className="lf-link" onClick={() => actions.regenerateItem(item.id)}>Sinh lại slide của mục này</button></p>
                    )}
                  </div>
                  <div className="va-item-side">
                    <span className="lf-meta">Số slide</span>
                    <Stepper label="số slide" value={item.slideCount} min={1} max={4} glyphs onChange={(v) => actions.setItem(item.id, { slideCount: v })} />
                    <span className="lf-meta">Số phút</span>
                    <Stepper label="số phút" value={item.minutes} min={1} max={30} onChange={(v) => actions.setItem(item.id, { minutes: v })} />
                  </div>
                </li>
              ))}
            </ol>
          </section>
        ))}
      </div>
      <footer className="va-foot">
        <TimeBudget lesson={lesson} />
        {generating ? (
          <span className="lf-meta"><ThinkingDots /> AI đang lập dàn ý</span>
        ) : lesson.slides.length ? (
          <button type="button" className="lf-btn" onClick={onOpenSlides}>Mở bộ slide</button>
        ) : (
          <button type="button" className="lf-btn lf-btn--primary" onClick={onBuild}>Dựng bộ slide</button>
        )}
      </footer>
    </div>
  );
}

function SlidesA({ lesson, actions }) {
  const [slideId, setSlideId] = useState(lesson.slides[0]?.id || null);
  const [elId, setElId] = useState(null);
  const [tab, setTab] = useState('el');
  const [confirmTarget, setConfirmTarget] = useState(null);
  const slide = lesson.slides.find((s) => s.id === slideId) || lesson.slides[0];
  useEffect(() => { if (!slideId && lesson.slides[0]) setSlideId(lesson.slides[0].id); }, [slideId, lesson.slides]);
  const index = slide ? lesson.slides.indexOf(slide) : -1;
  const el = slide?.elements.find((e) => e.id === elId) || null;

  return (
    <div className="va-slides lf-fade">
      <aside className="va-thumbs" aria-label="Danh sách slide">
        {lesson.items.map((item) => {
          const own = lesson.slides.filter((s) => s.itemId === item.id);
          if (!own.length) return null;
          return (
            <section key={item.id} className="va-thumb-group">
              <p className="va-thumb-item"><span>{lesson.items.indexOf(item) + 1}</span><MathText text={item.title} /></p>
              {own.map((s) => (
                <button key={s.id} type="button" className={`va-thumb ${s.id === slide?.id ? 'is-current' : ''} ${s.fresh ? 'lf-appear' : ''}`} onClick={() => { setSlideId(s.id); setElId(null); setConfirmTarget(null); }}>
                  <span className="va-thumb-n">{lesson.slides.indexOf(s) + 1}</span>
                  <SlideCanvas lesson={lesson} slide={s} mode="thumb" className="lf-sheet" />
                </button>
              ))}
            </section>
          );
        })}
        {lesson.generating === 'slides' && <p className="lf-meta va-thumbs-wait"><ThinkingDots /> Đang dựng slide</p>}
      </aside>
      <section className="va-canvas">
        <div className="va-canvas-bar">
          <span className="lf-meta">{slide ? `Slide ${index + 1}/${lesson.slides.length}. Bố cục mẫu: ${slide.template}` : 'Đang dựng slide'}</span>
          <span className="va-canvas-actions">
            <CheckButton lesson={lesson} />
            <ApprovalControl lesson={lesson} onApprove={actions.approve} />
            <button type="button" className="lf-btn lf-btn--primary" disabled={!lesson.slides.length || !!lesson.generating} onClick={() => actions.present(Math.max(0, index))}>Trình chiếu</button>
          </span>
        </div>
        <div className="va-canvas-desk lf-desk">
          {slide ? (
            <SlideCanvas
              key={slide.id} lesson={lesson} slide={slide} mode="edit" fit="contain" className="lf-sheet"
              selectedId={elId} onSelect={setElId}
              onMoveElement={(id, rect) => actions.moveElement(slide.id, id, rect)}
              onRequestConfirm={(itemId, visualId) => { setConfirmTarget({ itemId, visualId }); setTab('el'); }}
            />
          ) : (
            <p className="lf-meta va-canvas-wait"><ThinkingDots /> Đang dựng slide đầu tiên</p>
          )}
        </div>
      </section>
      <aside className="va-panel">
        <div className="lf-tabs" role="tablist">
          <button type="button" role="tab" aria-selected={tab === 'el'} onClick={() => setTab('el')}>Phần tử</button>
          <button type="button" role="tab" aria-selected={tab === 'ai'} onClick={() => setTab('ai')}>Trợ giảng AI</button>
        </div>
        {tab === 'el' && (confirmTarget
          ? <div className="lf-panel-body"><ConfirmForTarget lesson={lesson} target={confirmTarget} actions={actions} onClose={() => setConfirmTarget(null)} /></div>
          : <ElementPanel slide={slide} el={el} />)}
        {tab === 'ai' && <AssistantPanel />}
      </aside>
    </div>
  );
}
