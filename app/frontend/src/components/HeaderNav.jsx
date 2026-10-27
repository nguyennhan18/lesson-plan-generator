import React, { useState, useRef, useEffect } from 'react';
import { Box, Play, FileText, Wrench, BarChart2, Bot, Sliders, Maximize, Clock, Download, ChevronDown, Package } from 'lucide-react';

export default function HeaderNav({
  activeScreen,
  setActiveScreen,
  isLeftOpen,
  setIsLeftOpen,
  isRightOpen,
  setIsRightOpen,
  onToggleFullscreen,
  onStartPresentation,
  isPresentationMode,
  onExportDocx,
  onExportPptx,
  onExportDualPackage
}) {
  const [isExportOpen, setIsExportOpen] = useState(false);
  const exportMenuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target)) {
        setIsExportOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const tabs = [
    { key: 'presentation', label: 'Trình Chiếu Giảng Dạy', icon: Play },
    { key: 'lesson-plan', label: 'Soạn Giáo Án 5512', icon: FileText },
    { key: 'slide-editor', label: 'Xưởng Biên Tập Slide', icon: Wrench },
    { key: 'analytics', label: 'Phân Tích Lớp Học', icon: BarChart2 }
  ];

  return (
    <header className="h-14 glass-panel border-b border-slate-800 px-4 flex items-center justify-between shrink-0 z-20">
      {/* Brand Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-cyan-950/40">
          <Box size={18} />
        </div>
        <div className="hidden sm:block">
          <h1 className="text-xs font-extrabold tracking-wider text-white flex items-center gap-1.5">
            QUANTUM STUDIO <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">React 19 & Three.js</span>
          </h1>
          <p className="text-[10px] text-slate-400">Chuẩn CV 5512 • Trợ Giảng AI</p>
        </div>
      </div>

      {/* 4 Navigation Tabs */}
      <nav className="flex items-center gap-1 bg-slate-950/70 p-1 rounded-xl border border-slate-800/80 text-xs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeScreen === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveScreen(tab.key)}
              className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white shadow-md shadow-cyan-950/40'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
              }`}
            >
              <Icon size={14} />
              <span className="hidden md:inline">{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Right Controls */}
      <div className="flex items-center gap-2 text-xs">
        {/* Task 15.1: Nút "Bắt đầu Tiết học" (Start Presentation Mode) */}
        <button
          onClick={onStartPresentation}
          className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-semibold text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-950/50 border border-emerald-400/40 transition active:scale-95 cursor-pointer"
          title="Bắt đầu Tiết học: Trình chiếu Toàn màn hình (F5)"
        >
          <Play size={13} className="fill-white" />
          <span className="font-bold tracking-wide">Bắt đầu Tiết học</span>
          <span className="hidden xl:inline text-[10px] px-1 py-0.2 rounded bg-emerald-900/80 border border-emerald-400/30 text-emerald-200 font-mono">F5</span>
        </button>

        {/* Timer */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-cyan-400 font-mono text-xs">
          <Clock size={13} className="text-amber-400 animate-pulse" />
          <span>45:20</span>
        </div>

        {/* Task 19.2: Cụm nút bấm Tải về / Xuất bản (Word, PowerPoint, Trọn bộ ZIP) */}
        <div className="relative" ref={exportMenuRef}>
          <button
            onClick={() => setIsExportOpen(!isExportOpen)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-cyan-300 hover:text-cyan-200 border border-cyan-800/70 text-xs font-semibold flex items-center gap-1.5 transition shadow-sm cursor-pointer"
            title="Tải Giáo án Word, Bài giảng PowerPoint hoặc Trọn bộ ZIP"
          >
            <Download size={13} className="text-cyan-400" />
            <span className="hidden sm:inline">Tải Về</span>
            <ChevronDown size={12} className={`transition-transform duration-200 ${isExportOpen ? 'rotate-180' : ''}`} />
          </button>

          {isExportOpen && (
            <div className="absolute right-0 mt-2 w-72 glass-panel bg-slate-950/95 border border-slate-700/80 rounded-xl shadow-2xl p-1.5 z-50 space-y-1 backdrop-blur-xl animate-in fade-in zoom-in-95 duration-150">
              <div className="px-2.5 py-1.5 border-b border-slate-800/80 text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                <span>Xuất Bản Tài Liệu</span>
                <span className="text-[10px] text-cyan-400 font-normal">Dual-Mode 5512</span>
              </div>
              <button
                onClick={() => {
                  setIsExportOpen(false);
                  onExportDocx?.();
                }}
                className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-blue-950/60 border border-transparent hover:border-blue-800/50 flex items-start gap-2.5 transition text-xs group cursor-pointer"
              >
                <div className="p-1.5 rounded-md bg-blue-500/20 text-blue-400 group-hover:bg-blue-500/30 shrink-0 mt-0.5">
                  <FileText size={15} />
                </div>
                <div>
                  <div className="font-semibold text-white group-hover:text-blue-300">Tải Giáo Án Word (.docx)</div>
                  <div className="text-[10px] text-slate-400 leading-tight">Chuẩn CV 5512, tích hợp OMML & câu hỏi củng cố</div>
                </div>
              </button>

              <button
                onClick={() => {
                  setIsExportOpen(false);
                  onExportPptx?.();
                }}
                className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-amber-950/60 border border-transparent hover:border-amber-800/50 flex items-start gap-2.5 transition text-xs group cursor-pointer"
              >
                <div className="p-1.5 rounded-md bg-amber-500/20 text-amber-400 group-hover:bg-amber-500/30 shrink-0 mt-0.5">
                  <Play size={15} className="fill-amber-400" />
                </div>
                <div>
                  <div className="font-semibold text-white group-hover:text-amber-300">Tải Bài Giảng PowerPoint (.pptx)</div>
                  <div className="text-[10px] text-slate-400 leading-tight">Slide 16:9, ảnh 3D WebGL, đồ thị & Speaker notes</div>
                </div>
              </button>

              <button
                onClick={() => {
                  setIsExportOpen(false);
                  onExportDualPackage?.();
                }}
                className="w-full text-left px-2.5 py-2 rounded-lg bg-gradient-to-r from-emerald-950/40 via-teal-950/40 to-cyan-950/40 hover:from-emerald-950/70 hover:to-cyan-950/70 border border-emerald-800/50 flex items-start gap-2.5 transition text-xs group cursor-pointer"
              >
                <div className="p-1.5 rounded-md bg-emerald-500/20 text-emerald-400 group-hover:bg-emerald-500/30 shrink-0 mt-0.5">
                  <Package size={15} />
                </div>
                <div>
                  <div className="font-bold text-emerald-300 flex items-center gap-1.5">
                    <span>Tải Trọn Bộ Dual-Pack (.zip)</span>
                    <span className="text-[9px] px-1 rounded bg-emerald-900 border border-emerald-500/40 text-emerald-200">Gói Kép</span>
                  </div>
                  <div className="text-[10px] text-slate-400 leading-tight">Đồng bộ kép: Word 5512 + PowerPoint + Hướng dẫn</div>
                </div>
              </button>
            </div>
          )}
        </div>

        {/* Toggle Chat Copilot */}
        <button
          onClick={() => setIsLeftOpen(!isLeftOpen)}
          className={`px-2.5 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1.5 transition ${
            isLeftOpen
              ? 'bg-cyan-950/80 text-cyan-300 border-cyan-700'
              : 'bg-slate-900 text-slate-400 hover:text-white border-slate-800'
          }`}
          title="Bật/Tắt Chat Co-pilot (Phím C)"
        >
          <Bot size={14} className={isLeftOpen ? 'text-cyan-400' : ''} />
          <span className="hidden sm:inline">Trợ Giảng (C)</span>
        </button>

        {/* Toggle 3D / Graph Tools */}
        <button
          onClick={() => setIsRightOpen(!isRightOpen)}
          className={`px-2.5 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1.5 transition ${
            isRightOpen
              ? 'bg-amber-950/80 text-amber-300 border-amber-700'
              : 'bg-slate-900 text-slate-400 hover:text-white border-slate-800'
          }`}
          title="Bật/Tắt Công Cụ 3D/Đồ Thị (Phím T)"
        >
          <Sliders size={14} className={isRightOpen ? 'text-amber-400' : ''} />
          <span className="hidden sm:inline">Công Cụ (T)</span>
        </button>

        {/* Fullscreen Button */}
        <button
          onClick={onToggleFullscreen}
          className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 transition"
          title="Toàn màn hình (F5 hoặc F)"
        >
          <Maximize size={15} />
        </button>
      </div>
    </header>
  );
}
