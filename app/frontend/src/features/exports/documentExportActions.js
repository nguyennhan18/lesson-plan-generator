import { postJson } from '../../shared/api/client.js';

async function readExportResponse(response, expectedType) {
  const contentType = response.headers?.get('content-type')?.split(';')[0];
  if (!response.ok || contentType !== expectedType) {
    let message = '';
    if (contentType === 'application/json') {
      const error = await response.json();
      const detail = error.detail ?? error;
      message = typeof detail === 'string' ? detail : detail.message || 'Dữ liệu xuất không hợp lệ';
    }
    throw new Error(`HTTP ${response.status}: ${message || 'Máy chủ chưa trả đúng định dạng tệp'}`);
  }
  const blob = await response.blob();
  const bytes = new Uint8Array(await blob.slice(0,4).arrayBuffer());
  if (bytes[0] !== 0x50 || bytes[1] !== 0x4b || bytes[2] !== 3 || bytes[3] !== 4) throw new Error('Tệp trả về không phải gói Office/ZIP hợp lệ');
  return blob;
}
/**
 * Xuất Word, PowerPoint và ZIP từ dữ liệu do App quản lý.
 * Tạo lại các action mỗi lần render để luôn dùng trạng thái hiện tại.
 */
export function createDocumentExportActions({
  lessonPlan,
  hasPendingEdits=false,
  slideDeck,
  currentSlide,
  threeCanvasCaptureRef
}) {
  // ================= HÀM XUẤT FILE THẬT QUA FASTAPI =================
  const handleExportDocx = async () => {
    if(hasPendingEdits){alert("Có thay đổi chưa lưu. Hãy lưu slide trước khi xuất bài.");return;}
    if (!lessonPlan) {
      alert("Chưa có dữ liệu Kế hoạch bài dạy để xuất Word. Hãy bấm 'Sinh Giáo Án Bằng AI' trước!");
      return;
    }
    try {
      // Gửi kèm SlideDeck để backend đồng bộ hóa câu hỏi củng cố và thiết bị dạy học (Task 19.1)
      const docxPayload = slideDeck
        ? { plan: lessonPlan, slide_deck: slideDeck }
        : lessonPlan;

      const res = await postJson('/api/v1/lesson-plan/export-docx', docxPayload);
      const blob = await readExportResponse(res, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Giao_An_5512_${lessonPlan.lesson_title || 'Toan'}.docx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Lỗi khi tải file Word: " + e.message);
    }
  };

  const handleExportPptx = async () => {
    if(hasPendingEdits){alert("Có thay đổi chưa lưu. Hãy lưu slide trước khi xuất bài.");return;}
    if (!slideDeck || !slideDeck.slides?.length) {
      alert("Chưa có dữ liệu Slide để xuất PowerPoint!");
      return;
    }

    const payloadDeck = structuredClone(slideDeck);

    try {
      const res = await postJson('/api/v1/lesson-plan/export-slide', payloadDeck);
      const blob = await readExportResponse(res, 'application/vnd.openxmlformats-officedocument.presentationml.presentation');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Slide_${slideDeck.presentation_title || 'BaiGiang'}.pptx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Lỗi khi tải file PowerPoint: " + e.message);
    }
  };

  // Task 19.2: Tải Trọn Bộ Dual-Pack (.zip) đóng gói cả Kế hoạch bài dạy Word & Slide PowerPoint
  const handleExportDualPackage = async () => {
    if(hasPendingEdits){alert("Có thay đổi chưa lưu. Hãy lưu slide trước khi xuất bài.");return;}
    if (!lessonPlan && (!slideDeck || !slideDeck.slides?.length)) {
      alert("Chưa có dữ liệu Kế hoạch bài dạy hoặc Slide để xuất trọn bộ ZIP. Vui lòng bấm 'Sinh Giáo Án Bằng AI' trước!");
      return;
    }

    const payloadDeck = slideDeck ? structuredClone(slideDeck) : null;

    const dualPayload = {
      plan: lessonPlan,
      slide_deck: payloadDeck
    };

    try {
      const res = await postJson('/api/v1/lesson-plan/export-dual-package', dualPayload);
      const blob = await readExportResponse(res, 'application/zip');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const title = lessonPlan?.lesson_title || slideDeck?.presentation_title || 'LessonAI_5512';
      const cleanTitle = title.replace(/\s+/g, '_');
      a.download = `Tron_Bo_Giao_An_Va_Slide_${cleanTitle}.zip`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Lỗi khi tải gói kép ZIP: " + e.message);
    }
  };

  return { handleExportDocx, handleExportPptx, handleExportDualPackage };
}
