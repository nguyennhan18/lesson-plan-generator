import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, MessageSquare, Wrench, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';
import ThreeCanvas from './ThreeCanvas';

export default function PresentationStage({
  currentSlide,
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
  cameraPreset
}) {
  // Quiz State
  const [voted, setVoted] = useState(null);
  const [votes, setVotes] = useState({ A: 31, B: 6, C: 3, D: 2 });
  const [showSolution, setShowSolution] = useState(false);

  const totalVotes = Object.values(votes).reduce((a, b) => a + b, 0);

  const handleVote = (opt) => {
    setVoted(opt);
    setVotes(prev => ({ ...prev, [opt]: prev[opt] + 3 }));
  };

  const slidesMeta = [
    { title: "Hình Lập Phương ABCD.A'B'C'D' • Khối Đa Diện Đều", badge: 'HOẠT ĐỘNG 1: KHỞI ĐỘNG & ĐẶT VẤN ĐỀ', color: 'text-cyan-400', badgeColor: 'bg-blue-950 text-blue-300 border-blue-800' },
    { title: "1. Đường Chéo AC' & Góc Giữa Đường Thẳng Với Mặt Phẳng", badge: 'HOẠT ĐỘNG 2: HÌNH THÀNH KIẾN THỨC (PHẦN 1)', color: 'text-cyan-400', badgeColor: 'bg-cyan-950 text-cyan-300 border-cyan-800' },
    { title: "2. Đoạn Vuông Góc Chung AH ⊥ B'D' & Khoảng Cách", badge: 'HOẠT ĐỘNG 2: HÌNH THÀNH KIẾN THỨC (PHẦN 2)', color: 'text-emerald-400', badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-800' },
    { title: "3. Thiết Diện Mặt Phẳng (A'BD) & Diện Tích", badge: 'HOẠT ĐỘNG 3: LUYỆN TẬP & CỦNG CỐ', color: 'text-amber-400', badgeColor: 'bg-amber-950 text-amber-300 border-amber-800' },
    { title: "4. Khảo Sát Nhanh Cả Lớp (Live Poll) • Góc Giữa AC & A'D", badge: 'HOẠT ĐỘNG 4: VẬN DỤNG & QUIZ TRỰC TIẾP', color: 'text-rose-400', badgeColor: 'bg-rose-950 text-rose-300 border-rose-800' }
  ];

  return (
    <div className="flex-1 flex flex-col justify-between h-full p-3 overflow-hidden bg-slate-950/40 relative">
      {/* 1. Collapsed Dock Pills (If hidden) */}
      <div className="flex items-center justify-between mb-2">
        <div>
          {!isLeftOpen && (
            <button
              onClick={onToggleLeft}
              className="px-3 py-1 bg-slate-900/90 hover:bg-slate-800 text-cyan-400 border border-cyan-900/60 rounded-lg text-xs flex items-center gap-1.5 shadow-lg transition"
            >
              <MessageSquare size={13} />
              <span>Hiện Chat Co-pilot (C)</span>
            </button>
          )}
        </div>

        <div className="text-[11px] text-slate-400 tracking-wide font-mono hidden md:block">
          SÂN KHẤU 16:9 • THREE.JS 3D ENGINE • LIVE QUIZ INTERACTIVE
        </div>

        <div>
          {!isRightOpen && (
            <button
              onClick={onToggleRight}
              className="px-3 py-1 bg-slate-900/90 hover:bg-slate-800 text-amber-400 border border-amber-900/60 rounded-lg text-xs flex items-center gap-1.5 shadow-lg transition"
            >
              <span>Hiện Công Cụ 3D/Đồ Thị (T)</span>
              <Wrench size={13} />
            </button>
          )}
        </div>
      </div>

      {/* 2. Main 16:9 Cinema Viewport */}
      <div className="flex-1 flex items-center justify-center min-h-0">
        <div className="w-full h-full max-w-6xl aspect-video glass-panel rounded-2xl p-5 flex flex-col justify-between border-slate-800/80 shadow-2xl relative overflow-hidden">
          
          {/* Slide Header */}
          <div className="pb-3 border-b border-slate-800/80 flex items-center justify-between">
            <div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${slidesMeta[currentSlide].badgeColor}`}>
                {slidesMeta[currentSlide].badge}
              </span>
              <h2 className="text-base md:text-lg font-bold text-white mt-1 flex items-center gap-2">
                {slidesMeta[currentSlide].title}
              </h2>
            </div>
            <div className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-400">
              {currentSlide + 1} / 5
            </div>
          </div>

          {/* Slide Body Content */}
          <div className="flex-1 my-3 overflow-hidden">
            {currentSlide === 0 && (
              <div className="grid grid-cols-12 gap-4 h-full items-center">
                <div className="col-span-6 space-y-3 text-xs leading-relaxed">
                  <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1.5">
                    <strong className="text-cyan-400 block text-sm">🎯 Giả thiết bài toán:</strong>
                    <p className="text-slate-300">
                      Cho hình lập phương ABCD.A'B'C'D' có độ dài tất cả các cạnh bằng <strong>a</strong>.
                    </p>
                    <ul className="list-disc pl-4 text-slate-300 space-y-1">
                      <li>Đáy dưới ABCD và đáy trên A'B'C'D' là 2 hình vuông bằng nhau.</li>
                      <li>Các cạnh bên AA', BB', CC', DD' vuông góc với hai mặt phẳng đáy.</li>
                      <li>Hình lập phương có <strong>8 đỉnh</strong>, <strong>12 cạnh</strong> bằng nhau và <strong>6 mặt</strong> vuông.</li>
                    </ul>
                  </div>

                  <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-900/40">
                    <strong className="text-amber-400 block text-xs">❓ Câu hỏi trọng tâm bài giảng:</strong>
                    <p className="text-slate-300 mt-1">
                      Làm thế nào để tính <strong>đường chéo AC'</strong>, xác định <strong>khoảng cách từ A đến B'D'</strong> và dựng <strong>thiết diện (A'BD)</strong>?
                    </p>
                  </div>
                </div>

                <div className="col-span-6 h-full bg-slate-950/80 rounded-xl border border-slate-800 p-1 flex items-center justify-center">
                  <ThreeCanvas
                    slideIndex={0}
                    polyhedronType={polyhedronType}
                    edgeLength={edgeLength}
                    showHiddenLines={showHiddenLines}
                    showVertexLabels={showVertexLabels}
                    showAxes={showAxes}
                    cameraPreset={cameraPreset}
                  />
                </div>
              </div>
            )}

            {currentSlide === 1 && (
              <div className="grid grid-cols-12 gap-4 h-full items-center">
                <div className="col-span-6 space-y-3 text-xs leading-relaxed">
                  <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
                    <strong className="text-cyan-400 block text-sm">📐 Định lý Pytago 2 bước không gian:</strong>
                    <div className="p-2 rounded bg-slate-950 border border-slate-800/80 font-mono text-cyan-300">
                      {"1. Trong đáy (ABCD): AC = √(AB² + BC²) = a√2"}
                    </div>
                    <div className="p-2 rounded bg-slate-950 border border-slate-800/80 font-mono text-amber-300">
                      {"2. Do CC' ⊥ (ABCD) ⇒ ΔACC' vuông tại C"}
                    </div>
                    <div className="p-2.5 rounded bg-gradient-to-r from-rose-950/40 to-slate-950 border border-rose-800/60 font-mono text-rose-300 font-bold text-sm">
                      {"3. AC' = √(AC² + CC'²) = √(2a² + a²) = a√3"}
                    </div>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-900/50 border border-slate-800 text-[11px] text-slate-400">
                    💡 <strong>Lưu ý học sinh:</strong> Không nhầm lẫn giữa đường chéo mặt đáy (a√2) và đường chéo không gian (a√3).
                  </div>
                </div>

                <div className="col-span-6 h-full bg-slate-950/80 rounded-xl border border-slate-800 p-1 flex items-center justify-center">
                  <ThreeCanvas
                    slideIndex={1}
                    polyhedronType={polyhedronType}
                    edgeLength={edgeLength}
                    showHiddenLines={showHiddenLines}
                    showVertexLabels={showVertexLabels}
                    showAxes={showAxes}
                    cameraPreset={cameraPreset}
                  />
                </div>
              </div>
            )}

            {currentSlide === 2 && (
              <div className="grid grid-cols-12 gap-4 h-full items-center">
                <div className="col-span-6 space-y-3 text-xs leading-relaxed">
                  <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
                    <strong className="text-emerald-400 block text-sm">📏 Khoảng cách từ A đến đường thẳng B'D':</strong>
                    <p className="text-slate-300">
                      {"Xét tam giác AB'D' cân tại A với AB' = AD' = a√2 và B'D' = a√2."}
                    </p>
                    <div className="p-2.5 rounded bg-slate-950 border border-emerald-900/40 font-mono text-emerald-300">
                      {"Hạ AH ⊥ B'D' ⇒ H là trung điểm B'D'."}
                    </div>
                    <div className="p-2.5 rounded bg-slate-950 border border-emerald-900/60 font-mono text-emerald-400 font-bold text-sm">
                      {"AH = √(AB'² - B'H²) = √(2a² - a²/2) = a√6 / 2"}
                    </div>
                  </div>
                </div>

                <div className="col-span-6 h-full bg-slate-950/80 rounded-xl border border-slate-800 p-1 flex items-center justify-center">
                  <ThreeCanvas
                    slideIndex={2}
                    polyhedronType={polyhedronType}
                    edgeLength={edgeLength}
                    showHiddenLines={showHiddenLines}
                    showVertexLabels={showVertexLabels}
                    showAxes={showAxes}
                    cameraPreset={cameraPreset}
                  />
                </div>
              </div>
            )}

            {currentSlide === 3 && (
              <div className="grid grid-cols-12 gap-4 h-full items-center">
                <div className="col-span-6 space-y-3 text-xs leading-relaxed">
                  <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
                    <strong className="text-amber-400 block text-sm">▱ Thiết diện mặt phẳng (A'BD):</strong>
                    <p className="text-slate-300">
                      Mặt phẳng (A'BD) cắt các mặt của hình lập phương theo 3 đoạn thẳng: A'B, BD và DA'.
                    </p>
                    <ul className="list-disc pl-4 text-slate-300 space-y-1">
                      <li>{"A'B = a√2 (đường chéo mặt bên ABB'A')"}</li>
                      <li>{"BD = a√2 (đường chéo mặt đáy ABCD)"}</li>
                      <li>{"A'D = a√2 (đường chéo mặt bên ADD'A')"}</li>
                    </ul>
                    <div className="p-2.5 rounded bg-slate-950 border border-amber-800/60 font-mono text-amber-300 font-bold text-sm">
                      {"Thiết diện là ΔA'BD đều cạnh a√2 ⇒ S = a²√3 / 2"}
                    </div>
                  </div>
                </div>

                <div className="col-span-6 h-full bg-slate-950/80 rounded-xl border border-slate-800 p-1 flex items-center justify-center">
                  <ThreeCanvas
                    slideIndex={3}
                    polyhedronType={polyhedronType}
                    edgeLength={edgeLength}
                    showHiddenLines={showHiddenLines}
                    showVertexLabels={showVertexLabels}
                    showAxes={showAxes}
                    cameraPreset={cameraPreset}
                  />
                </div>
              </div>
            )}

            {currentSlide === 4 && (
              <div className="h-full flex flex-col justify-between py-1 text-xs">
                {/* Question */}
                <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
                  <div className="flex justify-between items-center text-[11px] mb-1">
                    <span className="font-bold text-amber-400">CÂU HỎI TRẮC NGHIỆM VẬN DỤNG</span>
                    <span className="text-slate-400 font-mono">{totalVotes} Học sinh đã nộp</span>
                  </div>
                  <h3 className="text-sm font-semibold text-white">
                    Trong hình lập phương ABCD.A'B'C'D', góc giữa hai đường thẳng <strong>AC</strong> và <strong>A'D</strong> bằng bao nhiêu độ?
                  </h3>
                </div>

                {/* 4 Options Grid */}
                <div className="grid grid-cols-2 gap-3 my-2">
                  {[
                    { key: 'A', text: 'A. 60° (Đáp án đúng)', correct: true },
                    { key: 'B', text: 'B. 90°', correct: false },
                    { key: 'C', text: 'C. 45°', correct: false },
                    { key: 'D', text: 'D. 120° (Bẫy sai lầm góc tù)', correct: false }
                  ].map((opt) => {
                    const pct = Math.round((votes[opt.key] / totalVotes) * 100);
                    const isSelected = voted === opt.key;
                    return (
                      <div
                        key={opt.key}
                        onClick={() => handleVote(opt.key)}
                        className={`p-3 rounded-xl border cursor-pointer transition relative overflow-hidden ${
                          isSelected
                            ? 'border-cyan-400 bg-slate-900 shadow-lg shadow-cyan-950/40'
                            : 'border-slate-800 bg-slate-900/60 hover:bg-slate-800/80'
                        }`}
                      >
                        <div className="flex justify-between items-center text-xs font-semibold mb-1 relative z-10">
                          <span className={opt.correct && voted ? 'text-emerald-400 flex items-center gap-1' : 'text-slate-200'}>
                            {opt.text}
                            {opt.correct && voted && <CheckCircle2 size={13} />}
                          </span>
                          <span className="font-mono text-cyan-400">{pct}%</span>
                        </div>
                        {/* Progress Bar Track */}
                        <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden relative z-10">
                          <div
                            className={`h-full transition-all duration-500 ${
                              opt.correct ? 'bg-emerald-500' : 'bg-slate-500'
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Collapsible Solution */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
                  <button
                    onClick={() => setShowSolution(!showSolution)}
                    className="w-full px-3 py-2 text-left text-xs font-semibold text-cyan-400 flex justify-between items-center hover:bg-slate-800/50"
                  >
                    <span>💡 Hướng dẫn giải chi tiết & Phân tích lỗi sai:</span>
                    {showSolution ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>
                  {showSolution && (
                    <div className="p-3 text-[11px] text-slate-300 border-t border-slate-800 leading-relaxed space-y-1 bg-slate-950/40">
                      <p>• Vì ABCD và A'B'C'D' là hình vuông nên AC // A'C'.</p>
                      <p>• Do đó: Góc giữa AC và A'D chính bằng <strong>góc giữa A'C' và A'D</strong>, tức góc C'A'D.</p>
                      <p>• Xét tam giác A'C'D: Ta có A'C' = a√2, A'D = a√2, C'D = a√2 ⇒ Tam giác A'C'D đều ⇒ góc C'A'D = <strong>60°</strong>.</p>
                      <p className="text-amber-400">⚠️ Bẫy sai lầm: Nhiều học sinh tính góc A'DC' = 120°, nhưng theo quy ước SGK góc giữa 2 đường thẳng luôn ≤ 90°.</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Slide Bottom Floating Strip */}
          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <div className="flex items-center gap-1 overflow-x-auto max-w-[70%]">
              {['1. Khởi động', '2. Đường chéo AC\'', '3. Vuông góc AH', '4. Thiết diện', '5. Live Quiz'].map((label, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentSlide(idx)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition ${
                    currentSlide === idx
                      ? 'bg-cyan-600 text-white font-semibold shadow-sm'
                      : 'bg-slate-900 text-slate-400 hover:text-white'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1.5 shrink-0">
              <button
                disabled={currentSlide === 0}
                onClick={() => setCurrentSlide(prev => Math.max(0, prev - 1))}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-cyan-300 disabled:opacity-40 border border-slate-800 flex items-center gap-1 text-[11px]"
              >
                <ChevronLeft size={13} /> Trước
              </button>
              <button
                disabled={currentSlide === 4}
                onClick={() => setCurrentSlide(prev => Math.min(4, prev + 1))}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-cyan-300 disabled:opacity-40 border border-slate-800 flex items-center gap-1 text-[11px]"
              >
                Sau <ChevronRight size={13} />
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
