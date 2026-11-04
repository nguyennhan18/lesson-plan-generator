import React, { useState, useEffect, useRef } from 'react';
import {restoreProject,saveProject,listProjects,loadProject,blankProject,normalizeDeck,mutateDeck,mutatePlan} from './shared/storage/projectStore.js';
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
  createLessonGenerationActions
} from './features/generation/lessonGenerationActions.js';
import { createDocumentExportActions } from './features/exports/documentExportActions.js';
import { usePresentationControls } from './features/presentation/usePresentationControls.js';

// ==============================================================================
// LessonAI-5512: Hệ Thống Sinh Giáo Án & Slide Động Bằng AI
// ==============================================================================

export default function App() {
  const [activeScreen, setActiveScreen] = useState('dashboard'); // 'dashboard' | 'outline' | 'presentation' | 'lesson-plan' | 'slide-editor' | 'analytics'
  const [currentSlide, setCurrentSlide] = useState(0);

  // Workflow Trạm 1 & Trạm 2 theo FRONTEND_ARCHITECTURE.md
  const [outline, setOutline] = useState(null);
  const [isGeneratingOutline, setIsGeneratingOutline] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState('gallery_monochrome');
  const [presentationConfig, setPresentationConfig] = useState({
    topic: '',
    subject: 'Toán học',
    grade: 12,
    num_slides: 8,
    class_proficiency: 'standard',
    use_rag: true,
    model_provider: 'gemini',
    model_id: null,
    tone: 'academic',
    text_content: 'concise',
    aspect_ratio: '16:9'
  });

  // Cockpit Dock States
  const [isLeftOpen, setIsLeftOpen] = useState(true);
  const [isRightOpen, setIsRightOpen] = useState(false);

  // 3D Geometry Shared Parameters & Parametric Modeling (Task 12.1)
  const [polyhedronType, setPolyhedronType] = useState(null);
  const [edgeLength, setEdgeLength] = useState(null);
  const [geoHeight, setGeoHeight] = useState(null);      // Task 12.1: Chiều cao h (1 đến 10)
  const [geoBaseEdge, setGeoBaseEdge] = useState(null);  // Task 12.1: Cạnh đáy a (1 đến 8)
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
  const [slideDeck, setDeckState] = useState(null);
  const [lessonPlan, setPlanState] = useState(null);
  const setLessonPlan = update => setPlanState(previous => mutatePlan(previous, typeof update === 'function' ? update(previous) : update));
  const [editorDirty,setEditorDirty]=useState(false);
  useEffect(()=>{
    if(!editorDirty)return;
    const handler=event=>{event.preventDefault();event.returnValue='';};
    window.addEventListener('beforeunload',handler);
    return()=>window.removeEventListener('beforeunload',handler);
  },[editorDirty]);
  const [projectId,setProjectId]=useState(null), [projects,setProjects]=useState([]), [storageReady,setStorageReady]=useState(false), [saveError,setSaveError]=useState('');
  const projectMeta=useRef({});
  const generationEpoch=useRef(0), saveQueue=useRef(Promise.resolve()), saveFailure=useRef(null);
  const deckRef=useRef(slideDeck);deckRef.current=slideDeck;
  const setSlideDeck=update=>setDeckState(previous=>{const value=typeof update==='function'?update(previous):update;return mutateDeck(previous,value?{...value,project_id:projectId||value.project_id}:value);});
  const restore=project=>{
    projectMeta.current=project;
    setStorageReady(true);
    generationEpoch.current++;
    setProjectId(project.project_id);setDeckState(project.deck?normalizeDeck(project.deck):null);setPlanState(project.plan||null);setOutline(project.outline||null);
    setPresentationConfig(project.config||{});setClassProficiency(project.classProficiency||'standard');setRecommendedOutcome(project.recommendedOutcome||'');setAnalyticsData(project.analytics||null);setCurrentSlide(0);setPolyhedronType(null);setGeoHeight(null);setGeoBaseEdge(null);setSaveError(project.migration_review||'');
  };
  useEffect(()=>{
    let active=true;
    restoreProject().then(project=>{if(active)restore(project);}).catch(e=>{if(active){setStorageReady(false);setSaveError(`Không nạp được dự án: ${e.message}. Tự lưu đang tạm dừng; hãy phục hồi JSON hoặc chọn tạo dự án mới.`);}});
    return ()=>{active=false;};
  },[]);

  // State đồng bộ Phân tích Bảng điểm Z-Score -> Soạn Giáo Án 5512
  const [analyticsData, setAnalyticsData] = useState(null);
  const [classProficiency, setClassProficiency] = useState('standard');
  const [recommendedOutcome, setRecommendedOutcome] = useState('');

  // 3. Trạng thái Loading khi gọi Gemini AI
  const [isAiGenerating, setIsAiGenerating] = useState(false);
  const [generationStep, setGenerationStep] = useState('');
  const currentProject={...projectMeta.current,schema_version:2,project_id:projectId,title:slideDeck?.presentation_title||outline?.title||presentationConfig.topic||'',deck:slideDeck,plan:lessonPlan,outline,config:presentationConfig,analytics:analyticsData,classProficiency,recommendedOutcome};
  const currentProjectRef=useRef(currentProject);currentProjectRef.current=currentProject;
  useEffect(()=>{
    if(!storageReady||!projectId)return;
    const snapshot=structuredClone(currentProject);
    saveQueue.current=saveQueue.current.catch(()=>{}).then(()=>saveProject(snapshot)).then(()=>{
      saveFailure.current=null;
      if(currentProjectRef.current.project_id===snapshot.project_id){localStorage.setItem('lessonai-active-project',snapshot.project_id);setSaveError(snapshot.migration_review||'');}
      return listProjects();
    }).then(setProjects).catch(e=>{saveFailure.current=e;setSaveError(`Chưa lưu: ${e.message}. Hãy tải JSON dự phòng.`);});
  },[storageReady,projectId,slideDeck,lessonPlan,outline,presentationConfig,analyticsData,classProficiency,recommendedOutcome]);
  const switchProject=async id=>{if(editorDirty){setSaveError("Hãy lưu slide đang sửa trước khi đổi dự án.");return;}try{await saveQueue.current;if(saveFailure.current)throw saveFailure.current;const project=id?await loadProject(id):blankProject();restore(project);setActiveScreen('dashboard');}catch(e){setSaveError(e.message);}};
  const downloadProject=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(currentProject,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='lesson-project.json';link.click();URL.revokeObjectURL(url);};


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
      setPolyhedronType,
      projectId, generationEpoch
    });

  const { handleExportDocx, handleExportPptx, handleExportDualPackage } =
    createDocumentExportActions({
      lessonPlan,
      hasPendingEdits:editorDirty,
      slideDeck,
      currentSlide,
      threeCanvasCaptureRef
    });

  const handleApplySlidePatch=(updated,base)=>{
    if(deckRef.current?.deck_id!==base.deck_id||deckRef.current?.revision!==base.revision)return false;
    const next=normalizeDeck(updated);deckRef.current=next;setDeckState(next);return true;
  };
  if(!storageReady&&!saveError)return <p className="p-8">Đang nạp dự án…</p>;

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#ffffff] text-[#141414] select-none">
      {!isPresentationMode&&<div className="flex gap-3 p-2 items-center border-b text-sm">
        <button disabled={isAiGenerating||isGeneratingOutline} onClick={()=>switchProject(null)}>Dự án mới</button>
        <select aria-label="Chọn dự án" value={projectId||''} disabled={isAiGenerating||isGeneratingOutline} onChange={e=>switchProject(e.target.value)}><option value={projectId||''}>{currentProject.title||'Dự án chưa đặt tên'}</option>{projects.filter(p=>p.project_id!==projectId).map(p=><option key={p.project_id} value={p.project_id}>{p.title||'Dự án chưa đặt tên'}</option>)}</select>
        <button onClick={downloadProject}>Tải JSON dự phòng</button>
        <label>Phục hồi JSON <input type="file" accept=".json" className="w-48" onChange={async e=>{try{const file=e.target.files?.[0];if(!file)return;const p=JSON.parse(await file.text());if(p.schema_version!==2||!p.project_id)throw new Error('Dự án không đúng định dạng');if(p.deck)p.deck=normalizeDeck(p.deck);await saveQueue.current;if(saveFailure.current)throw saveFailure.current;restore(p);}catch(e){setSaveError(e.message);}}}/></label>
        {saveError&&<span role="alert" className="text-red-700">{saveError}</span>}
      </div>}
      {/* 1. Header Navigation (Tự động ẩn hoàn toàn khi vào Chế độ Trình Chiếu Toàn Màn Hình - Task 15.2) */}
      {!isPresentationMode && (
        <HeaderNav
          activeScreen={activeScreen}
          setActiveScreen={screen=>{if(editorDirty){setSaveError("Hãy lưu slide đang sửa trước khi chuyển màn hình.");return;}setActiveScreen(screen);}}
          isLeftOpen={isLeftOpen}
          setIsLeftOpen={setIsLeftOpen}
          isRightOpen={isRightOpen}
          setIsRightOpen={setIsRightOpen}
          onToggleFullscreen={toggleFullscreen}
          onStartPresentation={()=>{if(editorDirty){setSaveError("Hãy lưu slide đang sửa trước khi trình chiếu.");return;}handleStartPresentation();}}
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
            <h3 className="text-lg font-bold text-[#141414]">Đang xử lý yêu cầu bài giảng</h3>
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
                key={slideDeck?.deck_id||projectId}
                isOpen={isLeftOpen}
                onToggle={() => setIsLeftOpen(false)}
                currentSlide={currentSlide}
                slideDeck={slideDeck}
                onApplyPatch={handleApplySlidePatch}
              />
            )}

            <PresentationStage
              key={slideDeck?.deck_id||projectId}
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
            key={projectId}
            lessonPlan={lessonPlan}
            onChangePlan={(next, expected) => setLessonPlan(previous => currentProjectRef.current.project_id === projectId && JSON.stringify(previous) === JSON.stringify(expected) ? next : previous)}
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
            onDirtyChange={setEditorDirty}
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
