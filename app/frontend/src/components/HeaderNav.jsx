import React from 'react';
import { Box, Play, FileText, Wrench, BarChart2, Bot, Sliders, Maximize, Clock } from 'lucide-react';

export default function HeaderNav({
  activeScreen,
  setActiveScreen,
  isLeftOpen,
  setIsLeftOpen,
  isRightOpen,
  setIsRightOpen,
  onToggleFullscreen
}) {
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
        {/* Timer */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-cyan-400 font-mono text-xs">
          <Clock size={13} className="text-amber-400 animate-pulse" />
          <span>45:20</span>
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
