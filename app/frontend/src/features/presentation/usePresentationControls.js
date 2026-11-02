import { useEffect } from 'react';
import {
  isFullscreenActive,
  requestPresentationFullscreen,
  exitPresentationFullscreen,
  onFullscreenChange
} from './fullscreenHelper.js';

/** Đồng bộ toàn màn hình và phím tắt; trạng thái vẫn thuộc App. */
export function usePresentationControls({
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
}) {
  useEffect(() => {
    const unsub = onFullscreenChange((active) => {
      setIsPresentationMode(active);
      if (!active) {
        setIsBlackout(false);
      }
    });
    return unsub;
  }, []);

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

  return { handleStartPresentation, handleExitPresentation, toggleFullscreen };
}
