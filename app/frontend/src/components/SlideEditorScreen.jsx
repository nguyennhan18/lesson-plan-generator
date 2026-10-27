import React, { useState, useEffect, useMemo } from 'react';
import { Presentation, Download, Plus, Trash2, Edit3, HelpCircle, Save, Sparkles, AlertTriangle, FileText, Package, BookOpen } from 'lucide-react';
import MathText from './MathText';
import MathLiveModal from './MathLiveModal';
import PedagogicalWarningModal from './PedagogicalWarningModal';
import { updateSlideFormulaInDeck } from '../utils/slideDeckStorage';
import { validateLatexSyntax } from '../utils/latexValidator';
import { auditSlideDeckLocal, auditSlideDeckRemote, mergeAuditWarnings } from '../utils/pedagogicalLinterClient';

export default function SlideEditorScreen({
  slideDeck,
  setSlideDeck,
  onExportPptx,
  onExportDocx,
  onExportDualPackage
}) {
  const slides = slideDeck?.slides || [];
  const [selectedSlide, setSelectedSlide] = useState(0);

  // Form states cho slide đang chọn
  const [title, setTitle] = useState('');
  const [bulletsText, setBulletsText] = useState('');
  const [latex, setLatex] = useState('');
  const [teacherNote, setTeacherNote] = useState('');

  // Task 8.2: Trạng thái mở Modal MathLive trong Xưởng Biên Tập Slide
  const [isMathModalOpen, setIsMathModalOpen] = useState(false);

  // Task 9.3: Trạng thái Highlight xác nhận khung Preview KaTeX vừa được cập nhật
  const [isFormulaUpdated, setIsFormulaUpdated] = useState(false);

  // Task 9.4: Trạng thái lưu lỗi kiểm tra cú pháp LaTeX tại Form Biên Tập
  const [editorLatexError, setEditorLatexError] = useState(null);

  // Task 10.4: Trạng thái Danh sách Cảnh báo Sư phạm (Human-in-the-Loop)
  const [remoteWarnings, setRemoteWarnings] = useState([]);
  const [dismissedWarningKeys, setDismissedWarningKeys] = useState([]);
  const [isWarningModalOpen, setIsWarningModalOpen] = useState(false);

  // Bản nháp trực tiếp (Live Draft Deck) phản ánh tức thì những gì GV đang gõ trên Form mà chưa cần bấm Lưu
  const liveDraftDeck = useMemo(() => {
    const draftSlides = slides.map((s, idx) => {
      if (idx !== selectedSlide) return s;
      return {
        ...s,
        title,
        bullet_points: String(bulletsText || '')
          .split('\n')
          .filter((line) => line.trim().length > 0),
        main_definition_latex: latex,
        teacher_note: teacherNote
      };
    });
    return { ...slideDeck, slides: draftSlides };
  }, [slideDeck, slides, selectedSlide, title, bulletsText, latex, teacherNote]);

  const localWarnings = useMemo(
    () => auditSlideDeckLocal(liveDraftDeck).warnings,
    [liveDraftDeck]
  );

  // Đồng bộ thêm kết quả kiểm định đại số SymPy từ Backend (/api/v1/validation/audit-deck)
  useEffect(() => {
    let isCancelled = false;
    auditSlideDeckRemote(liveDraftDeck).then((res) => {
      if (!isCancelled && res && Array.isArray(res.warnings)) {
        setRemoteWarnings(res.warnings);
      }
    });
    return () => {
      isCancelled = true;
    };
  }, [slideDeck]);

  const getWarningKey = (w) => `${w.slide_index}::${w.field || ''}::${w.detected_token || w.message}`;

  const activeWarnings = useMemo(() => {
    const merged = mergeAuditWarnings(localWarnings, remoteWarnings);
    return merged.filter((w) => !dismissedWarningKeys.includes(getWarningKey(w)));
  }, [localWarnings, remoteWarnings, dismissedWarningKeys]);

  const currentSlideWarnings = useMemo(
    () => activeWarnings.filter((w) => Number(w.slide_index) === selectedSlide + 1),
    [activeWarnings, selectedSlide]
  );

  const handleDismissWarning = (warningItem) => {
    const key = getWarningKey(warningItem);
    setDismissedWarningKeys((prev) => (prev.includes(key) ? prev : [...prev, key]));
  };

  useEffect(() => {
    if (!isFormulaUpdated) return;
    const timer = setTimeout(() => setIsFormulaUpdated(false), 2400);
    return () => clearTimeout(timer);
  }, [isFormulaUpdated]);

  // Đồng bộ khi đổi slide được chọn hoặc khi slideDeck thay đổi
  useEffect(() => {
    if (slides[selectedSlide]) {
      const cur = slides[selectedSlide];
      setTitle(cur.title || '');
      setBulletsText((cur.bullet_points || []).join('\n'));
      setLatex(cur.main_definition_latex || '');
      setTeacherNote(cur.teacher_note || '');
      setEditorLatexError(null);
    }
  }, [selectedSlide, slideDeck]);

  const handleSaveCurrentSlide = () => {
    if (!slides[selectedSlide]) return;

    // Task 9.4: Kiểm tra cú pháp LaTeX hợp lệ trước khi lưu vào Slide JSON
    if (String(latex || '').trim()) {
      const validation = validateLatexSyntax(latex, {
        displayMode: true,
        allowPlaceholdersForPreview: false
      });
      if (!validation.isValid) {
        setEditorLatexError(validation.errorMessage);
        return;
      }
    }
    setEditorLatexError(null);

    const updated = [...slides];
    const newBullets = bulletsText.split('\n').filter(line => line.trim().length > 0);
    updated[selectedSlide] = {
      ...updated[selectedSlide],
      title,
      bullet_points: newBullets,
      main_definition_latex: latex,
      teacher_note: teacherNote
    };
    if (setSlideDeck) {
      setSlideDeck({ ...slideDeck, slides: updated });
      setIsFormulaUpdated(true);
      alert(`Đã lưu thay đổi vào Slide ${selectedSlide + 1}!`);
    }
  };

  const handleAddNewSlide = () => {
    const newSlideNum = slides.length + 1;
    const newSlide = {
      slide_number: newSlideNum,
      title: `${newSlideNum}. Nội dung bổ sung mới`,
      activity_type: "LUYỆN TẬP & CỦNG CỐ",
      layout: "IMAGE_TEXT",
      bullet_points: ["Nhập các ý chính trọng tâm tại đây."],
      main_definition_latex: "",
      teacher_note: "Ghi chú dành riêng cho giáo viên.",
      has_3d: false
    };
    if (setSlideDeck) {
      const updated = [...slides, newSlide];
      setSlideDeck({ ...slideDeck, slides: updated });
      setSelectedSlide(updated.length - 1);
    }
  };

  const handleDeleteSlide = (idx, e) => {
    e.stopPropagation();
    if (slides.length <= 1) {
      alert("Không thể xóa slide duy nhất còn lại!");
      return;
    }
    if (window.confirm(`Thầy/Cô có chắc chắn muốn xóa Slide ${idx + 1}?`)) {
      const updated = slides.filter((_, i) => i !== idx);
      if (setSlideDeck) {
        setSlideDeck({ ...slideDeck, slides: updated });
        setSelectedSlide(Math.max(0, idx - 1));
      }
    }
  };

  const curSlide = slides[selectedSlide] || {};

  return (
    <div className="flex-1 p-5 overflow-y-auto max-w-7xl mx-auto space-y-4">
      {/* Tiêu đề màn hình */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            Xưởng Biên Tập Slide & Đồ Thị Toán Học
          </h2>
          <p className="text-xs text-slate-400">Chỉnh sửa trực tiếp từng slide bài giảng do AI sinh ra & Xuất file PowerPoint thật</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setIsWarningModalOpen(true)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition ${
              activeWarnings.length > 0
                ? 'bg-amber-500/20 hover:bg-amber-500/30 border-amber-400 text-amber-300 shadow-lg shadow-amber-950/50 animate-pulse'
                : 'bg-slate-900 hover:bg-slate-800 border-slate-700 text-slate-300'
            }`}
            title="Kiểm duyệt chính tả Tiếng Việt, biến đổi đại số SymPy và định lý SGK (Không tự động ghi đè)"
          >
            <AlertTriangle size={14} className={activeWarnings.length > 0 ? 'text-amber-400' : 'text-slate-400'} />
            <span>
              {activeWarnings.length > 0
                ? `⚠️ Cảnh báo (${activeWarnings.length})`
                : 'Kiểm duyệt Sư phạm'}
            </span>
          </button>

          {/* Task 19.2: Cụm nút bấm Tải về trên Xưởng Biên Tập Slide */}
          <button
            type="button"
            onClick={onExportPptx}
            className="px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-amber-950/40 transition active:scale-95 cursor-pointer"
            title="Xuất file PowerPoint (.pptx) chuẩn 16:9 kèm ảnh mô hình 3D và đồ thị"
          >
            <Download size={14} /> <span>Tải Slide (.pptx)</span>
          </button>

          <button
            type="button"
            onClick={onExportDocx}
            className="px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-blue-950/40 transition active:scale-95 cursor-pointer"
            title="Tải Giáo án Word (.docx) đồng bộ chuẩn CV 5512"
          >
            <FileText size={14} /> <span>Tải Word (.docx)</span>
          </button>

          <button
            type="button"
            onClick={onExportDualPackage}
            className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-emerald-950/40 border border-emerald-400/40 transition active:scale-95 cursor-pointer"
            title="Tải Trọn Bộ (.zip): Gói kép Word + PowerPoint đồng bộ 100%"
          >
            <Package size={14} /> <span>Tải Trọn Bộ (.zip)</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* Cột 1: Danh Sách Slide Thumbnails */}
        <div className="col-span-12 lg:col-span-3 glass-panel p-3.5 rounded-2xl border-slate-800 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-xs font-bold text-white">Danh Sách Slide ({slides.length})</span>
            <button
              onClick={handleAddNewSlide}
              className="p-1 px-2 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs flex items-center gap-1 font-medium"
            >
              <Plus size={13} /> Thêm Slide
            </button>
          </div>

          <div className="space-y-2 max-h-[560px] overflow-y-auto pr-1">
            {slides.map((s, idx) => {
              const slideWarnsCount = activeWarnings.filter(
                (w) => Number(w.slide_index) === idx + 1
              ).length;
              return (
                <div
                  key={idx}
                  onClick={() => setSelectedSlide(idx)}
                  className={`p-2.5 rounded-xl border cursor-pointer transition text-xs flex items-start justify-between gap-2 ${
                    selectedSlide === idx
                      ? 'border-cyan-500 bg-slate-900 shadow-md shadow-cyan-950/30'
                      : slideWarnsCount > 0
                      ? 'border-amber-500/70 bg-amber-950/30 hover:bg-amber-950/50'
                      : 'border-slate-800/80 bg-slate-900/40 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="truncate flex-1">
                    <div className="font-semibold text-white truncate flex items-center gap-1.5">
                      <span>Slide {idx + 1}: {s.title || `Trang ${idx + 1}`}</span>
                    </div>
                    <div className="text-[11px] text-slate-400 truncate mt-0.5 flex items-center gap-1.5 flex-wrap">
                      <span>{s.activity_type || 'Nội dung bài'}</span>
                      {s.source_refs && s.source_refs.length > 0 && (
                        <span className="px-1.5 py-0.2 rounded bg-indigo-950/80 border border-indigo-800 text-indigo-300 text-[10px] font-medium">
                          RAG KNTT 12
                        </span>
                      )}
                      {slideWarnsCount > 0 && (
                        <span
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedSlide(idx);
                            setIsWarningModalOpen(true);
                          }}
                          className="px-1.5 py-0.2 rounded bg-amber-500/25 border border-amber-400/60 text-amber-300 text-[10px] font-bold"
                          title="Nhấn để xem cảnh báo sư phạm của Slide này"
                        >
                          ⚠️ {slideWarnsCount} lỗi
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSlide(idx, e)}
                    className="text-slate-500 hover:text-rose-400 p-0.5 rounded transition"
                    title="Xóa slide này"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Cột 2: Trình Soạn Thảo Chi Tiết */}
        <div className="col-span-12 lg:col-span-5 glass-panel p-4 rounded-2xl border-slate-800 space-y-3.5 text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="font-bold text-white text-sm flex items-center gap-2">
              <Edit3 size={15} className="text-cyan-400" /> Biên Tập Slide {selectedSlide + 1}
            </h3>
            <div className="flex items-center gap-2">
              {curSlide.source_refs && curSlide.source_refs.length > 0 && (
                <span className="px-2 py-0.5 rounded bg-indigo-950/80 border border-indigo-800 text-indigo-300 text-[11px] font-medium flex items-center gap-1">
                  <BookOpen size={11} className="text-indigo-400" />
                  <span>KNTT 12</span>
                </span>
              )}
              {currentSlideWarnings.length > 0 && (
                <button
                  type="button"
                  onClick={() => setIsWarningModalOpen(true)}
                  className="px-2 py-0.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400 text-amber-300 text-[11px] font-bold flex items-center gap-1 transition"
                >
                  <AlertTriangle size={12} className="text-amber-400" />
                  <span>⚠️ {currentSlideWarnings.length} Cảnh báo</span>
                </button>
              )}
              <span className="text-[11px] text-cyan-400 font-mono">
                Bố cục: {curSlide.layout || 'IMAGE_TEXT'}
              </span>
            </div>
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Tiêu đề slide:</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500 font-medium"
            />
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Các ý gạch đầu dòng (Mỗi dòng một ý):</label>
            <textarea
              rows={4}
              value={bulletsText}
              onChange={(e) => setBulletsText(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white leading-relaxed focus:outline-none focus:border-cyan-500 font-mono text-[11px]"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-slate-400">Công thức Toán LaTeX trọng tâm:</label>
              <button
                type="button"
                onClick={() => setIsMathModalOpen(true)}
                className="px-2 py-0.5 rounded bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/60 text-[10px] font-semibold flex items-center gap-1 transition"
              >
                <Sparkles size={11} /> Gõ trực quan MathLive
              </button>
            </div>
            <input
              type="text"
              value={latex}
              onChange={(e) => {
                setLatex(e.target.value);
                setEditorLatexError(null);
              }}
              onDoubleClick={() => setIsMathModalOpen(true)}
              placeholder="VD: \Delta = b^2 - 4ac hoặc x = \frac{-b \pm \sqrt{\Delta}}{2a}"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-cyan-300 font-mono"
            />
            {editorLatexError && (
              <div className="mt-1.5 px-2.5 py-1.5 rounded-lg bg-rose-950/80 border border-rose-500/80 text-[11px] text-rose-200">
                ⚠️ <strong>Đã chặn lưu:</strong> {editorLatexError}
              </div>
            )}
            {latex && (
              <div
                onDoubleClick={() => setIsMathModalOpen(true)}
                title="Nhấp đúp (Double-Click) để sửa bằng MathLive"
                className={`mt-1.5 p-2 rounded-lg border text-center cursor-pointer transition-all duration-500 ${
                  isFormulaUpdated
                    ? 'bg-emerald-950/40 border-emerald-400 ring-2 ring-emerald-500/60'
                    : 'bg-slate-950/80 hover:bg-slate-900 border-cyan-800/50 hover:border-cyan-500'
                }`}
              >
                <span className="text-[10px] text-slate-400 block mb-0.5">
                  {isFormulaUpdated ? (
                    <span className="text-emerald-300 font-semibold">
                      ✓ Đã cập nhật & kết xuất KaTeX mới:
                    </span>
                  ) : (
                    'Hiển thị KaTeX chuẩn (Nhấp đúp để mở MathLive):'
                  )}
                </span>
                <MathText text={latex} block={true} />
              </div>
            )}
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Lời thoại riêng cho Giáo viên (Teacher Notes):</label>
            <textarea
              rows={2}
              value={teacherNote}
              onChange={(e) => setTeacherNote(e.target.value)}
              placeholder="Ghi chú phương pháp hoặc lời nhắc học sinh..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-300 text-[11px]"
            />
          </div>

          <button
            type="button"
            onClick={handleSaveCurrentSlide}
            className="w-full py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition flex items-center justify-center gap-2 shadow-lg shadow-cyan-950/40"
          >
            <Save size={15} /> Lưu Thay Đổi Vào Slide
          </button>
        </div>

        {/* Cột 3: Thanh Soi Quiz & Distractor */}
        <div className="col-span-12 lg:col-span-4 glass-panel p-4 rounded-2xl border-slate-800 space-y-3 text-xs">
          <h3 className="font-bold text-white text-sm pb-2 border-b border-slate-800 flex items-center gap-1.5">
            <HelpCircle size={15} className="text-amber-400" /> Cấu Hình Quiz & Bẫy Sai Lầm
          </h3>

          {curSlide.quiz_options && curSlide.quiz_options.length > 0 ? (
            <div className="space-y-2.5">
              <div className="text-[11px] text-slate-400">
                Slide này có câu hỏi trắc nghiệm tương tác:
              </div>
              {curSlide.quiz_options.map((opt) => (
                <div
                  key={opt.label}
                  className={`p-2.5 rounded-lg border space-y-1 ${
                    opt.is_correct
                      ? 'border-emerald-600/70 bg-emerald-950/30'
                      : 'border-slate-800 bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center justify-between font-semibold">
                    <span className={opt.is_correct ? 'text-emerald-300' : 'text-slate-200'}>
                      {opt.label}. {opt.text}
                    </span>
                    {opt.is_correct && <span className="text-[10px] text-emerald-400 font-bold">[Đáp án đúng]</span>}
                  </div>
                  {opt.distractor_rationale && (
                    <div className="text-[10px] text-slate-400 italic">
                      Lý do: {opt.distractor_rationale}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center text-slate-500 space-y-2">
              <p>Slide hiện tại là dạng trình bày lý thuyết / mô hình không gian 3D.</p>
              <p className="text-[11px] text-slate-600">Để biến thành slide Quiz, Thầy/Cô có thể nhờ Trợ Giảng AI thêm câu hỏi trắc nghiệm qua khung chat Co-pilot.</p>
            </div>
          )}
        </div>
      </div>

      {/* Task 8.2, Task 9.2 & Task 9.3: Modal Popup chỉnh sửa công thức Toán trực quan & Đồng bộ Slide JSON */}
      <MathLiveModal
        isOpen={isMathModalOpen}
        initialLatex={latex}
        fieldLabel={`Công thức trọng tâm (Slide ${selectedSlide + 1})`}
        onClose={() => setIsMathModalOpen(false)}
        onSave={(formattedLatex, rawExpandedLatex) => {
          setLatex(formattedLatex);
          setIsFormulaUpdated(true);
          if (setSlideDeck && slides[selectedSlide]) {
            const updatedDeck = updateSlideFormulaInDeck(slideDeck, {
              slideIndex: selectedSlide,
              targetField: 'main_definition_latex',
              formattedLatex,
              rawExpandedLatex
            });
            setSlideDeck(updatedDeck);
          }
        }}
      />

      {/* Task 10.4: Giao diện "Danh sách Cảnh báo Sư phạm" (Human-in-the-Loop) */}
      <PedagogicalWarningModal
        isOpen={isWarningModalOpen}
        onClose={() => setIsWarningModalOpen(false)}
        warnings={activeWarnings}
        currentSlideIndex={selectedSlide}
        onJumpToSlide={(idx) => setSelectedSlide(idx)}
        onOpenManualEdit={(item) => {
          const targetIdx = Math.max(0, Number(item.slide_index || 1) - 1);
          setSelectedSlide(targetIdx);
          setIsWarningModalOpen(false);
          if (item.field === 'main_definition_latex') {
            setIsMathModalOpen(true);
          }
        }}
        onDismissWarning={handleDismissWarning}
      />
    </div>
  );
}
