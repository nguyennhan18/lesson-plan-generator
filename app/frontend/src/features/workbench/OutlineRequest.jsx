import React, { useEffect, useState } from 'react';
import { CLASS_LEVEL_LABELS, outlineRequest } from './workbenchActions.js';

export default function OutlineRequest({ actions, onCreated, onBusyChange, disabled, defaultLevel = 'standard' }) {
  const [request, setRequest] = useState('');
  const [level, setLevel] = useState(defaultLevel);
  useEffect(() => {
    if (defaultLevel && CLASS_LEVEL_LABELS[defaultLevel]) {
      setLevel(defaultLevel);
    }
  }, [defaultLevel]);
  const [match, setMatch] = useState(null);
  const [changing, setChanging] = useState(false);
  const [choice, setChoice] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [lookupError, setLookupError] = useState('');
  const [lookupAttempt, setLookupAttempt] = useState(0);
  const query = request.trim();

  useEffect(() => {
    if (!query) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const result = await outlineRequest('/api/v1/workbench/outline/identify', { request: query }, { signal: controller.signal });
        if (!controller.signal.aborted) setMatch({ ...result, query });
      } catch (error) {
        if (!controller.signal.aborted) setLookupError(error.message);
      }
    }, 300);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, lookupAttempt]);

  const current = match?.query === query ? match : null;
  const lessonId = choice ?? current?.lesson_id;
  const textbook = current?.lessons.find(lesson => lesson.lesson_id === lessonId);
  const canGenerate = current && !busy && !disabled && (!changing || Boolean(textbook));

  async function generate(event) {
    event.preventDefault();
    if (!canGenerate) return;
    setBusy(true);
    onBusyChange(true);
    setError('');
    try {
      const created = await actions.generateLesson({ request: query, level, lesson_id: lessonId ?? null });
      if (created) onCreated();
    } catch (error) {
      setError(error.message.startsWith('[') ? error.message : `[invalid_ai_output] ${error.message}`);
    } finally {
      setBusy(false);
      onBusyChange(false);
    }
  }

  return (
    <form className="wb-form" onSubmit={generate}>
      <label>Yêu cầu soạn bài
        <textarea value={request} required maxLength={4000} rows={5} disabled={busy} onChange={event => {
          setRequest(event.target.value);
          setChoice(null);
          setChanging(false);
          setLookupError('');
          setError('');
          if (event.target.value.trim() === query && lookupError) setLookupAttempt(value => value + 1);
        }} />
      </label>
      <div className="wb-form-row">
        <p className="wb-meta" aria-live="polite">
          {textbook ? `Bài SGK: ${textbook.title}` : current ? 'Chưa nhận diện được bài SGK.' :
            query && !lookupError ? 'Đang nhận diện bài SGK…' : 'Bài SGK sẽ được nhận diện từ yêu cầu.'}
        </p>
        <button type="button" className="wb-btn" disabled={busy || !current?.lessons.length}
          onClick={() => setChanging(value => !value)}>{changing ? 'Xong' : 'Đổi bài'}</button>
      </div>
      {changing && current && <label>Bài SGK
        <select value={lessonId ?? ''} disabled={busy} onChange={event => setChoice(event.target.value || null)}>
          <option value="" disabled>Chọn bài SGK</option>
          {current.lessons.map(lesson => <option key={lesson.lesson_id} value={lesson.lesson_id}>{lesson.title}</option>)}
        </select>
      </label>}
      <label>Trình độ lớp
        <select value={level} disabled={busy} onChange={event => setLevel(event.target.value)}>
          {Object.entries(CLASS_LEVEL_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </label>
      {lookupError && <p role="alert">{lookupError} <button type="button" className="wb-btn" onClick={() => {
        setLookupError('');
        setLookupAttempt(value => value + 1);
      }}>Thử lại nhận diện</button></p>}
      {error && <p role="alert">{error}</p>}
      <button type="submit" className="wb-btn wb-btn--primary" disabled={!canGenerate}>
        {busy ? 'Đang lập dàn ý…' : error ? 'Thử lại' : 'Lập dàn ý'}
      </button>
    </form>
  );
}
