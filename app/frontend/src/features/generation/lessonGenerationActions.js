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
  const createSessionId = () => `lesson-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  const handleGenerateOutline = async (config) => {
    const epoch=generationEpoch?.current;
    setIsGeneratingOutline(true);
    setPresentationConfig(config);
    const sessionId = config.session_id || createSessionId();
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
          aspect_ratio: config.aspect_ratio || '16:9',
          session_id: sessionId
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
        session_id: data.session_id || sessionId,
        outline_slides: normalizedSlides
      });
      setActiveScreen('outline');
    } catch (err) {
      console.warn('Sử dụng dàn ý sư phạm thích ứng do gián đoạn AI:', err);
      // Zero-Crash Curated Local Fallback Outline
      const fallbackOutline = {
        topic: config.topic,
        title: `Dàn Ý: ${config.topic}`,
        subject: config.subject || 'Toán học',
        grade: parseInt(config.grade, 10) || 12,
        lesson_id: config.lesson_id || 'OUTLINE-LOCAL',
        session_id: sessionId,
        total_slides: 6,
        outline_slides: [
          {
            id: 'outline-slide-1',
            slide_number: 1,
            slide_index: 1,
            title: `Khởi Động: Đặt Vấn Đề Thực Tiễn - ${config.topic}`,
            activity_type: 'Khởi động',
            visual_type: 'Concept Highlight',
            bullet_points: [
              'Quan sát tình huống thực tế và đặt câu hỏi định hướng',
              'Gợi mở nhu cầu khám phá tri thức mới cho học sinh',
              'Mục tiêu cần đạt theo định hướng GDPT 2018'
            ],
            key_points: [
              'Quan sát tình huống thực tế và đặt câu hỏi định hướng',
              'Gợi mở nhu cầu khám phá tri thức mới cho học sinh',
              'Mục tiêu cần đạt theo định hướng GDPT 2018'
            ],
            has_3d: false,
            has_function_plot: false,
            has_quiz: false,
            estimated_minutes: 5
          },
          {
            id: 'outline-slide-2',
            slide_number: 2,
            slide_index: 2,
            title: 'Khám Phá: Khái Niệm & Định Nghĩa Trọng Tâm',
            activity_type: 'Hình thành kiến thức',
            visual_type: 'Concept Highlight',
            bullet_points: [
              'Hình thành định nghĩa chuẩn xác theo SGK Kết Nối Tri Thức',
              'Công thức toán học và điều kiện áp dụng cơ bản',
              'Ví dụ nhận diện trực tiếp trong các trường hợp đơn giản'
            ],
            key_points: [
              'Hình thành định nghĩa chuẩn xác theo SGK Kết Nối Tri Thức',
              'Công thức toán học và điều kiện áp dụng cơ bản',
              'Ví dụ nhận diện trực tiếp trong các trường hợp đơn giản'
            ],
            has_3d: false,
            has_function_plot: false,
            has_quiz: false,
            estimated_minutes: 10
          },
          {
            id: 'outline-slide-3',
            slide_number: 3,
            slide_index: 3,
            title: 'Trực Quan Hóa Đa Chiều: Không Gian & Đồ Thị',
            activity_type: 'Mô hình hóa 3D',
            visual_type: config.topic.toLowerCase().includes('đồ thị') ? '2D Function Plot' : '3D Geometry',
            bullet_points: [
              'Mô hình trực quan 3D WebGL / Đồ thị giải tích trực quan',
              'Thao tác xoay 360 độ, phóng to, thu nhỏ và khai triển 2D',
              'Phát hiện tính chất hình học và liên hệ trực tiếp với công thức đại số'
            ],
            key_points: [
              'Mô hình trực quan 3D WebGL / Đồ thị giải tích trực quan',
              'Thao tác xoay 360 độ, phóng to, thu nhỏ và khai triển 2D',
              'Phát hiện tính chất hình học và liên hệ trực tiếp với công thức đại số'
            ],
            has_3d: !config.topic.toLowerCase().includes('đồ thị'),
            has_function_plot: config.topic.toLowerCase().includes('đồ thị'),
            has_quiz: false,
            estimated_minutes: 10
          },
          {
            id: 'outline-slide-4',
            slide_number: 4,
            slide_index: 4,
            title: 'Luyện Tập: Phương Pháp Giải & Bài Tập Tiêu Biểu',
            activity_type: 'Luyện tập & Vận dụng',
            visual_type: 'Formula Breakdown',
            bullet_points: [
              'Hệ thống hóa các bước giải toán từng bước (Step-by-step)',
              'Phân tích các lỗi học sinh thường mắc phải và cách khắc phục',
              'Lời giải chi tiết và nhận xét phương pháp tối ưu'
            ],
            key_points: [
              'Hệ thống hóa các bước giải toán từng bước (Step-by-step)',
              'Phân tích các lỗi học sinh thường mắc phải và cách khắc phục',
              'Lời giải chi tiết và nhận xét phương pháp tối ưu'
            ],
            has_3d: false,
            has_function_plot: false,
            has_quiz: false,
            estimated_minutes: 10
          },
          {
            id: 'outline-slide-5',
            slide_number: 5,
            slide_index: 5,
            title: 'Củng Cố: Trắc Nghiệm Tương Tác & Live Poll',
            activity_type: 'Trắc nghiệm & Live Poll',
            visual_type: 'Interactive Quiz',
            bullet_points: [
              'Câu hỏi trắc nghiệm 4 lựa chọn A, B, C, D kiểm tra nhận thức',
              'Học sinh tham gia biểu quyết và nhận kết quả tức thì',
              'Giải thích chi tiết phương án đúng và phân tích bẫy phương án sai'
            ],
            key_points: [
              'Câu hỏi trắc nghiệm 4 lựa chọn A, B, C, D kiểm tra nhận thức',
              'Học sinh tham gia biểu quyết và nhận kết quả tức thì',
              'Giải thích chi tiết phương án đúng và phân tích bẫy phương án sai'
            ],
            has_3d: false,
            has_function_plot: false,
            has_quiz: true,
            estimated_minutes: 7
          },
          {
            id: 'outline-slide-6',
            slide_number: 6,
            slide_index: 6,
            title: 'Vận Dụng Thực Tế & Tổng Kết Tiết Học',
            activity_type: 'Vận dụng',
            visual_type: 'Summary Mindmap',
            bullet_points: [
              'Sơ đồ tư duy tóm tắt toàn bộ kiến thức then chốt',
              'Bài toán liên môn và ứng dụng thực tiễn trong kỹ thuật',
              'Nhiệm vụ rèn luyện tại nhà và định hướng bài học tiếp theo'
            ],
            key_points: [
              'Sơ đồ tư duy tóm tắt toàn bộ kiến thức then chốt',
              'Bài toán liên môn và ứng dụng thực tiễn trong kỹ thuật',
              'Nhiệm vụ rèn luyện tại nhà và định hướng bài học tiếp theo'
            ],
            has_3d: false,
            has_function_plot: false,
            has_quiz: false,
            estimated_minutes: 3
          }
        ]
      };
      setOutline(fallbackOutline);
      setActiveScreen('outline');
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
      outcome: recommendedOutcome,
      outline_slides: outline?.outline_slides || [],
      session_id: outline?.session_id || presentationConfig?.session_id
    };
    await handleGenerateFromAi(params);
  };

  // ================= HÀM GỌI AI SINH THẬT TOÀN BỘ BÀI DẠY =================
  const handleGenerateFromAi = async (params) => {
    const epoch=generationEpoch?.current;
    setIsAiGenerating(true);
    setGenerationStep('Đang gửi yêu cầu và kết nối Gemini AI...');
    const sessionId = params.session_id || outline?.session_id || createSessionId();
    const approvedOutlineSlides = params.outline_slides || outline?.outline_slides || undefined;

    try {
      // 1. Gọi API sinh Kế hoạch bài dạy 5512 thật (Role-Based Prompt Chain)
      setGenerationStep('AI đang phân tích Khung sư phạm & soạn Kế hoạch 5512...');
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
          target_outcome: params.outcome || '',
          outline_slides: approvedOutlineSlides,
          session_id: sessionId
        });

      if (!planRes.ok) throw new Error(`Lỗi sinh giáo án: HTTP ${planRes.status}`);
      const planData = await planRes.json();
      if (!planData.plan || planData.is_valid === false) throw new Error('Giáo án chưa đạt kiểm tra cấu trúc: ' + (planData.errors || []).join('; '));

      // 2. Gọi API sinh SlideDeck đồng bộ với Kế hoạch & Dàn ý đã duyệt (Role-Based Prompt Chain)
      setGenerationStep('AI đang thiết kế Kịch bản Slide, Đồ thị & Trắc nghiệm...');
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
          plan: planData.plan,
          outline_slides: approvedOutlineSlides,
          session_id: sessionId
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
