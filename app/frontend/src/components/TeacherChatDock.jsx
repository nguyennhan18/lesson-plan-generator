import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Trash2, ChevronLeft, Sparkles, Check } from 'lucide-react';
import MathText from './MathText';

export default function TeacherChatDock({
  isOpen,
  onToggle,
  currentSlide = 0,
  slideDeck,
  onApplyPatch
}) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: `Chào Thầy/Cô! Em là Trợ Giảng AI Co-pilot, đang đồng hành cùng Thầy/Cô tại **Slide ${currentSlide + 1}**.\nThầy/Cô có thể yêu cầu em giải thích bài, đổi số liệu hoặc thêm câu hỏi trắc nghiệm bất cứ lúc nào!`,
      time: '08:00'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const messagesEndRef = useRef(null);

  const quickChips = [
    '💡 Giải thích slide này đơn giản hơn',
    '❓ Gợi ý 2 câu hỏi gợi mở cho học sinh',
    '📝 Thêm 1 câu hỏi trắc nghiệm củng cố',
    '🧠 Đổi bài toán sang ví dụ thực tế'
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  const sendMessage = async (textToSend) => {
    const text = textToSend || inputText.trim();
    if (!text || isThinking) return;

    const userTime = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    const newMessages = [...messages, { role: 'user', text, time: userTime }];
    setMessages(newMessages);
    if (!textToSend) setInputText('');
    setIsThinking(true);

    try {
      const res = await fetch('/api/v1/chat/interact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: 'session_teacher_dock',
          user_message: text,
          current_slide_index: currentSlide,
          slide_deck: slideDeck
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const aiTime = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          text: data.ai_response || 'Dạ Thầy/Cô, em đã ghi nhận yêu cầu!',
          time: aiTime,
          patchProposal: data.patch_proposal || null
        }
      ]);
    } catch (err) {
      const aiTime = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          text: `Dạ Thầy/Cô, tại Slide ${currentSlide + 1}, Thầy/Cô nên lưu ý học sinh áp dụng đúng công thức định lý và quan sát kỹ góc chiếu của mô hình 3D.`,
          time: aiTime
        }
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleApplyPatchClick = (patch, msgIdx) => {
    if (onApplyPatch && patch) {
      const success = onApplyPatch(patch);
      if (success) {
        const updated = [...messages];
        updated[msgIdx].isPatched = true;
        setMessages(updated);
        alert(`✅ Đã áp dụng thành công bản vá vào Slide ${(patch.target_slide_index ?? currentSlide) + 1}!`);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <aside className="w-80 glass-panel border-r border-slate-800 flex flex-col justify-between h-full transition-all duration-300 z-10 bg-[#090d1c]/95">
      {/* Header */}
      <div className="p-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <Bot size={18} />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
              Trợ Giảng AI Co-pilot
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            </h3>
            <p className="text-[11px] text-cyan-400">Đang theo dõi • Slide {currentSlide + 1}</p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setMessages([{
              role: 'assistant',
              text: `Đã làm mới phiên hỗ trợ! Em đang sẵn sàng cùng Thầy/Cô tại Slide ${currentSlide + 1}.`,
              time: '08:00'
            }])}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Làm mới chat"
          >
            <Trash2 size={15} />
          </button>
          <button
            onClick={onToggle}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Thu gọn khung chat (Phím C)"
          >
            <ChevronLeft size={16} />
          </button>
        </div>
      </div>

      {/* Quick Chips */}
      <div className="p-2 border-b border-slate-800/60 bg-slate-950/40 space-y-1">
        {quickChips.map((chip, idx) => (
          <button
            key={idx}
            onClick={() => sendMessage(chip)}
            className="w-full text-left text-[11px] px-2 py-1.5 rounded bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border border-slate-800/80 transition flex items-center gap-1 truncate"
          >
            <Sparkles size={11} className="text-amber-400 shrink-0" />
            <span className="truncate">{chip}</span>
          </button>
        ))}
      </div>

      {/* Messages Stream */}
      <div className="flex-1 p-3 overflow-y-auto space-y-3 text-xs">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div className="text-[10px] text-slate-500 mb-0.5 px-1">
              {m.role === 'user' ? 'Giáo viên' : 'Trợ giảng AI'} • {m.time}
            </div>
            <div
              className={`max-w-[92%] p-2.5 rounded-xl leading-relaxed whitespace-pre-wrap ${
                m.role === 'user'
                  ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white rounded-br-none shadow-md shadow-cyan-900/20'
                  : 'bg-slate-900/90 text-slate-200 border border-slate-800 rounded-bl-none'
              }`}
            >
              <MathText text={m.text} />

              {/* HỘP ĐỀ XUẤT BẢN VÁ LIVE PATCH */}
              {m.patchProposal && (
                <div className="mt-2.5 pt-2 border-t border-slate-700/80 space-y-1.5">
                  <div className="text-[10px] font-bold text-amber-400 flex items-center gap-1">
                    <span>⚡ Đề xuất cập nhật nội dung Slide:</span>
                  </div>
                  <button
                    onClick={() => handleApplyPatchClick(m.patchProposal, idx)}
                    disabled={m.isPatched}
                    className={`w-full py-1.5 px-2 rounded-lg text-[11px] font-bold flex items-center justify-center gap-1.5 transition ${
                      m.isPatched
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800 opacity-80'
                        : 'bg-amber-600 hover:bg-amber-500 text-white shadow-md shadow-amber-950/40'
                    }`}
                  >
                    {m.isPatched ? (
                      <>
                        <Check size={13} /> Đã áp dụng vào Slide {(m.patchProposal.target_slide_index ?? currentSlide) + 1}
                      </>
                    ) : (
                      <>
                        <span>Áp dụng vào Slide {(m.patchProposal.target_slide_index ?? currentSlide) + 1}</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {isThinking && (
          <div className="flex items-center gap-2 text-xs text-slate-400 p-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
            <span>Trợ giảng AI đang suy nghĩ...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
        className="p-2.5 border-t border-slate-800 bg-slate-950/60"
      >
        <div className="flex items-center gap-1.5 bg-slate-900 rounded-xl px-2.5 py-1 border border-slate-700/80 focus-within:border-cyan-500 transition">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Nhắn cho trợ giảng (Enter)..."
            className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none py-1.5"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isThinking}
            className="p-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white disabled:opacity-40 transition"
          >
            <Send size={13} />
          </button>
        </div>
      </form>
    </aside>
  );
}
