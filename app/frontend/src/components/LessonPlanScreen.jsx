import React, { useState } from 'react';
import { FileText, Download, Sparkles, UploadCloud, CheckCircle } from 'lucide-react';

export default function LessonPlanScreen() {
  const [topic, setTopic] = useState('Hình lập phương & Quan hệ vuông góc trong không gian');
  const [subject, setSubject] = useState('Toán học');
  const [grade, setGrade] = useState('11');
  const [proficiency, setProficiency] = useState('standard');
  const [isGenerating, setIsGenerating] = useState(false);
  const [outcome, setOutcome] = useState('Học sinh xác định được góc giữa đường thẳng và mặt phẳng, tính được độ dài đường chéo hình lập phương AC = a√3 và dựng được thiết diện mặt phẳng.');

  const handleGenerate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
      alert("Đã sinh Kế hoạch bài dạy chuẩn 5512 thành công!");
    }, 1200);
  };

  const handleExportWord = () => {
    alert("Đang xuất file Word (.docx) chuẩn thể thức Công văn 5512...");
  };

  return (
    <div className="flex-1 p-5 overflow-y-auto max-w-7xl mx-auto space-y-4">
      {/* Screen Title */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>📝</span> Soạn Kế Hoạch Bài Dạy Chuẩn Công Văn 5512
          </h2>
          <p className="text-xs text-slate-400">Khởi tạo bài dạy tự động với cấu trúc 4 hoạt động & Phân loại học lực học sinh</p>
        </div>
        <button
          onClick={handleExportWord}
          className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-emerald-950/40 transition"
        >
          <Download size={14} /> Xuất File Word (.docx)
        </button>
      </div>

      <div className="grid grid-cols-12 gap-5">
        {/* Left Column: Form Setup */}
        <div className="col-span-12 lg:col-span-5 glass-panel p-4 rounded-2xl border-slate-800 space-y-3.5 text-xs">
          <h3 className="font-bold text-white text-sm pb-2 border-b border-slate-800 flex items-center gap-1.5">
            ⚙️ Thiết Lập Bài Dạy & Hồ Sơ Lớp
          </h3>

          <div>
            <label className="text-slate-400 block mb-1">Tên bài dạy / Chủ đề:</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-slate-400 block mb-1">Môn học:</label>
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-white"
              >
                <option value="Toán học">Toán học</option>
                <option value="Vật lý">Vật lý</option>
                <option value="Hóa học">Hóa học</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Khối lớp:</label>
              <select
                value={grade}
                onChange={(e) => setGrade(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-white"
              >
                <option value="11">Khối 11</option>
                <option value="12">Khối 12</option>
                <option value="10">Khối 10</option>
              </select>
            </div>
          </div>

          {/* Proficiency Pills */}
          <div>
            <label className="text-slate-400 block mb-1.5">Trình độ phân hóa học lực lớp:</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { key: 'basic', label: 'Cơ bản', color: 'border-emerald-500 text-emerald-300' },
                { key: 'standard', label: 'Chuẩn (SGK)', color: 'border-cyan-500 text-cyan-300' },
                { key: 'advanced', label: 'Nâng cao', color: 'border-purple-500 text-purple-300' }
              ].map((p) => (
                <button
                  key={p.key}
                  type="button"
                  onClick={() => setProficiency(p.key)}
                  className={`py-1.5 px-2 rounded-lg border text-center transition font-medium ${
                    proficiency === p.key
                      ? `bg-slate-800 ${p.color} shadow-sm`
                      : 'border-slate-800 text-slate-400 bg-slate-900/60 hover:text-white'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Yêu cầu cần đạt (Mục tiêu):</label>
            <textarea
              rows={3}
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white leading-relaxed focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Dropzone */}
          <div>
            <label className="text-slate-400 block mb-1">Tải lên Bảng điểm Excel / CSV (Tự động tính Z-Score):</label>
            <div className="p-4 rounded-xl border border-dashed border-cyan-800/80 bg-slate-950/60 hover:bg-slate-900/60 cursor-pointer text-center space-y-1 transition">
              <UploadCloud size={24} className="mx-auto text-cyan-400" />
              <div className="font-semibold text-white text-[11px]">Kéo thả file bảng điểm (.xlsx, .csv) vào đây</div>
              <div className="text-[10px] text-slate-400">Tự động phân nhóm lớp qua độ lệch chuẩn Gauss</div>
            </div>
          </div>

          <button
            type="button"
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-semibold flex items-center justify-center gap-2 shadow-lg shadow-cyan-950/30 transition"
          >
            <Sparkles size={16} />
            {isGenerating ? 'Đang gọi Gemini AI sinh giáo án...' : '🚀 Sinh Kế Hoạch Bài Dạy 5512 Bằng AI'}
          </button>
        </div>

        {/* Right Column: 5512 Preview */}
        <div className="col-span-12 lg:col-span-7 glass-panel p-5 rounded-2xl border-slate-800 space-y-4 text-xs leading-relaxed">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="font-bold text-white text-sm flex items-center gap-2">
              <FileText size={16} className="text-cyan-400" /> Kế Hoạch Bài Dạy Đã Kiểm Định (CV 5512)
            </h3>
            <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[11px] flex items-center gap-1">
              <CheckCircle size={12} /> Hợp chuẩn 100%
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-800/60 space-y-1">
            <strong className="text-white text-sm block">BÀI DẠY: HÌNH LẬP PHƯƠNG & QUAN HỆ VUÔNG GÓC</strong>
            <p className="text-slate-400 text-[11px]">Môn: Toán học | Khối 11 | Thời lượng: 1 tiết (45 phút) | Trình độ: Chuẩn (Standard)</p>
          </div>

          <div className="space-y-1.5">
            <strong className="text-cyan-400 block font-semibold text-xs uppercase tracking-wide">I. MỤC TIÊU BÀI DẠY</strong>
            <ul className="list-disc pl-4 text-slate-300 space-y-1">
              <li><strong>Kiến thức:</strong> Hiểu định nghĩa hình lập phương đều, công thức đường chéo AC' = a√3, khoảng cách từ điểm đến đường thẳng.</li>
              <li><strong>Năng lực:</strong> Tư duy hình học không gian 3 chiều, mô hình hóa toán học đời sống.</li>
              <li><strong>Phẩm chất:</strong> Cẩn thận, chính xác, tư duy logic phản biện.</li>
            </ul>
          </div>

          <div className="space-y-2 pt-2 border-t border-slate-800">
            <strong className="text-amber-400 block font-semibold text-xs uppercase tracking-wide">II. TIẾN TRÌNH 4 HOẠT ĐỘNG DẠY HỌC</strong>
            <div className="space-y-2">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <strong className="text-white block">Hoạt động 1: Mở đầu / Khởi động (7 phút)</strong>
                <span className="text-slate-400">GV chiếu mô hình 3D tương tác hình lập phương, đặt vấn đề tính đường chéo không gian.</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <strong className="text-white block">Hoạt động 2: Hình thành kiến thức mới (18 phút)</strong>
                <span className="text-slate-400">Chứng minh 2 bước Pytago: AC = a√2 ⇒ AC' = a√3; Dựng đường cao tam giác cân AH ⊥ B'D'.</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <strong className="text-white block">Hoạt động 3: Luyện tập (12 phút)</strong>
                <span className="text-slate-400">Xác định thiết diện cắt bởi mặt phẳng (A'BD) là tam giác đều và tính diện tích S = a²√3 / 2.</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <strong className="text-white block">Hoạt động 4: Vận dụng & Live Quiz (8 phút)</strong>
                <span className="text-slate-400">Học sinh làm trắc nghiệm trực tiếp trên bài giảng: Tính góc giữa hai đường thẳng chéo nhau $AC$ và $A'D$.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
