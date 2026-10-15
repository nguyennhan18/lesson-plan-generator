import React, { useState } from 'react';
import { Presentation, Download, Plus, Trash2, Edit3, HelpCircle } from 'lucide-react';

export default function SlideEditorScreen() {
  const [selectedSlide, setSelectedSlide] = useState(1);
  const [title, setTitle] = useState('1. Đường Chéo AC\' & Góc Giữa Đường Thẳng Với Mặt Phẳng');
  const [bullets, setBullets] = useState(`Trong mặt phẳng đáy (ABCD): AC = √(AB² + BC²) = a√2.
Vì CC' ⊥ (ABCD) nên tam giác ACC' vuông tại C.
Áp dụng định lý Pytago trong tam giác ACC': AC' = a√3.`);
  const [latex, setLatex] = useState("AC' = \\sqrt{(a\\sqrt{2})^2 + a^2} = a\\sqrt{3}");
  const [teacherNote, setTeacherNote] = useState("Nhắc nhở học sinh áp dụng quy tắc 2 bước Pytago. Không nhầm lẫn giữa đường chéo sàn (a√2) và không gian (a√3).");

  const slides = [
    { id: 0, label: 'Slide 1: Khởi động', sub: 'Hình lập phương ABCD.A\'B\'C\'D\'' },
    { id: 1, label: 'Slide 2: Khái niệm', sub: 'Đường chéo AC\' = a√3' },
    { id: 2, label: 'Slide 3: Khoảng cách', sub: 'Đoạn vuông góc AH ⊥ B\'D\'' },
    { id: 3, label: 'Slide 4: Thiết diện', sub: 'Mặt phẳng (A\'BD)' },
    { id: 4, label: 'Slide 5: Live Quiz', sub: 'Góc giữa AC và A\'D' }
  ];

  const handleExportPPTX = () => {
    alert("Đang đóng gói và xuất file PowerPoint (.pptx) chuẩn 16:9 kèm hình ảnh 3D và ghi chú giảng dạy...");
  };

  return (
    <div className="flex-1 p-5 overflow-y-auto max-w-7xl mx-auto space-y-4">
      {/* Screen Title */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>🛠️</span> Xưởng Biên Tập Slide & Đồ Thị Toán Học
          </h2>
          <p className="text-xs text-slate-400">Biên tập chi tiết từng slide bài giảng, công thức KaTeX & Đồ thị hàm số</p>
        </div>
        <button
          onClick={handleExportPPTX}
          className="px-3.5 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-amber-950/40 transition"
        >
          <Download size={14} /> Xuất PowerPoint (.pptx)
        </button>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* Col 1: Slide Thumbnails */}
        <div className="col-span-12 lg:col-span-3 glass-panel p-3.5 rounded-2xl border-slate-800 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-xs font-bold text-white">📑 Danh Sách Slide</span>
            <button className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs flex items-center gap-1">
              <Plus size={13} /> Thêm
            </button>
          </div>

          <div className="space-y-2">
            {slides.map((s) => (
              <div
                key={s.id}
                onClick={() => setSelectedSlide(s.id)}
                className={`p-2.5 rounded-xl border cursor-pointer transition text-xs ${
                  selectedSlide === s.id
                    ? 'border-cyan-500 bg-slate-900 shadow-md shadow-cyan-950/30'
                    : 'border-slate-800/80 bg-slate-900/40 hover:bg-slate-800/60'
                }`}
              >
                <div className="font-semibold text-white">{s.label}</div>
                <div className="text-[11px] text-slate-400 truncate mt-0.5">{s.sub}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Col 2: Slide WYSIWYG Editor */}
        <div className="col-span-12 lg:col-span-5 glass-panel p-4 rounded-2xl border-slate-800 space-y-3.5 text-xs">
          <h3 className="font-bold text-white text-sm pb-2 border-b border-slate-800 flex items-center gap-2">
            <Edit3 size={15} className="text-cyan-400" /> Nội Dung Trình Chiếu Slide
          </h3>

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
            <label className="text-slate-400 block mb-1">Bố cục layout:</label>
            <select className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-white">
              <option value="two">2 Cột (Nội dung lý thuyết + Mô hình 3D bên phải)</option>
              <option value="quiz">Quiz Trắc Nghiệm 4 Phương Án</option>
              <option value="single">1 Cột Toàn Cảnh</option>
            </select>
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Danh sách ý gạch đầu dòng:</label>
            <textarea
              rows={4}
              value={bullets}
              onChange={(e) => setBullets(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white leading-relaxed focus:outline-none focus:border-cyan-500 font-mono text-[11px]"
            />
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Công thức Toán LaTeX trọng tâm:</label>
            <input
              type="text"
              value={latex}
              onChange={(e) => setLatex(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-cyan-300 font-mono"
            />
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Lời thoại riêng cho Giáo viên (Teacher Notes):</label>
            <textarea
              rows={2}
              value={teacherNote}
              onChange={(e) => setTeacherNote(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-300 text-[11px]"
            />
          </div>

          <button
            onClick={() => alert("Đã lưu các thay đổi vào Slide!")}
            className="w-full py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition"
          >
            💾 Lưu Thay Đổi Vào Slide
          </button>
        </div>

        {/* Col 3: Quiz Inspector & Distractor Analysis */}
        <div className="col-span-12 lg:col-span-4 glass-panel p-4 rounded-2xl border-slate-800 space-y-3 text-xs">
          <h3 className="font-bold text-white text-sm pb-2 border-b border-slate-800 flex items-center gap-1.5">
            <HelpCircle size={15} className="text-amber-400" /> Cấu Hình Quiz & Bẫy Sai Lầm
          </h3>

          <div>
            <label className="text-slate-400 block mb-1">Câu hỏi trắc nghiệm:</label>
            <input
              type="text"
              defaultValue="Góc giữa AC và A'D bằng bao nhiêu độ?"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white"
            />
          </div>

          <div className="space-y-2">
            <div>
              <label className="text-emerald-400 block mb-0.5 font-semibold">Phương án A (Đáp án đúng):</label>
              <input
                type="text"
                defaultValue="60° (Tam giác A'C'D đều)"
                className="w-full bg-slate-900 border border-emerald-600/60 rounded-lg p-2 text-white"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-0.5">Phương án B (Nhiễu):</label>
              <input
                type="text"
                defaultValue="90° (Nhầm quan hệ vuông góc)"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-0.5">Phương án C (Nhiễu):</label>
              <input
                type="text"
                defaultValue="45°"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-0.5">Phương án D (Nhiễu):</label>
              <input
                type="text"
                defaultValue="120° (Bẫy góc tù)"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white"
              />
            </div>
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Phân tích bẫy tâm lý học sinh:</label>
            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-amber-300/90 leading-relaxed">
              HS hay chọn 120° vì tính trực tiếp góc giữa 2 vectơ thay vì góc giữa 2 đường thẳng (luôn ≤ 90°).
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
