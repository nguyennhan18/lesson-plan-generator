import React, { useState, useEffect } from 'react';
import HeaderNav from './components/HeaderNav';
import PresentationStage from './components/PresentationStage';
import TeacherChatDock from './components/TeacherChatDock';
import RightToolsDock from './components/RightToolsDock';
import LessonPlanScreen from './components/LessonPlanScreen';
import SlideEditorScreen from './components/SlideEditorScreen';
import AnalyticsScreen from './components/AnalyticsScreen';

export default function App() {
  const [activeScreen, setActiveScreen] = useState('presentation'); // 'presentation' | 'lesson-plan' | 'slide-editor' | 'analytics'
  const [currentSlide, setCurrentSlide] = useState(0);

  // Cockpit Dock States
  const [isLeftOpen, setIsLeftOpen] = useState(true);
  const [isRightOpen, setIsRightOpen] = useState(true);

  // 3D Geometry Shared Parameters
  const [polyhedronType, setPolyhedronType] = useState('cube');
  const [edgeLength, setEdgeLength] = useState(4.0);
  const [showHiddenLines, setShowHiddenLines] = useState(true);
  const [showVertexLabels, setShowVertexLabels] = useState(true);
  const [showAxes, setShowAxes] = useState(false);
  const [cameraPreset, setCameraPreset] = useState('iso');

  // Keyboard Shortcuts Handler
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger if user is typing in an input or textarea
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;

      if (e.key === 'c' || e.key === 'C') {
        setIsLeftOpen((prev) => !prev);
      } else if (e.key === 't' || e.key === 'T') {
        setIsRightOpen((prev) => !prev);
      } else if (e.key === 'ArrowLeft') {
        setCurrentSlide((prev) => Math.max(0, prev - 1));
      } else if (e.key === 'ArrowRight') {
        setCurrentSlide((prev) => Math.min(4, prev + 1));
      } else if (e.key === 'f' || e.key === 'F' || e.key === 'F5') {
        e.preventDefault();
        toggleFullscreen();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  const handleQuickGeom = (type) => {
    setActiveScreen('presentation');
    if (type === 'diagonal') {
      setCurrentSlide(1);
    } else if (type === 'altitude') {
      setCurrentSlide(2);
    } else if (type === 'cross_section') {
      setCurrentSlide(3);
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#050811] text-slate-100 overflow-hidden">
      {/* 1. Global Navigation Bar */}
      <HeaderNav
        activeScreen={activeScreen}
        setActiveScreen={setActiveScreen}
        isLeftOpen={isLeftOpen}
        setIsLeftOpen={setIsLeftOpen}
        isRightOpen={isRightOpen}
        setIsRightOpen={setIsRightOpen}
        onToggleFullscreen={toggleFullscreen}
      />

      {/* 2. Main Content Screens */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* SCREEN 1: PRESENTATION COCKPIT STAGE */}
        {activeScreen === 'presentation' && (
          <div className="w-full h-full flex overflow-hidden">
            {/* Left Teacher Chat Dock */}
            <TeacherChatDock
              isOpen={isLeftOpen}
              onToggle={() => setIsLeftOpen(false)}
              currentSlide={currentSlide}
            />

            {/* Center 16:9 Presentation Stage */}
            <PresentationStage
              currentSlide={currentSlide}
              setCurrentSlide={setCurrentSlide}
              isLeftOpen={isLeftOpen}
              isRightOpen={isRightOpen}
              onToggleLeft={() => setIsLeftOpen(true)}
              onToggleRight={() => setIsRightOpen(true)}
              polyhedronType={polyhedronType}
              edgeLength={edgeLength}
              showHiddenLines={showHiddenLines}
              showVertexLabels={showVertexLabels}
              showAxes={showAxes}
              cameraPreset={cameraPreset}
            />

            {/* Right Tools Dock */}
            <RightToolsDock
              isOpen={isRightOpen}
              onToggle={() => setIsRightOpen(false)}
              polyhedronType={polyhedronType}
              setPolyhedronType={setPolyhedronType}
              edgeLength={edgeLength}
              setEdgeLength={setEdgeLength}
              showHiddenLines={showHiddenLines}
              setShowHiddenLines={setShowHiddenLines}
              showVertexLabels={showVertexLabels}
              setShowVertexLabels={setShowVertexLabels}
              showAxes={showAxes}
              setShowAxes={setShowAxes}
              onCameraPreset={setCameraPreset}
              onQuickGeom={handleQuickGeom}
            />
          </div>
        )}

        {/* SCREEN 2: SOẠN KẾ HOẠCH BÀI DẠY 5512 */}
        {activeScreen === 'lesson-plan' && <LessonPlanScreen />}

        {/* SCREEN 3: XƯỞNG BIÊN TẬP SLIDE */}
        {activeScreen === 'slide-editor' && <SlideEditorScreen />}

        {/* SCREEN 4: PHÂN TÍCH LỚP HỌC */}
        {activeScreen === 'analytics' && <AnalyticsScreen />}
      </main>
    </div>
  );
}
