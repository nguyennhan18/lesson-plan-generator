import React, { useEffect, useMemo, useRef, useState } from 'react';
import Workbench from './features/workbench/Workbench.jsx';
import { createWorkbenchActions, emptyWorkbench } from './features/workbench/workbenchActions.js';

/**
 * LessonAI-5512: Bàn làm việc là giao diện mặc định và duy nhất (#59, spec #36).
 */
export default function App() {
  const [workbench, setWorkbench] = useState(emptyWorkbench);
  const workbenchRef = useRef(workbench);
  workbenchRef.current = workbench;
  const workbenchActions = useMemo(
    () => createWorkbenchActions({ getSession: () => workbenchRef.current, setSession: setWorkbench }),
    [],
  );

  useEffect(() => {
    workbenchActions.refreshLessons();
  }, [workbenchActions]);

  useEffect(() => {
    if (workbench.saveState === 'saved') return undefined;
    const handler = event => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [workbench.saveState]);

  return <Workbench session={workbench} actions={workbenchActions} />;
}
