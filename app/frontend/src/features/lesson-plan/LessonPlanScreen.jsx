import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Sparkles,
  BookOpen,
  CheckCircle,
  Wrench,
  Layers,
  Package,
  Eye,
  Database,
  X,
  Check,
  Loader2,
  ChevronRight
} from 'lucide-react';
import LessonPlanReview from './LessonPlanReview';
import LessonPlanEditor from './LessonPlanEditor';
import MathText from '../../shared/math/MathText';

export default function LessonPlanScreen({
  lessonPlan,
  onChangePlan,
  isGenerating,
  onGenerateFromAi,
  onExportDocx,
  onExportPptx,
  onExportDualPackage,
  externalProficiency,
  externalOutcome
}) {
  const [topic, setTopic] = useState('');
  const [subject, setSubject] = useState('Toán học');
  const [grade, setGrade] = useState('12');
  const [proficiency, setProficiency] = useState(externalProficiency || 'standard');
  const [outcome, setOutcome] = useState(externalOutcome || '');

  // Khung Chương trình Toán 12 từ API /api/v1/curriculum/math12
  const [curriculum, setCurriculum] = useState([]);
  const [selectedChapterId, setSelectedChapterId] = useState('');
  const [selectedLessonId, setSelectedLessonId] = useState('');
  // Tải danh mục Khung CT 2018 Toán 12 khi mount
  useEffect(() => {
    let isCancelled = false;
    fetch('/api/v1/curriculum/math12')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (isCancelled || !data?.chapters?.length) return;
        setCurriculum(data.chapters);
      })
      .catch((err) => {
        console.warn('[LessonPlanScreen] Không tải được cây CT 2018:', err);
      });

    return () => {
      isCancelled = true;
    };
  }, []);

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

  // Xử lý đổi Chương
  const handleChapterSelect = (chId) => {
    setSelectedChapterId(chId);
    setSelectedLessonId('');
  };

  // Xử lý đổi Bài học
  const handleLessonSelect = (lId, chId = selectedChapterId) => {
    setSelectedLessonId(lId);
    const ch = curriculum.find((c) => c.chapter_id === chId);
    const l = ch?.lessons?.find((item) => item.lesson_id === lId);

    if (l) {
      // Làm sạch tiền tố "Bài X: " để topic ngắn gọn tự nhiên
      const cleanTitle = l.title.replace(/^Bài\s+\d+:\s*/, '');
      setTopic(cleanTitle);
      if (Array.isArray(l.yccd) && l.yccd.length > 0) {
        setOutcome(l.yccd.join('; '));
      }
    }
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
        lesson_id: selectedLessonId,
        use_rag: true,
        proficiency,
        outcome
      });
    }
  };

  // CHUẨN HÓA ĐỌC SONG SONG CẤU TRÚC PHẲNG (BACKEND) & CẤU TRÚC LỒNG NHAU (MẪU)
  const knowledgeText =
    Array.isArray(lessonPlan?.knowledge_goals) && lessonPlan.knowledge_goals.length > 0
      ? lessonPlan.knowledge_goals.join(' • ')
      : lessonPlan?.objectives?.knowledge || 'Chưa có mục tiêu kiến thức.';

  const competencyList =
    Array.isArray(lessonPlan?.competency_goals) && lessonPlan.competency_goals.length > 0
      ? lessonPlan.competency_goals
      : Array.isArray(lessonPlan?.skills_goals) && lessonPlan.skills_goals.length > 0
      ? lessonPlan.skills_goals
      : null;

  const competencyText = competencyList
    ? competencyList.join(' • ')
    : lessonPlan?.objectives?.competencies || 'Chưa có mục tiêu năng lực.';

  const characterText =
    Array.isArray(lessonPlan?.character_goals) && lessonPlan.character_goals.length > 0
      ? lessonPlan.character_goals.join(' • ')
      : lessonPlan?.objectives?.qualities || 'Chưa có mục tiêu phẩm chất.';

  const equipmentList =
    Array.isArray(lessonPlan?.teaching_equipment) && lessonPlan.teaching_equipment.length > 0
      ? lessonPlan.teaching_equipment
      : null;

  // Lấy danh sách bài học thuộc chương đang chọn
  const currentChapter = curriculum.find((c) => c.chapter_id === selectedChapterId);
  const lessonsInChapter = currentChapter?.lessons || [];

  return (
    <div className="flex-1 p-5 overflow-y-auto max-w-7xl mx-auto space-y-4">
      {/* Header màn hình */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#e0e0e0]">
        <div>
          <h2 className="text-xl font-bold text-[#141414] flex items-center gap-2">
            Soạn Kế Hoạch Bài Dạy Chuẩn Công Văn 5512
          </h2>
          <p className="text-xs text-[#707070] mt-0.5">
            Soạn bài từ nội dung và mục tiêu do giáo viên lựa chọn
          </p>
        </div>
        <button
          onClick={onExportDocx}
          className="px-4 py-2 rounded-full bg-[#141414] hover:bg-[#262626] text-white text-xs font-semibold flex items-center gap-2 transition cursor-pointer"
        >
          <Download size={14} /> Xuất File Word (.docx)
        </button>
      </div>

      {/* THANH CHỌN BÀI DẠY THEO KHUNG CHƯƠNG TRÌNH TOÁN 12 CT GDPT 2018 (TASK 5.2) */}
      <div className="p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-3.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-xs font-bold text-[#141414] flex items-center gap-1.5">
            <BookOpen size={15} /> Khung Chương Trình Toán 12 (CT GDPT 2018 - Kết Nối Tri Thức):
          </div>

        </div>

        {/* 2 Dropdown Chương và Bài học */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 text-xs">
          <div className="md:col-span-5">
            <label className="text-[#707070] block mb-1 font-semibold">1. Chọn Chương học:</label>
            <select
              value={selectedChapterId}
              onChange={(e) => handleChapterSelect(e.target.value)}
              className="w-full bg-[#f0f0f0] border-none rounded-xl px-3 py-2 text-[#141414] font-medium focus:ring-2 focus:ring-[#141414] outline-none cursor-pointer"
            >
              <option value="">Chọn chương</option>
              {curriculum.length > 0 ? (
                curriculum.map((ch) => (
                  <option key={ch.chapter_id} value={ch.chapter_id}>
                    {ch.title}
                  </option>
                ))
              ) : (
                <option value="">Chưa có danh mục chương</option>
              )}
            </select>
          </div>

          <div className="md:col-span-7">
            <label className="text-[#707070] block mb-1 font-semibold">2. Chọn Bài học (SGK KNTT 12):</label>
            <select
              value={selectedLessonId}
              onChange={(e) => handleLessonSelect(e.target.value)}
              className="w-full bg-[#f0f0f0] border-none rounded-xl px-3 py-2 text-[#141414] font-medium focus:ring-2 focus:ring-[#141414] outline-none cursor-pointer"
            >
              <option value="">Chọn bài</option>
              {lessonsInChapter.length > 0 ? (
                lessonsInChapter.map((l) => (
                  <option key={l.lesson_id} value={l.lesson_id}>
                    [{l.lesson_id}] {l.title} ({l.available_slides_count || 0} slide, {l.available_questions_count || 0} câu hỏi)
                  </option>
                ))
              ) : (
                <option value="">Chưa chọn bài</option>
              )}
            </select>
          </div>
        </div>

        {/* Cột trái: Form cấu hình bài dạy */}
        <div className="col-span-12 lg:col-span-5 p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-4 text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-[#e0e0e0]">
            <h3 className="font-bold text-[#141414] text-sm flex items-center gap-1.5">
              Thiết Lập Bài Dạy & Hồ Sơ Lớp
            </h3>
            <span className="px-2.5 py-0.5 rounded-full bg-[#f3f3f3] border border-[#e0e0e0] text-[#141414] font-mono text-[11px] font-semibold">
              {selectedLessonId}
            </span>
          </div>

          <div>
            <label className="text-[#707070] block mb-1 font-semibold">Tên bài dạy / Chủ đề cần soạn:</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Nhập tên bài dạy của thầy/cô"
              className="w-full bg-[#f0f0f0] border-none rounded-2xl px-3.5 py-2.5 text-[#141414] text-sm focus:ring-2 focus:ring-[#141414] outline-none font-medium"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[#707070] block mb-1 font-semibold">Môn học:</label>
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full bg-[#f0f0f0] border-none rounded-xl px-3 py-2 text-[#141414] font-medium focus:ring-2 focus:ring-[#141414] outline-none cursor-pointer"
              >
                <option value="Toán học">Toán học (CT 2018)</option>
              </select>
            </div>
            <div>
              <label className="text-[#707070] block mb-1 font-semibold">Khối lớp:</label>
              <select
                value={grade}
                onChange={(e) => setGrade(e.target.value)}
                className="w-full bg-[#f0f0f0] border-none rounded-xl px-3 py-2 text-[#141414] font-medium focus:ring-2 focus:ring-[#141414] outline-none cursor-pointer"
              >
                <option value="12">Lớp 12 (Chuyên sâu KNTT)</option>
                <option value="11">Lớp 11</option>
                <option value="10">Lớp 10</option>
              </select>
            </div>
          </div>

          {/* Phân hóa học lực - Segmented Control Track */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-[#707070] font-semibold">Trình độ phân hóa học lực lớp:</label>
              {externalProficiency && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#f3f3f3] text-[#0066ff] border border-[#e0e0e0] font-semibold">
                  Đồng bộ từ Z-Score
                </span>
              )}
            </div>
            <div className="grid grid-cols-3 gap-1 bg-[#f3f3f3] p-1 rounded-full border border-[#e0e0e0]">
              {[
                { key: 'basic', label: 'Cơ bản' },
                { key: 'standard', label: 'Chuẩn (SGK)' },
                { key: 'advanced', label: 'Nâng cao' }
              ].map((p) => (
                <button
                  key={p.key}
                  type="button"
                  onClick={() => setProficiency(p.key)}
                  className={`py-1.5 px-2 rounded-full text-center transition font-semibold text-xs cursor-pointer ${
                    proficiency === p.key
                      ? 'bg-[#ffffff] text-[#141414] shadow-sm'
                      : 'text-[#707070] hover:text-[#141414]'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-[#707070] block mb-1 font-semibold">Yêu cầu cần đạt (Mục tiêu bài dạy):</label>
            <textarea
              rows={3}
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              className="w-full bg-[#f0f0f0] border-none rounded-2xl p-3 text-[#141414] leading-relaxed focus:ring-2 focus:ring-[#141414] outline-none"
            />
          </div>

          {/* Thông tin RAG Grounding */}
          <div className="p-3 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0] text-[11px] text-[#141414] space-y-1">
            <div className="font-bold text-[#141414] flex items-center gap-1.5">
              <Sparkles size={13} className="text-[#141414]" /> Pedagogical RAG Toán 12 KNTT:
            </div>
            <p className="text-[#707070]">
              Chỉ học liệu đã được duyệt mới được dùng làm nguồn. Bài AI tạo là bản nháp; cần đối chiếu đề, giả thiết, lời giải và nguồn trước khi giảng dạy.
            </p>
          </div>

          {/* NÚT GỌI AI THẬT */}
          <button
            type="button"
            onClick={handleTriggerGenerate}
            disabled={isGenerating}
            className="w-full py-3 rounded-full bg-[#141414] hover:bg-[#262626] text-white font-semibold flex items-center justify-center gap-2 transition disabled:opacity-50 cursor-pointer shadow-none"
          >
            <Sparkles size={16} />
            {isGenerating ? 'Đang gọi Gemini AI sinh bài dạy & slide...' : 'Gọi Gemini AI Sinh Bài Dạy & Bộ Slide'}
          </button>
        </div>

        {/* Cột phải: Khung hiển thị Kế hoạch 5512 do AI sinh ra */}
        <div className="col-span-12 lg:col-span-7 glass-panel p-5 rounded-2xl border-slate-800 space-y-4 text-xs leading-relaxed">
          <div className="flex flex-wrap items-center justify-between gap-2.5 pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-[#141414] text-sm flex items-center gap-2">
                <FileText size={16} className="text-[#141414]" /> Kế Hoạch Bài Dạy (CV 5512)
              </h3>
              <span className="px-2.5 py-0.5 rounded-full bg-[#f3f3f3] text-[#10b981] border border-[#e0e0e0] text-[11px] font-semibold flex items-center gap-1">
                <CheckCircle size={12} /> Cần đối chiếu nội dung
              </span>
            </div>

            {/* Cụm nút bấm Tải về */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <button
                type="button"
                onClick={onExportDocx}
                className="px-3.5 py-1.5 rounded-full bg-[#141414] hover:bg-[#262626] text-white font-semibold text-xs flex items-center gap-1.5 transition active:scale-95 cursor-pointer shadow-none"
                title="Tải Kế hoạch bài dạy Word (.docx) chuẩn CV 5512"
              >
                <FileText size={13} />
                <span>Tải Word (.docx)</span>
              </button>

              <button
                type="button"
                onClick={onExportPptx}
                className="px-3.5 py-1.5 rounded-full bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] border border-[#e0e0e0] font-semibold text-xs flex items-center gap-1.5 transition active:scale-95 cursor-pointer"
                title="Tải Bài giảng PowerPoint (.pptx)"
              >
                <Download size={13} />
                <span>Tải Slide (.pptx)</span>
              </button>

              <button
                type="button"
                onClick={onExportDualPackage}
                className="px-3.5 py-1.5 rounded-full bg-[#f3f3f3] hover:bg-[#e0e0e0] text-[#141414] border border-[#e0e0e0] font-semibold text-xs flex items-center gap-1.5 transition active:scale-95 cursor-pointer"
                title="Tải Trọn Bộ (.zip): Gói kép Word + PowerPoint đồng bộ 100%"
              >
                <Package size={13} />
                <span>Tải Trọn Bộ (.zip)</span>
              </button>
            </div>
          </div>

          {lessonPlan ? (
            <div className="space-y-4">
              <LessonPlanReview plan={lessonPlan} onChange={onChangePlan}/>
              <LessonPlanEditor plan={lessonPlan} onChange={onChangePlan}/>
              <div className="p-3.5 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0]">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-sm font-bold text-[#141414]">{lessonPlan.lesson_title}</h4>
                  <span className="px-2.5 py-0.5 rounded-full bg-[#ffffff] text-[#141414] border border-[#e0e0e0] text-[11px] font-semibold flex items-center gap-1 shrink-0">
                    <BookOpen size={12} />
                    <span>{lessonPlan.review_token?"Đã lưu xác nhận giáo án":"BẢN NHÁP — cần duyệt nội dung"}</span>
                  </span>
                </div>
                <div className="text-[11px] text-[#707070] mt-1">
                  Môn: {lessonPlan.subject} | Khối: {lessonPlan.grade} | Thời lượng: {lessonPlan.duration_periods || 1} tiết (45 phút)
                </div>
              </div>

              {/* I. Mục tiêu bài dạy */}
              <div className="space-y-1.5">
                <strong className="text-[#141414] block text-xs font-bold uppercase tracking-wider">I. YÊU CẦU CẦN ĐẠT (MỤC TIÊU BÀI DẠY):</strong>
                <ul className="list-disc pl-4 text-[#141414] space-y-1.5">
                  <li>
                    <strong className="text-[#141414]">1. Kiến thức:</strong> <MathText text={knowledgeText} />
                  </li>
                  <li>
                    <strong className="text-[#141414]">2. Năng lực:</strong> <MathText text={competencyText} />
                  </li>
                  <li>
                    <strong className="text-[#141414]">3. Phẩm chất:</strong> <MathText text={characterText} />
                  </li>
                </ul>
              </div>

              {/* Thiết bị dạy học và học liệu (nếu có) */}
              {equipmentList && (
                <div className="space-y-1">
                  <strong className="text-[#141414] flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider">
                    <Wrench size={13} /> II. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU:
                  </strong>
                  <ul className="list-disc pl-4 text-[#141414] space-y-1">
                    {equipmentList.map((eq, idx) => (
                      <li key={idx}><MathText text={eq} /></li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Tiến trình 4 hoạt động */}
              <div className="space-y-2.5">
                <strong className="text-[#141414] flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider">
                  <Layers size={13} /> {equipmentList ? 'III.' : 'II.'} TIẾN TRÌNH 4 HOẠT ĐỘNG DẠY HỌC (CV 5512):
                </strong>
                <div className="space-y-2.5">
                  {(lessonPlan.activities || []).map((act, i) => {
                    const actTitle = act.name || act.goal || `Hoạt động ${i + 1}`;
                    const actGoal = act.objective || act.goal || '';
                    const actProduct = act.expected_product || '';
                    const exec = act.execution;

                    return (
                      <div key={i} className="p-4 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0] space-y-2">
                        <div className="font-bold text-[#141414] flex items-center justify-between gap-2">
                          <span className="text-[#141414]">
                            Hoạt động {act.activity_number || i + 1}: <MathText text={actTitle} />
                          </span>
                          <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-[#ffffff] border border-[#e0e0e0] text-[#141414] font-mono shrink-0 font-semibold">
                            {act.time_minutes ?? "Chưa có thời lượng"} phút
                          </span>
                        </div>

                        {actGoal && (
                          <p className="text-[11px] text-[#141414]">
                            <strong className="text-[#141414]">• Mục tiêu: </strong>
                            <MathText text={actGoal} />
                          </p>
                        )}

                        {actProduct && (
                          <p className="text-[11px] text-[#141414]">
                            <strong className="text-[#141414]">• Sản phẩm: </strong>
                            <MathText text={actProduct} />
                          </p>
                        )}

                        {exec && (
                          <div className="pt-2 mt-2 border-t border-[#e0e0e0] grid grid-cols-1 gap-1.5 text-[11px] text-[#141414]">
                            {exec.step_1_assign && (
                              <div className="bg-[#ffffff] p-2.5 rounded-xl border border-[#e0e0e0]">
                                <strong className="text-[#141414]">B1. Chuyển giao: </strong>
                                <MathText text={exec.step_1_assign} />
                              </div>
                            )}
                            {exec.step_2_excute && (
                              <div className="bg-[#ffffff] p-2.5 rounded-xl border border-[#e0e0e0]">
                                <strong className="text-[#141414]">B2. Thực hiện: </strong>
                                <MathText text={exec.step_2_excute} />
                              </div>
                            )}
                            {exec.step_3_report && (
                              <div className="bg-[#ffffff] p-2.5 rounded-xl border border-[#e0e0e0]">
                                <strong className="text-[#141414]">B3. Báo cáo, thảo luận: </strong>
                                <MathText text={exec.step_3_report} />
                              </div>
                            )}
                            {exec.step_4_conclusion && (
                              <div className="bg-[#ffffff] p-2.5 rounded-xl border border-[#e0e0e0]">
                                <strong className="text-[#141414]">B4. Kết luận, nhận định: </strong>
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
            <div className="p-8 text-center text-[#707070] space-y-2">
              <FileText size={32} className="mx-auto text-[#adadad]" />
              <p>Chưa có dữ liệu giáo án mới. Hãy chọn bài toán SGK ở trên và bấm <strong>"Gọi Gemini AI Sinh Bài Dạy & Bộ Slide"</strong> để AI sinh dữ liệu thực tế!</p>
            </div>
          )}
        </div>
      </div>


    </div>
  );
}
