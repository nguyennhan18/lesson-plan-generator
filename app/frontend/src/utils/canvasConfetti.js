/**
 * Lightweight Canvas Confetti Engine - Task 16.2
 *
 * Hiệu ứng pháo hoa chúc mừng bằng HTML5 Canvas thuần:
 * - 0 phụ thuộc thư viện ngoài (Zero external dependencies).
 * - 60 FPS mượt mà qua requestAnimationFrame.
 * - Hỗ trợ màn hình Retina độ phân giải cao (High-DPI / devicePixelRatio).
 * - Vật lý bay chân thực: Vận tốc ban đầu, trọng lực (gravity), lực cản không khí (drag), xoay lật 3D (tilt flutter).
 * - Tự động dọn dẹp bộ nhớ và huỷ vòng lặp khi pháo hoa kết thúc.
 */

export function launchCanvasConfetti(canvas, options = {}) {
  if (!canvas || typeof window === 'undefined') return { cancel: () => {} };

  const ctx = canvas.getContext('2d');
  if (!ctx) return { cancel: () => {} };

  const dpr = window.devicePixelRatio || 1;
  const width = window.innerWidth;
  const height = window.innerHeight;

  canvas.width = width * dpr;
  canvas.height = height * dpr;
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;

  ctx.scale(dpr, dpr);

  const particleCount = options.particleCount || 80;
  const colors = options.colors || [
    '#10b981', // Emerald
    '#34d399', // Mint
    '#06b6d4', // Cyan
    '#38bdf8', // Sky
    '#f59e0b', // Amber
    '#fbbf24', // Yellow Gold
    '#8b5cf6', // Violet
    '#ec4899'  // Pink
  ];

  const originX = options.originX !== undefined ? options.originX : width * 0.5;
  const originY = options.originY !== undefined ? options.originY : height * 0.45;

  // Khởi tạo danh sách hạt pháo hoa
  const particles = [];
  for (let i = 0; i < particleCount; i++) {
    const angle = Math.random() * Math.PI * 2;
    const speed = 7 + Math.random() * 16;
    const spreadBias = -Math.abs(Math.sin(angle)) * speed * 1.1; // Ưu tiên bắn tung lên trên

    particles.push({
      x: originX + (Math.random() - 0.5) * 40,
      y: originY + (Math.random() - 0.5) * 20,
      vx: Math.cos(angle) * speed * 0.9,
      vy: spreadBias - 2,
      size: 5 + Math.random() * 6,
      aspectRatio: 0.5 + Math.random() * 0.8,
      color: colors[Math.floor(Math.random() * colors.length)],
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 8,
      tilt: Math.random() * 10,
      tiltSpeed: 0.08 + Math.random() * 0.12,
      gravity: 0.26 + Math.random() * 0.08,
      drag: 0.975,
      alpha: 1.0,
      decay: 0.009 + Math.random() * 0.008
    });
  }

  let animationFrameId = null;
  let isCancelled = false;

  const renderFrame = () => {
    if (isCancelled) return;

    ctx.clearRect(0, 0, width, height);

    let activeCount = 0;

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      if (p.alpha <= 0 || p.y > height + 50) continue;

      activeCount++;

      // Cập nhật vật lý hạt
      p.x += p.vx;
      p.y += p.vy;
      p.vx *= p.drag;
      p.vy = p.vy * p.drag + p.gravity;
      p.tilt += p.tiltSpeed;
      p.rotation += p.rotationSpeed;
      p.alpha = Math.max(0, p.alpha - p.decay);

      // Vẽ hạt confetti với hiệu ứng lật 3D
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate((p.rotation * Math.PI) / 180);
      ctx.scale(1, Math.sin(p.tilt)); // Hiệu ứng xoay tròn trong không gian 3 chiều

      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.alpha;
      ctx.fillRect(
        -p.size / 2,
        -(p.size * p.aspectRatio) / 2,
        p.size,
        p.size * p.aspectRatio
      );

      ctx.restore();
    }

    if (activeCount > 0) {
      animationFrameId = requestAnimationFrame(renderFrame);
    } else {
      ctx.clearRect(0, 0, width, height);
    }
  };

  animationFrameId = requestAnimationFrame(renderFrame);

  return {
    cancel: () => {
      isCancelled = true;
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
      ctx.clearRect(0, 0, width, height);
    }
  };
}
