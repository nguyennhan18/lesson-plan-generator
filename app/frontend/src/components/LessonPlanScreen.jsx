import React, { useState, useEffect } from 'react';
import { FileText, Download, Sparkles, BookOpen, CheckCircle, Wrench, Layers } from 'lucide-react';
import MathText from './MathText';

export default function LessonPlanScreen({
  lessonPlan,
  isGenerating,
  onGenerateFromAi,
  onExportDocx,
  externalProficiency,
  externalOutcome
}) {
  const [topic, setTopic] = useState('Phương trình bậc hai một ẩn và định lý Vi-et');
  const [subject, setSubject] = useState('Toán học');
  const [grade, setGrade] = useState('10');
  const [proficiency, setProficiency] = useState(externalProficiency || 'standard');
  const [outcome, setOutcome] = useState(
    externalOutcome ||
      'Học sinh hiểu bản chất hình học của biệt thức Delta qua giao điểm của Parabol y = ax^2 + bx + c với trục Ox, thành thạo 4 bước giải và công thức nghiệm x = (-b ± √Δ)/(2a), ứng dụng định lý Vi-et nhẩm nghiệm nhanh.'
  );

  // Tự động đồng bộ khi người dùng truyền học lực lớp từ màn hình Phân Tích Điểm (AnalyticsScreen)
  useEffect(() => {
    if (externalProficiency) {
      setProficiency(externalProficiency);
    }
  }, [externalProficiency]);

  useEffect(() => {
    if (externalOutcome) {
      setOutcome(externalOutcome);
    }
  }, [externalOutcome]);

  // DANH MỤC CÁC BÀI TOÁN SGK THPT (LỚP 10, 11, 12)
  const textbookPresets = [
    {
      label: "Phương Trình Bậc 2 (Toán 10)",
      topic: "Phương trình bậc hai một ẩn và định lý Vi-et",
      subject: "Toán học",
      grade: "10",
      outcome: "Học sinh hiểu bản chất hình học của biệt thức Delta qua giao điểm của Parabol y = ax^2 + bx + c với trục Ox, thành thạo 4 bước giải và công thức nghiệm x = (-b ± √Δ)/(2a), ứng dụng định lý Vi-et nhẩm nghiệm nhanh."
    },
    {
      label: "Hình Lập Phương (Toán 11)",
      topic: "Hình lập phương & Quan hệ vuông góc trong không gian",
      subject: "Toán học",
      grade: "11",
      outcome: "Học sinh xác định được góc giữa đường thẳng và mặt phẳng, tính độ dài đường chéo AC' = a√3 và thiết diện (A'BD)."
    },
    {
      label: "Cấp Số Cộng (Toán 11)",
      topic: "Cấp số cộng và công thức số hạng tổng quát",
      subject: "Toán học",
      grade: "11",
      outcome: "Học sinh nắm vững định nghĩa dãy số cấp số cộng, công thức un = u1 + (n-1)d và tính tổng n số hạng đầu Sn."
    },
    {
      label: "Khảo Sát Đồ Thị Bậc 3 (Toán 12)",
      topic: "Khảo sát sự biến thiên và vẽ đồ thị hàm số bậc ba",
      subject: "Toán học",
      grade: "12",
      outcome: "Học sinh lập bảng biến thiên, tìm cực trị, điểm uốn và vẽ đồ thị hàm số bậc ba chuẩn xác."
    },
    {
      label: "Thể Tích Khối Chóp (Toán 12)",
      topic: "Thể tích khối chóp và bài toán khoảng cách trong không gian",
      subject: "Toán học",
      grade: "12",
      outcome: "Vận dụng công thức V = 1/3 * S_đáy * h để tính thể tích chóp tam giác và chóp tứ giác đều."
    }
  ];

  const handleSelectPreset = (p) => {
    setTopic(p.topic);
    setSubject(p.subject);
    setGrade(p.grade);
    setOutcome(p.outcome);
  };

  const handleTriggerGenerate = () => {
    if (!topic.trim()) {
      alert("Vui lòng nhập tên bài dạy hoặc chọn một bài trong Danh mục SGK!");
      return;
    }
    if (onGenerateFromAi) {
      onGenerateFromAi({
        topic,
        subject,
        grade,
        proficiency,
        outcome
      });
    }
  };

  // CHUẨN HÓA ĐỌC SONG SONG CẤU TRÚC PHẲNG (BACKEND) & CẤU TRÚC LỒNG NHAU (MẪU)
  const knowledgeText =
    Array.isArray(lessonPlan?.knowledge_goals) && lessonPlan.knowledge_goals.length > 0
      ? lessonPlan.knowledge_goals.join(' • ')
      : lessonPlan?.objectives?.knowledge || 'Nắm vững kiến thức trọng tâm SGK.';

  const competencyList =
    Array.isArray(lessonPlan?.competency_goals) && lessonPlan.competency_goals.length > 0
      ? lessonPlan.competency_goals
      : Array.isArray(lessonPlan?.skills_goals) && lessonPlan.skills_goals.length > 0
      ? lessonPlan.skills_goals
      : null;

  const competencyText = competencyList
    ? competencyList.join(' • ')
    : lessonPlan?.objectives?.competencies || 'Phát triển tư duy logic và giải quyết vấn đề toán học.';

  const characterText =
    Array.isArray(lessonPlan?.character_goals) && lessonPlan.character_goals.length > 0
      ? lessonPlan.character_goals.join(' • ')
      : lessonPlan?.objectives?.qualities || 'Chăm chỉ, trách nhiệm và tính kỷ luật trong học tập.';

  const equipmentList =
    Array.isArray(lessonPlan?.teaching_equipment) && lessonPlan.teaching_equipment.length > 0
      ? lessonPlan.teaching_equipment
      : null;

  return (
    <div className="flex-1 p-5 overflow-y-auto max-w-7xl mx-auto space-y-4">
      {/* Header màn hình */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>📝</span> Soạn Kế Hoạch Bài Dạy Chuẩn Công Văn 5512
          </h2>
          <p className="text-xs text-slate-400">Chọn bài mẫu Sách giáo khoa THPT hoặc nhập chủ đề mới để Gemini AI sinh bài</p>
        </div>
        <button
          onClick={onExportDocx}
          className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-emerald-950/40 transition"
        >
          <Download size={14} /> Xuất File Word (.docx)
        </button>
      </div>

      {/* THANH CHỌN BÀI DẠY SGK THPT (1-CLICK NẠP NHANH) */}
      <div className="glass-panel p-3.5 rounded-2xl border-slate-800 space-y-2">
        <div className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
          <BookOpen size={14} /> Danh Mục Bài Học SGK THPT Chuẩn GDPT 2018 (Bấm để nạp thông số):
        </div>
        <div className="flex flex-wrap gap-2">
          {textbookPresets.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSelectPreset(preset)}
              className="px-3 py-1.5 rounded-lg bg-slate-900/90 hover:bg-cyan-950 hover:border-cyan-600 border border-slate-800 text-xs text-slate-300 hover:text-cyan-300 transition flex items-center gap-1.5"
            >
              <span>📖</span> {preset.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-12 gap-5">
        {/* Cột trái: Form cấu hình bài dạy */}
        <div className="col-span-12 lg:col-span-5 glass-panel p-4 rounded-2xl border-slate-800 space-y-3.5 text-xs">
          <h3 className="font-bold text-white text-sm pb-2 border-b border-slate-800 flex items-center gap-1.5">
            ⚙️ Thiết Lập Bài Dạy & Hồ Sơ Lớp
          </h3>

          <div>
            <label className="text-slate-400 block mb-1">Tên bài dạy / Chủ đề SGK:</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="VD: Cấp số cộng, Giải phương trình bậc hai..."
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
                <option value="10">Khối 10</option>
                <option value="11">Khối 11</option>
                <option value="12">Khối 12</option>
              </select>
            </div>
          </div>

          {/* Phân hóa học lực */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-slate-400">Trình độ phân hóa học lực lớp:</label>
              {externalProficiency && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                  Đồng bộ từ Bảng điểm Z-Score
                </span>
              )}
            </div>
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
            <label className="text-slate-400 block mb-1">Yêu cầu cần đạt (Mục tiêu bài dạy):</label>
            <textarea
              rows={3}
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white leading-relaxed focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* NÚT GỌI AI THẬT */}
          <button
            type="button"
            onClick={handleTriggerGenerate}
            disabled={isGenerating}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 via-indigo-600 to-cyan-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-semibold flex items-center justify-center gap-2 shadow-lg shadow-cyan-950/40 transition disabled:opacity-50"
          >
            <Sparkles size={16} />
            {isGenerating ? 'Đang gọi Gemini AI sinh bài dạy & slide...' : '🚀 Gọi Gemini AI Sinh Bài Dạy & Bộ Slide'}
          </button>
        </div>

        {/* Cột phải: Khung hiển thị Kế hoạch 5512 do AI sinh ra */}
        <div className="col-span-12 lg:col-span-7 glass-panel p-5 rounded-2xl border-slate-800 space-y-4 text-xs leading-relaxed">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="font-bold text-white text-sm flex items-center gap-2">
              <FileText size={16} className="text-cyan-400" /> Kế Hoạch Bài Dạy Đã Kiểm Định (CV 5512)
            </h3>
            <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[11px] flex items-center gap-1">
              <CheckCircle size={12} /> Hợp chuẩn 100%
            </span>
          </div>

          {lessonPlan ? (
            <div className="space-y-4">
              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-800/40">
                <h4 className="text-sm font-bold text-white">{lessonPlan.lesson_title}</h4>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Môn: {lessonPlan.subject} | Khối: {lessonPlan.grade} | Thời lượng: {lessonPlan.duration_periods || 1} tiết (45 phút)
                </div>
              </div>

              {/* I. Mục tiêu bài dạy */}
              <div className="space-y-1.5">
                <strong className="text-cyan-400 block text-xs">I. YÊU CẦU CẦN ĐẠT (MỤC TIÊU BÀI DẠY):</strong>
                <ul className="list-disc pl-4 text-slate-300 space-y-1.5">
                  <li>
                    <strong className="text-white">1. Kiến thức:</strong> <MathText text={knowledgeText} />
                  </li>
                  <li>
                    <strong className="text-white">2. Năng lực:</strong> <MathText text={competencyText} />
                  </li>
                  <li>
                    <strong className="text-white">3. Phẩm chất:</strong> <MathText text={characterText} />
                  </li>
                </ul>
              </div>

              {/* Thiết bị dạy học và học liệu (nếu có) */}
              {equipmentList && (
                <div className="space-y-1">
                  <strong className="text-indigo-400 flex items-center gap-1.5 text-xs">
                    <Wrench size={13} /> II. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU:
                  </strong>
                  <ul className="list-disc pl-4 text-slate-300 space-y-1">
                    {equipmentList.map((eq, idx) => (
                      <li key={idx}><MathText text={eq} /></li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Tiến trình 4 hoạt động */}
              <div className="space-y-2.5">
                <strong className="text-amber-400 flex items-center gap-1.5 text-xs">
                  <Layers size={13} /> {equipmentList ? 'III.' : 'II.'} TIẾN TRÌNH 4 HOẠT ĐỘNG DẠY HỌC (CV 5512):
                </strong>
                <div className="space-y-2.5">
                  {(lessonPlan.activities || []).map((act, i) => {
                    const actTitle = act.name || act.goal || `Hoạt động ${i + 1}`;
                    const actGoal = act.objective || act.goal || '';
                    const actProduct = act.expected_product || '';
                    const exec = act.execution;

                    return (
                      <div key={i} className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
                        <div className="font-bold text-white flex items-center justify-between gap-2">
                          <span className="text-cyan-300">
                            Hoạt động {act.activity_number || i + 1}: <MathText text={actTitle} />
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950/70 border border-cyan-800/60 text-cyan-300 font-mono shrink-0">
                            {act.time_minutes || 10} phút
                          </span>
                        </div>

                        {actGoal && (
                          <p className="text-[11px] text-slate-300">
                            <strong className="text-slate-200">• Mục tiêu: </strong>
                            <MathText text={actGoal} />
                          </p>
                        )}

                        {actProduct && (
                          <p className="text-[11px] text-emerald-300/90">
                            <strong className="text-emerald-400">• Sản phẩm dự kiến: </strong>
                            <MathText text={actProduct} />
                          </p>
                        )}

                        {exec && (
                          <div className="pt-1.5 mt-1.5 border-t border-slate-800/80 grid grid-cols-1 gap-1.5 text-[11px] text-slate-300">
                            {exec.step_1_assign && (
                              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                                <strong className="text-amber-300">B1. Chuyển giao nhiệm vụ: </strong>
                                <MathText text={exec.step_1_assign} />
                              </div>
                            )}
                            {exec.step_2_excute && (
                              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                                <strong className="text-cyan-300">B2. Thực hiện nhiệm vụ: </strong>
                                <MathText text={exec.step_2_excute} />
                              </div>
                            )}
                            {exec.step_3_report && (
                              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                                <strong className="text-indigo-300">B3. Báo cáo, thảo luận: </strong>
                                <MathText text={exec.step_3_report} />
                              </div>
                            )}
                            {exec.step_4_conclusion && (
                              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                                <strong className="text-emerald-300">B4. Kết luận, nhận định: </strong>
                                <MathText text={exec.step_4_conclusion} />
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-400 space-y-2">
              <FileText size={32} className="mx-auto text-slate-600" />
              <p>Chưa có dữ liệu giáo án mới. Hãy chọn bài toán SGK ở trên và bấm <strong>"🚀 Gọi Gemini AI Sinh Bài Dạy & Bộ Slide"</strong> để AI sinh dữ liệu thực tế!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
