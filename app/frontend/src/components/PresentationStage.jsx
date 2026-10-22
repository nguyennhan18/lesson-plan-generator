import React, { useState, useEffect, useMemo, useRef } from 'react';
import { ChevronLeft, ChevronRight, MessageSquare, Wrench, HelpCircle, Check, Eye, LineChart, Box, FileText, Edit3, AlertTriangle, Layers, Compass, Sparkles, BookOpen, Sliders, MoveVertical, Maximize2, Minimize2, RotateCcw, Calculator, Zap, Tag, Moon } from 'lucide-react';
import ThreeCanvas from './ThreeCanvas';
import UnfoldedNetViewer from './UnfoldedNetViewer';
import FunctionPlotter from './FunctionPlotter';
import MathText from './MathText';
import MathLiveModal from './MathLiveModal';
import PedagogicalWarningModal from './PedagogicalWarningModal';
import { updateSlideFormulaInDeck, loadSlideDrawingsFromStorage, saveSlideDrawingsToStorage } from '../utils/slideDeckStorage';
import { auditSlideDeckLocal, auditSlideDeckRemote } from '../utils/pedagogicalLinterClient';
import { computeParametricCoordinatesLocal, fetchParametricCoordinatesRemote } from '../utils/geometryClient';
import PresentationFloatingBar from './PresentationFloatingBar';
import InteractiveQuizCard from './InteractiveQuizCard';
import AnnotationCanvas from './AnnotationCanvas';
import WhiteboardOverlay from './WhiteboardOverlay';

