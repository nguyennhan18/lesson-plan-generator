import React, { useState, useEffect, useRef } from 'react';
import HeaderNav from './shared/components/HeaderNav';
import PresentationDashboard from './features/dashboard/PresentationDashboard';
import OutlineWorkspace from './features/generation/OutlineWorkspace';
import PresentationStage from './features/presentation/PresentationStage';
import TeacherChatDock from './features/chat/TeacherChatDock';
import RightToolsDock from './features/geometry/RightToolsDock';
import LessonPlanScreen from './features/lesson-plan/LessonPlanScreen';
import SlideEditorScreen from './features/slide-editor/SlideEditorScreen';
import AnalyticsScreen from './features/analytics/AnalyticsScreen';
import {
  createLessonGenerationActions,
  defaultInitialOutline
} from './features/generation/lessonGenerationActions.js';
import { createDocumentExportActions } from './features/exports/documentExportActions.js';
import {
  loadSlideDeckFromBrowserMemory,
  saveSlideDeckToBrowserMemory
} from './shared/storage/slideDeckStorage.js';
import { usePresentationControls } from './features/presentation/usePresentationControls.js';

// ==============================================================================
// LessonAI-5512: Hệ Thống Sinh Giáo Án & Slide Động Bằng AI
// ==============================================================================

export default function App() {
  const [activeScreen, setActiveScreen] = useState('dashboard'); // 'dashboard' | 'outline' | 'presentation' | 'lesson-plan' | 'slide-editor' | 'analytics'
  const [currentSlide, setCurrentSlide] = useState(0);

  // Workflow Trạm 1 & Trạm 2 theo FRONTEND_ARCHITECTURE.md
  const [outline, setOutline] = useState(defaultInitialOutline);
  const [isGeneratingOutline, setIsGeneratingOutline] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState('gallery_monochrome');
  const [presentationConfig, setPresentationConfig] = useState({
    topic: 'Hệ trục tọa độ trong không gian Oxyz',
    subject: 'Toán học',
    grade: 12,
    num_slides: 8,
    class_proficiency: 'standard',
    use_rag: true,
    model_provider: 'gemini',
    model_id: 'gemini-2.5-flash',
    tone: 'academic',
    text_content: 'concise',
    aspect_ratio: '16:9'
  });

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

  const { handleStartPresentation, handleExitPresentation, toggleFullscreen } =
    usePresentationControls({
      slideDeck,
      activeScreen,
      isPresentationMode,
      isBlackout,
      setActiveScreen,
      setIsPresentationMode,
      setIsBlackout,
      setCurrentSlide,
      setIsLeftOpen,
      setIsRightOpen
    });

  const { handleGenerateOutline, handleGenerateFromOutline, handleGenerateFromAi } =
    createLessonGenerationActions({
      outline,
      presentationConfig,
      classProficiency,
      recommendedOutcome,
      setIsGeneratingOutline,
      setPresentationConfig,
      setOutline,
      setActiveScreen,
      setIsAiGenerating,
      setGenerationStep,
      setLessonPlan,
      setSlideDeck,
      setCurrentSlide,
      setPolyhedronType
    });

  const { handleExportDocx, handleExportPptx, handleExportDualPackage } =
    createDocumentExportActions({
      lessonPlan,
      slideDeck,
      currentSlide,
      threeCanvasCaptureRef
    });

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
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#ffffff] text-[#141414] select-none">
      {/* 1. Header Navigation (Tự động ẩn hoàn toàn khi vào Chế độ Trình Chiếu Toàn Màn Hình - Task 15.2) */}
      {!isPresentationMode && (
        <HeaderNav
          activeScreen={activeScreen}
          setActiveScreen={setActiveScreen}
          isLeftOpen={isLeftOpen}
          setIsLeftOpen={setIsLeftOpen}
          isRightOpen={isRightOpen}
          setIsRightOpen={setIsRightOpen}
          onToggleFullscreen={toggleFullscreen}
          onStartPresentation={handleStartPresentation}
          isPresentationMode={isPresentationMode}
          onExportDocx={handleExportDocx}
          onExportPptx={handleExportPptx}
          onExportDualPackage={handleExportDualPackage}
        />
      )}

      {/* Thông báo trạng thái đang gọi AI toàn màn hình */}
      {isAiGenerating && (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-4">
          <div className="w-14 h-14 border-4 border-[#141414] border-t-transparent rounded-full animate-spin"></div>
          <div className="text-center space-y-1">
            <h3 className="text-lg font-bold text-[#141414]">Gemini AI Đang Xử Lý Sư Phạm Chuyên Sâu</h3>
            <p className="text-sm text-[#0066ff] font-mono animate-pulse">{generationStep}</p>
            <p className="text-xs text-[#707070]">Đang tạo Kế hoạch 5512, đồng bộ SlideDeck và kết xuất Đồ thị Matplotlib...</p>
          </div>
        </div>
      )}

      {/* 2. Main Content Screens */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* TRẠM 1: DASHBOARD KHỞI TẠO BÀI GIẢNG (MẶC ĐỊNH) */}
        {activeScreen === 'dashboard' && (
          <PresentationDashboard
            onGenerateOutline={handleGenerateOutline}
            isGeneratingOutline={isGeneratingOutline}
            recentDeck={slideDeck}
            onOpenRecentDeck={() => setActiveScreen('presentation')}
            onNavigateScreen={setActiveScreen}
          />
        )}

        {/* TRẠM 2: DUYỆT DÀN Ý & BẢNG MÀU (OUTLINE & THEME WORKSPACE) */}
        {activeScreen === 'outline' && (
          <OutlineWorkspace
            outline={outline}
            setOutline={setOutline}
            onBackToDashboard={() => setActiveScreen('dashboard')}
            onGenerateFullPresentation={handleGenerateFromOutline}
            isGenerating={isAiGenerating}
            selectedTheme={selectedTheme}
            setSelectedTheme={setSelectedTheme}
          />
        )}

        {/* TRẠM 3: SÂN KHẤU TRÌNH CHIẾU GIẢNG DẠY (Ưu tiên số 1) */}
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
              theme={selectedTheme}
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
