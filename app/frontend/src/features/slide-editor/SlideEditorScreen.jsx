import React, { useState, useEffect, useMemo } from 'react';
import { Presentation, Download, Plus, Trash2, Edit3, HelpCircle, Save, Sparkles, AlertTriangle, FileText, Package, BookOpen } from 'lucide-react';
import MathText from '../../shared/math/MathText';
import MathLiveModal from '../../shared/math/MathLiveModal';
import PedagogicalWarningModal from '../../shared/validation/PedagogicalWarningModal';
import { updateSlideFormulaInDeck } from '../../shared/storage/slideDeckStorage.js';
import { validateLatexSyntax } from '../../shared/math/latexValidator.js';
import { auditSlideDeckLocal, auditSlideDeckRemote, mergeAuditWarnings } from '../../shared/validation/pedagogicalLinterClient.js';

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
    <div className="flex-1 p-5 overflow-y-auto max-w-7xl mx-auto space-y-4 bg-[#ffffff] text-[#141414]">
      {/* Tiêu đề màn hình */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#e0e0e0]">
        <div>
          <h2 className="text-xl font-bold text-[#141414] flex items-center gap-2">
            Xưởng Biên Tập Slide & Đồ Thị Toán Học
          </h2>
          <p className="text-xs text-[#707070] mt-0.5">Chỉnh sửa trực tiếp từng slide bài giảng do AI sinh ra & Xuất file PowerPoint thật</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setIsWarningModalOpen(true)}
            className={`px-3.5 py-1.5 rounded-full border text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
              activeWarnings.length > 0
                ? 'bg-[#f3f3f3] hover:bg-[#e0e0e0] border-[#f59e0b] text-[#141414]'
                : 'bg-[#ffffff] hover:bg-[#f3f3f3] border-[#e0e0e0] text-[#707070]'
            }`}
            title="Kiểm duyệt chính tả Tiếng Việt, biến đổi đại số SymPy và định lý SGK"
          >
            <AlertTriangle size={14} className={activeWarnings.length > 0 ? 'text-[#f59e0b]' : 'text-[#707070]'} />
            <span>
              {activeWarnings.length > 0
                ? `⚠️ Cảnh báo (${activeWarnings.length})`
                : 'Kiểm duyệt Sư phạm'}
            </span>
          </button>

          {/* Cụm nút bấm Tải về trên Xưởng Biên Tập Slide */}
          <button
            type="button"
            onClick={onExportPptx}
            className="px-4 py-2 rounded-full bg-[#141414] hover:bg-[#262626] text-white text-xs font-semibold flex items-center gap-1.5 transition active:scale-95 cursor-pointer shadow-none"
            title="Xuất file PowerPoint (.pptx) chuẩn 16:9"
          >
            <Download size={14} /> <span>Tải Slide (.pptx)</span>
          </button>

          <button
            type="button"
            onClick={onExportDocx}
            className="px-4 py-2 rounded-full bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] border border-[#e0e0e0] text-xs font-semibold flex items-center gap-1.5 transition active:scale-95 cursor-pointer"
            title="Tải Giáo án Word (.docx) đồng bộ chuẩn CV 5512"
          >
            <FileText size={14} /> <span>Tải Word (.docx)</span>
          </button>

          <button
            type="button"
            onClick={onExportDualPackage}
            className="px-4 py-2 rounded-full bg-[#f3f3f3] hover:bg-[#e0e0e0] text-[#141414] border border-[#e0e0e0] text-xs font-semibold flex items-center gap-1.5 transition active:scale-95 cursor-pointer"
            title="Tải Trọn Bộ (.zip): Gói kép Word + PowerPoint đồng bộ 100%"
          >
            <Package size={14} /> <span>Tải Trọn Bộ (.zip)</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* Cột 1: Danh Sách Slide Thumbnails */}
        <div className="col-span-12 lg:col-span-3 p-4 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#e0e0e0]">
            <span className="text-xs font-bold text-[#141414]">Danh Sách Slide ({slides.length})</span>
            <button
              onClick={handleAddNewSlide}
              className="px-3 py-1 rounded-full bg-[#141414] text-white text-xs flex items-center gap-1 font-semibold cursor-pointer"
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
                  className={`p-3 rounded-2xl border cursor-pointer transition text-xs flex items-start justify-between gap-2 ${
                    selectedSlide === idx
                      ? 'border-[#141414] bg-[#f3f3f3] font-semibold text-[#141414]'
                      : slideWarnsCount > 0
                      ? 'border-[#f59e0b] bg-[#ffffff] text-[#141414]'
                      : 'border-[#e0e0e0] bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414]'
                  }`}
                >
                  <div className="truncate flex-1">
                    <div className="font-semibold text-[#141414] truncate flex items-center gap-1.5">
                      <span>Slide {idx + 1}: {s.title || `Trang ${idx + 1}`}</span>
                    </div>
                    <div className="text-[11px] text-[#707070] truncate mt-1 flex items-center gap-1.5 flex-wrap">
                      <span>{s.activity_type || 'Nội dung bài'}</span>
                      {s.source_refs && s.source_refs.length > 0 && (
                        <span className="px-2 py-0.2 rounded-full bg-[#f3f3f3] border border-[#e0e0e0] text-[#141414] text-[10px] font-medium">
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
                          className="px-2 py-0.2 rounded-full bg-[#f3f3f3] border border-[#f59e0b] text-[#f59e0b] text-[10px] font-bold"
                          title="Nhấn để xem cảnh báo sư phạm của Slide này"
                        >
                          ⚠️ {slideWarnsCount} lỗi
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSlide(idx, e)}
                    className="text-[#adadad] hover:text-[#ef4444] p-1 rounded-full transition cursor-pointer"
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
        <div className="col-span-12 lg:col-span-5 p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-3.5 text-xs text-[#141414]">
          <div className="flex items-center justify-between pb-2 border-b border-[#e0e0e0]">
            <h3 className="font-bold text-[#141414] text-sm flex items-center gap-2">
              <Edit3 size={15} /> Biên Tập Slide {selectedSlide + 1}
            </h3>
            <div className="flex items-center gap-2">
              {curSlide.source_refs && curSlide.source_refs.length > 0 && (
                <span className="px-2.5 py-0.5 rounded-full bg-[#f3f3f3] border border-[#e0e0e0] text-[#141414] text-[11px] font-semibold flex items-center gap-1">
                  <BookOpen size={11} />
                  <span>KNTT 12</span>
                </span>
              )}
              {currentSlideWarnings.length > 0 && (
                <button
                  type="button"
                  onClick={() => setIsWarningModalOpen(true)}
                  className="px-2.5 py-0.5 rounded-full bg-[#f3f3f3] border border-[#f59e0b] text-[#141414] text-[11px] font-semibold flex items-center gap-1 transition cursor-pointer"
                >
                  <AlertTriangle size={12} className="text-[#f59e0b]" />
                  <span>⚠️ {currentSlideWarnings.length} Cảnh báo</span>
                </button>
              )}
              <span className="text-[11px] text-[#707070] font-mono">
                {curSlide.layout || 'IMAGE_TEXT'}
              </span>
            </div>
          </div>

          <div>
            <label className="text-[#707070] block mb-1 font-semibold">Tiêu đề slide:</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-[#f0f0f0] border-none rounded-2xl px-3.5 py-2.5 text-[#141414] focus:ring-2 focus:ring-[#141414] outline-none font-medium"
            />
          </div>

          <div>
            <label className="text-[#707070] block mb-1 font-semibold">Các ý gạch đầu dòng (Mỗi dòng một ý):</label>
            <textarea
              rows={4}
              value={bulletsText}
              onChange={(e) => setBulletsText(e.target.value)}
              className="w-full bg-[#f0f0f0] border-none rounded-2xl p-3 text-[#141414] leading-relaxed focus:ring-2 focus:ring-[#141414] outline-none font-mono text-[11px]"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-[#707070] font-semibold">Công thức Toán LaTeX trọng tâm:</label>
              <button
                type="button"
                onClick={() => setIsMathModalOpen(true)}
                className="px-3 py-1 rounded-full bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] border border-[#e0e0e0] text-[11px] font-semibold flex items-center gap-1 transition cursor-pointer"
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
              className="w-full bg-[#f0f0f0] border-none rounded-2xl px-3.5 py-2.5 text-[#141414] font-mono focus:ring-2 focus:ring-[#141414] outline-none"
            />
            {editorLatexError && (
              <div className="mt-1.5 px-3 py-2 rounded-xl bg-[#ffffff] border border-[#ef4444] text-[11px] text-[#ef4444]">
                ⚠️ <strong>Đã chặn lưu:</strong> {editorLatexError}
              </div>
            )}
            {latex && (
              <div
                onDoubleClick={() => setIsMathModalOpen(true)}
                title="Nhấp đúp (Double-Click) để sửa bằng MathLive"
                className={`mt-2 p-3 rounded-2xl border text-center cursor-pointer transition-all duration-300 ${
                  isFormulaUpdated
                    ? 'bg-[#ffffff] border-[#141414] ring-2 ring-[#141414]'
                    : 'bg-[#f3f3f3] hover:bg-[#ffffff] border-[#e0e0e0]'
                }`}
              >
                <span className="text-[10px] text-[#707070] block mb-1">
                  {isFormulaUpdated ? (
                    <span className="text-[#10b981] font-semibold">
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
            <label className="text-[#707070] block mb-1 font-semibold">Lời thoại riêng cho Giáo viên (Teacher Notes):</label>
            <textarea
              rows={2}
              value={teacherNote}
              onChange={(e) => setTeacherNote(e.target.value)}
              placeholder="Ghi chú phương pháp hoặc lời nhắc học sinh..."
              className="w-full bg-[#f0f0f0] border-none rounded-2xl p-3 text-[#141414] text-[11px] focus:ring-2 focus:ring-[#141414] outline-none"
            />
          </div>

          <button
            type="button"
            onClick={handleSaveCurrentSlide}
            className="w-full py-3 rounded-full bg-[#141414] hover:bg-[#262626] text-white font-semibold transition flex items-center justify-center gap-2 cursor-pointer shadow-none"
          >
            <Save size={15} /> Lưu Thay Đổi Vào Slide
          </button>
        </div>

        {/* Cột 3: Thanh Soi Quiz & Distractor */}
        <div className="col-span-12 lg:col-span-4 p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-3 text-xs text-[#141414]">
          <h3 className="font-bold text-[#141414] text-sm pb-2 border-b border-[#e0e0e0] flex items-center gap-1.5">
            <HelpCircle size={15} /> Cấu Hình Quiz & Bẫy Sai Lầm
          </h3>

          {curSlide.quiz_options && curSlide.quiz_options.length > 0 ? (
            <div className="space-y-2.5">
              <div className="text-[11px] text-[#707070]">
                Slide này có câu hỏi trắc nghiệm tương tác:
              </div>
              {curSlide.quiz_options.map((opt) => (
                <div
                  key={opt.label}
                  className={`p-3 rounded-2xl border space-y-1 ${
                    opt.is_correct
                      ? 'border-[#141414] bg-[#f3f3f3]'
                      : 'border-[#e0e0e0] bg-[#ffffff]'
                  }`}
                >
                  <div className="flex items-center justify-between font-semibold">
                    <span className="text-[#141414]">
                      {opt.label}. {opt.text}
                    </span>
                    {opt.is_correct && <span className="text-[10px] text-[#10b981] font-bold">[Đáp án đúng]</span>}
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
