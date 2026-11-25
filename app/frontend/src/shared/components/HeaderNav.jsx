import React, { useState, useRef, useEffect } from 'react';
import { Box, Play, FileText, Wrench, BarChart2, Bot, Sliders, Maximize, Clock, Download, ChevronDown, Package, Sparkles, Layers } from 'lucide-react';

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
    { key: 'dashboard', label: '1. Khởi Tạo', icon: Sparkles },
    { key: 'outline', label: '2. Dàn Ý & Theme', icon: Layers },
    { key: 'presentation', label: '3. Trình Chiếu', icon: Play },
    { key: 'lesson-plan', label: 'Giáo Án 5512', icon: FileText },
    { key: 'slide-editor', label: 'Biên Tập Slide', icon: Wrench },
    { key: 'analytics', label: 'Phân Tích', icon: BarChart2 }
  ];

  return (
    <div className="w-full max-w-7xl mx-auto pt-2.5 pb-1 px-4 shrink-0 z-20">
      <header className="h-14 bg-[#f3f3f3] border border-[#e0e0e0] rounded-full px-3 sm:px-4 flex items-center justify-between">
        {/* Brand Logo with 30% Squircle App Icon */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-[30%] bg-[#141414] flex items-center justify-center text-white shrink-0">
            <Box size={18} />
          </div>
          <div className="hidden sm:block">
            <h1 className="text-xs font-bold text-[#141414] flex items-center gap-1.5 leading-tight">
              QUANTUM STUDIO
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#e0e0e0] text-[#141414] font-medium">
                Bản soạn của giáo viên
              </span>
            </h1>
            <p className="text-[11px] text-[#707070] leading-tight">Chuẩn CV 5512 • Trợ Giảng AI Co-pilot</p>
          </div>
        </div>

        {/* 4 Navigation Tabs - Segmented Stadium Track */}
        <nav className="flex items-center gap-1 bg-[#ffffff] p-1 rounded-full border border-[#e0e0e0] text-xs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeScreen === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveScreen(tab.key)}
                className={`px-3 py-1.5 rounded-full font-semibold transition flex items-center gap-1.5 cursor-pointer ${
                  isActive
                    ? 'bg-[#141414] text-white shadow-none'
                    : 'text-[#707070] hover:text-[#141414] hover:bg-[#f3f3f3]'
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
          {/* Primary CTA Button: Bắt đầu Tiết học */}
          <button
            onClick={onStartPresentation}
            className="px-4 py-2 rounded-full bg-[#141414] hover:bg-[#262626] text-white font-semibold text-xs flex items-center gap-1.5 transition active:scale-95 cursor-pointer shadow-none"
            title="Bắt đầu Tiết học: Trình chiếu Toàn màn hình (F5)"
          >
            <Play size={13} className="fill-white" />
            <span className="font-semibold">Bắt đầu Tiết học</span>
            <span className="hidden xl:inline text-[10px] px-1.5 py-0.2 rounded-full bg-[#262626] text-[#adadad] font-mono">
              F5
            </span>
          </button>


          {/* Export Dropdown Pill */}
          <div className="relative" ref={exportMenuRef}>
            <button
              onClick={() => setIsExportOpen(!isExportOpen)}
              className="px-3 py-1.5 rounded-full bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] border border-[#e0e0e0] text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
              title="Tải Giáo án Word, Bài giảng PowerPoint hoặc Trọn bộ ZIP"
            >
              <Download size={13} className="text-[#141414]" />
              <span className="hidden sm:inline">Tải Về</span>
              <ChevronDown size={12} className={`transition-transform duration-200 ${isExportOpen ? 'rotate-180' : ''}`} />
            </button>

            {isExportOpen && (
              <div className="absolute right-0 mt-2 w-72 bg-[#ffffff] border border-[#e0e0e0] rounded-2xl shadow-xl p-2 z-50 space-y-1">
                <div className="px-3 py-1.5 border-b border-[#f0f0f0] text-[11px] font-bold text-[#707070] uppercase tracking-wider flex items-center justify-between">
                  <span>Xuất Bản Tài Liệu</span>
                  <span className="text-[10px] text-[#0066ff] font-semibold">Dual-Mode 5512</span>
                </div>
                <button
                  onClick={() => {
                    setIsExportOpen(false);
                    onExportDocx?.();
                  }}
                  className="w-full text-left px-3 py-2 rounded-xl hover:bg-[#f3f3f3] flex items-start gap-2.5 transition text-xs group cursor-pointer"
                >
                  <div className="p-1.5 rounded-lg bg-[#f0f0f0] text-[#141414] shrink-0 mt-0.5">
                    <FileText size={15} />
                  </div>
                  <div>
                    <div className="font-semibold text-[#141414]">Tải Giáo Án Word (.docx)</div>
                    <div className="text-[11px] text-[#707070] leading-tight">Chuẩn CV 5512, tích hợp OMML & câu hỏi củng cố</div>
                  </div>
                </button>

                <button
                  onClick={() => {
                    setIsExportOpen(false);
                    onExportPptx?.();
                  }}
                  className="w-full text-left px-3 py-2 rounded-xl hover:bg-[#f3f3f3] flex items-start gap-2.5 transition text-xs group cursor-pointer"
                >
                  <div className="p-1.5 rounded-lg bg-[#f0f0f0] text-[#141414] shrink-0 mt-0.5">
                    <Play size={15} className="fill-[#141414]" />
                  </div>
                  <div>
                    <div className="font-semibold text-[#141414]">Tải Bài Giảng PowerPoint (.pptx)</div>
                    <div className="text-[11px] text-[#707070] leading-tight">Slide 16:9, ảnh 3D WebGL, đồ thị & Speaker notes</div>
                  </div>
                </button>

                <button
                  onClick={() => {
                    setIsExportOpen(false);
                    onExportDualPackage?.();
                  }}
                  className="w-full text-left px-3 py-2 rounded-xl bg-[#f3f3f3] hover:bg-[#e0e0e0] flex items-start gap-2.5 transition text-xs group cursor-pointer"
                >
                  <div className="p-1.5 rounded-lg bg-[#141414] text-white shrink-0 mt-0.5">
                    <Package size={15} />
                  </div>
                  <div>
                    <div className="font-bold text-[#141414] flex items-center gap-1.5">
                      <span>Tải Trọn Bộ Dual-Pack (.zip)</span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-[#0066ff] text-white font-medium">Gói Kép</span>
                    </div>
                    <div className="text-[11px] text-[#707070] leading-tight">Đồng bộ kép: Word 5512 + PowerPoint + Hướng dẫn</div>
                  </div>
                </button>
              </div>
            )}
          </div>

          {/* Toggle Chat Copilot Pill */}
          <button
            onClick={() => setIsLeftOpen(!isLeftOpen)}
            className={`px-3 py-1.5 rounded-full border text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
              isLeftOpen
                ? 'bg-[#141414] text-white border-[#141414]'
                : 'bg-[#ffffff] text-[#141414] border-[#e0e0e0] hover:bg-[#f3f3f3]'
            }`}
            title="Bật/Tắt Chat Co-pilot (Phím C)"
          >
            <Bot size={14} />
            <span className="hidden sm:inline">Trợ Giảng (C)</span>
          </button>

          {/* Toggle 3D / Graph Tools Pill */}
          <button
            onClick={() => setIsRightOpen(!isRightOpen)}
            className={`px-3 py-1.5 rounded-full border text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
              isRightOpen
                ? 'bg-[#141414] text-white border-[#141414]'
                : 'bg-[#ffffff] text-[#141414] border-[#e0e0e0] hover:bg-[#f3f3f3]'
            }`}
            title="Bật/Tắt Công Cụ 3D/Đồ Thị (Phím T)"
          >
            <Sliders size={14} />
            <span className="hidden sm:inline">Công Cụ (T)</span>
          </button>

          {/* Fullscreen Button Pill */}
          <button
            onClick={onToggleFullscreen}
            className="p-2 rounded-full bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] border border-[#e0e0e0] transition cursor-pointer"
            title="Toàn màn hình (F5 hoặc F)"
          >
            <Maximize size={15} />
          </button>
        </div>
      </header>
    </div>
  );
}
