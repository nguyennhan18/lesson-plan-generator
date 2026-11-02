import { postJson } from '../../shared/api/client.js';
/** Dàn ý và quy trình sinh giáo án → slide; trạng thái được truyền từ App. */
export const defaultInitialOutline = {
  topic: 'Hệ trục tọa độ trong không gian Oxyz',
  title: 'Dàn Ý: Hệ Trục Tọa Độ Trong Không Gian Oxyz',
  subject: 'Toán học',
  grade: 12,
  lesson_id: 'M12-C2-B2',
  total_slides: 6,
  outline_slides: [
    {
      id: 'outline-slide-1',
      slide_number: 1,
      slide_index: 1,
      title: 'Khởi Động: Không Gian 3 Chiều Quanh Ta',
      activity_type: 'Khởi động',
      visual_type: 'Concept Highlight',
      bullet_points: [
        'Liên hệ thực tiễn vị trí của một máy bay trên bầu trời với kinh độ, vĩ độ và độ cao.',
        'Nhu cầu thiết lập hệ tọa độ 3 chiều để xác định vị trí một điểm bất kỳ trong không gian.',
        'Mục tiêu cần đạt: Nắm vững định nghĩa 3 trục Ox, Oy, Oz và các mặt phẳng tọa độ.'
      ],
      key_points: [
        'Liên hệ thực tiễn vị trí của một máy bay trên bầu trời với kinh độ, vĩ độ và độ cao.',
        'Nhu cầu thiết lập hệ tọa độ 3 chiều để xác định vị trí một điểm bất kỳ trong không gian.',
        'Mục tiêu cần đạt: Nắm vững định nghĩa 3 trục Ox, Oy, Oz và các mặt phẳng tọa độ.'
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
      title: 'Khám Phá: Định Nghĩa Hệ Trục Tọa Độ Oxyz',
      activity_type: 'Hình thành kiến thức',
      visual_type: 'Concept Highlight',
      bullet_points: [
        'Hệ gồm 3 trục Ox, Oy, Oz vuông góc với nhau từng đôi một tại gốc O.',
        'Các vectơ đơn vị tương ứng i, j, k thỏa mãn |i| = |j| = |k| = 1 và i.j = j.k = k.i = 0.',
        'Các mặt phẳng tọa độ: Mặt phẳng (Oxy), (Oyz), (Ozx).'
      ],
      key_points: [
        'Hệ gồm 3 trục Ox, Oy, Oz vuông góc với nhau từng đôi một tại gốc O.',
        'Các vectơ đơn vị tương ứng i, j, k thỏa mãn |i| = |j| = |k| = 1 và i.j = j.k = k.i = 0.',
        'Các mặt phẳng tọa độ: Mặt phẳng (Oxy), (Oyz), (Ozx).'
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
      title: 'Trực Quan Hóa 3D: Tọa Độ Điểm M(x, y, z)',
      activity_type: 'Mô hình hóa 3D',
      visual_type: '3D Geometry',
      bullet_points: [
        'Biểu diễn vectơ OM = x*i + y*j + z*k thông qua hình hộp chữ nhật trong không gian.',
        'Chiếu điểm M vuông góc lên các trục Ox, Oy, Oz để tìm tọa độ x, y, z.',
        'Tương tác xoay 360 độ và quan sát hình chiếu điểm M lên các mặt phẳng tọa độ.'
      ],
      key_points: [
        'Biểu diễn vectơ OM = x*i + y*j + z*k thông qua hình hộp chữ nhật trong không gian.',
        'Chiếu điểm M vuông góc lên các trục Ox, Oy, Oz để tìm tọa độ x, y, z.',
        'Tương tác xoay 360 độ và quan sát hình chiếu điểm M lên các mặt phẳng tọa độ.'
      ],
      has_3d: true,
      has_function_plot: false,
      has_quiz: false,
      estimated_minutes: 12
    },
    {
      id: 'outline-slide-4',
      slide_number: 4,
      slide_index: 4,
      title: 'Luyện Tập: Tọa Độ Của Vectơ & Các Phép Toán',
      activity_type: 'Luyện tập & Vận dụng',
      visual_type: 'Formula Breakdown',
      bullet_points: [
        'Tọa độ của tổng, hiệu hai vectơ và tích của một số với một vectơ.',
        'Tích vô hướng của hai vectơ: u.v = x1*x2 + y1*y2 + z1*z2.',
        'Tính độ dài vectơ và khoảng cách giữa hai điểm trong không gian.'
      ],
      key_points: [
        'Tọa độ của tổng, hiệu hai vectơ và tích của một số với một vectơ.',
        'Tích vô hướng của hai vectơ: u.v = x1*x2 + y1*y2 + z1*z2.',
        'Tính độ dài vectơ và khoảng cách giữa hai điểm trong không gian.'
      ],
      has_3d: false,
      has_function_plot: false,
      has_quiz: false,
      estimated_minutes: 8
    },
    {
      id: 'outline-slide-5',
      slide_number: 5,
      slide_index: 5,
      title: 'Củng Cố: Trắc Nghiệm Tương Tác & Live Poll',
      activity_type: 'Trắc nghiệm & Live Poll',
      visual_type: 'Interactive Quiz',
      bullet_points: [
        'Câu hỏi kiểm tra nhanh: Xác định tọa độ hình chiếu của điểm M(2; -3; 5) lên mặt phẳng (Oxy).',
        'Biểu quyết trực tiếp lớp học và phân tích tỉ lệ chọn các phương án A, B, C, D.',
        'Khắc sâu quy tắc: Chiếu lên mặt phẳng nào thì giữ nguyên tọa độ đó, thành phần còn lại bằng 0.'
      ],
      key_points: [
        'Câu hỏi kiểm tra nhanh: Xác định tọa độ hình chiếu của điểm M(2; -3; 5) lên mặt phẳng (Oxy).',
        'Biểu quyết trực tiếp lớp học và phân tích tỉ lệ chọn các phương án A, B, C, D.',
        'Khắc sâu quy tắc: Chiếu lên mặt phẳng nào thì giữ nguyên tọa độ đó, thành phần còn lại bằng 0.'
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
        'Ứng dụng hệ tọa độ Oxyz trong công nghệ định vị GPS, mô phỏng đồ họa 3D và kiến trúc xây dựng.',
        'Sơ đồ tư duy liên kết: Gốc O -> 3 Trục -> Tọa độ Vectơ -> Tọa độ Điểm.',
        'Nhiệm vụ về nhà: Bài tập 2.1 - 2.8 SGK Toán 12 Tập 1.'
      ],
      key_points: [
        'Ứng dụng hệ tọa độ Oxyz trong công nghệ định vị GPS, mô phỏng đồ họa 3D và kiến trúc xây dựng.',
        'Sơ đồ tư duy liên kết: Gốc O -> 3 Trục -> Tọa độ Vectơ -> Tọa độ Điểm.',
        'Nhiệm vụ về nhà: Bài tập 2.1 - 2.8 SGK Toán 12 Tập 1.'
      ],
      has_3d: false,
      has_function_plot: false,
      has_quiz: false,
      estimated_minutes: 3
    }
  ]
};

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
  setPolyhedronType
}) {
  // ================= TRẠM 1 -> TRẠM 2: KHỞI TẠO DÀN Ý BÀI GIẢNG =================
  const handleGenerateOutline = async (config) => {
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
          model_id: config.model_id || 'gemini-2.5-flash',
          tone: config.tone || 'academic',
          text_content: config.text_content || 'concise',
          aspect_ratio: config.aspect_ratio || '16:9'
        });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
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
      console.warn('Sử dụng dàn ý sư phạm thích ứng do gián đoạn AI:', err);
      // Zero-Crash Curated Local Fallback Outline
      const fallbackOutline = {
        topic: config.topic,
        title: `Dàn Ý: ${config.topic}`,
        subject: config.subject || 'Toán học',
        grade: parseInt(config.grade, 10) || 12,
        lesson_id: config.lesson_id || 'OUTLINE-LOCAL',
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
    const params = {
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
    setIsAiGenerating(true);
    setGenerationStep('Đang gửi yêu cầu và kết nối Gemini AI...');

    try {
      // 1. Gọi API sinh Kế hoạch bài dạy 5512 thật
      setGenerationStep('Gemini đang phân tích sư phạm và soạn Kế hoạch 5512...');
      const planRes = await postJson('/api/v1/lesson-plan/generate', {
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
      setLessonPlan(planData.plan);

      // 2. Gọi API sinh SlideDeck đồng bộ với Kế hoạch vừa sinh
      setGenerationStep('Gemini đang thiết kế bộ Slide bài giảng tương ứng...');
      const slideRes = await postJson('/api/v1/slide/generate', {
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
      setSlideDeck(slideData);
      setCurrentSlide(0);

      // Tự động nhận diện mô hình 3D nếu chủ đề là Hình học không gian
      const lowerTopic = params.topic.toLowerCase();
      if (lowerTopic.includes('lập phương')) setPolyhedronType('cube');
      else if (lowerTopic.includes('chóp tam giác')) setPolyhedronType('triangular_pyramid');
      else if (lowerTopic.includes('chóp tứ giác') || lowerTopic.includes('s.abcd')) setPolyhedronType('rectangular_pyramid');

      // Chuyển thẳng về Màn hình Trình Chiếu để giáo viên bắt đầu tiết học
      setActiveScreen('presentation');
      alert(`Đã gọi Gemini AI sinh thành công Kế hoạch bài dạy và ${slideData.slides?.length || 0} slide cho chủ đề: "${params.topic}"!`);
    } catch (err) {
      console.error(err);
      alert(`Không thể sinh bài từ AI: ${err.message}. Vui lòng kiểm tra server FastAPI và GEMINI_API_KEY.`);
    } finally {
      setIsAiGenerating(false);
      setGenerationStep('');
    }
  };

  return { handleGenerateOutline, handleGenerateFromOutline, handleGenerateFromAi };
}
