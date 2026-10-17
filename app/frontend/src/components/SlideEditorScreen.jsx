import React, { useState, useEffect } from 'react';
import { Presentation, Download, Plus, Trash2, Edit3, HelpCircle, Save, Sparkles } from 'lucide-react';
import MathText from './MathText';
import MathLiveModal from './MathLiveModal';

export default function SlideEditorScreen({
  slideDeck,
  setSlideDeck,
  onExportPptx
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

  // Đồng bộ khi đổi slide được chọn hoặc khi slideDeck thay đổi
  useEffect(() => {
    if (slides[selectedSlide]) {
      const cur = slides[selectedSlide];
      setTitle(cur.title || '');
      setBulletsText((cur.bullet_points || []).join('\n'));
      setLatex(cur.main_definition_latex || '');
      setTeacherNote(cur.teacher_note || '');
    }
  }, [selectedSlide, slideDeck]);

  const handleSaveCurrentSlide = () => {
    if (!slides[selectedSlide]) return;
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
      alert(`💾 Đã lưu thay đổi vào Slide ${selectedSlide + 1}!`);
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
            <span>🛠️</span> Xưởng Biên Tập Slide & Đồ Thị Toán Học
          </h2>
          <p className="text-xs text-slate-400">Chỉnh sửa trực tiếp từng slide bài giảng do AI sinh ra & Xuất file PowerPoint thật</p>
        </div>
        <button
          onClick={onExportPptx}
          className="px-3.5 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-amber-950/40 transition"
        >
          <Download size={14} /> Xuất PowerPoint (.pptx)
        </button>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* Cột 1: Danh Sách Slide Thumbnails */}
        <div className="col-span-12 lg:col-span-3 glass-panel p-3.5 rounded-2xl border-slate-800 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-xs font-bold text-white">📑 Danh Sách Slide ({slides.length})</span>
            <button
              onClick={handleAddNewSlide}
              className="p-1 px-2 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs flex items-center gap-1 font-medium"
            >
              <Plus size={13} /> Thêm Slide
            </button>
          </div>

          <div className="space-y-2 max-h-[560px] overflow-y-auto pr-1">
            {slides.map((s, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedSlide(idx)}
                className={`p-2.5 rounded-xl border cursor-pointer transition text-xs flex items-start justify-between gap-2 ${
                  selectedSlide === idx
                    ? 'border-cyan-500 bg-slate-900 shadow-md shadow-cyan-950/30'
                    : 'border-slate-800/80 bg-slate-900/40 hover:bg-slate-800/60'
                }`}
              >
                <div className="truncate">
                  <div className="font-semibold text-white truncate">Slide {idx + 1}: {s.title || `Trang ${idx + 1}`}</div>
                  <div className="text-[11px] text-slate-400 truncate mt-0.5">{s.activity_type || 'Nội dung bài'}</div>
                </div>
                <button
                  onClick={(e) => handleDeleteSlide(idx, e)}
                  className="text-slate-500 hover:text-rose-400 p-0.5 rounded transition"
                  title="Xóa slide này"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Cột 2: Trình Soạn Thảo Chi Tiết */}
        <div className="col-span-12 lg:col-span-5 glass-panel p-4 rounded-2xl border-slate-800 space-y-3.5 text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="font-bold text-white text-sm flex items-center gap-2">
              <Edit3 size={15} className="text-cyan-400" /> Biên Tập Slide {selectedSlide + 1}
            </h3>
            <span className="text-[11px] text-cyan-400 font-mono">
              Bố cục: {curSlide.layout || 'IMAGE_TEXT'}
            </span>
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
              onChange={(e) => setLatex(e.target.value)}
              onDoubleClick={() => setIsMathModalOpen(true)}
              placeholder="VD: \Delta = b^2 - 4ac hoặc x = \frac{-b \pm \sqrt{\Delta}}{2a}"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-cyan-300 font-mono"
            />
            {latex && (
              <div
                onDoubleClick={() => setIsMathModalOpen(true)}
                title="Nhấp đúp (Double-Click) để sửa bằng MathLive"
                className="mt-1.5 p-2 bg-slate-950/80 hover:bg-slate-900 rounded-lg border border-cyan-800/50 hover:border-cyan-500 text-center cursor-pointer transition"
              >
                <span className="text-[10px] text-slate-400 block mb-0.5">
                  Hiển thị KaTeX chuẩn (Nhấp đúp để mở MathLive):
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

      {/* Task 8.2: Modal Popup chỉnh sửa công thức Toán trực quan (MathLive) */}
      <MathLiveModal
        isOpen={isMathModalOpen}
        initialLatex={latex}
        fieldLabel={`Công thức trọng tâm (Slide ${selectedSlide + 1})`}
        onClose={() => setIsMathModalOpen(false)}
        onSave={(formattedLatex) => setLatex(formattedLatex)}
      />
    </div>
  );
}
