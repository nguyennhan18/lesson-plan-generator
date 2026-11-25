import React, { useState } from 'react';
import {
  Sparkles,
  ArrowLeft,
  Play,
  Plus,
  Trash2,
  ChevronUp,
  ChevronDown,
  Layers,
  Palette,
  Box,
  Compass,
  CheckCircle2,
  HelpCircle,
  Activity,
  Edit3,
  Sliders,
  FileSpreadsheet
} from 'lucide-react';

/**
 * Trạm 2: Duyệt Dàn Ý & Bảng Màu (OutlineWorkspace.jsx)
 * Tuân thủ FRONTEND_ARCHITECTURE.md (Mục 3.2 & Mục 7 - Outline & Theme Workspace)
 * - Hiển thị từng Slide dưới dạng Thẻ Dàn Ý tương tác (Outline Cards)
 * - Cho phép giáo viên chỉnh sửa tiêu đề, từng gạch đầu dòng, thêm/bớt slide, sắp xếp thứ tự
 * - Bộ chọn Theme bảng màu sư phạm (ThemeSettings)
 * - Phân tích cơ cấu hoạt động sư phạm (Khởi động, Khái niệm, Luyện tập, Vận dụng, 3D, Quiz)
 * - Nút bấm CTA "Sinh Bài Giảng & Slide Chi Tiết" (Generate Presentation)
 */
