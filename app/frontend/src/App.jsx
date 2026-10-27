import React, { useState, useEffect, useRef } from 'react';
import HeaderNav from './components/HeaderNav';
import PresentationStage from './components/PresentationStage';
import TeacherChatDock from './components/TeacherChatDock';
import RightToolsDock from './components/RightToolsDock';
import LessonPlanScreen from './components/LessonPlanScreen';
import SlideEditorScreen from './components/SlideEditorScreen';
import AnalyticsScreen from './components/AnalyticsScreen';
import {
  loadSlideDeckFromBrowserMemory,
  saveSlideDeckToBrowserMemory
} from './utils/slideDeckStorage';
import {
  isFullscreenActive,
  requestPresentationFullscreen,
  exitPresentationFullscreen,
  togglePresentationFullscreen,
  onFullscreenChange
} from './utils/fullscreenHelper';

// ==============================================================================
// LessonAI-5512: Hệ Thống Sinh Giáo Án & Slide Động Bằng AI
// ==============================================================================

export default function App() {
  const [activeScreen, setActiveScreen] = useState('lesson-plan'); // 'presentation' | 'lesson-plan' | 'slide-editor' | 'analytics'
  const [currentSlide, setCurrentSlide] = useState(0);

  // Cockpit Dock States
  const [isLeftOpen, setIsLeftOpen] = useState(true);
  const [isRightOpen, setIsRightOpen] = useState(false);

  // 3D Geometry Shared Parameters & Parametric Modeling (Task 12.1)
  const [polyhedronType, setPolyhedronType] = useState('cube');
  const [edgeLength, setEdgeLength] = useState(4.0);
  const [geoHeight, setGeoHeight] = useState(4.0);      // Task 12.1: Chiều cao h (1 đến 10)
  const [geoBaseEdge, setGeoBaseEdge] = useState(4.0);  // Task 12.1: Cạnh đáy a (1 đến 8)
  const [showHiddenLines, setShowHiddenLines] = useState(true);
  const [showVertexLabels, setShowVertexLabels] = useState(true);
  const [showAxes, setShowAxes] = useState(true);
  const [cameraPreset, setCameraPreset] = useState('iso');
  const [showUnfoldedNet, setShowUnfoldedNet] = useState(false);

  // Task 14.1: Ref lưu trữ hàm capture3DSnapshot từ ThreeCanvas phục vụ xuất PPTX kèm ảnh chụp 3D
  const threeCanvasCaptureRef = useRef(null);

  // Task 15.1: Quản lý Chế độ Trình chiếu Toàn màn hình (Web Presentation Mode)
  const [isPresentationMode, setIsPresentationMode] = useState(false);

  // Task 15.3: Trạng thái Làm Tối Màn Hình (Blackout Mode - Phím B)
  const [isBlackout, setIsBlackout] = useState(false);

  useEffect(() => {
    const unsub = onFullscreenChange((active) => {
      setIsPresentationMode(active);
      if (!active) {
        setIsBlackout(false);
      }
    });
    return unsub;
  }, []);

  // ================= CENTRAL STATE (ĐỒNG BỘ 2 CHIỀU VỚI BỘ NHỚ TRÌNH DUYỆT - TASK 9.2) =================
  const [slideDeck, setSlideDeck] = useState(() =>
    loadSlideDeckFromBrowserMemory(null)
  );
  const [lessonPlan, setLessonPlan] = useState(null);

  // Task 9.2: Tự động đồng bộ cấu trúc Slide JSON vào bộ nhớ trình duyệt (sessionStorage) mỗi khi cập nhật
  useEffect(() => {
    saveSlideDeckToBrowserMemory(slideDeck);
  }, [slideDeck]);

  // State đồng bộ Phân tích Bảng điểm Z-Score -> Soạn Giáo Án 5512
  const [analyticsData, setAnalyticsData] = useState(null);
  const [classProficiency, setClassProficiency] = useState('standard');
  const [recommendedOutcome, setRecommendedOutcome] = useState('');

  // 3. Trạng thái Loading khi gọi Gemini AI
  const [isAiGenerating, setIsAiGenerating] = useState(false);
  const [generationStep, setGenerationStep] = useState('');

  const handleClassificationSuccess = (result) => {
    setAnalyticsData(result);
    if (result?.class_label) {
      setClassProficiency(result.class_label);
    }
    if (result?.target_outcome) {
      setRecommendedOutcome(result.target_outcome);
    }
  };

  const handleApplyAnalyticsToLessonPlan = (proficiencyLabel, outcomeText) => {
    if (proficiencyLabel) setClassProficiency(proficiencyLabel);
    if (outcomeText) setRecommendedOutcome(outcomeText);
    setActiveScreen('lesson-plan');
  };

  // Keyboard Shortcuts Handler (Task 15.3: ArrowLeft, ArrowRight, Space, PageUp, PageDown, Home, End, Escape, B, F5)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA', 'SELECT', 'MATH-FIELD'].includes(e.target.tagName)) return;

      const maxIdx = (slideDeck?.slides?.length || 1) - 1;

      // 1. Phím B hoặc b: Làm tối màn hình (Blackout mode)
      if (e.key === 'b' || e.key === 'B') {
        if (activeScreen === 'presentation' || isPresentationMode) {
          e.preventDefault();
          setIsBlackout((prev) => !prev);
          return;
        }
      }

      // Nếu màn hình đang ở chế độ Blackout, ấn phím điều hướng hoặc Escape sẽ tắt Blackout
      if (isBlackout) {
        if (e.key === 'Escape') {
          e.preventDefault();
          setIsBlackout(false);
          return;
        } else if (['ArrowLeft', 'ArrowRight', 'Space', ' ', 'PageUp', 'PageDown', 'Home', 'End', 'Enter'].includes(e.key)) {
          setIsBlackout(false);
        }
      }

      // 2. Phím Thoát Trình Chiếu (Escape)
      if (e.key === 'Escape') {
        if (isPresentationMode) {
          e.preventDefault();
          handleExitPresentation();
          return;
        }
      }

      // 3. Phím F / F5: Bật / Tắt Toàn Màn Hình
      if (e.key === 'f' || e.key === 'F' || e.key === 'F5') {
        e.preventDefault();
        toggleFullscreen();
        return;
      }

      // 4. Phím Lùi Slide (ArrowLeft, PageUp, hoặc Backspace khi không trong input)
      if (e.key === 'ArrowLeft' || e.key === 'PageUp' || (isPresentationMode && (e.key === 'p' || e.key === 'P' || e.key === 'Backspace'))) {
        e.preventDefault();
        setCurrentSlide((prev) => Math.max(0, prev - 1));
        return;
      }

      // 5. Phím Tiến Slide (ArrowRight, PageDown, Spacebar, hoặc 'n' khi presentation)
      if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ' || e.code === 'Space' || (isPresentationMode && (e.key === 'n' || e.key === 'N'))) {
        e.preventDefault();
        setCurrentSlide((prev) => Math.min(maxIdx, prev + 1));
        return;
      }

      // 6. Phím Home / End: Về slide đầu hoặc slide cuối
      if (e.key === 'Home') {
        e.preventDefault();
        setCurrentSlide(0);
        return;
      }
      if (e.key === 'End') {
        e.preventDefault();
        setCurrentSlide(maxIdx);
        return;
      }

      // 7. Phím C: Đóng/Mở Trợ Giảng AI (khi không ở Chế độ Trình chiếu)
      if ((e.key === 'c' || e.key === 'C') && !isPresentationMode) {
        setIsLeftOpen((prev) => !prev);
        return;
      }

      // 8. Phím T: Đóng/Mở Công Cụ 3D/Đồ Thị (khi không ở Chế độ Trình chiếu)
      if ((e.key === 't' || e.key === 'T') && !isPresentationMode) {
        setIsRightOpen((prev) => !prev);
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [slideDeck, isPresentationMode, isBlackout, activeScreen]);

  // Task 15.1: Xử lý kích hoạt Chế độ Trình Chiếu Toàn Màn Hình (Start Presentation)
  const handleStartPresentation = async () => {
    setActiveScreen('presentation');
    setIsPresentationMode(true);
    setIsBlackout(false);
    await requestPresentationFullscreen(document.documentElement);
  };

  const handleExitPresentation = async () => {
    setIsPresentationMode(false);
    setIsBlackout(false);
    if (isFullscreenActive()) {
      await exitPresentationFullscreen();
    }
  };

  const toggleFullscreen = async () => {
    if (!isFullscreenActive()) {
      await handleStartPresentation();
    } else {
      await handleExitPresentation();
    }
  };

  // ================= HÀM GỌI AI SINH THẬT TOÀN BỘ BÀI DẠY =================
  const handleGenerateFromAi = async (params) => {
    setIsAiGenerating(true);
    setGenerationStep('Đang gửi yêu cầu và kết nối Gemini AI...');

    try {
      // 1. Gọi API sinh Kế hoạch bài dạy 5512 thật
      setGenerationStep('Gemini đang phân tích sư phạm và soạn Kế hoạch 5512...');
      const planRes = await fetch('/api/v1/lesson-plan/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: params.topic,
          subject: params.subject,
          grade: parseInt(params.grade, 10),
          lesson_id: params.lesson_id || undefined,
          use_rag: params.use_rag !== undefined ? params.use_rag : true,
          class_proficiency: params.proficiency || 'standard',
          target_outcome: params.outcome || ''
        })
      });

      if (!planRes.ok) throw new Error(`Lỗi sinh giáo án: HTTP ${planRes.status}`);
      const planData = await planRes.json();
      setLessonPlan(planData.plan);

      // 2. Gọi API sinh SlideDeck đồng bộ với Kế hoạch vừa sinh
      setGenerationStep('Gemini đang thiết kế bộ Slide bài giảng tương ứng...');
      const slideRes = await fetch('/api/v1/slide/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: params.topic,
          subject: params.subject,
          grade: parseInt(params.grade, 10),
          lesson_id: params.lesson_id || undefined,
          use_rag: params.use_rag !== undefined ? params.use_rag : true,
          class_proficiency: params.proficiency || 'standard',
          target_outcome: params.outcome || '',
          plan: planData.plan
        })
      });

      if (!slideRes.ok) throw new Error(`Lỗi sinh slide: HTTP ${slideRes.status}`);
      const slideData = await slideRes.json();
      setSlideDeck(slideData);
      setCurrentSlide(0);

      // Tự động nhận diện mô hình 3D nếu chủ đề là Hình học không gian
      const lowerTopic = params.topic.toLowerCase();
      if (lowerTopic.includes('lập phương')) setPolyhedronType('cube');
      else if (lowerTopic.includes('chóp tam giác')) setPolyhedronType('triangular_pyramid');
      else if (lowerTopic.includes('chóp tứ giác') || lowerTopic.includes('s.abcd')) setPolyhedronType('rectangular_pyramid');

      // Chuyển thẳng về Màn hình Trình Chiếu để giáo viên bắt đầu tiết học
      setActiveScreen('presentation');
      alert(`Đã gọi Gemini AI sinh thành công Kế hoạch bài dạy và ${slideData.slides?.length || 0} slide cho chủ đề: "${params.topic}"!`);
    } catch (err) {
      console.error(err);
      alert(`Không thể sinh bài từ AI: ${err.message}. Vui lòng kiểm tra server FastAPI và GEMINI_API_KEY.`);
    } finally {
      setIsAiGenerating(false);
      setGenerationStep('');
    }
  };

  // ================= HÀM XUẤT FILE THẬT QUA FASTAPI =================
  const handleExportDocx = async () => {
    if (!lessonPlan) {
      alert("Chưa có dữ liệu Kế hoạch bài dạy để xuất Word. Hãy bấm 'Sinh Giáo Án Bằng AI' trước!");
      return;
    }
    try {
      // Gửi kèm SlideDeck để backend đồng bộ hóa câu hỏi củng cố và thiết bị dạy học (Task 19.1)
      const docxPayload = slideDeck
        ? { plan: lessonPlan, slide_deck: slideDeck }
        : lessonPlan;

      const res = await fetch('/api/v1/lesson-plan/export-docx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(docxPayload)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Giao_An_5512_${lessonPlan.lesson_title || 'Toan'}.docx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Lỗi khi tải file Word: " + e.message);
    }
  };

  const handleExportPptx = async () => {
    if (!slideDeck || !slideDeck.slides?.length) {
      alert("Chưa có dữ liệu Slide để xuất PowerPoint!");
      return;
    }

    // Task 14.2 & 18.2: Thu thập ảnh chụp mô hình không gian 3D dạng Base64 Data URL
    let snapshot3d = null;
    if (typeof threeCanvasCaptureRef.current === 'function') {
      try {
        snapshot3d = threeCanvasCaptureRef.current();
      } catch (err) {
        console.warn('[handleExportPptx] Không thể chụp snapshot qua ref:', err);
      }
    }
    if (!snapshot3d && typeof window !== 'undefined' && typeof window.__threeCanvasCaptureSnapshot === 'function') {
      try {
        snapshot3d = window.__threeCanvasCaptureSnapshot();
      } catch (err) {
        console.warn('[handleExportPptx] Không thể chụp snapshot qua window:', err);
      }
    }

    // Đóng gói chuỗi Base64 Data URL vào payload gửi tới backend
    const payloadDeck = {
      ...slideDeck,
      slides: (slideDeck.slides || []).map((s, idx) => {
        const slideCopy = { ...s };
        if (snapshot3d) {
          if (slideCopy.has_3d || slideCopy.polyhedron_type) {
            if (idx === currentSlide || !slideCopy.snapshot_3d_base64) {
              slideCopy.snapshot_3d_base64 = snapshot3d;
            }
          } else if (idx === currentSlide) {
            slideCopy.snapshot_3d_base64 = snapshot3d;
          }
        }
        return slideCopy;
      })
    };

    if (snapshot3d) {
      payloadDeck.snapshot_3d_base64 = snapshot3d;
    }

    try {
      const res = await fetch('/api/v1/lesson-plan/export-slide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadDeck)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Slide_${slideDeck.presentation_title || 'BaiGiang'}.pptx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Lỗi khi tải file PowerPoint: " + e.message);
    }
  };

  // Task 19.2: Tải Trọn Bộ Dual-Pack (.zip) đóng gói cả Kế hoạch bài dạy Word & Slide PowerPoint
  const handleExportDualPackage = async () => {
    if (!lessonPlan && (!slideDeck || !slideDeck.slides?.length)) {
      alert("Chưa có dữ liệu Kế hoạch bài dạy hoặc Slide để xuất trọn bộ ZIP. Vui lòng bấm 'Sinh Giáo Án Bằng AI' trước!");
      return;
    }

    // Thu thập ảnh chụp 3D WebGL (nếu có)
    let snapshot3d = null;
    if (typeof threeCanvasCaptureRef.current === 'function') {
      try {
        snapshot3d = threeCanvasCaptureRef.current();
      } catch (err) {
        console.warn('[handleExportDualPackage] Lỗi snapshot ref:', err);
      }
    }
    if (!snapshot3d && typeof window !== 'undefined' && typeof window.__threeCanvasCaptureSnapshot === 'function') {
      try {
        snapshot3d = window.__threeCanvasCaptureSnapshot();
      } catch (err) {
        console.warn('[handleExportDualPackage] Lỗi snapshot window:', err);
      }
    }

    const payloadDeck = slideDeck
      ? {
          ...slideDeck,
          slides: (slideDeck.slides || []).map((s, idx) => {
            const slideCopy = { ...s };
            if (snapshot3d) {
              if (slideCopy.has_3d || slideCopy.polyhedron_type) {
                if (idx === currentSlide || !slideCopy.snapshot_3d_base64) {
                  slideCopy.snapshot_3d_base64 = snapshot3d;
                }
              } else if (idx === currentSlide) {
                slideCopy.snapshot_3d_base64 = snapshot3d;
              }
            }
            return slideCopy;
          }),
          snapshot_3d_base64: snapshot3d || slideDeck.snapshot_3d_base64
        }
      : null;

    const dualPayload = {
      plan: lessonPlan,
      slide_deck: payloadDeck
    };

    try {
      const res = await fetch('/api/v1/lesson-plan/export-dual-package', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dualPayload)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const title = lessonPlan?.lesson_title || slideDeck?.presentation_title || 'LessonAI_5512';
      const cleanTitle = title.replace(/\s+/g, '_');
      a.download = `Tron_Bo_Giao_An_Va_Slide_${cleanTitle}.zip`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Lỗi khi tải gói kép ZIP: " + e.message);
    }
  };

  // Áp dụng Live Patch từ Trợ giảng AI vào Slide hiện tại (Hỗ trợ cả chuẩn SlidePatchProposal của Backend & mẫu cũ)
  const handleApplySlidePatch = (patch) => {
    if (!patch) return false;
    const targetIdx =
      patch.target_slide_index !== undefined && patch.target_slide_index !== null
        ? patch.target_slide_index
        : currentSlide;
    const updatedSlides = [...(slideDeck.slides || [])];

    if (updatedSlides[targetIdx]) {
      const target = { ...updatedSlides[targetIdx] };

      const newTitle = patch.title || patch.updated_title;
      if (newTitle) target.title = newTitle;

      const newBullets = patch.bullet_points || patch.updated_bullet_points;
      if (Array.isArray(newBullets) && newBullets.length > 0) {
        target.bullet_points = newBullets;
      }

      const newLatex = patch.main_definition_latex || patch.updated_latex;
      if (newLatex) target.main_definition_latex = newLatex;

      const newTeacherNote = patch.teacher_note || patch.updated_teacher_note;
      if (newTeacherNote) target.teacher_note = newTeacherNote;

      // Xử lý khi bản vá bổ sung Câu hỏi Trắc nghiệm (QuizData từ Backend)
      if (patch.quiz) {
        target.layout = 'QUIZ_OPTION';
        if (patch.quiz.question) {
          target.bullet_points = [patch.quiz.question];
        }
        if (Array.isArray(patch.quiz.options) && patch.quiz.options.length > 0) {
          const correctLetter = String(patch.quiz.correct_answer || 'A').trim().toUpperCase();
          target.quiz_options = patch.quiz.options.map((optStr, idx) => {
            const labels = ['A', 'B', 'C', 'D'];
            const label = labels[idx] || String(idx + 1);
            const cleanText = String(optStr).replace(/^[A-D]\.\s*/, '');
            const isCorrect = label === correctLetter;
            return {
              label,
              text: cleanText,
              is_correct: isCorrect,
              distractor_rationale: isCorrect
                ? (patch.quiz.explanation || 'Đáp án chính xác.')
                : 'Phương án gây nhiễu, học sinh cần kiểm tra lại công thức.'
            };
          });
        }
      } else if (patch.new_quiz_option) {
        target.quiz_options = [...(target.quiz_options || []), patch.new_quiz_option];
      }

      updatedSlides[targetIdx] = target;
      setSlideDeck({ ...slideDeck, slides: updatedSlides });
      setCurrentSlide(targetIdx);
      return true;
    }
    return false;
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#050811] text-slate-100 select-none">
      {/* 1. Header Navigation (Tự động ẩn hoàn toàn khi vào Chế độ Trình Chiếu Toàn Màn Hình - Task 15.2) */}
      {!isPresentationMode && (
        <HeaderNav
          activeScreen={activeScreen}
          setActiveScreen={setActiveScreen}
          currentSlide={currentSlide}
          totalSlides={slideDeck?.slides?.length || 1}
          presentationTitle={slideDeck?.presentation_title || 'LessonAI-5512'}
          onExportDocx={handleExportDocx}
          onExportPptx={handleExportPptx}
          onExportDualPackage={handleExportDualPackage}
          onToggleFullscreen={toggleFullscreen}
          onStartPresentation={handleStartPresentation}
          isPresentationMode={isPresentationMode}
          isAiGenerating={isAiGenerating}
          generationStep={generationStep}
        />
      )}

      {/* Thông báo trạng thái đang gọi AI toàn màn hình */}
      {isAiGenerating && (
        <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex flex-col items-center justify-center gap-4">
          <div className="w-14 h-14 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <div className="text-center space-y-1">
            <h3 className="text-lg font-bold text-white">Gemini AI Đang Xử Lý Sư Phạm Chuyên Sâu</h3>
            <p className="text-sm text-cyan-400 font-mono animate-pulse">{generationStep}</p>
            <p className="text-xs text-slate-500">Đang tạo Kế hoạch 5512, đồng bộ SlideDeck và kết xuất Đồ thị Matplotlib...</p>
          </div>
        </div>
      )}

      {/* 2. Main Content Screens */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* MÀN HÌNH 1: SÂN KHẤU TRÌNH CHIẾU GIẢNG DẠY (Ưu tiên số 1) */}
        {activeScreen === 'presentation' && (
          <div className={`w-full h-full flex overflow-hidden ${isPresentationMode ? 'bg-black' : ''}`}>
            {/* Ẩn bong bóng chat và dock trợ giảng AI khi trình chiếu - Task 15.2 */}
            {!isPresentationMode && (
              <TeacherChatDock
                isOpen={isLeftOpen}
                onToggle={() => setIsLeftOpen(false)}
                currentSlide={currentSlide}
                slideDeck={slideDeck}
                onApplyPatch={handleApplySlidePatch}
              />
            )}

            <PresentationStage
              slideDeck={slideDeck}
              setSlideDeck={setSlideDeck}
              currentSlide={currentSlide}
              setCurrentSlide={setCurrentSlide}
              isLeftOpen={isLeftOpen}
              isRightOpen={isRightOpen}
              onToggleLeft={() => setIsLeftOpen(true)}
              onToggleRight={() => setIsRightOpen(true)}
              polyhedronType={polyhedronType}
              setPolyhedronType={setPolyhedronType}
              edgeLength={edgeLength}
              geoHeight={geoHeight}
              setGeoHeight={setGeoHeight}
              geoBaseEdge={geoBaseEdge}
              setGeoBaseEdge={setGeoBaseEdge}
              showHiddenLines={showHiddenLines}
              setShowHiddenLines={setShowHiddenLines}
              showVertexLabels={showVertexLabels}
              setShowVertexLabels={setShowVertexLabels}
              showAxes={showAxes}
              setShowAxes={setShowAxes}
              cameraPreset={cameraPreset}
              onCameraPreset={setCameraPreset}
              showUnfoldedNet={showUnfoldedNet}
              setShowUnfoldedNet={setShowUnfoldedNet}
              onNavigateScreen={setActiveScreen}
              onCaptureReady={(fn) => {
                threeCanvasCaptureRef.current = fn;
              }}
              isPresentationMode={isPresentationMode}
              onExitPresentation={handleExitPresentation}
              isBlackout={isBlackout}
              onToggleBlackout={setIsBlackout}
            />

            {/* Ẩn sidebar công cụ 3D/đồ thị khi trình chiếu - Task 15.2 */}
            {!isPresentationMode && (
              <RightToolsDock
                isOpen={isRightOpen}
                onToggle={() => setIsRightOpen(false)}
                polyhedronType={polyhedronType}
                setPolyhedronType={setPolyhedronType}
                edgeLength={edgeLength}
                setEdgeLength={setEdgeLength}
                geoHeight={geoHeight}
                setGeoHeight={setGeoHeight}
                geoBaseEdge={geoBaseEdge}
                setGeoBaseEdge={setGeoBaseEdge}
                showHiddenLines={showHiddenLines}
                setShowHiddenLines={setShowHiddenLines}
                showVertexLabels={showVertexLabels}
                setShowVertexLabels={setShowVertexLabels}
                showAxes={showAxes}
                setShowAxes={setShowAxes}
                cameraPreset={cameraPreset}
                onCameraPreset={setCameraPreset}
                showUnfoldedNet={showUnfoldedNet}
                setShowUnfoldedNet={setShowUnfoldedNet}
              />
            )}
          </div>
        )}

        {/* MÀN HÌNH 2: SOẠN KẾ HOẠCH BÀI DẠY 5512 (Kèm Danh mục Bài SGK & Nút Gọi AI Thật) */}
        {activeScreen === 'lesson-plan' && (
          <LessonPlanScreen
            lessonPlan={lessonPlan}
            isGenerating={isAiGenerating}
            onGenerateFromAi={handleGenerateFromAi}
            onExportDocx={handleExportDocx}
            onExportPptx={handleExportPptx}
            onExportDualPackage={handleExportDualPackage}
            externalProficiency={classProficiency}
            externalOutcome={recommendedOutcome}
          />
        )}

        {/* MÀN HÌNH 3: XƯỞNG BIÊN TẬP SLIDE (Kết nối SlideDeck thật & Xuất PPTX thật) */}
        {activeScreen === 'slide-editor' && (
          <SlideEditorScreen
            slideDeck={slideDeck}
            setSlideDeck={setSlideDeck}
            onExportPptx={handleExportPptx}
            onExportDocx={handleExportDocx}
            onExportDualPackage={handleExportDualPackage}
          />
        )}

        {/* MÀN HÌNH 4: PHÂN TÍCH LỚP HỌC (Z-Score & Bảng điểm thực) */}
        {activeScreen === 'analytics' && (
          <AnalyticsScreen
            analyticsData={analyticsData}
            onClassificationSuccess={handleClassificationSuccess}
            onApplyToLessonPlan={handleApplyAnalyticsToLessonPlan}
          />
        )}
      </main>
    </div>
  );
}
