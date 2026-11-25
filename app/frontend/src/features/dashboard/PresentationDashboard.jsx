import React, { useState } from 'react';
import {
  Sparkles,
  Layers,
  Cpu,
  BookOpen,
  ArrowRight,
  Clock,
  CheckCircle2,
  Sliders,
  Play,
  RotateCcw,
  Compass,
  BarChart2,
  Box,
  FileSpreadsheet
} from 'lucide-react';

/**
 * Trạm 1: Dashboard Khởi Tạo Bài Giảng (PresentationDashboard.jsx)
 * Tuân thủ FRONTEND_ARCHITECTURE.md (Mục 3.1 & Mục 7 - Input Data Pipeline)
 * - Hộp nhập lệnh thông minh (NotebookInputBox)
 * - Thanh công cụ nút cấu hình dạng viên thuốc (Pill Settings: Model, Số slide, Khối lớp, RAG SGK, Học lực)
 * - Danh sách bài giảng gần đây trong bộ nhớ (Recent Presentations)
 * - Chuyển tiếp mượt mà sang Trạm 2: Duyệt Dàn Ý (Outline Workspace)
 */
export default function PresentationDashboard({
  onGenerateOutline,
  isGeneratingOutline = false,
  recentDeck = null,
  onOpenRecentDeck,
  onNavigateScreen
}) {
  const [topic, setTopic] = useState('');
  const [subject, setSubject] = useState('Toán học');
  const [grade, setGrade] = useState(12);
  const [numSlides, setNumSlides] = useState(8);
  const [classProficiency, setClassProficiency] = useState('standard');
  const [modelProvider, setModelProvider] = useState('gemini');
  const [modelId, setModelId] = useState('');
  const [useRag, setUseRag] = useState(true);
  const [textContent, setTextContent] = useState('concise'); // 'concise' | 'detailed'

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!topic.trim()) {
      alert('Vui lòng nhập chủ đề bài giảng !');
      return;
    }

    onGenerateOutline?.({
      topic: topic.trim(),
      subject,
      grade,
      num_slides: numSlides,
      class_proficiency: classProficiency,
      model_provider: modelProvider,
      model_id: modelId || null,
      use_rag: useRag,
      text_content: textContent,
      tone: 'academic',
      language: 'vi'
    });
  };

  return (
    <div className="w-full h-full overflow-y-auto bg-[#ffffff] text-[#141414] p-4 sm:p-6 md:p-8">
      <div className="max-w-5xl mx-auto space-y-8 pb-12">
        {/* 1. Header Banner Trạm 1 */}
        <div className="text-center space-y-2 pt-2 sm:pt-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#f3f3f3] border border-[#e0e0e0] text-xs font-semibold text-[#141414]">
            <span className="w-2 h-2 rounded-full bg-[#0066ff] animate-pulse"></span>
            <span>Trạm 1: Khởi Tạo Đề Tài & Cấu Hình Đầu Vào</span>
          </div>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-[#141414] tracking-tight">
            Thiết Kế Bài Giảng AI Chuẩn Sư Phạm 5512
          </h1>
          <p className="text-xs sm:text-sm text-[#707070] max-w-2xl mx-auto leading-relaxed">
            Nhập chủ đề hoặc từ khóa môn Toán. Hệ thống tự động đối chiếu Sách Giáo Khoa GDPT 2018,
            lập Dàn ý chi tiết (Outline) và sẵn sàng sinh bộ Slide kèm mô hình 3D tương tác.
          </p>
        </div>

        {/* 2. Hộp nhập lệnh trung tâm (NotebookInputBox) */}
        <div className="p-5 sm:p-6 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-5">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#141414] flex items-center gap-1.5 uppercase tracking-wide">
                <BookOpen size={14} className="text-[#141414]" />
                <span>Chủ đề / Bài dạy cần soạn thảo:</span>
              </label>
              <span className="text-[11px] text-[#707070]">
                Bản nháp cần kiểm tra trước khi giảng dạy
              </span>
            </div>

            <div className="relative">
              <textarea
                rows={3}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Nhập chủ đề, mục tiêu và dữ kiện cần dùng trong bài giảng."
                className="w-full bg-[#f0f0f0] border-none rounded-2xl p-4 text-sm sm:text-base text-[#141414] placeholder-[#adadad] outline-none focus:ring-2 focus:ring-[#141414] transition font-medium resize-none leading-relaxed"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    handleSubmit(e);
                  }
                }}
              />
            </div>
          </div>

          {/* 3. Thanh nút cấu hình dạng viên thuốc (Pill Settings Bar) */}
          <div className="space-y-3 pt-1 border-t border-[#e0e0e0]">
            <div className="flex items-center justify-between text-xs text-[#707070] font-medium">
              <span className="flex items-center gap-1">
                <Sliders size={13} className="text-[#141414]" />
                <span>Cấu hình thông số đầu vào (Pill Settings):</span>
              </span>
              <span>Bấm phím <kbd className="px-1.5 py-0.5 rounded bg-[#f3f3f3] border border-[#e0e0e0] font-mono text-[10px]">Ctrl+Enter</kbd> để tạo dàn ý</span>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs">
              {/* Pill 1: Số lượng Slide */}
              <div className="flex items-center bg-[#f3f3f3] border border-[#e0e0e0] rounded-full p-0.5">
                <span className="px-2.5 text-[#707070] text-[11px] font-medium">Số slide:</span>
                {[6, 8, 10, 12].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setNumSlides(num)}
                    className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                      numSlides === num
                        ? 'bg-[#141414] text-white'
                        : 'text-[#707070] hover:text-[#141414]'
                    }`}
                  >
                    {num}
                  </button>
                ))}
              </div>

              {/* Pill 2: Khối lớp */}
              <div className="flex items-center bg-[#f3f3f3] border border-[#e0e0e0] rounded-full p-0.5">
                <span className="px-2.5 text-[#707070] text-[11px] font-medium">Khối:</span>
                {[10, 11, 12].map((g) => (
                  <button
                    key={g}
                    type="button"
                    onClick={() => setGrade(g)}
                    className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                      grade === g
                        ? 'bg-[#141414] text-white'
                        : 'text-[#707070] hover:text-[#141414]'
                    }`}
                  >
                    Lớp {g}
                  </button>
                ))}
              </div>

              {/* Pill 3: Phân hóa học lực */}
              <div className="flex items-center bg-[#f3f3f3] border border-[#e0e0e0] rounded-full p-0.5">
                <span className="px-2.5 text-[#707070] text-[11px] font-medium">Học lực:</span>
                {[
                  { key: 'basic', label: 'Cơ bản' },
                  { key: 'standard', label: 'Chuẩn' },
                  { key: 'advanced', label: 'Nâng cao' }
                ].map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => setClassProficiency(item.key)}
                    className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                      classProficiency === item.key
                        ? 'bg-[#141414] text-white'
                        : 'text-[#707070] hover:text-[#141414]'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              {/* Pill 4: Mô hình AI */}
              <div className="flex items-center bg-[#f3f3f3] border border-[#e0e0e0] rounded-full p-0.5">
                <span className="px-2.5 text-[#707070] text-[11px] font-medium flex items-center gap-1">
                  <Cpu size={12} /> Model:
                </span>
                {[
                  { id: '', label: 'Gemini tự động' },
                  { id: 'llama-3.3-70b-versatile', label: 'Groq Llama 3.3' }
                ].map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => {
                      setModelId(m.id);
                      setModelProvider(m.id.includes('llama') ? 'groq' : 'gemini');
                    }}
                    className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                      modelId === m.id
                        ? 'bg-[#141414] text-white'
                        : 'text-[#707070] hover:text-[#141414]'
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>

              {/* Pill 5: RAG SGK GDPT 2018 Toggle */}
              <button
                type="button"
                onClick={() => setUseRag(!useRag)}
                className={`px-3.5 py-1.5 rounded-full border text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
                  useRag
                    ? 'bg-[#ffffff] border-[#141414] text-[#141414]'
                    : 'bg-[#f3f3f3] border-[#e0e0e0] text-[#707070]'
                }`}
                title="Bật/Tắt đối chiếu dữ liệu với Sách giáo khoa Toán 12 KNTT"
              >
                <CheckCircle2 size={13} className={useRag ? 'text-[#0066ff]' : 'text-[#adadad]'} />
                <span>RAG SGK KNTT 12</span>
              </button>

              {/* Pill 6: Tỷ lệ 16:9 Cinema */}
              <div className="px-3 py-1.5 rounded-full bg-[#f3f3f3] border border-[#e0e0e0] text-[#141414] text-xs font-semibold flex items-center gap-1">
                <span>16:9 Widescreen</span>
              </div>
            </div>
          </div>

          {/* 4. Nút bấm CTA chính: Khởi Tạo Dàn Ý */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-3">
            <div className="text-xs text-[#707070] flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#10b981]"></span>
              <span>Sẵn sàng: Giáo án 5512 + SlideDeck + Mô hình 3D</span>
            </div>

            <button
              type="button"
              onClick={handleSubmit}
              disabled={isGeneratingOutline || !topic.trim()}
              className="px-6 py-3 rounded-full bg-[#141414] hover:bg-[#262626] disabled:opacity-50 text-white font-semibold text-sm flex items-center gap-2 transition active:scale-95 cursor-pointer shadow-none"
            >
              {isGeneratingOutline ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Đang phân tích sư phạm & tạo dàn ý...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>Khởi Tạo Dàn Ý (Generate Outline)</span>
                  <ArrowRight size={15} />
                </>
              )}
            </button>
          </div>
        </div>

        {/* 4. Bài thuyết trình gần đây trong bộ nhớ (Recent Presentations) */}
        {recentDeck && (
          <div className="p-5 rounded-[24px] bg-[#f3f3f3] border border-[#e0e0e0] flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-2xl bg-[#ffffff] border border-[#e0e0e0] flex items-center justify-center text-[#141414]">
                <Layers size={20} />
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#707070] block">
                  Bài thuyết trình gần đây nhất:
                </span>
                <h4 className="text-sm font-bold text-[#141414]">
                  {recentDeck.presentation_title || 'Bài giảng Toán học'}
                </h4>
                <p className="text-xs text-[#707070]">
                  Gồm {recentDeck.slides?.length || 0} slide • Đã nạp sẵn trong bộ nhớ trình duyệt
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => onNavigateScreen?.('presentation')}
                className="px-4 py-2 rounded-full bg-[#ffffff] hover:bg-[#e0e0e0] border border-[#e0e0e0] text-[#141414] text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
              >
                <Play size={13} />
                <span>Mở Trình Chiếu</span>
              </button>
              <button
                type="button"
                onClick={() => onNavigateScreen?.('lesson-plan')}
                className="px-4 py-2 rounded-full bg-[#141414] hover:bg-[#262626] text-white text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-none"
              >
                <FileSpreadsheet size={13} />
                <span>Xem Giáo Án 5512</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
