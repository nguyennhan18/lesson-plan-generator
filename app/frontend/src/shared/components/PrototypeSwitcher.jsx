/**
 * PROTOTYPE, wipe me. Thanh chuyển biến thể của prototype giao diện. Chỉ hiện khi chạy dev.
 * Phím ← và → đổi biến thể, trừ khi đang gõ chữ hoặc đang trình chiếu.
 */
import React, { useEffect } from 'react';

export default function PrototypeSwitcher({ variants, current, onChange, summary, hidden = false }) {
  const index = Math.max(0, variants.findIndex((v) => v.key === current));
  const go = (delta) => onChange(variants[(index + delta + variants.length) % variants.length].key);

  useEffect(() => {
    const onKey = (e) => {
      if (document.body.dataset.presenting === 'true') return;
      const t = e.target;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)) return;
      if (e.key === 'ArrowLeft') go(-1);
      if (e.key === 'ArrowRight') go(1);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  if (!import.meta.env.DEV || hidden) return null;
  const v = variants[index];
  const pill = {
    position: 'fixed', left: '50%', bottom: 14, transform: 'translateX(-50%)', zIndex: 100,
    display: 'flex', alignItems: 'center', gap: 10, padding: '6px 8px', maxWidth: 'calc(100vw - 32px)',
    background: '#ffe600', color: '#000', border: '1px solid #000', borderRadius: 999,
    boxShadow: '0 4px 14px rgba(0,0,0,.18)', font: '500 13px/1.3 system-ui, sans-serif'
  };
  const arrow = { width: 30, height: 30, borderRadius: 999, border: '1px solid #000', background: '#fff', cursor: 'pointer', fontSize: 15 };
  return (
    <div style={pill} role="toolbar" aria-label="Chuyển biến thể prototype">
      <button type="button" style={arrow} onClick={() => go(-1)} aria-label="Biến thể trước">←</button>
      <span style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <strong>Prototype {v.key} ({v.name})</strong>
        {summary && <span style={{ opacity: 0.75, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{summary}</span>}
      </span>
      <button type="button" style={arrow} onClick={() => go(1)} aria-label="Biến thể sau">→</button>
    </div>
  );
}
