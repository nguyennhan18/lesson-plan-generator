/**
 * Quiz Audio Feedback Synthesizer (Web Audio API) - Task 16.2
 *
 * Tính năng âm thanh thông minh không phụ thuộc tệp âm thanh bên ngoài (.mp3/.wav):
 * - 0ms độ trễ (Zero latency): Tạo sóng dao động Oscillator trực tiếp trong trình duyệt.
 * - 100% Offline & An toàn: Không phụ thuộc CDN hay mạng Internet phòng học.
 * - Âm thanh Chính xác (playCorrect): Hòa âm 2 nốt E5 (659.25 Hz) & A5 (880.00 Hz) ngân vang, chúc mừng tích cực.
 * - Âm thanh Chưa đúng (playWrong): Âm trầm nhẹ nhàng (220 Hz -> 140 Hz) mang tính xây dựng, sư phạm.
 */

class QuizAudioFeedback {
  constructor() {
    this.ctx = null;
    this.isMuted = false;
    this.masterVolume = 0.25; // Âm lượng chuẩn dịu nhẹ cho lớp học
  }

  /**
   * Khởi tạo AudioContext an toàn khi có tương tác người dùng
   */
  initContext() {
    if (typeof window === 'undefined') return null;

    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }

    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }

    return this.ctx;
  }

  /**
   * Phát âm thanh chúc mừng khi chọn ĐÚNG (Task 16.2)
   * Nốt E5 (659.25 Hz) chuyển tiếp lên A5 (880.00 Hz) với envelope decay mượt mà
   */
  playCorrect() {
    if (this.isMuted) return;
    const ctx = this.initContext();
    if (!ctx) return;

    try {
      const now = ctx.currentTime;

      // Note 1: E5 (659.25 Hz)
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(659.25, now);

      gain1.gain.setValueAtTime(0.0001, now);
      gain1.gain.exponentialRampToValueAtTime(this.masterVolume, now + 0.02);
      gain1.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);

      osc1.connect(gain1);
      gain1.connect(ctx.destination);

      osc1.start(now);
      osc1.stop(now + 0.35);

      // Note 2: A5 (880.00 Hz) - Bắt đầu sau 0.09s tạo hiệu ứng Ting-Ting rực rỡ
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(880.00, now + 0.09);

      gain2.gain.setValueAtTime(0.0001, now + 0.09);
      gain2.gain.exponentialRampToValueAtTime(this.masterVolume * 1.1, now + 0.11);
      gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.65);

      osc2.connect(gain2);
      gain2.connect(ctx.destination);

      osc2.start(now + 0.09);
      osc2.stop(now + 0.65);
    } catch (e) {
      console.warn('[QuizAudioFeedback] Không thể phát âm thanh đúng:', e);
    }
  }

  /**
   * Phát âm thanh khi chọn CHƯA ĐÚNG (Task 16.3 chuẩn bị sẵn)
   * Âm trầm nhẹ nhàng, không gây ức chế cho học sinh
   */
  playWrong() {
    if (this.isMuted) return;
    const ctx = this.initContext();
    if (!ctx) return;

    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(220, now);
      osc.frequency.exponentialRampToValueAtTime(140, now + 0.28);

      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(this.masterVolume * 0.7, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.3);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.3);
    } catch (e) {
      console.warn('[QuizAudioFeedback] Không thể phát âm thanh sai:', e);
    }
  }

  /**
   * Bật/Tắt âm thanh toàn cục
   */
  setMuted(muted) {
    this.isMuted = !!muted;
  }

  toggleMute() {
    this.isMuted = !this.isMuted;
    return this.isMuted;
  }
}

export const quizAudio = new QuizAudioFeedback();
export default QuizAudioFeedback;
