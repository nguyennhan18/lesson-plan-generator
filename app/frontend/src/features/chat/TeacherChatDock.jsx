import { postJson } from '../../shared/api/client.js';
import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Trash2, ChevronLeft, Sparkles, Check } from 'lucide-react';
import MathText from '../../shared/math/MathText';

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
    'Giải thích slide này đơn giản hơn',
    'Gợi ý 2 câu hỏi gợi mở cho học sinh',
    'Thêm 1 câu hỏi trắc nghiệm củng cố',
    'Đổi bài toán sang ví dụ thực tế'
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
      const res = await postJson('/api/v1/chat/interact', {
          session_id: 'session_teacher_dock',
          user_message: text,
          current_slide_index: currentSlide,
          slide_deck: slideDeck
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
          patchProposal: data.suggested_patch || data.patch_proposal || null
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
        alert(`Đã áp dụng thành công bản vá vào Slide ${(patch.target_slide_index ?? currentSlide) + 1}!`);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <aside className="w-80 bg-[#ffffff] border-r border-[#e0e0e0] flex flex-col justify-between h-full transition-all duration-300 z-10 shrink-0">
      {/* Header */}
      <div className="p-3 border-b border-[#e0e0e0] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-[30%] bg-[#141414] text-white flex items-center justify-center shrink-0">
            <Bot size={17} />
          </div>
          <div>
            <h3 className="text-xs font-bold text-[#141414] flex items-center gap-1.5 leading-tight">
              Trợ Giảng AI Co-pilot
              <span className="w-2 h-2 rounded-full bg-[#10b981]"></span>
            </h3>
            <p className="text-[11px] text-[#707070] leading-tight">Đang theo dõi • Slide {currentSlide + 1}</p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setMessages([{
              role: 'assistant',
              text: `Đã làm mới phiên hỗ trợ! Em đang sẵn sàng cùng Thầy/Cô tại Slide ${currentSlide + 1}.`,
              time: '08:00'
            }])}
            className="p-1.5 rounded-full text-[#707070] hover:text-[#141414] hover:bg-[#f3f3f3] transition cursor-pointer"
            title="Làm mới chat"
          >
            <Trash2 size={15} />
          </button>
          <button
            onClick={onToggle}
            className="p-1.5 rounded-full text-[#707070] hover:text-[#141414] hover:bg-[#f3f3f3] transition cursor-pointer"
            title="Thu gọn khung chat (Phím C)"
          >
            <ChevronLeft size={16} />
          </button>
        </div>
      </div>

      {/* Quick Chips - Stadium Pills */}
      <div className="p-2.5 border-b border-[#f0f0f0] bg-[#ffffff] space-y-1.5">
        {quickChips.map((chip, idx) => (
          <button
            key={idx}
            onClick={() => sendMessage(chip)}
            className="w-full text-left text-[11px] px-3 py-1.5 rounded-full bg-[#f3f3f3] hover:bg-[#e0e0e0] text-[#141414] font-medium transition flex items-center gap-1.5 truncate cursor-pointer"
          >
            <Sparkles size={11} className="text-[#141414] shrink-0" />
            <span className="truncate">{chip}</span>
          </button>
        ))}
      </div>

      {/* Messages Stream */}
      <div className="flex-1 p-3 overflow-y-auto space-y-3 text-xs bg-[#ffffff]">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div className="text-[10px] text-[#707070] mb-0.5 px-1">
              {m.role === 'user' ? 'Giáo viên' : 'Trợ giảng AI'} • {m.time}
            </div>
            <div
              className={`max-w-[92%] p-3 rounded-2xl leading-relaxed whitespace-pre-wrap ${
                m.role === 'user'
                  ? 'bg-[#141414] text-white rounded-br-sm'
                  : 'bg-[#f3f3f3] text-[#141414] border border-[#e0e0e0] rounded-bl-sm'
              }`}
            >
              <MathText text={m.text} />

              {/* HỘP ĐỀ XUẤT BẢN VÁ LIVE PATCH */}
              {m.patchProposal && (
                <div className="mt-2.5 pt-2 border-t border-[#e0e0e0] space-y-1.5">
                  <div className="text-[10px] font-bold text-[#141414] flex items-center gap-1">
                    <span>Đề xuất cập nhật nội dung Slide:</span>
                  </div>
                  {m.patchProposal.preview_explanation && (
                    <div className="text-[10px] text-[#707070] italic">
                      {m.patchProposal.preview_explanation}
                    </div>
                  )}
                  <button
                    onClick={() => handleApplyPatchClick(m.patchProposal, idx)}
                    disabled={m.isPatched}
                    className={`w-full py-2 px-3 rounded-full text-xs font-semibold flex items-center justify-center gap-1.5 transition cursor-pointer ${
                      m.isPatched
                        ? 'bg-[#f3f3f3] text-[#707070] border border-[#e0e0e0] opacity-90'
                        : 'bg-[#141414] hover:bg-[#262626] text-white'
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
          <div className="flex items-center gap-2 text-xs text-[#707070] p-2">
            <span className="w-2 h-2 rounded-full bg-[#141414] animate-ping"></span>
            <span>Trợ giảng AI đang suy nghĩ...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
        className="p-3 border-t border-[#e0e0e0] bg-[#ffffff]"
      >
        <div className="flex items-center gap-2 bg-[#f0f0f0] rounded-full px-3 py-1 focus-within:ring-2 focus-within:ring-[#141414] focus-within:bg-[#ffffff] border border-transparent transition">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Nhắn cho trợ giảng (Enter)..."
            className="flex-1 bg-transparent text-xs text-[#141414] placeholder-[#adadad] focus:outline-none py-1.5"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isThinking}
            className="p-1.5 rounded-full bg-[#141414] hover:bg-[#262626] text-white disabled:opacity-30 transition cursor-pointer"
          >
            <Send size={13} />
          </button>
        </div>
      </form>
    </aside>
  );
}
