/**
 * Task 15.1: HTML5 Fullscreen API Helper
 * Hỗ trợ đa nền tảng (Vendor Prefixes) và lắng nghe sự kiện đồng bộ trạng thái Fullscreen.
 */

export function isFullscreenActive() {
  if (typeof document === 'undefined') return false;
  return Boolean(
    document.fullscreenElement ||
    document.webkitFullscreenElement ||
    document.mozFullScreenElement ||
    document.msFullscreenElement
  );
}

export async function requestPresentationFullscreen(element = document.documentElement) {
  if (!element) return false;
  try {
    if (element.requestFullscreen) {
      await element.requestFullscreen();
    } else if (element.webkitRequestFullscreen) {
      await element.webkitRequestFullscreen();
    } else if (element.mozRequestFullScreen) {
      await element.mozRequestFullScreen();
    } else if (element.msRequestFullscreen) {
      await element.msRequestFullscreen();
    }
    return true;
  } catch (err) {
    console.warn('[fullscreenHelper] requestFullscreen failed or blocked:', err);
    return false;
  }
}

export async function exitPresentationFullscreen() {
  if (typeof document === 'undefined') return false;
  try {
    if (document.exitFullscreen) {
      await document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      await document.webkitExitFullscreen();
    } else if (document.mozCancelFullScreen) {
      await document.mozCancelFullScreen();
    } else if (document.msExitFullscreen) {
      await document.msExitFullscreen();
    }
    return true;
  } catch (err) {
    console.warn('[fullscreenHelper] exitFullscreen failed:', err);
    return false;
  }
}

export async function togglePresentationFullscreen(element = document.documentElement) {
  if (isFullscreenActive()) {
    return await exitPresentationFullscreen();
  } else {
    return await requestPresentationFullscreen(element);
  }
}

export function onFullscreenChange(callback) {
  if (typeof document === 'undefined') return () => {};

  const handler = () => {
    callback(isFullscreenActive());
  };

  document.addEventListener('fullscreenchange', handler);
  document.addEventListener('webkitfullscreenchange', handler);
  document.addEventListener('mozfullscreenchange', handler);
  document.addEventListener('MSFullscreenChange', handler);

  return () => {
    document.removeEventListener('fullscreenchange', handler);
    document.removeEventListener('webkitfullscreenchange', handler);
    document.removeEventListener('mozfullscreenchange', handler);
    document.removeEventListener('MSFullscreenChange', handler);
  };
}