export default function PresentationStage({
  slideDeck,
  setSlideDeck,
  currentSlide = 0,
  setCurrentSlide,
  isLeftOpen,
  isRightOpen,
  onToggleLeft,
  onToggleRight,
  polyhedronType,
  setPolyhedronType,
  edgeLength,
  geoHeight,
  setGeoHeight,
  geoBaseEdge,
  setGeoBaseEdge,
  showHiddenLines,
  setShowHiddenLines,
  showVertexLabels,
  setShowVertexLabels,
  showAxes,
  setShowAxes,
  cameraPreset,
  onCameraPreset,
  showUnfoldedNet = false,
  setShowUnfoldedNet,
  onSwitchSample,
  // Task 14.1: Cầu nối Snapshot 3D WebGL
  onCaptureReady,
  // Task 15.2: Chế độ Trình chiếu Toàn màn hình 16:9 Cinema
  isPresentationMode = false,
  onExitPresentation,
  // Task 15.3: Trạng thái Làm tối màn hình (Blackout Mode - Phím B)
  isBlackout = false,
  onToggleBlackout
}) {
  const slides = slideDeck?.slides || [];
  const slide = slides[currentSlide] || {};

  // Trạng thái bình chọn Quiz tương tác
  const [votedOption, setVotedOption] = useState(null);
  const [votes, setVotes] = useState({ A: 28, B: 7, C: 4, D: 3 });
  const [showExplanation, setShowExplanation] = useState(false);

  // Chế độ hiển thị trực quan bên phải: 'auto' | '2d' | '3d' | 'pptx'
  const [visualMode, setVisualMode] = useState('auto');

  // Task 17.1 & Task 17.3 & Task 17.4: Quản lý Hệ thống Bút vẽ Chú thích, Undo/Redo & Lưu trữ theo Slide
  const deckId = slideDeck?.id || 'default_deck';
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const [currentTool, setCurrentTool] = useState('pen'); // 'pen' | 'highlighter' | 'eraser'
  const [drawingColor, setDrawingColor] = useState('#ef4444');
  const [brushSize, setBrushSize] = useState(3);

  // Khởi tạo slideDrawingsMap từ bộ nhớ lưu trữ browser (sessionStorage)
  const [slideDrawingsMap, setSlideDrawingsMap] = useState(() => loadSlideDrawingsFromStorage(deckId));
  const [slideUndoStacks, setSlideUndoStacks] = useState({});
  const [slideRedoStacks, setSlideRedoStacks] = useState({});

  // Tự động đồng bộ slideDrawingsMap vào storage mỗi khi có nét vẽ mới
  useEffect(() => {
    saveSlideDrawingsToStorage(slideDrawingsMap, deckId);
  }, [slideDrawingsMap, deckId]);

  // Task 17.4: Chế độ Bảng Viết Toàn Màn Hình (Whiteboard / Blackboard Mode)
  const [isWhiteboardOpen, setIsWhiteboardOpen] = useState(false);
  const [whiteboardStrokes, setWhiteboardStrokes] = useState([]);
  const [whiteboardUndoStack, setWhiteboardUndoStack] = useState([]);
  const [whiteboardRedoStack, setWhiteboardRedoStack] = useState([]);

  const currentStrokes = slideDrawingsMap[currentSlide] || [];
  const currentUndoStack = slideUndoStacks[currentSlide] || [];
  const currentRedoStack = slideRedoStacks[currentSlide] || [];

  const handleStrokesChange = (newStrokes, previousStrokes) => {
    const prevState = previousStrokes !== undefined ? previousStrokes : (slideDrawingsMap[currentSlide] || []);
    setSlideUndoStacks((prev) => ({
      ...prev,
      [currentSlide]: [...(prev[currentSlide] || []), prevState]
    }));
    setSlideRedoStacks((prev) => ({
      ...prev,
      [currentSlide]: []
    }));
    setSlideDrawingsMap((prev) => ({
      ...prev,
      [currentSlide]: newStrokes
    }));
  };

  const handleUndoStrokes = useCallback(() => {
    setSlideUndoStacks((prevUndo) => {
      const currentUndo = prevUndo[currentSlide] || [];
      if (currentUndo.length === 0) return prevUndo;

      const previousState = currentUndo[currentUndo.length - 1];
      const remainingUndo = currentUndo.slice(0, currentUndo.length - 1);

      setSlideRedoStacks((prevRedo) => ({
        ...prevRedo,
        [currentSlide]: [...(prevRedo[currentSlide] || []), slideDrawingsMap[currentSlide] || []]
      }));

      setSlideDrawingsMap((prevMap) => ({
        ...prevMap,
        [currentSlide]: previousState
      }));

      return {
        ...prevUndo,
        [currentSlide]: remainingUndo
      };
    });
  }, [currentSlide, slideDrawingsMap]);

  const handleRedoStrokes = useCallback(() => {
    setSlideRedoStacks((prevRedo) => {
      const currentRedo = prevRedo[currentSlide] || [];
      if (currentRedo.length === 0) return prevRedo;

      const nextState = currentRedo[currentRedo.length - 1];
      const remainingRedo = currentRedo.slice(0, currentRedo.length - 1);

      setSlideUndoStacks((prevUndo) => ({
        ...prevUndo,
        [currentSlide]: [...(prevUndo[currentSlide] || []), slideDrawingsMap[currentSlide] || []]
      }));

      setSlideDrawingsMap((prevMap) => ({
        ...prevMap,
        [currentSlide]: nextState
      }));

      return {
        ...prevRedo,
        [currentSlide]: remainingRedo
      };
    });
  }, [currentSlide, slideDrawingsMap]);

  const handleClearAllStrokes = useCallback(() => {
    const currentList = slideDrawingsMap[currentSlide] || [];
    if (currentList.length === 0) return;

    setSlideUndoStacks((prev) => ({
      ...prev,
      [currentSlide]: [...(prev[currentSlide] || []), currentList]
    }));
    setSlideRedoStacks((prev) => ({
      ...prev,
      [currentSlide]: []
    }));
    setSlideDrawingsMap((prev) => ({
      ...prev,
      [currentSlide]: []
    }));
  }, [currentSlide, slideDrawingsMap]);

  // Quản lý Undo / Redo / Clear riêng biệt cho Bảng Viết Phụ (Whiteboard)
  const handleWhiteboardStrokesChange = (newStrokes, previousStrokes) => {
    const prevState = previousStrokes !== undefined ? previousStrokes : whiteboardStrokes;
    setWhiteboardUndoStack((prev) => [...prev, prevState]);
    setWhiteboardRedoStack([]);
    setWhiteboardStrokes(newStrokes);
  };

  const handleWhiteboardUndo = useCallback(() => {
    setWhiteboardUndoStack((prevUndo) => {
      if (prevUndo.length === 0) return prevUndo;
      const prevState = prevUndo[prevUndo.length - 1];
      const remainingUndo = prevUndo.slice(0, prevUndo.length - 1);
      setWhiteboardRedoStack((prevRedo) => [...prevRedo, whiteboardStrokes]);
      setWhiteboardStrokes(prevState);
      return remainingUndo;
    });
  }, [whiteboardStrokes]);

  const handleWhiteboardRedo = useCallback(() => {
    setWhiteboardRedoStack((prevRedo) => {
      if (prevRedo.length === 0) return prevRedo;
      const nextState = prevRedo[prevRedo.length - 1];
      const remainingRedo = prevRedo.slice(0, prevRedo.length - 1);
      setWhiteboardUndoStack((prevUndo) => [...prevUndo, whiteboardStrokes]);
      setWhiteboardStrokes(nextState);
      return remainingRedo;
    });
  }, [whiteboardStrokes]);

  const handleWhiteboardClear = useCallback(() => {
    if (whiteboardStrokes.length === 0) return;
    setWhiteboardUndoStack((prev) => [...prev, whiteboardStrokes]);
    setWhiteboardRedoStack([]);
    setWhiteboardStrokes([]);
  }, [whiteboardStrokes]);

  // Task 17.2, 17.3, 17.4: Phím tắt Bút vẽ (P), Dạ quang (H), Tẩy (E), Bảng phụ (W), Hoàn tác (Ctrl+Z), Làm lại (Ctrl+Y)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA', 'SELECT', 'MATH-FIELD'].includes(e.target.tagName)) return;

      // Undo: Ctrl+Z / Cmd+Z (không kèm Shift)
      if ((e.ctrlKey || e.metaKey) && (e.key === 'z' || e.key === 'Z') && !e.shiftKey) {
        e.preventDefault();
        if (isWhiteboardOpen) {
          handleWhiteboardUndo();
        } else {
          handleUndoStrokes();
        }
        return;
      }

      // Redo: Ctrl+Y / Cmd+Shift+Z / Ctrl+Shift+Z
      if (
        ((e.ctrlKey || e.metaKey) && (e.key === 'y' || e.key === 'Y')) ||
        ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'z' || e.key === 'Z'))
      ) {
        e.preventDefault();
        if (isWhiteboardOpen) {
          handleWhiteboardRedo();
        } else {
          handleRedoStrokes();
        }
        return;
      }

      // Bật/tắt Bảng phụ Whiteboard: Phím W
      if (e.key === 'w' || e.key === 'W') {
        e.preventDefault();
        setIsWhiteboardOpen((prev) => !prev);
        return;
      }

      if (e.key === 'p' || e.key === 'P') {
        e.preventDefault();
        setIsDrawingMode((prev) => {
          if (!prev) setCurrentTool('pen');
          return !prev;
        });
      } else if (e.key === 'h' || e.key === 'H') {
        e.preventDefault();
        setIsDrawingMode(true);
        setCurrentTool('highlighter');
      } else if (e.key === 'e' || e.key === 'E') {
        e.preventDefault();
        setIsDrawingMode(true);
        setCurrentTool('eraser');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleUndoStrokes, handleRedoStrokes, isWhiteboardOpen, handleWhiteboardUndo, handleWhiteboardRedo]);

  // Task 8.2: Trạng thái Modal Popup chỉnh sửa công thức Toán (MathLive) khi click đúp
  const [mathModalState, setMathModalState] = useState({
    isOpen: false,
    targetField: 'main_definition_latex', // 'main_definition_latex' | 'bullet_point'
    bulletIndex: null,
    initialLatex: '',
    fieldLabel: ''
  });

  // Task 9.3: Trạng thái đánh dấu hiệu ứng Highlight xác nhận vị trí công thức vừa được render lại bằng KaTeX
  const [recentlyUpdatedFormula, setRecentlyUpdatedFormula] = useState(null);

  // Task 13.3: Quản lý chế độ xem Song Song 3D + Hình Khai Triển Phẳng 2D (Unfolded Net)
  const [localShowUnfoldedNet, setLocalShowUnfoldedNet] = useState(false);
  const activeShowUnfoldedNet = typeof showUnfoldedNet === 'boolean' ? showUnfoldedNet : localShowUnfoldedNet;
  const handleToggleUnfoldedNet = setShowUnfoldedNet || setLocalShowUnfoldedNet;

  // Task 12.1 & 12.2: Quản lý tham số hình học động & Tọa độ đỉnh chóp S(0, 0, h)
  const [localHeight, setLocalHeight] = useState(4.0);
  const [localBaseEdge, setLocalBaseEdge] = useState(4.0);
  const activeHeight = typeof geoHeight === 'number' ? geoHeight : localHeight;
  const activeBaseEdge = typeof geoBaseEdge === 'number' ? geoBaseEdge : localBaseEdge;
  const handleHeightChange = setGeoHeight || setLocalHeight;
  const handleBaseEdgeChange = setGeoBaseEdge || setLocalBaseEdge;

  // Tính toán tọa độ và các đại lượng hình học theo thời gian thực (0ms phản hồi tức thì)
  const parametricMetrics = useMemo(() => {
    return computeParametricCoordinatesLocal(polyhedronType, activeHeight, activeBaseEdge);
  }, [polyhedronType, activeHeight, activeBaseEdge]);

  // Task 14.1: Quản lý hàm chụp snapshot khung hình 3D từ ThreeCanvas
  const threeCaptureRef = useRef(null);
  const handleCaptureReady = (captureFn) => {
    threeCaptureRef.current = captureFn;
    if (typeof onCaptureReady === 'function') {
      onCaptureReady(captureFn);
    }
  };

  // Task 12.4: ID điều phối requestAnimationFrame cho thanh trượt h và a (60 FPS mượt mà)
  const rafHeightRef = useRef(null);
  const rafBaseRef = useRef(null);

  // Bắt sự kiện oninput của slider và điều phối render mượt mà 60 FPS qua requestAnimationFrame
  const handleHeightInput = (val) => {
    const num = parseFloat(val);
    if (!isNaN(num)) {
      if (rafHeightRef.current) {
        cancelAnimationFrame(rafHeightRef.current);
      }
      rafHeightRef.current = requestAnimationFrame(() => {
        handleHeightChange?.(num);
        fetchParametricCoordinatesRemote(polyhedronType, num, activeBaseEdge);
      });
    }
  };

  const handleBaseEdgeInput = (val) => {
    const num = parseFloat(val);
    if (!isNaN(num)) {
      if (rafBaseRef.current) {
        cancelAnimationFrame(rafBaseRef.current);
      }
      rafBaseRef.current = requestAnimationFrame(() => {
        handleBaseEdgeChange?.(num);
        fetchParametricCoordinatesRemote(polyhedronType, activeHeight, num);
      });
    }
  };

  // Dọn dẹp requestAnimationFrame khi component unmount
  useEffect(() => {
    return () => {
      if (rafHeightRef.current) cancelAnimationFrame(rafHeightRef.current);
      if (rafBaseRef.current) cancelAnimationFrame(rafBaseRef.current);
    };
  }, []);

  // Task 12.3: Công thức và chuỗi KaTeX thể tích động tự động thay số theo slider
  const volumeLatex = useMemo(() => {
    const aVal = Number(activeBaseEdge).toFixed(1);
    const hVal = Number(activeHeight).toFixed(1);
    const sBaseVal = Number(parametricMetrics.measurements.base_area).toFixed(1);
    const volVal = Number(parametricMetrics.measurements.volume).toFixed(1);

    if (polyhedronType === 'prism_triangle') {
      return {
        name: "Lăng Trụ Đứng Tam Giác ABC.A'B'C'",
        generalFormula: "V = S_{\\text{đáy}} \\cdot h",
        substFormula: `V = ${sBaseVal} \\cdot ${hVal} = ${volVal}`
      };
    } else if (polyhedronType === 'cube') {
      return {
        name: "Hình Lập Phương ABCD.A'B'C'D'",
        generalFormula: "V = a^3",
        substFormula: `V = ${aVal}^3 = ${volVal}`
      };
    } else if (polyhedronType === 'pyramid_triangle') {
      return {
        name: "Hình Chóp Tam Giác S.ABC (SA \\bot \\text{đáy})",
        generalFormula: "V = \\frac{1}{3} S_{\\text{đáy}} \\cdot h",
        substFormula: `V = \\frac{1}{3} \\cdot ${sBaseVal} \\cdot ${hVal} = ${volVal}`
      };
    } else {
      // Default: pyramid_square S.ABCD
      return {
        name: "Hình Chóp Tứ Giác S.ABCD (SA \\bot \\text{đáy})",
        generalFormula: "V = \\frac{1}{3} S_{\\text{đáy}} \\cdot h = \\frac{1}{3} a^2 h",
        substFormula: `V = \\frac{1}{3} \\cdot ${sBaseVal} \\cdot ${hVal} = ${volVal}`
      };
    }
  }, [polyhedronType, activeBaseEdge, activeHeight, parametricMetrics]);

  // Task 10.4: Trạng thái Bộ lọc Kiểm duyệt Sư phạm (Danh sách Cảnh báo vàng — Human-in-the-Loop)
  const [deckWarnings, setDeckWarnings] = useState(() => auditSlideDeckLocal(slideDeck).warnings);
  const [dismissedWarningKeys, setDismissedWarningKeys] = useState([]);
  const [isWarningModalOpen, setIsWarningModalOpen] = useState(false);

  // Đồng bộ kiểm duyệt tức thì (Local 0ms) + bất đồng bộ qua Backend SymPy (/api/v1/validation/audit-deck)
  useEffect(() => {
    let isCancelled = false;
    const localAudit = auditSlideDeckLocal(slideDeck);
    setDeckWarnings(localAudit.warnings);

    auditSlideDeckRemote(slideDeck).then((remoteAudit) => {
      if (!isCancelled && remoteAudit && Array.isArray(remoteAudit.warnings)) {
        setDeckWarnings(remoteAudit.warnings);
      }
    });

    return () => {
      isCancelled = true;
    };
  }, [slideDeck]);

  const getWarningKey = (w) => `${w.slide_index}::${w.field || ''}::${w.detected_token || w.message}`;

  const activeWarnings = useMemo(
    () => deckWarnings.filter((w) => !dismissedWarningKeys.includes(getWarningKey(w))),
    [deckWarnings, dismissedWarningKeys]
  );

  const currentSlideWarnings = useMemo(
    () => activeWarnings.filter((w) => Number(w.slide_index) === currentSlide + 1),
    [activeWarnings, currentSlide]
  );

  const handleDismissWarning = (warningItem) => {
    const key = getWarningKey(warningItem);
    setDismissedWarningKeys((prev) => (prev.includes(key) ? prev : [...prev, key]));
  };

  // Mở trình chỉnh sửa để Giáo viên TỰ SỬA (tuyệt đối KHÔNG tự ý ghi đè bài của GV)
  const handleOpenManualEditFromWarning = (warningItem) => {
    const targetIdx = Math.max(0, Number(warningItem.slide_index || 1) - 1);
    if (setCurrentSlide && targetIdx !== currentSlide) {
      setCurrentSlide(targetIdx);
    }
    const targetSlideObj = slides[targetIdx] || {};
    const field = String(warningItem.field || '');
    setIsWarningModalOpen(false);

    if (field === 'main_definition_latex') {
      handleOpenMathModal(
        'main_definition_latex',
        targetSlideObj.main_definition_latex || '',
        `Công thức trọng tâm (Slide ${targetIdx + 1})`
      );
      return;
    }

    const bulletMatch = field.match(/^bullet_points\[(\d+)\]/);
    if (bulletMatch) {
      const bIdx = Number(bulletMatch[1]);
      const bulletVal = targetSlideObj.bullet_points?.[bIdx] || '';
      handleOpenMathModal(
        'bullet_point',
        bulletVal,
        `Ý trọng tâm #${bIdx + 1} (Slide ${targetIdx + 1})`,
        bIdx
      );
    }
  };

  const handleOpenMathModal = (targetField, initialValue, fieldLabel, bulletIndex = null) => {
    setMathModalState({
      isOpen: true,
      targetField,
      bulletIndex,
      initialLatex: initialValue || '',
      fieldLabel
    });
  };

  // Task 9.2 & Task 9.3: Cập nhật chuỗi LaTeX mới vào Slide JSON và kích hoạt re-render KaTeX kèm hiệu ứng Highlight
  const handleSaveMathModal = (formattedLatex, rawExpandedLatex = '') => {
    if (!setSlideDeck || !slides[currentSlide]) return;
    const updatedDeck = updateSlideFormulaInDeck(slideDeck, {
      slideIndex: currentSlide,
      targetField: mathModalState.targetField,
      bulletIndex: mathModalState.bulletIndex,
      formattedLatex,
      rawExpandedLatex
    });
    setSlideDeck(updatedDeck);

    // Kích hoạt hiệu ứng highlight xác nhận công thức vừa được render lại bằng KaTeX
    setRecentlyUpdatedFormula({
      slideIndex: currentSlide,
      targetField: mathModalState.targetField,
      bulletIndex: mathModalState.bulletIndex,
      timestamp: Date.now()
    });
  };

  // Tự động tắt hiệu ứng highlight sau 2.4 giây
  useEffect(() => {
    if (!recentlyUpdatedFormula) return;
    const timer = setTimeout(() => {
      setRecentlyUpdatedFormula(null);
    }, 2400);
    return () => clearTimeout(timer);
  }, [recentlyUpdatedFormula]);

  const isFormulaRecentlyUpdated = (targetField, bulletIndex = null) => {
    if (!recentlyUpdatedFormula) return false;
    if (recentlyUpdatedFormula.slideIndex !== currentSlide) return false;
    if (recentlyUpdatedFormula.targetField !== targetField) return false;
    if (targetField === 'bullet_point' && recentlyUpdatedFormula.bulletIndex !== bulletIndex) {
      return false;
    }
    return true;
  };

  // Reset bình chọn khi chuyển slide
  useEffect(() => {
    setVotedOption(null);
    setShowExplanation(false);
  }, [currentSlide]);

  const handleVote = (label) => {
    setVotedOption(label);
    setVotes(prev => ({ ...prev, [label]: (prev[label] || 0) + 1 }));
    setShowExplanation(true);
  };

  const totalVotes = Object.values(votes).reduce((a, b) => a + b, 0);

  // Task 11.1: Thuật toán nhận diện ngữ cảnh và Bố cục Trình chiếu Động chuẩn PowerPoint
  const fullContextText = `${slideDeck?.presentation_title || ''} ${slide.title || ''} ${slide.bullet_points?.join(' ') || ''}`.toLowerCase();

  // Kiểm tra đồ thị 2D thực sự
  const hasValidChartSpec = Boolean(
    slide.chart_spec &&
    slide.chart_spec.kind &&
    slide.chart_spec.kind !== 'none' &&
    slide.chart_spec.expression &&
    String(slide.chart_spec.expression).trim().length > 0
  );
  const hasChartData = Boolean(slide.has_chart === true || slide.chart_image_base64 || hasValidChartSpec);

  // Kiểm tra hình học không gian 3D thực sự
  const isExplicit3D = slide.has_3d === true || Boolean(slide.polyhedron_type);
  const isContextual3D = /không gian|lập phương|khối chóp|hình chóp|lăng trụ|tứ diện|s\.abc|s\.abcd|mặt phẳng đáy|thiết diện/i.test(fullContextText);
  const is3DGeometry = isExplicit3D || (isContextual3D && !hasChartData);

  // Tự động nhận diện loại khối đa diện của slide (S.ABC, S.ABCD, Lập phương, Lăng trụ)
  const targetPolyhedronFromSlide = useMemo(() => {
    if (slide.polyhedron_type) return slide.polyhedron_type;
    if (fullContextText.includes('s.abcd') || fullContextText.includes('chóp tứ giác')) return 'pyramid_square';
    if (fullContextText.includes('s.abc') || fullContextText.includes('chóp tam giác') || fullContextText.includes('tứ diện')) return 'pyramid_triangle';
    if (fullContextText.includes('lăng trụ')) return 'prism_triangle';
    if (fullContextText.includes('lập phương')) return 'cube';
    return polyhedronType || 'pyramid_square';
  }, [slide.polyhedron_type, fullContextText, polyhedronType]);

  // Tự động đồng bộ loại khối đa diện vào State khi chuyển slide
  useEffect(() => {
    if (setPolyhedronType && is3DGeometry && targetPolyhedronFromSlide && targetPolyhedronFromSlide !== polyhedronType) {
      setPolyhedronType(targetPolyhedronFromSlide);
    }
  }, [currentSlide, targetPolyhedronFromSlide, is3DGeometry]);

  // Quyết định chế độ hiển thị hiệu dụng (auto | 2d | 3d | pptx | text)
  let effectiveVisual = visualMode;
  if (visualMode === 'auto') {
    if (is3DGeometry) {
      effectiveVisual = '3d';
    } else if (hasChartData) {
      effectiveVisual = '2d';
    } else {
      effectiveVisual = 'text'; // Slide lý thuyết thuần túy -> Toàn màn hình 100%
    }
  }

  // Quyết định xem có chia cột hiển thị Panel trực quan bên phải hay không
  // CHỈ hiển thị panel bên phải khi:
  // 1. Chế độ xem thủ công 2D/3D được bật, HOẶC
  // 2. Chế độ 'auto' và slide thuộc layout 'IMAGE_TEXT' có đồ thị/3D thực sự, HOẶC slide có cờ has_3d/has_chart
  const isExplicitVisualMode = visualMode === '2d' || visualMode === '3d';
  const isVisualEligible = (slide.layout === 'IMAGE_TEXT' || slide.has_3d === true || hasChartData) && (hasChartData || is3DGeometry);
  const shouldShowVisualPanel = visualMode === 'pptx' ? false : (isExplicitVisualMode || (visualMode === 'auto' && isVisualEligible));

  // Xác định badge hoạt động sư phạm
  const activityTag = slide.activity_type || `HOẠT ĐỘNG ${currentSlide + 1}`;
  const isQuizLayout = slide.layout === 'QUIZ_OPTION' || Boolean(slide.quiz_options?.length);

  return (
    <div
      className={`flex flex-col justify-between overflow-hidden relative ${
        isPresentationMode
          ? 'fixed inset-0 z-50 bg-black flex items-center justify-center p-0 md:p-3 w-screen h-screen select-none'
          : 'flex-1 h-full p-3 bg-slate-950/40'
      }`}
    >
      {/* 1. Thanh Top Điều Khiển Nhanh (Ẩn hoàn toàn trong Chế độ Trình Chiếu - Task 15.2) */}
      {!isPresentationMode && (
        <div className="flex items-center justify-between mb-2 shrink-0">
          <div className="flex items-center gap-2">
            {!isLeftOpen && (
              <button
                onClick={onToggleLeft}
                className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-cyan-400 border border-cyan-800/80 rounded-lg text-xs flex items-center gap-1.5 shadow-lg transition"
                title="Mở Trợ Giảng AI Co-pilot (Phím C)"
              >
                <MessageSquare size={13} />
                <span>Hiện Trợ Giảng AI (C)</span>
              </button>
            )}

            {/* Nút chuyển nhanh bài mẫu (Quick Topic Switcher) */}
            {onSwitchSample && (
              <div className="hidden lg:flex items-center gap-1 bg-slate-900/90 border border-slate-800 rounded-lg p-0.5 text-[11px]">
                <span className="text-slate-400 px-1.5">Mẫu:</span>
                <button
                  onClick={() => onSwitchSample('quadratic')}
                  className={`px-2 py-0.5 rounded transition ${
                    fullContextText.includes('bậc hai') || fullContextText.includes('phương trình')
                      ? 'bg-cyan-600 text-white font-semibold'
                      : 'text-slate-300 hover:text-white'
                  }`}
                >
                  PT Bậc Hai (Toán 10)
                </button>
                <button
                  onClick={() => onSwitchSample('cube')}
                  className={`px-2 py-0.5 rounded transition ${
                    fullContextText.includes('lập phương')
                      ? 'bg-cyan-600 text-white font-semibold'
                      : 'text-slate-300 hover:text-white'
                  }`}
                >
                  Hình Lập Phương (Toán 11)
                </button>
              </div>
            )}
          </div>

          <div className="text-[11px] text-slate-400 tracking-wide font-mono hidden md:flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>SÂN KHẤU 16:9 • TOÁN HỌC CHUẨN KaTeX • CÔNG VĂN 5512</span>
          </div>

          <div>
            {!isRightOpen && (
              <button
                onClick={onToggleRight}
                className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-amber-400 border border-amber-800/80 rounded-lg text-xs flex items-center gap-1.5 shadow-lg transition"
                title="Mở Công Cụ 3D/Đồ Thị (Phím T)"
              >
                <span>Công Cụ Giảng Dạy (T)</span>
                <Wrench size={13} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* 2. SÂN KHẤU CHÍNH 16:9 CINEMA (Không gian trọng tâm của Giáo viên - Task 15.2) */}
      <div
        className={`flex items-center justify-center min-h-0 ${
          isPresentationMode ? 'w-full h-full' : 'flex-1'
        }`}
      >
        <div
          className={`glass-panel flex flex-col justify-between shadow-2xl relative overflow-hidden bg-[#090d1c] transition-all duration-300 ${
            isPresentationMode
              ? 'w-full aspect-[16/9] max-h-screen rounded-none md:rounded-2xl p-4 md:p-6 lg:p-7 border border-slate-800/90'
              : 'w-full h-full max-w-6xl aspect-video rounded-2xl p-5 border-slate-800 bg-[#090d1c]/90'
          }`}
          style={
            isPresentationMode
              ? {
                  maxWidth: 'calc(100vh * 16 / 9)',
                  maxHeight: '100vh'
                }
              : undefined
          }
        >

          {/* Header của Slide */}
          <div className="pb-2.5 border-b border-slate-800/80 flex items-center justify-between shrink-0">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] md:text-xs font-bold px-2.5 py-0.5 rounded border border-cyan-800 bg-cyan-950/70 text-cyan-300 uppercase tracking-wider">
                  {activityTag}
                </span>
                {isPresentationMode && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-700/80 bg-emerald-950/80 text-emerald-300 uppercase tracking-wider flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    16:9 Cinema
                  </span>
                )}
              </div>
              <h2
                className={`font-bold text-white flex items-center gap-2 ${
                  isPresentationMode ? 'text-lg md:text-2xl lg:text-3xl mt-1.5' : 'text-base md:text-xl mt-1'
                }`}
              >
                <MathText text={slide.title || "Tiêu đề bài giảng"} />
              </h2>
            </div>

            {/* Thanh chuyển đổi chế độ trực quan (Visual Mode Switcher) & Cảnh báo Sư phạm ⚠️ */}
            <div className="flex items-center gap-2">
              {currentSlideWarnings.length > 0 && (
                <button
                  type="button"
                  onClick={() => setIsWarningModalOpen(true)}
                  className="px-2.5 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400 text-amber-300 text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-amber-950/50 animate-pulse transition"
                  title="Phát hiện cảnh báo chính tả hoặc công thức trên Slide này — Nhấn để xem gợi ý (Không tự động ghi đè)"
                >
                  <AlertTriangle size={14} className="text-amber-400" />
                  <span>⚠️ {currentSlideWarnings.length} Cảnh báo</span>
                </button>
              )}

              <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs">
                <button
                  onClick={() => setVisualMode('auto')}
                  className={`px-2.5 py-1 rounded-md flex items-center gap-1 transition ${
                    visualMode === 'auto'
                      ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                  title="Chế độ Tự động: Tự động điều chỉnh bố cục Toàn màn hình hoặc Chia đôi 2D/3D theo đúng chuẩn PowerPoint"
                >
                  <Eye size={13} />
                  <span className="hidden sm:inline">Tự Động (Chuẩn PPT)</span>
                </button>
                <button
                  onClick={() => setVisualMode('2d')}
                  className={`px-2 py-1 rounded-md flex items-center gap-1 transition ${
                    visualMode === '2d'
                      ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                  title="Ép hiển thị đồ thị hàm số / Parabol 2D"
                >
                  <LineChart size={13} />
                  <span className="hidden sm:inline">2D</span>
                </button>
                <button
                  onClick={() => setVisualMode('3d')}
                  className={`px-2 py-1 rounded-md flex items-center gap-1 transition ${
                    visualMode === '3d'
                      ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                  title="Ép hiển thị khối hình học không gian 3D"
                >
                  <Box size={13} />
                  <span className="hidden sm:inline">3D</span>
                </button>
                <button
                  onClick={() => setVisualMode('pptx')}
                  className={`px-2.5 py-1 rounded-md flex items-center gap-1 transition ${
                    visualMode === 'pptx'
                      ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                  title="Xem trước bản in PowerPoint 1:1"
                >
                  <FileText size={13} />
                  <span className="hidden sm:inline">Bản In PPTX</span>
                </button>
              </div>

              <div className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-400 shadow-inner">
                Slide {currentSlide + 1} / {slides.length || 1}
              </div>

              {/* Task 15.3: Nút Tối Màn Hình (Blackout Mode - Phím B) */}
              {isPresentationMode && (
                <button
                  onClick={() => onToggleBlackout?.(!isBlackout)}
                  className={`px-2.5 py-1 rounded-lg border text-xs font-semibold flex items-center gap-1.5 transition shadow-sm ml-1 ${
                    isBlackout
                      ? 'bg-amber-500/30 border-amber-500 text-amber-200'
                      : 'bg-slate-800/90 hover:bg-slate-700 border-slate-700 text-slate-300'
                  }`}
                  title="Làm tối màn hình để học sinh tập trung vào lời giảng (Phím B)"
                >
                  <Moon size={13} />
                  <span className="hidden sm:inline">Tối màn hình</span>
                  <kbd className="hidden md:inline px-1 py-0.2 bg-slate-900 border border-slate-700 rounded text-[9px] font-mono">B</kbd>
                </button>
              )}

              {/* Task 15.2: Nút Thoát Trình Chiếu Toàn Màn Hình */}
              {isPresentationMode && onExitPresentation && (
                <button
                  onClick={onExitPresentation}
                  className="px-2.5 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/60 text-rose-300 text-xs font-semibold flex items-center gap-1.5 transition shadow-sm ml-1"
                  title="Thoát Chế độ Trình chiếu (Phím Esc hoặc F5)"
                >
                  <Minimize2 size={13} />
                  <span className="hidden sm:inline">Thoát</span>
                  <kbd className="hidden md:inline px-1 py-0.2 bg-rose-950/80 border border-rose-700/60 rounded text-[9px] font-mono">Esc</kbd>
                </button>
              )}
            </div>
          </div>

          {/* Body của Slide */}
          <div className="flex-1 my-2.5 overflow-y-auto">
            {/* TRƯỜNG HỢP A: BẢN IN PPTX 1:1 PREVIEW (Xóa bỏ hoàn toàn bất nhất Web vs File tải về) */}
            {effectiveVisual === 'pptx' ? (
              <div className="h-full w-full bg-slate-100 rounded-xl p-6 text-slate-900 flex flex-col justify-between shadow-2xl border-4 border-slate-300">
                {/* Header PPTX */}
                <div className="border-b-2 border-blue-900 pb-2 flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold text-blue-900">
                      <MathText text={slide.title || "Tiêu đề bài học"} />
                    </h3>
                    <p className="text-xs text-slate-600">{activityTag} • Chương trình GDPT 2018</p>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-blue-100 text-blue-900 font-bold text-xs border border-blue-300">
                    PowerPoint Native 16:9
                  </span>
                </div>

                {/* Nội dung chia 2 cột như trong file PPTX */}
                <div className="grid grid-cols-12 gap-5 my-3 items-center flex-1">
                  <div className="col-span-7 space-y-3">
                    <ul className="space-y-2 text-sm text-slate-800 font-serif">
                      {(slide.bullet_points || []).map((pt, i) => {
                        const isUpdated = isFormulaRecentlyUpdated('bullet_point', i);
                        return (
                          <li
                            key={i}
                            onDoubleClick={() =>
                              handleOpenMathModal(
                                'bullet_point',
                                pt,
                                `Ý trọng tâm #${i + 1} (Slide ${currentSlide + 1})`,
                                i
                              )
                            }
                            title="Nhấp đúp (Double-Click) để chỉnh sửa công thức bằng MathLive"
                            className={`flex items-start gap-2 leading-relaxed rounded px-1.5 py-0.5 cursor-pointer transition-all duration-500 ${
                              isUpdated
                                ? 'bg-emerald-100 ring-2 ring-emerald-500 shadow-sm'
                                : 'hover:bg-blue-100/70'
                            }`}
                          >
                            <span className="text-blue-700 font-bold">•</span>
                            <span className="flex-1"><MathText text={pt} /></span>
                            {isUpdated && (
                              <span className="text-[10px] font-sans font-bold text-emerald-700 bg-emerald-200/80 px-1.5 py-0.5 rounded shrink-0">
                                ✓ Đã cập nhật KaTeX
                              </span>
                            )}
                          </li>
                        );
                      })}
                    </ul>

                    {slide.main_definition_latex && (
                      <div
                        onDoubleClick={() =>
                          handleOpenMathModal(
                            'main_definition_latex',
                            slide.main_definition_latex,
                            `Công thức trọng tâm (Slide ${currentSlide + 1})`
                          )
                        }
                        title="Nhấp đúp (Double-Click) để chỉnh sửa công thức bằng MathLive"
                        className={`p-3 border-l-4 rounded text-blue-950 font-bold text-base my-2 cursor-pointer transition-all duration-500 relative group ${
                          isFormulaRecentlyUpdated('main_definition_latex')
                            ? 'bg-emerald-50 border-emerald-600 ring-2 ring-emerald-500 shadow-md'
                            : 'bg-blue-50 hover:bg-blue-100/80 border-blue-800'
                        }`}
                      >
                        <MathText text={slide.main_definition_latex} block={true} />
                        {isFormulaRecentlyUpdated('main_definition_latex') ? (
                          <span className="text-[10px] font-sans font-bold text-emerald-700 bg-emerald-200/90 px-2 py-0.5 rounded absolute top-1 right-2">
                            ✓ Đã cập nhật KaTeX
                          </span>
                        ) : (
                          <span className="opacity-0 group-hover:opacity-100 transition text-[10px] font-normal text-blue-700 absolute top-1 right-2">
                            Click đúp để sửa MathLive
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Cột đồ thị ảnh Matplotlib hoặc công thức */}
                  <div className="col-span-5 flex flex-col items-center justify-center p-3 bg-white rounded-lg border border-slate-200 shadow-sm h-full max-h-[260px]">
                    {slide.chart_image_base64 ? (
                      <img
                        src={slide.chart_image_base64}
                        alt="Đồ thị Matplotlib Native"
                        className="max-h-[220px] object-contain rounded"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center text-center p-4 bg-slate-50 rounded">
                        <LineChart size={36} className="text-blue-500 mb-2" />
                        <span className="text-xs font-bold text-slate-700">Đồ thị Matplotlib Native</span>
                        <p className="text-[11px] text-slate-500 mt-1">
                          {slide.chart_spec?.chart_title || "Sẽ tự động xuất đồ thị khi tải file .pptx"}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer PPTX */}
                <div className="border-t border-slate-300 pt-2 flex items-center justify-between text-xs text-slate-500">
                  <span>Kế hoạch bài dạy môn Toán THPT - Công văn 5512/BGDĐT</span>
                  <span className="font-semibold text-blue-900">Trang {currentSlide + 1} / {slides.length}</span>
                </div>
              </div>
            ) : isQuizLayout ? (
              /* TRƯỜNG HỢP B: QUIZ TRẮC NGHIỆM TƯƠNG TÁC (TASK 16.1) */
              <div className="h-full flex flex-col justify-between">
                <InteractiveQuizCard
                  slide={slide}
                  currentSlide={currentSlide}
                  votedOption={votedOption}
                  onVote={handleVote}
                  votes={votes}
                  onResetVotes={() => {
                    setVotedOption(null);
                    setShowExplanation(false);
                  }}
                  showExplanation={showExplanation}
                  onToggleExplanation={() => setShowExplanation((prev) => !prev)}
                  isPresentationMode={isPresentationMode}
                />

                {/* Hộp thoại phân tích bẫy sai lầm sư phạm (Distractor Rationale) */}
                {showExplanation && (
                  <div className="p-3 mt-2 rounded-xl bg-slate-900/95 border border-slate-700 text-xs space-y-1">
                    <strong className="text-amber-400 flex items-center gap-1.5 font-bold">
                      Phân Tích Sư Phạm & Bẫy Sai Lầm (Distractor Analysis):
                    </strong>
                    <div className="text-slate-300 leading-relaxed space-y-1">
                      {slide.quiz_options?.map((opt) => (
                        <div key={opt.label}>
                          <span className="font-bold text-cyan-300">{opt.label}:</span> <MathText text={opt.distractor_rationale || opt.text} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : shouldShowVisualPanel ? (
              /* TRƯỜNG HỢP C1: BỐ CỤC CHIA ĐÔI IMAGE_TEXT (LÝ THUYẾT BÊN TRÁI + KHUNG 2D/3D BÊN PHẢI) */
              <div className="grid grid-cols-12 gap-5 h-full items-center">
                {/* Cột trái: Nội dung kiến thức & Công thức KaTeX */}
                <div className="col-span-12 lg:col-span-6 space-y-3 text-xs leading-relaxed">
                  <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <strong className="text-cyan-400 block text-xs font-semibold uppercase tracking-wider">
                        Trọng tâm kiến thức:
                      </strong>
                      <span className="text-[10px] text-slate-500">
                        Nhấp đúp vào dòng bất kỳ để sửa Toán
                      </span>
                    </div>
                    <ul className="space-y-2 text-slate-200">
                      {(slide.bullet_points || []).map((pt, i) => {
                        const isUpdated = isFormulaRecentlyUpdated('bullet_point', i);
                        return (
                          <li
                            key={i}
                            onDoubleClick={() =>
                              handleOpenMathModal(
                                'bullet_point',
                                pt,
                                `Ý trọng tâm #${i + 1} (Slide ${currentSlide + 1})`,
                                i
                              )
                            }
                            title="Nhấp đúp (Double-Click) để chỉnh sửa công thức bằng MathLive"
                            className={`flex items-start gap-2 leading-relaxed rounded-lg px-2 py-1 border cursor-pointer transition-all duration-500 group ${
                              isUpdated
                                ? 'bg-emerald-950/40 border-emerald-400 ring-2 ring-emerald-500/60 shadow-lg shadow-emerald-950/50'
                                : 'hover:bg-slate-800/80 border-transparent hover:border-cyan-800/50'
                            }`}
                          >
                            <span className="text-cyan-400 font-bold shrink-0">•</span>
                            <span className="flex-1"><MathText text={pt} /></span>
                            {isUpdated ? (
                              <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 border border-emerald-400/60 text-emerald-300 text-[10px] font-semibold shrink-0 flex items-center gap-1">
                                <Check size={10} /> Đã cập nhật KaTeX
                              </span>
                            ) : (
                              <Edit3 size={12} className="text-cyan-400 opacity-0 group-hover:opacity-100 shrink-0 mt-1 transition" />
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  </div>

                  {/* Hiển thị công thức toán trọng tâm dạng KaTeX chuẩn */}
                  {slide.main_definition_latex && (
                    <div
                      onDoubleClick={() =>
                        handleOpenMathModal(
                          'main_definition_latex',
                          slide.main_definition_latex,
                          `Công thức trọng tâm (Slide ${currentSlide + 1})`
                        )
                      }
                      title="Nhấp đúp (Double-Click) để mở trình gõ công thức trực quan MathLive"
                      className={`p-3.5 rounded-xl border font-mono text-cyan-300 text-center text-sm md:text-base font-bold shadow-lg cursor-pointer transition-all duration-500 relative group ${
                        isFormulaRecentlyUpdated('main_definition_latex')
                          ? 'bg-emerald-950/50 border-emerald-400 ring-2 ring-emerald-400/80 shadow-emerald-950/70'
                          : 'bg-gradient-to-r from-cyan-950/40 via-indigo-950/30 to-slate-950 border-cyan-800/60 hover:border-cyan-400'
                      }`}
                    >
                      <MathText text={slide.main_definition_latex} block={true} />
                      <div className="mt-1.5 flex items-center justify-center gap-1 text-[10px] font-sans font-normal">
                        {isFormulaRecentlyUpdated('main_definition_latex') ? (
                          <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-400/60 text-emerald-300 font-semibold flex items-center gap-1">
                            <Check size={11} /> Đã cập nhật & kết xuất KaTeX mới
                          </span>
                        ) : (
                          <span className="text-cyan-400/80 group-hover:text-cyan-300 flex items-center gap-1">
                            <Edit3 size={11} />
                            <span>Nhấp đúp (Double-Click) để sửa công thức bằng MathLive</span>
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Lời thoại gợi ý giảng dạy cho giáo viên */}
                  {slide.teacher_note && (
                    <div className="p-2.5 rounded-xl bg-amber-950/20 border border-amber-900/40 text-[11px] text-amber-300 flex items-start gap-2">
                      <span>
                        <strong>Lời nhắc sư phạm:</strong> <MathText text={slide.teacher_note} />
                      </span>
                    </div>
                  )}

                  {/* TASK 12.3: BẢNG THÔNG SỐ ĐỘNG BÊN CẠNH HÌNH & CÔNG THỨC THỂ TÍCH TỰ ĐỘNG NHẢY SỐ */}
                  {effectiveVisual === '3d' && (
                    <div className="p-3.5 rounded-xl bg-gradient-to-br from-slate-900/90 via-slate-950/90 to-indigo-950/40 border border-cyan-800/50 shadow-lg space-y-2.5">
                      {/* Tiêu đề & Tên khối */}
                      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                        <div className="flex items-center gap-1.5">
                          <Calculator size={14} className="text-cyan-400" />
                          <span className="text-[11px] font-bold text-white uppercase tracking-wider">
                            Bảng Thông Số Động & Thể Tích
                          </span>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950/70 border border-cyan-700/60 text-cyan-300 font-medium">
                          {volumeLatex.name}
                        </span>
                      </div>

                      {/* 4 Thẻ chỉ số nhảy số tự động theo Slider */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                        <div className="p-1.5 rounded-lg bg-slate-900/80 border border-emerald-900/40">
                          <div className="text-[10px] text-slate-400 font-medium">Cạnh đáy a</div>
                          <div className="text-sm font-bold font-mono text-emerald-400">
                            {Number(activeBaseEdge).toFixed(1)}
                          </div>
                        </div>

                        <div className="p-1.5 rounded-lg bg-slate-900/80 border border-cyan-900/40">
                          <div className="text-[10px] text-slate-400 font-medium">Chiều cao h</div>
                          <div className="text-sm font-bold font-mono text-cyan-400">
                            {Number(activeHeight).toFixed(1)}
                          </div>
                        </div>

                        <div className="p-1.5 rounded-lg bg-slate-900/80 border border-amber-900/40">
                          <div className="text-[10px] text-slate-400 font-medium">Sđáy</div>
                          <div className="text-sm font-bold font-mono text-amber-300">
                            {Number(parametricMetrics.measurements.base_area).toFixed(1)}
                          </div>
                        </div>

                        <div className="p-1.5 rounded-lg bg-indigo-950/50 border border-indigo-700/50 shadow-inner">
                          <div className="text-[10px] text-indigo-300 font-bold">Thể tích V</div>
                          <div className="text-sm font-black font-mono text-cyan-300">
                            {Number(parametricMetrics.measurements.volume).toFixed(1)}
                          </div>
                        </div>
                      </div>


                      {/* Công thức KaTeX động: Công thức tổng quát & Thế số trực tiếp */}
                      <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800/80 space-y-1 font-mono text-xs">
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <span className="text-slate-400">Công thức:</span>
                          <span className="text-cyan-300 font-semibold">
                            <MathText text={`$${volumeLatex.generalFormula}$`} />
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800/60">
                          <span className="text-emerald-400 font-semibold">Thế số tức thì:</span>
                          <span className="text-amber-300 font-bold">
                            <MathText text={`$${volumeLatex.substFormula}$`} />
                          </span>
                        </div>
                      </div>

                    </div>
                  )}
                </div>

                {/* Cột phải: KHÔNG GIAN TRỰC QUAN ĐÚNG BẢN CHẤT BÀI TOÁN */}
                <div className="col-span-12 lg:col-span-6 h-full min-h-[260px] bg-slate-950/90 rounded-2xl border border-slate-800 p-2.5 flex flex-col justify-between relative overflow-hidden shadow-inner">
                  {effectiveVisual === '2d' ? (
                    /* 1. ĐỒ THỊ 2D / PARABOL CHO ĐẠI SỐ & PHƯƠNG TRÌNH */
                    slide.chart_image_base64 ? (
                      <div className="w-full h-full flex flex-col items-center justify-between">
                        <div className="flex-1 w-full flex items-center justify-center p-1">
                          <img
                            src={slide.chart_image_base64}
                            alt="Đồ thị hàm số đồng bộ PPTX"
                            className="max-h-[210px] w-auto object-contain rounded"
                          />
                        </div>
                        <div className="w-full flex items-center justify-between text-[10px] text-slate-400 bg-slate-900/80 px-2.5 py-1 rounded border border-slate-800">
                          <span className="text-cyan-400 font-semibold">
                            {slide.chart_spec?.chart_title || "Đồ thị Matplotlib Native"}
                          </span>
                          <span className="text-emerald-400">Đồng bộ 1:1 với file PowerPoint</span>
                        </div>
                      </div>

                    ) : (
                      <FunctionPlotter
                        defaultExpr={slide.chart_spec?.expression || 'x**2 - 4'}
                        title={slide.chart_spec?.chart_title || 'Đồ thị Parabol y = f(x)'}
                        pedagogicalPurpose={slide.chart_spec?.pedagogical_purpose}
                        compact={false}
                        allowEdit={true}
                      />
                    )
                  ) : (
                    /* 2. THREE.JS 3D WEBGL CHO HÌNH HỌC KHÔNG GIAN */
                    <div className="w-full h-full flex flex-col justify-between relative">
                      {/* Thanh công cụ chọn nhanh mô hình 3D ngay trên khung hình */}
                      <div className="flex items-center justify-between px-2 py-1 bg-slate-900/90 border border-slate-800 rounded-lg text-[11px] mb-1 z-10">
                        <div className="flex items-center gap-1">
                          <Box size={13} className="text-cyan-400" />
                          <span className="text-white font-semibold">Khối 3D:</span>
                        </div>
                        <div className="flex items-center gap-1 overflow-x-auto">
                          <button
                            type="button"
                            onClick={() => setPolyhedronType?.('pyramid_square')}
                            className={`px-2 py-0.5 rounded text-[10px] font-medium transition ${
                              polyhedronType === 'pyramid_square'
                                ? 'bg-cyan-600 text-white shadow-sm'
                                : 'bg-slate-800 text-slate-300 hover:text-white'
                            }`}
                          >
                            S.ABCD
                          </button>
                          <button
                            type="button"
                            onClick={() => setPolyhedronType?.('pyramid_triangle')}
                            className={`px-2 py-0.5 rounded text-[10px] font-medium transition ${
                              polyhedronType === 'pyramid_triangle'
                                ? 'bg-cyan-600 text-white shadow-sm'
                                : 'bg-slate-800 text-slate-300 hover:text-white'
                            }`}
                          >
                            S.ABC
                          </button>
                          <button
                            type="button"
                            onClick={() => setPolyhedronType?.('cube')}
                            className={`px-2 py-0.5 rounded text-[10px] font-medium transition ${
                              polyhedronType === 'cube'
                                ? 'bg-cyan-600 text-white shadow-sm'
                                : 'bg-slate-800 text-slate-300 hover:text-white'
                            }`}
                          >
                            Lập Phương
                          </button>
                          <button
                            type="button"
                            onClick={() => setPolyhedronType?.('prism_triangle')}
                            className={`px-2 py-0.5 rounded text-[10px] font-medium transition ${
                              polyhedronType === 'prism_triangle'
                                ? 'bg-cyan-600 text-white shadow-sm'
                                : 'bg-slate-800 text-slate-300 hover:text-white'
                            }`}
                          >
                            Lăng Trụ
                          </button>
                          {setShowVertexLabels && (
                            <button
                              type="button"
                              onClick={() => setShowVertexLabels?.(!showVertexLabels)}
                              className={`px-2 py-0.5 rounded text-[10px] font-medium transition border flex items-center gap-1 ${
                                showVertexLabels
                                  ? 'bg-indigo-500/20 text-indigo-300 border-indigo-400/60 shadow-sm'
                                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                              }`}
                              title="Bật/Tắt hiển thị tên các đỉnh (S, A, B, C, D) theo chuẩn SGK Toán"
                            >
                              <Tag size={10} className={showVertexLabels ? 'text-indigo-400' : 'text-slate-400'} />
                              <span>Tên Đỉnh</span>
                            </button>
                          )}
                          {setShowAxes && (
                            <button
                              type="button"
                              onClick={() => setShowAxes?.(!showAxes)}
                              className={`px-2 py-0.5 rounded text-[10px] font-medium transition border ${
                                showAxes
                                  ? 'bg-amber-500/20 text-amber-300 border-amber-400/60'
                                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                              }`}
                              title="Bật/Tắt hệ trục tọa độ Oxyz và mặt phẳng đáy Oxy"
                            >
                              Oxyz
                            </button>
                          )}
                          {setShowHiddenLines && (
                            <button
                              type="button"
                              onClick={() => setShowHiddenLines?.(!showHiddenLines)}
                              className={`px-2 py-0.5 rounded text-[10px] font-medium transition border ${
                                showHiddenLines
                                  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-400/60'
                                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                              }`}
                              title="Bật/Tắt đường nét đứt (cạnh khuất chuẩn SGK)"
                            >
                              Nét Đứt
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => handleToggleUnfoldedNet?.(!activeShowUnfoldedNet)}
                            className={`px-2 py-0.5 rounded text-[10px] font-medium transition border flex items-center gap-1 ${
                              activeShowUnfoldedNet
                                ? 'bg-amber-500/25 text-amber-300 border-amber-400/70 shadow-sm font-semibold'
                                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                            }`}
                            title="Bật/Tắt chế độ xem song song Hình Khai Triển Phẳng 2D (Unfolded Net) để trực quan hóa Diện tích xung quanh S_xq"
                          >
                            <Layers size={10} className={activeShowUnfoldedNet ? 'text-amber-400' : 'text-slate-400'} />
                            <span>Khai Triển 2D</span>
                          </button>
                        </div>
                      </div>

                      {/* Thanh công cụ chọn nhanh 4 góc nhìn chuẩn SGK (Task 13.2) */}
                      <div className="flex items-center justify-between px-2 py-1 bg-slate-900/80 border border-slate-800 rounded-lg text-[10px] mb-1 z-10">
                        <div className="flex items-center gap-1 text-slate-400 font-medium">
                          <Compass size={12} className="text-cyan-400" />
                          <span>Góc nhìn SGK:</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => onCameraPreset?.('iso')}
                            className={`px-1.5 py-0.5 rounded transition ${
                              cameraPreset === 'iso'
                                ? 'bg-cyan-600 text-white font-semibold shadow-sm'
                                : 'bg-slate-800 text-slate-300 hover:text-white'
                            }`}
                            title="Góc nhìn phối cảnh 3 chiều chuẩn SGK (Isometric)"
                          >
                            Phối Cảnh
                          </button>
                          <button
                            type="button"
                            onClick={() => onCameraPreset?.('front')}
                            className={`px-1.5 py-0.5 rounded transition ${
                              cameraPreset === 'front'
                                ? 'bg-cyan-600 text-white font-semibold shadow-sm'
                                : 'bg-slate-800 text-slate-300 hover:text-white'
                            }`}
                            title="Hình chiếu đứng: Chiếu từ trước ra sau (Front View)"
                          >
                            Chiếu Đứng
                          </button>
                          <button
                            type="button"
                            onClick={() => onCameraPreset?.('top')}
                            className={`px-1.5 py-0.5 rounded transition ${
                              cameraPreset === 'top'
                                ? 'bg-cyan-600 text-white font-semibold shadow-sm'
                                : 'bg-slate-800 text-slate-300 hover:text-white'
                            }`}
                            title="Hình chiếu bằng: Chiếu từ trên xuống đáy Oxy (Top View)"
                          >
                            Chiếu Bằng
                          </button>
                          <button
                            type="button"
                            onClick={() => onCameraPreset?.('side')}
                            className={`px-1.5 py-0.5 rounded transition ${
                              cameraPreset === 'side'
                                ? 'bg-cyan-600 text-white font-semibold shadow-sm'
                                : 'bg-slate-800 text-slate-300 hover:text-white'
                            }`}
                            title="Hình chiếu cạnh: Chiếu vuông góc từ bên hông 90° (Side View)"
                          >
                            Chiếu Cạnh
                          </button>
                        </div>
                      </div>

                      {/* Khung Hiển Thị Trực Quan: 3D Đơn hoặc Song Song 3D + 2D Net (Task 13.3) */}
                      <div className={`flex-1 w-full relative min-h-[220px] rounded-lg overflow-hidden ${
                        activeShowUnfoldedNet ? 'grid grid-cols-1 md:grid-cols-2 gap-2' : 'flex'
                      }`}>
                        {/* Cột 1: Khung WebGL Canvas 3D */}
                        <div className="w-full h-full relative min-h-[210px] rounded-lg overflow-hidden bg-slate-950/70 border border-slate-800/80">
                          <ThreeCanvas
                            slideIndex={currentSlide}
                            polyhedronType={polyhedronType}
                            edgeLength={edgeLength}
                            heightParam={activeHeight}
                            baseParam={activeBaseEdge}
                            showHiddenLines={showHiddenLines}
                            showVertexLabels={showVertexLabels}
                            showAxes={showAxes}
                            cameraPreset={cameraPreset}
                            onCaptureReady={handleCaptureReady}
                          />
                          {activeShowUnfoldedNet && (
                            <div className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-slate-900/85 border border-slate-700/80 text-[9px] text-cyan-300 font-medium z-10 pointer-events-none">
                              Mô hình 3D
                            </div>
                          )}
                        </div>

                        {/* Cột 2: Bản vẽ Khai Triển Phẳng 2D (Side-by-Side Net) */}
                        {activeShowUnfoldedNet && (
                          <div className="w-full h-full relative min-h-[210px] rounded-lg overflow-hidden">
                            <UnfoldedNetViewer
                              polyhedronType={polyhedronType}
                              heightParam={activeHeight}
                              baseParam={activeBaseEdge}
                              showVertexLabels={showVertexLabels}
                            />
                          </div>
                        )}
                      </div>

                      {/* THANH ĐIỀU KHIỂN THAM SỐ HÌNH HỌC (TASK 12.1: SLIDER CONTROLS h & a) */}
                      <div className="mt-2 p-2.5 bg-slate-950/85 backdrop-blur-md rounded-lg border border-slate-800/90 shadow-md">
                        <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-slate-800/70">
                          <div className="flex items-center gap-1.5">
                            <Sliders size={13} className="text-cyan-400" />
                            <span className="text-[11px] font-bold text-slate-200 tracking-wide uppercase">
                              Tham Số Hình Học
                            </span>
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-950/80 border border-emerald-600/40 text-emerald-400 font-mono font-semibold flex items-center gap-0.5">
                              <Zap size={9} /> 60 FPS rAF
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              handleHeightChange?.(4.0);
                              handleBaseEdgeChange?.(4.0);
                            }}
                            className="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-[10px] text-cyan-300 hover:text-white border border-slate-700/60 flex items-center gap-1 transition"
                            title="Đặt lại tham số chuẩn h = 4.0, a = 4.0"
                          >
                            <RotateCcw size={9} />
                            <span>Mặc định (h=4, a=4)</span>
                          </button>
                        </div>

                        {/* Task 12.3: Bảng thông số nhảy số động theo thời gian thực (Sđáy, h, V) */}
                        <div className="grid grid-cols-3 gap-1.5 mb-2 py-1 px-2 rounded-md bg-slate-900/90 border border-slate-800/90 text-center font-mono">
                          <div className="text-[10px]">
                            <span className="text-slate-400">Sđáy: </span>
                            <span className="text-amber-300 font-bold">{Number(parametricMetrics.measurements.base_area).toFixed(1)}</span>
                          </div>
                          <div className="text-[10px]">
                            <span className="text-slate-400">h: </span>
                            <span className="text-cyan-300 font-bold">{Number(activeHeight).toFixed(1)}</span>
                          </div>
                          <div className="text-[10px]">
                            <span className="text-indigo-300 font-semibold">V: </span>
                            <span className="text-emerald-300 font-black">{Number(parametricMetrics.measurements.volume).toFixed(1)}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                          {/* Slider 1: Chiều cao h (1 đến 10) */}
                          <div className="flex flex-col space-y-1 bg-slate-900/60 p-1.5 rounded border border-slate-800/60">
                            <div className="flex items-center justify-between">
                              <span className="text-slate-300 font-medium flex items-center gap-1">
                                <MoveVertical size={11} className="text-cyan-400" />
                                <span>Chiều cao <span className="font-mono text-cyan-300 font-bold">h</span>:</span>
                              </span>
                              <span className="px-1.5 py-0.2 rounded bg-cyan-950/80 border border-cyan-700/50 text-cyan-300 font-mono font-bold text-[10px]">
                                {Number(activeHeight).toFixed(1)}
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className="text-[9px] text-slate-500 font-mono">1</span>
                              <input
                                type="range"
                                min="1"
                                max="10"
                                step="0.5"
                                value={activeHeight}
                                onInput={(e) => handleHeightInput(e.target.value)}
                                onChange={(e) => handleHeightInput(e.target.value)}
                                className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400 focus:outline-none"
                              />
                              <span className="text-[9px] text-slate-500 font-mono">10</span>
                            </div>
                          </div>

                          {/* Slider 2: Cạnh đáy a (1 đến 8) */}
                          <div className="flex flex-col space-y-1 bg-slate-900/60 p-1.5 rounded border border-slate-800/60">
                            <div className="flex items-center justify-between">
                              <span className="text-slate-300 font-medium flex items-center gap-1">
                                <Maximize2 size={11} className="text-emerald-400" />
                                <span>Cạnh đáy <span className="font-mono text-emerald-300 font-bold">a</span>:</span>
                              </span>
                              <span className="px-1.5 py-0.2 rounded bg-emerald-950/80 border border-emerald-700/50 text-emerald-300 font-mono font-bold text-[10px]">
                                {Number(activeBaseEdge).toFixed(1)}
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className="text-[9px] text-slate-500 font-mono">1</span>
                              <input
                                type="range"
                                min="1"
                                max="8"
                                step="0.5"
                                value={activeBaseEdge}
                                onInput={(e) => handleBaseEdgeInput(e.target.value)}
                                onChange={(e) => handleBaseEdgeInput(e.target.value)}
                                className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400 focus:outline-none"
                              />
                              <span className="text-[9px] text-slate-500 font-mono">8</span>
                            </div>
                          </div>
                        </div>

                        {/* Hiển thị tọa độ đỉnh chóp S(0, 0, h) theo thời gian thực (Task 12.2) */}
                        <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-slate-800/80 text-[10px]">
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-400">Tọa độ đỉnh chóp:</span>
                            <span className="px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800/70 text-cyan-300 font-mono font-bold tracking-wider">
                              S(0.0, 0.0, {Number(activeHeight).toFixed(1)})
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5 text-slate-400">
                            <span>Gốc O:</span>
                            <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300 font-mono">
                              (0, 0, 0)
                            </span>
                          </div>
                        </div>
                      </div>


                      <div className="mt-1 px-2 py-0.5 bg-slate-900/80 backdrop-blur rounded text-[10px] text-slate-400 border border-slate-800 flex items-center justify-between">
                        <span>Chuột trái: Xoay 360° quanh Ox, Oy, Oz</span>
                        <span>Cuộn chuột: Thu phóng</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : slide.layout === 'TWO_COLUMN' ? (
              /* TRƯỜNG HỢP C2: BỐ CỤC TOÀN MÀN HÌNH 2 CỘT HỌC THUẬT (PHƯƠNG PHÁP + BÀI GIẢI MẪU TỪNG BƯỚC CHUẨN SGK) */
              <div className="grid grid-cols-12 gap-5 h-full items-stretch">
                {/* Cột 1: Quy trình & Phương pháp giải (Chiếm 50% toàn màn hình) */}
                <div className="col-span-12 lg:col-span-6 flex flex-col justify-between space-y-3 p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                        <strong className="text-cyan-400 text-xs md:text-sm font-bold uppercase tracking-wider">
                          Quy Trình & Phương Pháp Giải
                        </strong>
                      </div>
                      <span className="text-[10px] text-slate-400">Lý thuyết trọng tâm</span>
                    </div>

                    <ul className="space-y-2.5 text-xs text-slate-200 leading-relaxed">
                      {(slide.bullet_points || []).map((pt, i) => {
                        const isUpdated = isFormulaRecentlyUpdated('bullet_point', i);
                        return (
                          <li
                            key={i}
                            onDoubleClick={() =>
                              handleOpenMathModal(
                                'bullet_point',
                                pt,
                                `Bước phương pháp #${i + 1} (Slide ${currentSlide + 1})`,
                                i
                              )
                            }
                            className={`flex items-start gap-2.5 p-2 rounded-xl border cursor-pointer transition-all ${
                              isUpdated
                                ? 'bg-emerald-950/40 border-emerald-400 ring-2 ring-emerald-500/60'
                                : 'bg-slate-950/60 hover:bg-slate-800/80 border-slate-800/80 hover:border-cyan-700/60'
                            }`}
                          >
                            <span className="w-5 h-5 rounded-full bg-cyan-950 border border-cyan-700 text-cyan-300 font-bold text-[11px] flex items-center justify-center shrink-0 mt-0.5">
                              {i + 1}
                            </span>
                            <span className="flex-1"><MathText text={pt} /></span>
                          </li>
                        );
                      })}
                    </ul>
                  </div>

                  {slide.main_definition_latex && (
                    <div
                      onDoubleClick={() =>
                        handleOpenMathModal(
                          'main_definition_latex',
                          slide.main_definition_latex,
                          `Công thức tổng quát (Slide ${currentSlide + 1})`
                        )
                      }
                      className="p-3 rounded-xl bg-gradient-to-r from-cyan-950/50 via-slate-900 to-indigo-950/40 border border-cyan-800/70 text-center font-mono text-cyan-300 text-sm md:text-base font-bold shadow-md cursor-pointer hover:border-cyan-400 transition"
                    >
                      <MathText text={slide.main_definition_latex} block={true} />
                      <span className="text-[10px] font-sans font-normal text-cyan-400/80 block mt-1">
                        Công thức tổng quát áp dụng
                      </span>
                    </div>
                  )}
                </div>

                {/* Cột 2: Ví Dụ Minh Họa & Lời Giải Mẫu Từng Bước Chuẩn SGK (Chiếm 50% còn lại của toàn màn hình) */}
                <div className="col-span-12 lg:col-span-6 flex flex-col justify-between space-y-3 p-4 rounded-2xl bg-gradient-to-br from-slate-900/90 to-slate-950 border border-indigo-900/60 shadow-xl">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between border-b border-indigo-900/60 pb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        <strong className="text-emerald-400 text-xs md:text-sm font-bold uppercase tracking-wider flex items-center gap-1.5">
                          <BookOpen size={14} /> Ví Dụ Minh Họa & Bài Giải Mẫu
                        </strong>
                      </div>
                      <span className="text-[10px] text-emerald-300/80 font-mono">Chuẩn SGK GDPT 2018</span>
                    </div>

                    <div className="space-y-2 text-xs leading-relaxed max-h-[320px] overflow-y-auto pr-1">
                      {Array.isArray(slide.worked_solution_steps) && slide.worked_solution_steps.length > 0 ? (
                        slide.worked_solution_steps.map((step, idx) => (
                          <div
                            key={idx}
                            className={`p-2.5 rounded-xl border ${
                              idx === 0
                                ? 'bg-amber-950/30 border-amber-800/60 text-amber-200 font-semibold'
                                : idx === slide.worked_solution_steps.length - 1
                                ? 'bg-emerald-950/40 border-emerald-700/70 text-emerald-200 font-semibold'
                                : 'bg-slate-900/80 border-slate-800 text-slate-200'
                            }`}
                          >
                            <MathText text={step} />
                          </div>
                        ))
                      ) : (
                        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-400 space-y-2 text-center">
                          <p>Chưa có các bước bài giải mẫu riêng biệt.</p>
                          <p className="text-[11px] text-slate-500">Giáo viên có thể phân tích trực tiếp trên lớp hoặc nhờ Trợ Giảng AI soạn thêm bài tập giải mẫu chi tiết qua khung Chat Co-pilot.</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {slide.teacher_note && (
                    <div className="p-2.5 rounded-xl bg-amber-950/20 border border-amber-900/40 text-[11px] text-amber-300 flex items-start gap-2">
                      <span><strong>Lời nhắc sư phạm:</strong> <MathText text={slide.teacher_note} /></span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* TRƯỜNG HỢP C3: BỐ CỤC TOÀN MÀN HÌNH 100% CONCEPT_HIGHLIGHT / SINGLE_COLUMN (ĐỊNH NGHĨA & CÔNG THỨC RỘNG RÃI) */
              <div className="h-full flex flex-col justify-between gap-3 p-1">
                {/* Hero Formula Box: Công thức toán trọng tâm đặt chính giữa nổi bật */}
                {slide.main_definition_latex && (
                  <div
                    onDoubleClick={() =>
                      handleOpenMathModal(
                        'main_definition_latex',
                        slide.main_definition_latex,
                        `Công thức cốt lõi (Slide ${currentSlide + 1})`
                      )
                    }
                    title="Nhấp đúp (Double-Click) để chỉnh sửa công thức bằng MathLive"
                    className={`p-4 md:p-5 rounded-2xl border font-mono text-cyan-300 text-center text-base md:text-xl font-bold shadow-2xl cursor-pointer transition-all duration-500 relative group ${
                      isFormulaRecentlyUpdated('main_definition_latex')
                        ? 'bg-emerald-950/60 border-emerald-400 ring-2 ring-emerald-400/80'
                        : 'bg-gradient-to-r from-cyan-950/60 via-slate-900/90 to-indigo-950/60 border-cyan-700/80 hover:border-cyan-400'
                    }`}
                  >
                    <MathText text={slide.main_definition_latex} block={true} />
                    <div className="mt-2 flex items-center justify-center gap-2 text-xs font-sans font-medium text-cyan-400">
                      <Sparkles size={14} className="text-amber-400" />
                      <span>Định lý / Hệ thức trọng tâm bài học • Click đúp để sửa MathLive</span>
                    </div>
                  </div>
                )}

                {/* Grid các thẻ kiến thức trải rộng 100% màn hình */}
                <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-3 overflow-y-auto">
                  {(slide.bullet_points || []).map((pt, i) => {
                    const isUpdated = isFormulaRecentlyUpdated('bullet_point', i);
                    return (
                      <div
                        key={i}
                        onDoubleClick={() =>
                          handleOpenMathModal(
                            'bullet_point',
                            pt,
                            `Ý kiến thức #${i + 1} (Slide ${currentSlide + 1})`,
                            i
                          )
                        }
                        className={`p-3.5 rounded-2xl border flex items-start gap-3 cursor-pointer transition-all leading-relaxed ${
                          isUpdated
                            ? 'bg-emerald-950/40 border-emerald-400 ring-2 ring-emerald-500/60 shadow-lg'
                            : 'bg-slate-900/70 hover:bg-slate-800/80 border-slate-800 hover:border-cyan-700/60'
                        }`}
                      >
                        <span className="w-6 h-6 rounded-lg bg-cyan-950 border border-cyan-800 text-cyan-400 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                          {i + 1}
                        </span>
                        <div className="flex-1 text-xs md:text-sm text-slate-100 font-medium">
                          <MathText text={pt} />
                        </div>
                      </div>

                    );
                  })}
                </div>

                {/* Footer lời nhắc sư phạm */}
                {slide.teacher_note && (
                  <div className="p-2.5 rounded-xl bg-amber-950/20 border border-amber-900/40 text-[11px] text-amber-300 flex items-start gap-2">
                    <span><strong>Lời nhắc sư phạm cho Giáo viên:</strong> <MathText text={slide.teacher_note} /></span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer Điều Khiển Slide: Chuyển slide & Filmstrip Thumbnails */}
          <div className="pt-2.5 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 shrink-0">
            {/* Filmstrip thumbnails nhanh (Kèm biểu tượng ⚠️ vàng nếu Slide có cảnh báo) */}
            <div className="flex items-center gap-1.5 overflow-x-auto max-w-xl py-0.5">
              {slides.map((s, idx) => {
                const slideWarnsCount = activeWarnings.filter(
                  (w) => Number(w.slide_index) === idx + 1
                ).length;
                return (
                  <button
                    key={idx}
                    onClick={() => setCurrentSlide(idx)}
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-medium whitespace-nowrap transition flex items-center gap-1 ${
                      currentSlide === idx
                        ? 'bg-cyan-600 text-white shadow-md shadow-cyan-950/50'
                        : slideWarnsCount > 0
                        ? 'bg-amber-950/60 text-amber-200 border border-amber-500/70 hover:bg-amber-900/60'
                        : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
                    }`}
                  >
                    <span>
                      {idx + 1}. {s.title?.split('•')[0]?.slice(0, 16) || `Slide ${idx + 1}`}
                    </span>
                    {slideWarnsCount > 0 && (
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          setCurrentSlide(idx);
                          setIsWarningModalOpen(true);
                        }}
                        title={`Slide ${idx + 1} có ${slideWarnsCount} cảnh báo sư phạm — Nhấn để xem`}
                        className="ml-0.5 px-1 rounded bg-amber-500/30 text-amber-300 text-[10px] font-bold"
                      >
                        ⚠️{slideWarnsCount}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Nút Trước / Sau */}
            <div className="flex items-center gap-2">
              {isPresentationMode && (
                <span className="text-[11px] font-mono text-slate-500 hidden xl:inline mr-2">
                  [← / → / Space]: Chuyển slide • [B]: Tối màn hình • [Esc / F5]: Thoát
                </span>
              )}
              <button
                onClick={() => setCurrentSlide(Math.max(0, currentSlide - 1))}
                disabled={currentSlide === 0}
                className={`rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-slate-300 hover:text-white border border-slate-800 font-semibold flex items-center gap-1 transition ${
                  isPresentationMode ? 'px-3.5 py-2 text-xs md:text-sm' : 'px-3 py-1.5 text-xs'
                }`}
                title="Phím ←"
              >
                <ChevronLeft size={isPresentationMode ? 18 : 16} /> Trước
              </button>
              <button
                onClick={() => setCurrentSlide(Math.min(slides.length - 1, currentSlide + 1))}
                disabled={currentSlide >= slides.length - 1}
                className={`rounded-lg bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 disabled:opacity-40 text-white font-semibold flex items-center gap-1 shadow-lg shadow-cyan-950/40 transition ${
                  isPresentationMode ? 'px-4 py-2 text-xs md:text-sm' : 'px-3.5 py-1.5 text-xs'
                }`}
                title="Phím →"
              >
                Sau <ChevronRight size={isPresentationMode ? 18 : 16} />
              </button>
            </div>
          </div>

          {/* Task 17.1: Lớp Canvas Vẽ Chú Thích Phủ Tràn Khung Hình 16:9 */}
          <AnnotationCanvas
            isActive={isDrawingMode}
            tool={currentTool}
            color={drawingColor}
            size={brushSize}
            slideIndex={currentSlide}
            strokes={currentStrokes}
            onStrokesChange={handleStrokesChange}
            isPresentationMode={isPresentationMode}
          />
        </div>
      </div>

      {/* Task 8.2: Modal Popup chỉnh sửa công thức Toán trực quan (MathLive) */}
      <MathLiveModal
        isOpen={mathModalState.isOpen}
        initialLatex={mathModalState.initialLatex}
        fieldLabel={mathModalState.fieldLabel}
        onClose={() => setMathModalState((prev) => ({ ...prev, isOpen: false }))}
        onSave={handleSaveMathModal}
      />

      {/* Task 10.4: Giao diện "Danh sách Cảnh báo Sư phạm" (Human-in-the-Loop) */}
      <PedagogicalWarningModal
        isOpen={isWarningModalOpen}
        onClose={() => setIsWarningModalOpen(false)}
        warnings={activeWarnings}
        currentSlideIndex={currentSlide}
        onJumpToSlide={(idx) => setCurrentSlide?.(idx)}
        onOpenManualEdit={handleOpenManualEditFromWarning}
        onDismissWarning={handleDismissWarning}
      />

      {/* Task 15.3: Màn Hình Tối Blackout Curtain (Phím B) */}
      {isBlackout && (
        <div
          onClick={() => onToggleBlackout?.(false)}
          className="fixed inset-0 z-[60] bg-black flex flex-col items-center justify-center cursor-pointer transition-opacity duration-300 select-none"
          title="Nhấp chuột hoặc ấn phím B để tiếp tục bài giảng"
        >
          <div className="text-center space-y-3 opacity-40 hover:opacity-90 transition duration-300">
            <div className="w-14 h-14 rounded-full border border-slate-700 mx-auto flex items-center justify-center text-slate-400 bg-slate-950/80 shadow-2xl">
              <Moon size={28} />
            </div>
            <p className="text-slate-300 text-base font-medium tracking-wide">
              Màn hình tạm tắt để tập trung bài giảng
            </p>
            <div className="flex items-center justify-center gap-2 text-xs font-mono text-slate-500">
              <kbd className="px-2 py-0.5 bg-slate-900 border border-slate-700 rounded text-slate-300 font-bold">B</kbd>
              <span>hoặc click chuột / ấn phím bất kỳ để tiếp tục</span>
            </div>
          </div>
        </div>
      )}

      {/* Task 15.4: Thanh Điều Khiển Mờ Nổi (Floating Control Bar HUD) với Đồng Hồ 45 Phút */}
      {isPresentationMode && (
        <PresentationFloatingBar
          currentSlide={currentSlide}
          totalSlides={slides.length || 1}
          onPrevSlide={() => setCurrentSlide(Math.max(0, currentSlide - 1))}
          onNextSlide={() => setCurrentSlide(Math.min(slides.length - 1, currentSlide + 1))}
          onSelectSlide={(idx) => setCurrentSlide?.(idx)}
          slides={slides}
          isBlackout={isBlackout}
          onToggleBlackout={onToggleBlackout}
          onExitPresentation={onExitPresentation}
          visualMode={visualMode}
          onSelectVisualMode={setVisualMode}
          // Task 17.2: Quản lý Công cụ Bút vẽ Sư phạm
          isDrawingMode={isDrawingMode}
          onToggleDrawingMode={setIsDrawingMode}
          currentTool={currentTool}
          onSelectTool={setCurrentTool}
          drawingColor={drawingColor}
          onSelectColor={setDrawingColor}
          brushSize={brushSize}
          onSelectBrushSize={setBrushSize}
          // Task 17.3: Quản lý Hoàn tác (Undo), Làm lại (Redo), Tẩy nét & Xóa toàn bộ
          canUndo={currentUndoStack.length > 0}
          canRedo={currentRedoStack.length > 0}
          onUndo={handleUndoStrokes}
          onRedo={handleRedoStrokes}
          onClearCanvas={handleClearAllStrokes}
          hasStrokes={currentStrokes.length > 0}
          // Task 17.4: Chế độ Bảng trắng Toàn màn hình & Đồng bộ trạng thái nét vẽ
          isWhiteboardOpen={isWhiteboardOpen}
          onToggleWhiteboard={setIsWhiteboardOpen}
          slideDrawingsMap={slideDrawingsMap}
        />
      )}

      {/* Task 17.4: Chế độ Bảng Viết Toàn Màn Hình (Whiteboard / Blackboard Mode) */}
      <WhiteboardOverlay
        isOpen={isWhiteboardOpen}
        onClose={() => setIsWhiteboardOpen(false)}
        tool={currentTool}
        color={drawingColor}
        size={brushSize}
        onSelectTool={setCurrentTool}
        onSelectColor={setDrawingColor}
        strokes={whiteboardStrokes}
        onStrokesChange={handleWhiteboardStrokesChange}
        canUndo={whiteboardUndoStack.length > 0}
        canRedo={whiteboardRedoStack.length > 0}
        onUndo={handleWhiteboardUndo}
        onRedo={handleWhiteboardRedo}
        onClear={handleWhiteboardClear}
      />
    </div>
  );
}
