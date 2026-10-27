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
import MathText from './MathText';

export default function LessonPlanScreen({
  lessonPlan,
  isGenerating,
  onGenerateFromAi,
  onExportDocx,
  onExportPptx,
  onExportDualPackage,
  externalProficiency,
  externalOutcome
}) {
  const [topic, setTopic] = useState('Tính đơn điệu và cực trị của hàm số');
  const [subject, setSubject] = useState('Toán học');
  const [grade, setGrade] = useState('12');
  const [proficiency, setProficiency] = useState(externalProficiency || 'standard');
  const [outcome, setOutcome] = useState(externalOutcome || '');

  // Khung Chương trình Toán 12 từ API /api/v1/curriculum/math12
  const [curriculum, setCurriculum] = useState([]);
  const [selectedChapterId, setSelectedChapterId] = useState('M12-C1');
  const [selectedLessonId, setSelectedLessonId] = useState('M12-C1-B1');
  const [ragStats, setRagStats] = useState({ slides: 82, questions: 261, periods: 4 });

  // Trạng thái Modal Xem Trước Tài Nguyên RAG (Task 5.2)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [previewTab, setPreviewTab] = useState('yccd'); // 'yccd' | 'slides' | 'questions'

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

        // Tìm bài M12-C1-B1 mặc định
        const ch1 = data.chapters[0];
        if (ch1?.lessons?.length) {
          const l1 = ch1.lessons[0];
          setSelectedChapterId(ch1.chapter_id);
          setSelectedLessonId(l1.lesson_id);
          setRagStats({
            slides: l1.available_slides_count || 0,
            questions: l1.available_questions_count || 0,
            periods: l1.periods || 2
          });
        }
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

  // DANH MỤC CÁC BÀI TOÁN TOÁN 12 CHUẨN CT GDPT 2018 (SGK KẾT NỐI TRI THỨC)
  const textbookPresets = [
    {
      label: "1. Đơn Điệu & Cực Trị (Chương 1)",
      lessonId: "M12-C1-B1",
      chapterId: "M12-C1",
      topic: "Tính đơn điệu và cực trị của hàm số",
      subject: "Toán học",
      grade: "12",
      outcome: "Học sinh thành thạo xét dấu f'(x), lập bảng biến thiên, xác định chính xác các khoảng đồng biến, nghịch biến và tọa độ điểm cực đại, cực tiểu của hàm số."
    },
    {
      label: "2. Khảo Sát Đồ Thị Bậc 3 (Chương 1)",
      lessonId: "M12-C1-B4",
      chapterId: "M12-C1",
      topic: "Khảo sát sự biến thiên và vẽ đồ thị hàm số bậc ba",
      subject: "Toán học",
      grade: "12",
      outcome: "Học sinh lập bảng biến thiên, tìm điểm cực trị, điểm uốn nhận làm tâm đối xứng và vẽ đồ thị hàm số bậc ba chuẩn xác."
    },
    {
      label: "3. Tọa Độ Oxyz Không Gian (Chương 2)",
      lessonId: "M12-C2-B2",
      chapterId: "M12-C2",
      topic: "Hệ trục tọa độ trong không gian Oxyz",
      subject: "Toán học",
      grade: "12",
      outcome: "Học sinh nắm vững tọa độ điểm, biểu thức tọa độ của vectơ, tính tích vô hướng, độ dài vectơ và khoảng cách giữa hai điểm trong không gian Oxyz."
    },
    {
      label: "4. Phương Sai & Độ Lệch Chuẩn (Chương 3)",
      lessonId: "M12-C3-B2",
      chapterId: "M12-C3",
      topic: "Phương sai và độ lệch chuẩn của mẫu số liệu ghép nhóm",
      subject: "Toán học",
      grade: "12",
      outcome: "Học sinh lập bảng giá trị đại diện c_i, tính số trung bình, phương sai s^2 và độ lệch chuẩn s để đánh giá mức độ phân tán và độ rủi ro thực tế."
    },
    {
      label: "5. Ứng Dụng Tích Phân (Chương 4)",
      lessonId: "M12-C4-B3",
      chapterId: "M12-C4",
      topic: "Ứng dụng hình học của tích phân tính diện tích hình phẳng",
      subject: "Toán học",
      grade: "12",
      outcome: "Học sinh vận dụng công thức Newton-Leibniz và tích phân từng phần tính diện tích hình phẳng giới hạn bởi đồ thị hàm số và các trục tọa độ."
    },
    {
      label: "6. Xác Suất Toàn Phần & Bayes (Chương 6)",
      lessonId: "M12-C6-B2",
      chapterId: "M12-C6",
      topic: "Công thức xác suất toàn phần và công thức Bayes",
      subject: "Toán học",
      grade: "12",
      outcome: "Học sinh biểu diễn bài toán bằng sơ đồ hình cây, vận dụng chính xác công thức xác suất toàn phần và định lý Bayes trong bài toán thực tế."
    }
  ];

  // Xử lý đổi Chương
  const handleChapterSelect = (chId) => {
    setSelectedChapterId(chId);
    const ch = curriculum.find((c) => c.chapter_id === chId);
    if (ch?.lessons?.length) {
      const firstLesson = ch.lessons[0];
      handleLessonSelect(firstLesson.lesson_id, chId);
    }
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
      setRagStats({
        slides: l.available_slides_count || 0,
        questions: l.available_questions_count || 0,
        periods: l.periods || 2
      });
    }
  };

  const handleSelectPreset = (p) => {
    setTopic(p.topic);
    setSubject(p.subject);
    setGrade(p.grade);
    setOutcome(p.outcome);
    if (p.lessonId) setSelectedLessonId(p.lessonId);
    if (p.chapterId) setSelectedChapterId(p.chapterId);

    // Cập nhật ragStats nếu tìm thấy bài trong curriculum
    const ch = curriculum.find((c) => c.chapter_id === p.chapterId);
    const l = ch?.lessons?.find((item) => item.lesson_id === p.lessonId);
    if (l) {
      setRagStats({
        slides: l.available_slides_count || 0,
        questions: l.available_questions_count || 0,
        periods: l.periods || 2
      });
    }
  };

  const handleOpenPreview = async () => {
    setIsPreviewOpen(true);
    setIsLoadingPreview(true);
    try {
      const res = await fetch('/api/v1/rag/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lesson_id: selectedLessonId,
          topic: topic,
          proficiency: proficiency || 'standard',
          k_slides: 4,
          k_questions: 4
        })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPreviewData(data);
    } catch (err) {
      console.error('[LessonPlanScreen] Lỗi khi gọi preview RAG:', err);
    } finally {
      setIsLoadingPreview(false);
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

  // Lấy danh sách bài học thuộc chương đang chọn
  const currentChapter = curriculum.find((c) => c.chapter_id === selectedChapterId);
  const lessonsInChapter = currentChapter?.lessons || [];

  return (
    <div className="flex-1 p-5 overflow-y-auto max-w-7xl mx-auto space-y-4">
      {/* Header màn hình */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            Soạn Kế Hoạch Bài Dạy Chuẩn Công Văn 5512
          </h2>
          <p className="text-xs text-slate-400">
            Chuyên sâu Toán 12 (CT GDPT 2018 - SGK Kết nối tri thức) • Tích hợp Pedagogical RAG
          </p>
        </div>
        <button
          onClick={onExportDocx}
          className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-emerald-950/40 transition"
        >
          <Download size={14} /> Xuất File Word (.docx)
        </button>
      </div>

      {/* THANH CHỌN BÀI DẠY THEO KHUNG CHƯƠNG TRÌNH TOÁN 12 CT GDPT 2018 (TASK 5.2) */}
      <div className="glass-panel p-4 rounded-2xl border-slate-800 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
            <BookOpen size={15} /> Khung Chương Trình Toán 12 (CT GDPT 2018 - Kết Nối Tri Thức):
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2 py-0.5 rounded-md bg-indigo-950 border border-indigo-800 text-indigo-300 font-medium flex items-center gap-1">
              <Database size={12} className="text-indigo-400" />
              <span>Kho RAG: {ragStats.slides} slide • {ragStats.questions} bài tập ({ragStats.periods} tiết)</span>
            </span>
            <button
              type="button"
              onClick={handleOpenPreview}
              className="px-2.5 py-1 rounded-md bg-cyan-900/60 hover:bg-cyan-800 text-cyan-200 border border-cyan-700/80 font-medium flex items-center gap-1 transition"
              title="Xem trước slide mẫu và câu hỏi thực tế trong kho Pedagogical RAG"
            >
              <Eye size={12} />
              <span>Xem Trước Kho RAG</span>
            </button>
          </div>
        </div>

        {/* 2 Dropdown Chương và Bài học */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 text-xs">
          <div className="md:col-span-5">
            <label className="text-slate-400 block mb-1 font-semibold">1. Chọn Chương học:</label>
            <select
              value={selectedChapterId}
              onChange={(e) => handleChapterSelect(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-white font-medium focus:outline-none focus:border-cyan-500"
            >
              {curriculum.length > 0 ? (
                curriculum.map((ch) => (
                  <option key={ch.chapter_id} value={ch.chapter_id}>
                    {ch.title}
                  </option>
                ))
              ) : (
                <option value="M12-C1">Chương I. Ứng dụng đạo hàm khảo sát hàm số</option>
              )}
            </select>
          </div>

          <div className="md:col-span-7">
            <label className="text-slate-400 block mb-1 font-semibold">2. Chọn Bài học (SGK KNTT 12):</label>
            <select
              value={selectedLessonId}
              onChange={(e) => handleLessonSelect(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-white font-medium focus:outline-none focus:border-cyan-500 text-cyan-200"
            >
              {lessonsInChapter.length > 0 ? (
                lessonsInChapter.map((l) => (
                  <option key={l.lesson_id} value={l.lesson_id}>
                    [{l.lesson_id}] {l.title} ({l.available_slides_count || 0} slide, {l.available_questions_count || 0} câu hỏi)
                  </option>
                ))
              ) : (
                <option value="M12-C1-B1">Bài 1: Tính đơn điệu và cực trị của hàm số</option>
              )}
            </select>
          </div>
        </div>

        {/* Cụm Preset 1-Click nhanh */}
        <div className="pt-2 border-t border-slate-800/80">
          <div className="text-[11px] text-slate-400 mb-1.5 font-medium">Hoặc nạp nhanh 6 chủ đề tiêu biểu:</div>
          <div className="flex flex-wrap gap-1.5">
            {textbookPresets.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectPreset(preset)}
                className={`px-2.5 py-1 rounded-lg border text-xs transition flex items-center gap-1 ${
                  selectedLessonId === preset.lessonId
                    ? 'bg-cyan-950 border-cyan-600 text-cyan-200 font-semibold shadow-sm'
                    : 'bg-slate-900/80 hover:bg-slate-800 border-slate-800 text-slate-300'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-5">
        {/* Cột trái: Form cấu hình bài dạy */}
        <div className="col-span-12 lg:col-span-5 glass-panel p-4 rounded-2xl border-slate-800 space-y-3.5 text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="font-bold text-white text-sm flex items-center gap-1.5">
              Thiết Lập Bài Dạy & Hồ Sơ Lớp
            </h3>
            <span className="px-2 py-0.5 rounded bg-indigo-950 border border-indigo-800 text-indigo-300 font-mono text-[11px]">
              {selectedLessonId}
            </span>
          </div>

          <div>
            <label className="text-slate-400 block mb-1 font-semibold">Tên bài dạy / Chủ đề cần soạn:</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="VD: Tính đơn điệu, Khảo sát hàm số, Hệ tọa độ Oxyz, Phương sai ghép nhóm, Tích phân..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500 font-medium"
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
                <option value="Toán học">Toán học (CT 2018)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Khối lớp:</label>
              <select
                value={grade}
                onChange={(e) => setGrade(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-white font-medium text-cyan-300"
              >
                <option value="12">Lớp 12 (Chuyên sâu KNTT)</option>
                <option value="11">Lớp 11</option>
                <option value="10">Lớp 10</option>
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

          {/* Thông tin RAG Grounding */}
          <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-[11px] text-slate-300 space-y-1">
            <div className="font-semibold text-cyan-300 flex items-center gap-1">
              <Sparkles size={13} className="text-cyan-400" /> Pedagogical RAG Toán 12 KNTT:
            </div>
            <p className="text-slate-400">
              Hệ thống sẽ neo tự động giáo án vào YCCĐ chuẩn, lấy slide bài giảng thực tế từ 1.847 slide KNTT 12 và bổ sung câu hỏi trắc nghiệm có lời giải 3 bước.
            </p>
          </div>

          {/* NÚT GỌI AI THẬT */}
          <button
            type="button"
            onClick={handleTriggerGenerate}
            disabled={isGenerating}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 via-indigo-600 to-cyan-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-semibold flex items-center justify-center gap-2 shadow-lg shadow-cyan-950/40 transition disabled:opacity-50"
          >
            <Sparkles size={16} />
            {isGenerating ? 'Đang gọi Gemini AI sinh bài dạy & slide...' : 'Gọi Gemini AI Sinh Bài Dạy & Bộ Slide'}
          </button>
        </div>

        {/* Cột phải: Khung hiển thị Kế hoạch 5512 do AI sinh ra */}
        <div className="col-span-12 lg:col-span-7 glass-panel p-5 rounded-2xl border-slate-800 space-y-4 text-xs leading-relaxed">
          <div className="flex flex-wrap items-center justify-between gap-2.5 pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <FileText size={16} className="text-cyan-400" /> Kế Hoạch Bài Dạy (CV 5512)
              </h3>
              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[11px] flex items-center gap-1">
                <CheckCircle size={12} /> Hợp chuẩn 100%
              </span>
            </div>

            {/* Cụm nút bấm Tải về */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <button
                type="button"
                onClick={onExportDocx}
                className="px-2.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center gap-1.5 shadow-md shadow-blue-950/40 transition active:scale-95 cursor-pointer"
                title="Tải Kế hoạch bài dạy Word (.docx) chuẩn CV 5512 tích hợp công thức OMML"
              >
                <FileText size={13} />
                <span>Tải Word (.docx)</span>
              </button>

              <button
                type="button"
                onClick={onExportPptx}
                className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 hover:text-amber-200 border border-amber-800/60 font-medium text-xs flex items-center gap-1.5 transition active:scale-95 cursor-pointer"
                title="Tải Bài giảng PowerPoint (.pptx) đồng bộ từ giáo án này"
              >
                <Download size={13} />
                <span>Tải Slide (.pptx)</span>
              </button>

              <button
                type="button"
                onClick={onExportDualPackage}
                className="px-2.5 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-950/40 border border-emerald-400/40 transition active:scale-95 cursor-pointer"
                title="Tải Trọn Bộ (.zip): Gói kép Word + PowerPoint đồng bộ 100%"
              >
                <Package size={13} />
                <span>Tải Trọn Bộ (.zip)</span>
              </button>
            </div>
          </div>

          {lessonPlan ? (
            <div className="space-y-4">
              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-800/40">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-sm font-bold text-white">{lessonPlan.lesson_title}</h4>
                  <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 text-[11px] font-medium flex items-center gap-1 shrink-0">
                    <BookOpen size={12} className="text-indigo-400" />
                    <span>Nguồn RAG: KNTT 12</span>
                  </span>
                </div>
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
              <p>Chưa có dữ liệu giáo án mới. Hãy chọn bài toán SGK ở trên và bấm <strong>"Gọi Gemini AI Sinh Bài Dạy & Bộ Slide"</strong> để AI sinh dữ liệu thực tế!</p>
            </div>
          )}
        </div>
      </div>

      {/* MODAL XEM TRƯỚC TÀI NGUYÊN RAG (TASK 5.2) */}
      {isPreviewOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-4xl max-h-[85vh] bg-[#0b1022] rounded-2xl border border-slate-700 shadow-2xl flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between shrink-0 bg-slate-950/60">
              <div className="flex items-center gap-2">
                <Database size={18} className="text-cyan-400" />
                <h3 className="text-sm font-bold text-white">
                  Tài Nguyên Sư Phạm Pedagogical RAG — {selectedLessonId}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsPreviewOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Sub-header & Navigation Tabs */}
            <div className="px-4 py-2 border-b border-slate-800 bg-slate-900/50 flex flex-wrap items-center justify-between gap-2 shrink-0">
              <div className="text-xs text-slate-300 font-medium truncate">
                Bài dạy: <span className="text-cyan-300 font-semibold">{topic}</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs">
                <button
                  type="button"
                  onClick={() => setPreviewTab('yccd')}
                  className={`px-3 py-1 rounded-lg font-medium transition ${
                    previewTab === 'yccd'
                      ? 'bg-cyan-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  YCCĐ & Dàn Ý
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewTab('slides')}
                  className={`px-3 py-1 rounded-lg font-medium transition ${
                    previewTab === 'slides'
                      ? 'bg-cyan-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  Slide Mẫu KNTT ({previewData?.slides_preview?.length || ragStats.slides})
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewTab('questions')}
                  className={`px-3 py-1 rounded-lg font-medium transition ${
                    previewTab === 'questions'
                      ? 'bg-cyan-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  Câu Hỏi & Lời Giải 3 Bước ({previewData?.questions_preview?.length || ragStats.questions})
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-4 overflow-y-auto flex-1 space-y-4 text-xs">
              {isLoadingPreview ? (
                <div className="py-12 text-center text-slate-400 flex flex-col items-center justify-center gap-2">
                  <Loader2 size={24} className="animate-spin text-cyan-400" />
                  <span>Đang truy xuất kho dữ liệu sư phạm KNTT 12 trong &lt; 30ms...</span>
                </div>
              ) : previewData ? (
                <>
                  {/* TAB 1: YCCĐ & DÀN Ý */}
                  {previewTab === 'yccd' && (
                    <div className="space-y-4">
                      <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                        <strong className="text-cyan-400 block text-xs">
                          Mục Tiêu Yêu Cầu Cần Đạt (Khung CT 2018):
                        </strong>
                        <ul className="space-y-1.5 pl-2">
                          {(previewData.yccd || []).map((y, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-slate-300">
                              <Check size={14} className="text-emerald-400 mt-0.5 shrink-0" />
                              <span>{y}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {previewData.deck_outline && previewData.deck_outline.length > 0 && (
                        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                          <strong className="text-amber-400 block text-xs">
                            Dàn Ý Slide Bài Giảng Giáo Viên Gốc (KNTT 12):
                          </strong>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {previewData.deck_outline.map((out, idx) => (
                              <div
                                key={idx}
                                className="p-2 rounded-lg bg-slate-950 border border-slate-800/80 flex items-center gap-2 text-slate-300 text-[11px]"
                              >
                                <ChevronRight size={12} className="text-cyan-400 shrink-0" />
                                <span className="truncate">{out}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {previewData.keywords && previewData.keywords.length > 0 && (
                        <div className="space-y-1.5">
                          <span className="text-slate-400 block text-[11px] font-semibold">
                            Từ khóa chuyên môn trọng tâm:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {previewData.keywords.map((kw, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 rounded-md bg-cyan-950 border border-cyan-800/80 text-cyan-300 text-[11px]"
                              >
                                #{kw}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* TAB 2: SLIDE MẪU */}
                  {previewTab === 'slides' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {(previewData.slides_preview || []).map((s, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 flex flex-col justify-between"
                        >
                          <div className="space-y-1.5">
                            <div className="flex items-center justify-between gap-1.5">
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                                {s.activity_type || 'Nội dung'}
                              </span>
                              <span className="text-[10px] text-slate-400 font-mono">
                                {s.layout_hint || 'IMAGE_TEXT'}
                              </span>
                            </div>
                            <h4 className="font-bold text-white text-xs">{s.title}</h4>
                            {s.bullet_points && s.bullet_points.length > 0 && (
                              <ul className="list-disc pl-4 text-slate-300 space-y-1 text-[11px]">
                                {s.bullet_points.slice(0, 3).map((bp, bidx) => (
                                  <li key={bidx}>
                                    <MathText text={bp} />
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>

                          {s.main_definition_latex && (
                            <div className="p-2 rounded bg-slate-950 border border-slate-800 text-[11px] text-cyan-200 overflow-x-auto">
                              <MathText text={s.main_definition_latex} />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* TAB 3: CÂU HỎI & LỜI GIẢI 3 BƯỚC */}
                  {previewTab === 'questions' && (
                    <div className="space-y-3">
                      {(previewData.questions_preview || []).map((q, idx) => (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-bold text-amber-300">
                              Câu {idx + 1} ({q.difficulty === 'hard' ? 'Nâng cao' : q.difficulty === 'easy' ? 'Nhận biết' : 'Thông hiểu'})
                            </span>
                            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
                              Đáp án: {q.answer || 'A'}
                            </span>
                          </div>

                          <div className="text-white font-medium">
                            <MathText text={q.question} />
                          </div>

                          {/* Phương án trắc nghiệm */}
                          {q.quiz_options && q.quiz_options.length > 0 && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
                              {q.quiz_options.map((opt, oidx) => (
                                <div
                                  key={oidx}
                                  className={`p-2 rounded-lg border text-[11px] ${
                                    opt.is_correct
                                      ? 'bg-emerald-950/40 border-emerald-700/80 text-emerald-200'
                                      : 'bg-slate-950 border-slate-800 text-slate-300'
                                  }`}
                                >
                                  <div>
                                    <strong>{opt.label || opt.option}: </strong>
                                    <MathText text={opt.text} />
                                  </div>
                                  {opt.distractor_rationale && (
                                    <div className="text-[10px] text-rose-300/80 mt-1 italic">
                                      ⚠️ Bẫy sai lầm: {opt.distractor_rationale}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Lời giải 3 bước chuẩn RAG */}
                          {q.worked_solution_steps && q.worked_solution_steps.length > 0 && (
                            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 space-y-1.5 text-[11px]">
                              <strong className="text-indigo-300 block">Lời giải 3 bước sư phạm:</strong>
                              {q.worked_solution_steps.map((st, sidx) => {
                                const stepTitle = typeof st === 'object' ? st.step : `Bước ${sidx + 1}`;
                                const stepMath = typeof st === 'object' ? st.math || st.note : st;
                                return (
                                  <div key={sidx} className="text-slate-300 pl-2 border-l border-indigo-700/60">
                                    <strong className="text-white">{stepTitle}: </strong>
                                    <MathText text={stepMath} />
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div className="py-8 text-center text-slate-400">
                  Không có dữ liệu xem trước cho bài học này.
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-slate-800 bg-slate-950 flex items-center justify-between shrink-0">
              <span className="text-[11px] text-slate-400">
                Pedagogical RAG Engine • In-Memory BM25 • Khung CT GDPT 2018
              </span>
              <button
                type="button"
                onClick={() => setIsPreviewOpen(false)}
                className="px-4 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition"
              >
                Đóng Xem Trước
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
