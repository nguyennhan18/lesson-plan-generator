import React, { Suspense, lazy } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import 'katex/dist/katex.min.css';
import './styles/index.css';

// PROTOTYPE, wipe me: /?prototype=lesson-flow mở prototype giao diện mới, chỉ khi chạy dev.
const LessonFlowPrototype = import.meta.env.DEV && new URLSearchParams(window.location.search).get('prototype') === 'lesson-flow'
  ? lazy(() => import('./features/prototype-lesson-flow/LessonFlowPrototype.jsx'))
  : null;

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(
    <React.StrictMode>
      {LessonFlowPrototype ? <Suspense fallback={null}><LessonFlowPrototype /></Suspense> : <App />}
    </React.StrictMode>
  );
}
