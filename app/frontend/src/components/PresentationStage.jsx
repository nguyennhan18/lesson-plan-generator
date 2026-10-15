import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, MessageSquare, Wrench, HelpCircle, Check, Eye, LineChart, Box, FileText } from 'lucide-react';
import ThreeCanvas from './ThreeCanvas';
import FunctionPlotter from './FunctionPlotter';
import MathText from './MathText';

export default function PresentationStage({
  slideDeck,
  currentSlide = 0,
  setCurrentSlide,
  isLeftOpen,
  isRightOpen,
  onToggleLeft,
  onToggleRight,
  polyhedronType,
  edgeLength,
  showHiddenLines,
  showVertexLabels,
  showAxes,
  cameraPreset,
  onSwitchSample
}) {
  const slides = slideDeck?.slides || [];
  const slide = slides[currentSlide] || {};

  // Trạng thái bình chọn Quiz tương tác
  const [votedOption, setVotedOption] = useState(null);
  const [votes, setVotes] = useState({ A: 28, B: 7, C: 4, D: 3 });
  const [showExplanation, setShowExplanation] = useState(false);

  // Chế độ hiển thị trực quan bên phải: 'auto' | '2d' | '3d' | 'pptx'
  const [visualMode, setVisualMode] = useState('auto');

  // Reset bình chọn khi chuyển slide
  useEffect(() => {
    setVotedOption(null);
    setShowExplanation(false);
  }, [currentSlide]);

  const handleVote = (label) => {
    setVotedOption(label);
    setVotes(prev => ({ ...prev, [label]: (prev[label] || 0) + 1 }));
    setShowExplanation(true);
  };

  const totalVotes = Object.values(votes).reduce((a, b) => a + b, 0);

  // Xác định ngữ cảnh bài học: Đại số / Phương trình (2D) hay Hình học không gian (3D)
  const fullContextText = `${slideDeck?.presentation_title || ''} ${slide.title || ''} ${slide.bullet_points?.join(' ') || ''}`.toLowerCase();
  const is3DGeometry = /không gian|lập phương|khối chóp|lăng trụ|tứ diện|mặt phẳng|góc giữa|thiết diện|thể tích khối chóp/i.test(fullContextText) || slide.has_3d === true;
  const hasChartData = Boolean(slide.has_chart || slide.chart_image_base64 || slide.chart_spec?.expression);

  // Quyết định chế độ hiển thị hiệu dụng
  let effectiveVisual = visualMode;
  if (visualMode === 'auto') {
    if (hasChartData || !is3DGeometry) {
      effectiveVisual = '2d';
    } else {
      effectiveVisual = '3d';
    }
  }

  // Xác định badge hoạt động sư phạm
  const activityTag = slide.activity_type || `HOẠT ĐỘNG ${currentSlide + 1}`;
  const isQuizLayout = slide.layout === 'QUIZ_OPTION' || Boolean(slide.quiz_options?.length);

  return (
    <div className="flex-1 flex flex-col justify-between h-full p-3 overflow-hidden bg-slate-950/40 relative">
      {/* 1. Thanh Top Điều Khiển Nhanh */}
      <div className="flex items-center justify-between mb-2 shrink-0">
        <div className="flex items-center gap-2">
          {!isLeftOpen && (
            <button
              onClick={onToggleLeft}
              className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-cyan-400 border border-cyan-800/80 rounded-lg text-xs flex items-center gap-1.5 shadow-lg transition"
              title="Mở Trợ Giảng AI Co-pilot (Phím C)"
            >
              <MessageSquare size={13} />
              <span>Hiện Trợ Giảng AI (C)</span>
            </button>
          )}

          {/* Nút chuyển nhanh bài mẫu (Quick Topic Switcher) */}
          {onSwitchSample && (
            <div className="hidden lg:flex items-center gap-1 bg-slate-900/90 border border-slate-800 rounded-lg p-0.5 text-[11px]">
              <span className="text-slate-400 px-1.5">Mẫu:</span>
              <button
                onClick={() => onSwitchSample('quadratic')}
                className={`px-2 py-0.5 rounded transition ${
                  fullContextText.includes('bậc hai') || fullContextText.includes('phương trình')
                    ? 'bg-cyan-600 text-white font-semibold'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                🏀 PT Bậc Hai (Toán 10)
              </button>
              <button
                onClick={() => onSwitchSample('cube')}
                className={`px-2 py-0.5 rounded transition ${
                  fullContextText.includes('lập phương')
                    ? 'bg-cyan-600 text-white font-semibold'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                🧊 Hình Lập Phương (Toán 11)
              </button>
            </div>
          )}
        </div>

        <div className="text-[11px] text-slate-400 tracking-wide font-mono hidden md:flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>SÂN KHẤU 16:9 • TOÁN HỌC CHUẨN KaTeX • CÔNG VĂN 5512</span>
        </div>

        <div>
          {!isRightOpen && (
            <button
              onClick={onToggleRight}
              className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-amber-400 border border-amber-800/80 rounded-lg text-xs flex items-center gap-1.5 shadow-lg transition"
              title="Mở Công Cụ 3D/Đồ Thị (Phím T)"
            >
              <span>Công Cụ Giảng Dạy (T)</span>
              <Wrench size={13} />
            </button>
          )}
        </div>
      </div>

      {/* 2. SÂN KHẤU CHÍNH 16:9 CINEMA (Không gian trọng tâm của Giáo viên) */}
      <div className="flex-1 flex items-center justify-center min-h-0">
        <div className="w-full h-full max-w-6xl aspect-video glass-panel rounded-2xl p-5 flex flex-col justify-between border-slate-800 shadow-2xl relative overflow-hidden bg-[#090d1c]/90">

          {/* Header của Slide */}
          <div className="pb-2.5 border-b border-slate-800/80 flex items-center justify-between shrink-0">
            <div>
              <span className="text-[10px] font-bold px-2.5 py-0.5 rounded border border-cyan-800 bg-cyan-950/70 text-cyan-300 uppercase tracking-wider">
                {activityTag}
              </span>
              <h2 className="text-base md:text-xl font-bold text-white mt-1 flex items-center gap-2">
                <MathText text={slide.title || "Tiêu đề bài giảng"} />
              </h2>
            </div>

            {/* Thanh chuyển đổi chế độ trực quan (Visual Mode Switcher) */}
            <div className="flex items-center gap-2">
              <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs">
                <button
                  onClick={() => setVisualMode('2d')}
                  className={`px-2.5 py-1 rounded-md flex items-center gap-1 transition ${
                    effectiveVisual === '2d'
                      ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                  title="Hiển thị đồ thị hàm số / Parabol 2D"
                >
                  <LineChart size={13} />
                  <span className="hidden sm:inline">Đồ Thị 2D</span>
                </button>
                <button
                  onClick={() => setVisualMode('3d')}
                  className={`px-2.5 py-1 rounded-md flex items-center gap-1 transition ${
                    effectiveVisual === '3d'
                      ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                  title="Hiển thị khối hình học không gian 3D"
                >
                  <Box size={13} />
                  <span className="hidden sm:inline">Không Gian 3D</span>
                </button>
                <button
                  onClick={() => setVisualMode('pptx')}
                  className={`px-2.5 py-1 rounded-md flex items-center gap-1 transition ${
                    effectiveVisual === 'pptx'
                      ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                  title="Xem trước bản in PowerPoint 1:1"
                >
                  <FileText size={13} />
                  <span className="hidden sm:inline">Bản In PPTX 1:1</span>
                </button>
              </div>

              <div className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-400 shadow-inner">
                Slide {currentSlide + 1} / {slides.length || 1}
              </div>
            </div>
          </div>

          {/* Body của Slide */}
          <div className="flex-1 my-2.5 overflow-y-auto">
            {/* TRƯỜNG HỢP A: BẢN IN PPTX 1:1 PREVIEW (Xóa bỏ hoàn toàn bất nhất Web vs File tải về) */}
            {effectiveVisual === 'pptx' ? (
              <div className="h-full w-full bg-slate-100 rounded-xl p-6 text-slate-900 flex flex-col justify-between shadow-2xl border-4 border-slate-300">
                {/* Header PPTX */}
                <div className="border-b-2 border-blue-900 pb-2 flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold text-blue-900">
                      <MathText text={slide.title || "Tiêu đề bài học"} />
                    </h3>
                    <p className="text-xs text-slate-600">{activityTag} • Chương trình GDPT 2018</p>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-blue-100 text-blue-900 font-bold text-xs border border-blue-300">
                    PowerPoint Native 16:9
                  </span>
                </div>

                {/* Nội dung chia 2 cột như trong file PPTX */}
                <div className="grid grid-cols-12 gap-5 my-3 items-center flex-1">
                  <div className="col-span-7 space-y-3">
                    <ul className="space-y-2 text-sm text-slate-800 font-serif">
                      {(slide.bullet_points || []).map((pt, i) => (
                        <li key={i} className="flex items-start gap-2 leading-relaxed">
                          <span className="text-blue-700 font-bold">•</span>
                          <span><MathText text={pt} /></span>
                        </li>
                      ))}
                    </ul>

                    {slide.main_definition_latex && (
                      <div className="p-3 bg-blue-50 border-l-4 border-blue-800 rounded text-blue-950 font-bold text-base my-2">
                        <MathText text={slide.main_definition_latex} block={true} />
                      </div>
                    )}
                  </div>

                  {/* Cột đồ thị ảnh Matplotlib hoặc công thức */}
                  <div className="col-span-5 flex flex-col items-center justify-center p-3 bg-white rounded-lg border border-slate-200 shadow-sm h-full max-h-[260px]">
                    {slide.chart_image_base64 ? (
                      <img
                        src={slide.chart_image_base64}
                        alt="Đồ thị Matplotlib Native"
                        className="max-h-[220px] object-contain rounded"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center text-center p-4 bg-slate-50 rounded">
                        <LineChart size={36} className="text-blue-500 mb-2" />
                        <span className="text-xs font-bold text-slate-700">Đồ thị Matplotlib Native</span>
                        <p className="text-[11px] text-slate-500 mt-1">
                          {slide.chart_spec?.chart_title || "Sẽ tự động xuất đồ thị khi tải file .pptx"}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer PPTX */}
                <div className="border-t border-slate-300 pt-2 flex items-center justify-between text-xs text-slate-500">
                  <span>Kế hoạch bài dạy môn Toán THPT - Công văn 5512/BGDĐT</span>
                  <span className="font-semibold text-blue-900">Trang {currentSlide + 1} / {slides.length}</span>
                </div>
              </div>
            ) : isQuizLayout ? (
              /* TRƯỜNG HỢP B: QUIZ TRẮC NGHIỆM TƯƠNG TÁC (LIVE POLL) */
              <div className="h-full flex flex-col justify-between gap-3">
                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span className="font-semibold text-amber-400 flex items-center gap-1.5">
                      <HelpCircle size={15} /> CÂU HỎI VẬN DỤNG & CỦNG CỐ NHANH
                    </span>
                    <span className="font-mono text-cyan-400">Đã bình chọn: {totalVotes} HS</span>
                  </div>
                  <p className="text-sm md:text-base text-white font-medium leading-relaxed">
                    <MathText text={slide.bullet_points?.[0] || "Chọn khẳng định đúng trong các phương án sau:"} />
                  </p>
                </div>

                {/* 4 Phương án A, B, C, D */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {(slide.quiz_options || [
                    { label: "A", text: "Phương án A", is_correct: true, distractor_rationale: "Đáp án chuẩn xác." },
                    { label: "B", text: "Phương án B", is_correct: false, distractor_rationale: "Học sinh dễ nhầm dấu." },
                    { label: "C", text: "Phương án C", is_correct: false, distractor_rationale: "Quên áp dụng điều kiện." },
                    { label: "D", text: "Phương án D", is_correct: false, distractor_rationale: "Nhầm công thức." }
                  ]).map((opt) => {
                    const isSelected = votedOption === opt.label;
                    const optVote = votes[opt.label] || 0;
                    const pct = Math.round((optVote / (totalVotes || 1)) * 100);

                    return (
                      <div
                        key={opt.label}
                        onClick={() => handleVote(opt.label)}
                        className={`p-3 rounded-xl border cursor-pointer transition text-xs space-y-1.5 relative overflow-hidden ${
                          isSelected
                            ? opt.is_correct
                              ? 'border-emerald-500 bg-emerald-950/40 text-emerald-200'
                              : 'border-rose-500 bg-rose-950/40 text-rose-200'
                            : 'border-slate-800 bg-slate-900/60 hover:border-slate-700 text-slate-200'
                        }`}
                      >
                        <div className="flex items-center justify-between font-semibold">
                          <span className="text-sm">
                            <strong>{opt.label}.</strong> <MathText text={opt.text} />
                          </span>
                          {isSelected && (
                            <span className="text-[11px] font-bold">
                              {opt.is_correct ? '✅ CHÍNH XÁC' : '❌ CHƯA ĐÚNG'}
                            </span>
                          )}
                          <span className="font-mono text-slate-400">{pct}%</span>
                        </div>

                        {/* Thanh phần trăm tiến trình */}
                        <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all duration-500 ${opt.is_correct ? 'bg-emerald-500' : 'bg-slate-600'}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Hộp thoại phân tích bẫy sai lầm sư phạm (Distractor Rationale) */}
                {showExplanation && (
                  <div className="p-3 rounded-xl bg-slate-900/95 border border-slate-700 text-xs space-y-1">
                    <strong className="text-amber-400 flex items-center gap-1.5 font-bold">
                      💡 Phân Tích Sư Phạm & Bẫy Sai Lầm (Distractor Analysis):
                    </strong>
                    <div className="text-slate-300 leading-relaxed space-y-1">
                      {slide.quiz_options?.map((opt) => (
                        <div key={opt.label}>
                          <span className="font-bold text-cyan-300">{opt.label}:</span> <MathText text={opt.distractor_rationale || opt.text} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* TRƯỜNG HỢP C: BÀI GIẢNG LÝ THUYẾT / ĐỒ THỊ 2D / HÌNH HỌC 3D */
              <div className="grid grid-cols-12 gap-5 h-full items-center">
                {/* Cột trái: Nội dung kiến thức & Công thức KaTeX */}
                <div className="col-span-12 lg:col-span-6 space-y-3 text-xs leading-relaxed">
                  <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                    <strong className="text-cyan-400 block text-xs font-semibold uppercase tracking-wider">
                      📌 Trọng tâm kiến thức:
                    </strong>
                    <ul className="space-y-2 text-slate-200">
                      {(slide.bullet_points || []).map((pt, i) => (
                        <li key={i} className="flex items-start gap-2 leading-relaxed">
                          <span className="text-cyan-400 font-bold shrink-0">•</span>
                          <span><MathText text={pt} /></span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Hiển thị công thức toán trọng tâm dạng KaTeX chuẩn */}
                  {slide.main_definition_latex && (
                    <div className="p-3 rounded-xl bg-gradient-to-r from-cyan-950/40 via-indigo-950/30 to-slate-950 border border-cyan-800/60 font-mono text-cyan-300 text-center text-sm md:text-base font-bold shadow-lg">
                      <MathText text={slide.main_definition_latex} block={true} />
                    </div>
                  )}

                  {/* Lời thoại gợi ý giảng dạy cho giáo viên */}
                  {slide.teacher_note && (
                    <div className="p-2.5 rounded-xl bg-amber-950/20 border border-amber-900/40 text-[11px] text-amber-300 flex items-start gap-2">
                      <span className="shrink-0 text-sm">💬</span>
                      <span>
                        <strong>Lời nhắc sư phạm:</strong> <MathText text={slide.teacher_note} />
                      </span>
                    </div>
                  )}
                </div>

                {/* Cột phải: KHÔNG GIAN TRỰC QUAN ĐÚNG BẢN CHẤT BÀI TOÁN */}
                <div className="col-span-12 lg:col-span-6 h-full min-h-[250px] bg-slate-950/90 rounded-2xl border border-slate-800 p-3 flex flex-col justify-between relative overflow-hidden shadow-inner">
                  {effectiveVisual === '2d' ? (
                    /* 1. ĐỒ THỊ 2D / PARABOL CHO ĐẠI SỐ & PHƯƠNG TRÌNH */
                    slide.chart_image_base64 ? (
                      <div className="w-full h-full flex flex-col items-center justify-between">
                        <div className="flex-1 w-full flex items-center justify-center p-1">
                          <img
                            src={slide.chart_image_base64}
                            alt="Đồ thị hàm số đồng bộ PPTX"
                            className="max-h-[210px] w-auto object-contain rounded"
                          />
                        </div>
                        <div className="w-full flex items-center justify-between text-[10px] text-slate-400 bg-slate-900/80 px-2.5 py-1 rounded border border-slate-800">
                          <span className="text-cyan-400 font-semibold">
                            {slide.chart_spec?.chart_title || "Đồ thị Matplotlib Native"}
                          </span>
                          <span className="text-emerald-400">Đồng bộ 1:1 với file PowerPoint</span>
                        </div>
                      </div>
                    ) : (
                      <FunctionPlotter
                        defaultExpr={slide.chart_spec?.expression || 'x**2 - 4'}
                        title={slide.chart_spec?.chart_title || 'Đồ thị Parabol y = f(x)'}
                        pedagogicalPurpose={slide.chart_spec?.pedagogical_purpose}
                        compact={false}
                        allowEdit={true}
                      />
                    )
                  ) : (
                    /* 2. THREE.JS 3D WEBGL CHO HÌNH HỌC KHÔNG GIAN */
                    <div className="w-full h-full relative flex items-center justify-center">
                      <ThreeCanvas
                        slideIndex={currentSlide}
                        polyhedronType={polyhedronType}
                        edgeLength={edgeLength}
                        showHiddenLines={showHiddenLines}
                        showVertexLabels={showVertexLabels}
                        showAxes={showAxes}
                        cameraPreset={cameraPreset}
                      />
                      <div className="absolute bottom-2 left-2 bg-slate-900/80 backdrop-blur px-2.5 py-1 rounded-md text-[10px] text-slate-400 border border-slate-800">
                        Chuột trái: Xoay 360° • Cuộn chuột: Thu phóng
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Footer Điều Khiển Slide: Chuyển slide & Filmstrip Thumbnails */}
          <div className="pt-2.5 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 shrink-0">
            {/* Filmstrip thumbnails nhanh */}
            <div className="flex items-center gap-1.5 overflow-x-auto max-w-xl py-0.5">
              {slides.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentSlide(idx)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-medium whitespace-nowrap transition ${
                    currentSlide === idx
                      ? 'bg-cyan-600 text-white shadow-md shadow-cyan-950/50'
                      : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
                  }`}
                >
                  {idx + 1}. {s.title?.split('•')[0]?.slice(0, 16) || `Slide ${idx + 1}`}
                </button>
              ))}
            </div>

            {/* Nút Trước / Sau */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentSlide(Math.max(0, currentSlide - 1))}
                disabled={currentSlide === 0}
                className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-slate-300 hover:text-white border border-slate-800 text-xs font-semibold flex items-center gap-1 transition"
                title="Phím ←"
              >
                <ChevronLeft size={16} /> Trước
              </button>
              <button
                onClick={() => setCurrentSlide(Math.min(slides.length - 1, currentSlide + 1))}
                disabled={currentSlide >= slides.length - 1}
                className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 disabled:opacity-40 text-white text-xs font-semibold flex items-center gap-1 shadow-lg shadow-cyan-950/40 transition"
                title="Phím →"
              >
                Sau <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
