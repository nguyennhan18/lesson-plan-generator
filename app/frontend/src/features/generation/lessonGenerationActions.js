import { postJson } from '../../shared/api/client.js';
/** Dàn ý và quy trình sinh giáo án → slide; trạng thái được truyền từ App. */
export function createLessonGenerationActions({
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
  setPolyhedronType, projectId, generationEpoch
}) {
  // ================= TRẠM 1 -> TRẠM 2: KHỞI TẠO DÀN Ý BÀI GIẢNG =================
  const handleGenerateOutline = async (config) => {
    const epoch=generationEpoch?.current;
    setIsGeneratingOutline(true);
    setPresentationConfig(config);
    try {
      const res = await postJson('/api/v1/presentation/outline', {
          topic: config.topic,
          subject: config.subject || 'Toán học',
          grade: parseInt(config.grade, 10) || 12,
          num_slides: parseInt(config.num_slides, 10) || 8,
          lesson_id: config.lesson_id || undefined,
          class_proficiency: config.class_proficiency || 'standard',
          use_rag: config.use_rag !== undefined ? config.use_rag : true,
          model_provider: config.model_provider || 'gemini',
          model_id: config.model_id || null,
          tone: config.tone || 'academic',
          text_content: config.text_content || 'concise',
          aspect_ratio: config.aspect_ratio || '16:9'
        });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      if(generationEpoch&&generationEpoch.current!==epoch)return;
      const normalizedSlides = (data.outline_slides || []).map((s, idx) => ({
        ...s,
        id: s.id || `outline-slide-${idx + 1}`,
        slide_index: s.slide_index || s.slide_number || idx + 1,
        bullet_points: s.bullet_points || s.key_points || [],
        key_points: s.key_points || s.bullet_points || []
      }));
      setOutline({
        ...data,
        outline_slides: normalizedSlides
      });
      setActiveScreen('outline');
    } catch (err) {
      alert(`Không tạo được dàn ý: ${err.message}. Nội dung đang soạn được giữ nguyên.`);
    } finally {
      setIsGeneratingOutline(false);
    }
  };

  // ================= TRẠM 2 -> TRẠM 3: SINH BÀI GIẢNG TỪ DÀN Ý ĐÃ DUYỆT =================
  const handleGenerateFromOutline = async () => {
    if (!outline?.outline_slides?.length) { alert('Chưa có dàn ý đã duyệt.'); return; }
    const params = {
      approved_outline: structuredClone(outline),
      model_provider: presentationConfig.model_provider,
      model_id: presentationConfig.model_id,
      topic: outline?.topic || presentationConfig.topic,
      subject: outline?.subject || presentationConfig.subject || 'Toán học',
      grade: outline?.grade || presentationConfig.grade || 12,
      lesson_id: outline?.lesson_id || presentationConfig.lesson_id,
      use_rag: presentationConfig.use_rag,
      proficiency: presentationConfig.class_proficiency || classProficiency || 'standard',
      outcome: recommendedOutcome
    };
    await handleGenerateFromAi(params);
  };

  // ================= HÀM GỌI AI SINH THẬT TOÀN BỘ BÀI DẠY =================
  const handleGenerateFromAi = async (params) => {
    const epoch=generationEpoch?.current;
    setIsAiGenerating(true);
    setGenerationStep('Đang gửi yêu cầu và kết nối dịch vụ AI...');

    try {
      // 1. Gọi API sinh Kế hoạch bài dạy 5512 thật
      setGenerationStep('Hệ thống đang phân tích sư phạm và soạn Kế hoạch 5512...');
      const planRes = await postJson('/api/v1/lesson-plan/generate', {
          approved_outline: params.approved_outline,
          model_provider: params.model_provider,
          model_id: params.model_id,
          topic: params.topic,
          subject: params.subject,
          grade: parseInt(params.grade, 10),
          lesson_id: params.lesson_id || undefined,
          use_rag: params.use_rag !== undefined ? params.use_rag : true,
          class_proficiency: params.proficiency || 'standard',
          target_outcome: params.outcome || ''
        });

      if (!planRes.ok) throw new Error(`Lỗi sinh giáo án: HTTP ${planRes.status}`);
      const planData = await planRes.json();
      if (!planData.plan || planData.is_valid === false) throw new Error('Giáo án chưa đạt kiểm tra cấu trúc: ' + (planData.errors || []).join('; '));

      // 2. Gọi API sinh SlideDeck đồng bộ với Kế hoạch vừa sinh
      setGenerationStep('Hệ thống đang thiết kế bộ Slide bài giảng tương ứng...');
      const slideRes = await postJson('/api/v1/slide/generate', {
          approved_outline: params.approved_outline,
          model_provider: params.model_provider,
          model_id: params.model_id,
          topic: params.topic,
          subject: params.subject,
          grade: parseInt(params.grade, 10),
          lesson_id: params.lesson_id || undefined,
          use_rag: params.use_rag !== undefined ? params.use_rag : true,
          class_proficiency: params.proficiency || 'standard',
          target_outcome: params.outcome || '',
          plan: planData.plan
        });

      if (!slideRes.ok) throw new Error(`Lỗi sinh slide: HTTP ${slideRes.status}`);
      const slideData = await slideRes.json();
      if (!slideData.slides?.length) throw new Error("Máy chủ chưa trả nội dung slide");
      if(generationEpoch&&generationEpoch.current!==epoch)return;
      setLessonPlan(planData.plan);
      setSlideDeck({...slideData,project_id:projectId||slideData.project_id});
      setCurrentSlide(0);

      setActiveScreen('presentation');
      alert(`Đã tạo bản nháp cần duyệt gồm giáo án và ${slideData.slides?.length || 0} slide cho chủ đề: "${params.topic}"!`);
    } catch (err) {
      console.error(err);
      alert(`Không thể sinh bài từ AI: ${err.message}. Vui lòng kiểm tra kết nối và cấu hình nhà cung cấp.`);
    } finally {
      setIsAiGenerating(false);
      setGenerationStep('');
    }
  };

  return { handleGenerateOutline, handleGenerateFromOutline, handleGenerateFromAi };
}