export default function OutlineWorkspace({
  outline,
  setOutline,
  onBackToDashboard,
  onGenerateFullPresentation,
  isGenerating = false,
  selectedTheme = 'gallery_monochrome',
  setSelectedTheme
}) {
  const slides = outline?.outline_slides || [];

  // Danh sách Theme bảng màu chuẩn Mobbin Design
  const themes = [
    {
      id: 'gallery_monochrome',
      name: 'Gallery Monochrome',
      desc: 'Mực đen tối giản, nền trắng thuần khiết, viền mỏng 1px',
      primary: '#141414',
      bg: '#ffffff',
      accent: '#0066ff'
    },
    {
      id: 'cobalt_academic',
      name: 'Cobalt Academic',
      desc: 'Xanh coban học thuật, phong thái sư phạm đại học',
      primary: '#0f172a',
      bg: '#f8fafc',
      accent: '#2563eb'
    },
    {
      id: 'forest_emerald',
      name: 'Forest Emerald',
      desc: 'Xanh lục bảo dịu mắt, phù hợp lớp học đường dài',
      primary: '#064e3b',
      bg: '#f0fdf4',
      accent: '#059669'
    },
    {
      id: 'crimson_scholar',
      name: 'Crimson Scholar',
      desc: 'Đỏ mận bác học, trang trọng và nhiệt huyết',
      primary: '#881337',
      bg: '#fff1f2',
      accent: '#e11d48'
    },
    {
      id: 'warm_amber',
      name: 'Warm Amber',
      desc: 'Hổ phách ấm áp, thân thiện và giàu năng lượng',
      primary: '#292524',
      bg: '#fffbeb',
      accent: '#d97706'
    }
  ];

  const activityOptions = [
    'Khởi động',
    'Hình thành kiến thức',
    'Luyện tập & Trắc nghiệm',
    'Vận dụng & Mở rộng',
    'Tổng kết & Dặn dò'
  ];

  const visualOptions = [
    'Concept Highlight',
    '3D Geometry',
    '2D Function Plot',
    'Interactive Quiz',
    'Text & Formula',
    'Title & Overview'
  ];

  // Thao tác chỉnh sửa từng slide trong dàn ý
  const handleUpdateSlideTitle = (idx, newTitle) => {
    const updated = [...slides];
    updated[idx] = { ...updated[idx], title: newTitle };
    setOutline({ ...outline, outline_slides: updated });
  };

  const handleUpdateSlideActivity = (idx, newAct) => {
    const updated = [...slides];
    updated[idx] = { ...updated[idx], activity_type: newAct };
    setOutline({ ...outline, outline_slides: updated });
  };

  const handleUpdateSlideVisual = (idx, newVis) => {
    const updated = [...slides];
    const is3d = newVis === '3D Geometry';
    updated[idx] = {
      ...updated[idx],
      visual_type: newVis,
      has_3d: is3d,
      polyhedron_type: is3d ? (updated[idx].polyhedron_type || null) : null
    };
    setOutline({ ...outline, outline_slides: updated });
  };

  const handleUpdateBullet = (slideIdx, bulletIdx, text) => {
    const updated = [...slides];
    const targetSlide = { ...updated[slideIdx] };
    const bullets = [...(targetSlide.bullet_points || targetSlide.key_points || [])];
    bullets[bulletIdx] = text;
    targetSlide.bullet_points = bullets;
    targetSlide.key_points = bullets;
    updated[slideIdx] = targetSlide;
    setOutline({ ...outline, outline_slides: updated });
  };

  const handleAddBullet = (slideIdx) => {
    const updated = [...slides];
    const targetSlide = { ...updated[slideIdx] };
    const bullets = [...(targetSlide.bullet_points || targetSlide.key_points || []), ''];
    targetSlide.bullet_points = bullets;
    targetSlide.key_points = bullets;
    updated[slideIdx] = targetSlide;
    setOutline({ ...outline, outline_slides: updated });
  };

  const handleDeleteBullet = (slideIdx, bulletIdx) => {
    const updated = [...slides];
    const targetSlide = { ...updated[slideIdx] };
    const bullets = (targetSlide.bullet_points || targetSlide.key_points || []).filter((_, i) => i !== bulletIdx);
    targetSlide.bullet_points = bullets;
    targetSlide.key_points = bullets;
    updated[slideIdx] = targetSlide;
    setOutline({ ...outline, outline_slides: updated });
  };

  const handleMoveSlide = (idx, direction) => {
    const targetIdx = idx + direction;
    if (targetIdx < 0 || targetIdx >= slides.length) return;
    const updated = [...slides];
    const temp = updated[idx];
    updated[idx] = updated[targetIdx];
    updated[targetIdx] = temp;
    // Cập nhật lại số thứ tự
    updated.forEach((s, i) => {
      s.slide_index = i + 1;
    });
    setOutline({ ...outline, outline_slides: updated });
  };

  const handleDeleteSlide = (idx) => {
    if (slides.length <= 3) {
      alert('Dàn ý bài giảng cần tối thiểu 3 slide!');
      return;
    }
    const updated = slides.filter((_, i) => i !== idx).map((s, i) => ({ ...s, slide_index: i + 1 }));
    setOutline({ ...outline, outline_slides: updated, num_slides: updated.length });
  };

  const handleAddNewSlide = () => {
    const newIdx = slides.length + 1;
    const newSlide = {
      id: `outline-slide-${newIdx}`,
      slide_index: newIdx,
      title: `Trang ${newIdx}: Nội dung thảo luận & bài tập`,
      activity_type: 'Luyện tập & Trắc nghiệm',
      visual_type: 'Concept Highlight',
      bullet_points: [
        'Ý chính 1: Nêu câu hỏi hoặc giả thiết bài toán.',
        'Ý chính 2: Hướng dẫn các bước phân tích và suy luận.'
      ],
      math_focus: '',
      has_3d: false
    };
    const updated = [...slides, newSlide];
    setOutline({ ...outline, outline_slides: updated, num_slides: updated.length });
  };

  // Thống kê phân bổ sư phạm của Dàn ý
  const count3D = slides.filter((s) => s.has_3d || s.visual_type === '3D Geometry').length;
  const countQuiz = slides.filter((s) => s.visual_type === 'Interactive Quiz' || s.activity_type?.includes('Trắc nghiệm')).length;
  const countPlots = slides.filter((s) => s.visual_type === '2D Function Plot').length;

  return (
    <div className="w-full h-full overflow-y-auto bg-[#ffffff] text-[#141414] p-4 sm:p-6 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6 pb-12">
        {/* 1. Header Toolbar Trạm 2 */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#e0e0e0]">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onBackToDashboard}
              className="p-2 rounded-full border border-[#e0e0e0] bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] transition cursor-pointer"
              title="Quay lại Dashboard sửa cấu hình đề tài"
            >
              <ArrowLeft size={16} />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full bg-[#f3f3f3] border border-[#e0e0e0] text-[10px] font-mono font-semibold text-[#141414]">
                  Trạm 2: Duyệt Dàn Ý (Outline)
                </span>
                <span className="text-[11px] text-[#707070]">
                  {slides.length} slide bài giảng
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-[#141414] leading-tight">
                {outline?.title || 'Dàn Ý Bài Thuyết Trình Sư Phạm'}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={handleAddNewSlide}
              className="px-3.5 py-2 rounded-full border border-[#e0e0e0] bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
            >
              <Plus size={14} />
              <span>Thêm Slide</span>
            </button>

            <button
              type="button"
              onClick={onGenerateFullPresentation}
              disabled={isGenerating || slides.length === 0}
              className="px-5 py-2 rounded-full bg-[#141414] hover:bg-[#262626] disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-2 transition active:scale-95 cursor-pointer shadow-none"
            >
              {isGenerating ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Đang sinh Giáo án 5512 & Slide...</span>
                </>
              ) : (
                <>
                  <Sparkles size={14} />
                  <span>Sinh Bài Giảng & Slide Chi Tiết</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 2. Bố cục 2 Cột: Danh sách Thẻ Dàn Ý (Trái) & Theme Settings (Phải) */}
        <div className="grid grid-cols-12 gap-6">
          {/* CỘT TRÁI (8 / 12): Danh sách các thẻ Slide Dàn Ý */}
          <div className="col-span-12 lg:col-span-8 space-y-4">
            <div className="flex items-center justify-between text-xs text-[#707070] font-medium">
              <span>Chỉnh sửa trực tiếp tiêu đề và các ý chính gạch đầu dòng:</span>
              <span>Dàn ý chuẩn Công văn 5512</span>
            </div>

            {slides.length === 0 ? (
              <div className="p-8 rounded-[24px] bg-[#f8f8f8] border border-[#e0e0e0] text-center space-y-4">
                <Layers size={36} className="mx-auto text-[#707070]" />
                <h3 className="text-base font-bold text-[#141414]">Chưa có dữ liệu dàn ý</h3>
                <p className="text-xs text-[#707070] max-w-md mx-auto">
                  Bạn có thể quay lại Trạm 1 để nhập chủ đề bài giảng hoặc bấm nút bên dưới để tạo slide mới.
                </p>
                <div className="flex justify-center gap-3">
                  <button
                    onClick={onBackToDashboard}
                    className="px-4 py-2 rounded-full border border-[#e0e0e0] bg-[#ffffff] hover:bg-[#f3f3f3] text-xs font-semibold text-[#141414] cursor-pointer"
                  >
                    Về Trạm 1: Khởi Tạo
                  </button>
                  <button
                    onClick={handleAddNewSlide}
                    className="px-4 py-2 rounded-full bg-[#141414] text-white hover:bg-[#262626] text-xs font-semibold cursor-pointer"
                  >
                    + Thêm Slide Mới
                  </button>
                </div>
              </div>
            ) : (
              slides.map((slide, idx) => (
                <div
                  key={slide.id || idx}
                  className="p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-4 transition hover:border-[#141414]/40"
                >
                {/* Dòng 1: Badge STT + Bộ chọn Hoạt động + Bộ chọn Trực quan + Nút Điều hướng */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#e0e0e0]">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="w-7 h-7 rounded-full bg-[#141414] text-white font-mono text-xs font-bold flex items-center justify-center shrink-0">
                      {idx + 1}
                    </span>

                    {/* Bộ chọn Hoạt động sư phạm */}
                    <select
                      value={slide.activity_type}
                      onChange={(e) => handleUpdateSlideActivity(idx, e.target.value)}
                      className="px-3 py-1 rounded-full bg-[#f3f3f3] border border-[#e0e0e0] text-xs font-semibold text-[#141414] outline-none cursor-pointer"
                    >
                      {activityOptions.map((act) => (
                        <option key={act} value={act}>
                          {act}
                        </option>
                      ))}
                    </select>

                    {/* Bộ chọn Visual Engine */}
                    <select
                      value={slide.visual_type}
                      onChange={(e) => handleUpdateSlideVisual(idx, e.target.value)}
                      className="px-3 py-1 rounded-full bg-[#f3f3f3] border border-[#e0e0e0] text-xs font-semibold text-[#0066ff] outline-none cursor-pointer font-mono"
                    >
                      {visualOptions.map((vis) => (
                        <option key={vis} value={vis}>
                          {vis}
                        </option>
                      ))}
                    </select>

                    {slide.has_3d && (
                      <span className="px-2.5 py-0.5 rounded-full bg-[#141414] text-white text-[10px] font-mono font-semibold flex items-center gap-1">
                        <Box size={10} /> 3D WebGL
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => handleMoveSlide(idx, -1)}
                      disabled={idx === 0}
                      className="p-1.5 rounded-full text-[#707070] hover:text-[#141414] hover:bg-[#f3f3f3] disabled:opacity-30 disabled:pointer-events-none transition cursor-pointer"
                      title="Chuyển slide lên trên"
                    >
                      <ChevronUp size={15} />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleMoveSlide(idx, 1)}
                      disabled={idx === slides.length - 1}
                      className="p-1.5 rounded-full text-[#707070] hover:text-[#141414] hover:bg-[#f3f3f3] disabled:opacity-30 disabled:pointer-events-none transition cursor-pointer"
                      title="Chuyển slide xuống dưới"
                    >
                      <ChevronDown size={15} />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteSlide(idx)}
                      className="p-1.5 rounded-full text-[#707070] hover:text-[#ef4444] hover:bg-rose-50 transition cursor-pointer"
                      title="Xóa slide này khỏi dàn ý"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>

                {/* Dòng 2: Ô sửa Tiêu đề Slide */}
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-[#707070]">Tiêu đề slide:</label>
                  <input
                    type="text"
                    value={slide.title}
                    onChange={(e) => handleUpdateSlideTitle(idx, e.target.value)}
                    className="w-full bg-[#f0f0f0] border-none rounded-2xl px-3.5 py-2 text-sm font-bold text-[#141414] outline-none focus:ring-2 focus:ring-[#141414] transition"
                  />
                </div>

                {/* Dòng 3: Danh sách các gạch đầu dòng (Bullet Points) */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[11px] text-[#707070] font-medium">
                    <span>Nội dung ý chính (Bullet Points):</span>
                    <button
                      type="button"
                      onClick={() => handleAddBullet(idx)}
                      className="text-[#0066ff] hover:underline flex items-center gap-1 font-semibold cursor-pointer"
                    >
                      <Plus size={11} /> Thêm ý chính
                    </button>
                  </div>

                  <div className="space-y-1.5">
                    {(slide.bullet_points || slide.key_points || []).map((bp, bpIdx) => (
                      <div key={bpIdx} className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#141414] shrink-0"></span>
                        <input
                          type="text"
                          value={bp}
                          onChange={(e) => handleUpdateBullet(idx, bpIdx, e.target.value)}
                          className="flex-1 bg-[#f0f0f0] border-none rounded-xl px-3 py-1.5 text-xs text-[#141414] outline-none focus:ring-1 focus:ring-[#141414] transition"
                        />
                        <button
                          type="button"
                          onClick={() => handleDeleteBullet(idx, bpIdx)}
                          className="text-[#adadad] hover:text-[#ef4444] p-1 transition cursor-pointer"
                          title="Xóa ý này"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )))}

            {/* Nút thêm slide ở cuối */}
            <button
              type="button"
              onClick={handleAddNewSlide}
              className="w-full py-3.5 rounded-[24px] border border-dashed border-[#e0e0e0] hover:border-[#141414] bg-[#ffffff] hover:bg-[#f3f3f3] text-xs font-semibold text-[#141414] flex items-center justify-center gap-2 transition cursor-pointer"
            >
              <Plus size={15} />
              <span>Thêm Trang Slide Mới Vào Dàn Ý</span>
            </button>
          </div>

          {/* CỘT PHẢI (4 / 12): Theme Settings & Thống kê sư phạm */}
          <div className="col-span-12 lg:col-span-4 space-y-5">
            {/* 1. Theme Settings (Chọn Bảng Màu) */}
            <div className="p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b border-[#e0e0e0]">
                <Palette size={16} className="text-[#141414]" />
                <h3 className="text-sm font-bold text-[#141414]">Bộ Bảng Màu (Theme Settings)</h3>
              </div>

              <div className="space-y-2.5">
                {themes.map((th) => {
                  const isCur = selectedTheme === th.id;
                  return (
                    <div
                      key={th.id}
                      onClick={() => setSelectedTheme?.(th.id)}
                      className={`p-3 rounded-2xl border transition cursor-pointer flex items-center justify-between gap-3 ${
                        isCur
                          ? 'bg-[#f3f3f3] border-[#141414] ring-1 ring-[#141414]'
                          : 'bg-[#ffffff] border-[#e0e0e0] hover:bg-[#f3f3f3]'
                      }`}
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-[#141414]">{th.name}</span>
                          {isCur && <CheckCircle2 size={13} className="text-[#0066ff]" />}
                        </div>
                        <p className="text-[10px] text-[#707070] leading-tight">{th.desc}</p>
                      </div>

                      {/* Swatch màu */}
                      <div className="flex items-center gap-1 shrink-0">
                        <span
                          className="w-4 h-4 rounded-full border border-black/10"
                          style={{ backgroundColor: th.primary }}
                        />
                        <span
                          className="w-4 h-4 rounded-full border border-black/10"
                          style={{ backgroundColor: th.accent }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 2. Thống kê phân bổ sư phạm */}
            <div className="p-5 rounded-[24px] bg-[#f3f3f3] border border-[#e0e0e0] space-y-3.5">
              <div className="flex items-center gap-2 pb-2 border-b border-[#e0e0e0]">
                <Activity size={16} className="text-[#141414]" />
                <h3 className="text-sm font-bold text-[#141414]">Cơ Cấu Sư Phạm Bài Giảng</h3>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[#707070]">Tổng số slide:</span>
                  <span className="font-bold font-mono text-[#141414]">{slides.length} slide</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#707070]">Slide 3D không gian:</span>
                  <span className="font-bold font-mono text-[#141414]">{count3D} slide</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#707070]">Đồ thị hàm số 2D:</span>
                  <span className="font-bold font-mono text-[#141414]">{countPlots} slide</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#707070]">Trắc nghiệm & Live Poll:</span>
                  <span className="font-bold font-mono text-[#141414]">{countQuiz} slide</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#707070]">Tỷ lệ khung hình:</span>
                  <span className="font-semibold text-[#141414]">16:9 Widescreen</span>
                </div>
              </div>
            </div>

            {/* 3. Nút tiến trình tạo bài giảng */}
            <div className="p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-3">
              <h4 className="text-xs font-bold text-[#141414] uppercase tracking-wider">
                Bước tiếp theo:
              </h4>
              <p className="text-xs text-[#707070] leading-relaxed">
                Sau khi duyệt dàn ý, AI sẽ thiết kế chi tiết từng slide bài giảng, chèn công thức Toán KaTeX,
                tích hợp mô hình 3D và đồng bộ Kế hoạch bài dạy 5512.
              </p>
              <button
                type="button"
                onClick={onGenerateFullPresentation}
                disabled={isGenerating || slides.length === 0}
                className="w-full py-3 rounded-full bg-[#141414] hover:bg-[#262626] disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center gap-2 transition active:scale-95 cursor-pointer shadow-none"
              >
                <Sparkles size={14} />
                <span>Sinh Bài Giảng & Slide Chi Tiết</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
