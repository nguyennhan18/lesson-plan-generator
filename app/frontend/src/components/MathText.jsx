import React from 'react';
import katex from 'katex';

/**
 * MathText - Component hiển thị công thức Toán học chuẩn KaTeX
 * Tự động nhận diện cú pháp inline ($...$), block ($$...$$), và các lệnh LaTeX thuần.
 * Thiết kế an toàn, không bao giờ gây sập UI nếu công thức bị lỗi cú pháp.
 */
export default function MathText({ text = '', block = false, className = '' }) {
  if (!text) return null;
  const rawStr = String(text);

  // 1. Chế độ khối (Block Display Mode) hoặc chuỗi thuần công thức
  if (block) {
    const cleanFormula = rawStr.replace(/^\$\$|\$\$$/g, '').trim();
    try {
      const html = katex.renderToString(cleanFormula, {
        displayMode: true,
        throwOnError: false,
        strict: false
      });
      return (
        <div
          className={`katex-block-wrapper overflow-x-auto my-1.5 ${className}`}
          dangerouslySetInnerHTML={{ __html: html }}
        />
      );
    } catch (e) {
      return <div className={`font-mono text-cyan-300 ${className}`}>{cleanFormula}</div>;
    }
  }

  // 2. Chế độ Inline / Pha trộn văn bản và công thức ($...$ và $$...$$)
  const parts = [];
  const mathRegex = /(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$)/g;
  let lastIndex = 0;
  let match;

  while ((match = mathRegex.exec(rawStr)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: rawStr.substring(lastIndex, match.index) });
    }
    const token = match[0];
    if (token.startsWith('$$')) {
      parts.push({ type: 'display', content: token.slice(2, -2) });
    } else {
      parts.push({ type: 'inline', content: token.slice(1, -1) });
    }
    lastIndex = match.index + token.length;
  }

  if (lastIndex < rawStr.length) {
    parts.push({ type: 'text', content: rawStr.substring(lastIndex) });
  }

  // 3. Nếu không có cặp dấu $ nào nhưng chứa các lệnh LaTeX đặc thù (VD: \frac, \Delta, \sqrt)
  if (parts.length === 1 && parts[0].type === 'text') {
    const content = parts[0].content;
    if (/\\(frac|Delta|sqrt|alpha|beta|pi|times|pm|sum|int|le|ge|neq|in|subset|quad|text|mathbf)/.test(content)) {
      try {
        const html = katex.renderToString(content, {
          displayMode: false,
          throwOnError: false,
          strict: false
        });
        return (
          <span
            className={className}
            dangerouslySetInnerHTML={{ __html: html }}
          />
        );
      } catch (e) {
        // Fallback về text thường
      }
    }
  }

  return (
    <span className={`inline-math-container ${className}`}>
      {parts.map((p, idx) => {
        if (p.type === 'text') {
          return <span key={idx}>{p.content}</span>;
        }
        try {
          const html = katex.renderToString(p.content, {
            displayMode: p.type === 'display',
            throwOnError: false,
            strict: false
          });
          return (
            <span
              key={idx}
              dangerouslySetInnerHTML={{ __html: html }}
              className={p.type === 'display' ? 'block my-1 text-center' : 'inline-block px-0.5'}
            />
          );
        } catch (e) {
          return <span key={idx} className="font-mono text-cyan-300 font-semibold">{p.content}</span>;
        }
      })}
    </span>
  );
}
