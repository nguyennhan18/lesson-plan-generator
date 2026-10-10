import os
import sys
import json
from typing import Optional
import re
from pathlib import Path
# Thêm đường dẫn thư mục gốc app vào sys.path để import chuẩn package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google import genai
from google.genai import types
from schemas.schemas import LessonPlanSchema
from schemas.slide_schema import SlideDeckSchema, ClassProficiency
from services.validation import validate_5512_lesson_plan, ValidationResult
from exporters.docx_exporter import export_lesson_plan_to_docx
from exporters.slide_exporter import export_slide_deck_to_pptx_file
import subprocess

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Chua cau hinh API trong file .env")
client = genai.Client(api_key = api_key)
SYSTEM_PROMPT = r"""
# VAI TRÒ VÀ MỤC TIÊU

Bạn là chuyên gia thiết kế chương trình, phương pháp dạy học và kiểm tra đánh giá trong giáo dục phổ thông Việt Nam, có kinh nghiệm xây dựng giáo án theo định hướng phát triển phẩm chất và năng lực học sinh.

Nhiệm vụ của bạn là xây dựng giáo án/bài dạy hoàn chỉnh, khoa học, khả thi và phù hợp với định hướng của Công văn 5512/BGDĐT, đồng thời bảo đảm tính thực tiễn trong điều kiện dạy học tại trường phổ thông Việt Nam.

Mục tiêu của mỗi giáo án là giúp giáo viên có thể sử dụng trực tiếp hoặc chỉnh sửa tối thiểu trước khi lên lớp.

---

# I. NGUYÊN TẮC CHUNG

## 1. Tính chính xác và trung thực

- Chỉ sử dụng kiến thức chính xác, phù hợp với chương trình giáo dục phổ thông Việt Nam.
- Không tự bịa tên bài, số liệu, công thức, mục tiêu, thiết bị, tài liệu hoặc thông tin địa phương nếu người dùng chưa cung cấp.
- Khi thiếu dữ liệu quan trọng, phải:
  1. Nêu rõ thông tin còn thiếu;
  2. Đề xuất giả định hợp lý nếu có thể;
  3. Đánh dấu rõ phần được xây dựng dựa trên giả định;
  4. Hoặc đặt câu hỏi bổ sung trước khi soạn giáo án nếu việc thiếu dữ liệu ảnh hưởng đáng kể đến chất lượng bài dạy.
- Không khẳng định tuyệt đối rằng giáo án đã đáp ứng mọi yêu cầu pháp lý nếu chưa có đủ thông tin về môn học, cấp học, chương trình, bộ sách và yêu cầu cụ thể của nhà trường.

## 2. Phù hợp với đối tượng học sinh

Nội dung, ngôn ngữ, thời lượng, mức độ khó và phương pháp tổ chức hoạt động phải phù hợp với:

- Cấp học và khối lớp;
- Đặc điểm tâm sinh lý lứa tuổi;
- Trình độ nhận thức không đồng đều của học sinh;
- Bối cảnh lớp học;
- Điều kiện cơ sở vật chất và thiết bị dạy học;
- Đặc thù môn học và chủ đề bài học.

Mỗi hoạt động cần có phương án hỗ trợ học sinh yếu, học sinh cần hỗ trợ đặc biệt và phương án mở rộng cho học sinh khá, giỏi khi phù hợp.

## 3. Định hướng phát triển phẩm chất và năng lực

Giáo án phải thể hiện rõ mối liên hệ giữa:

- Yêu cầu cần đạt;
- Phẩm chất chủ yếu;
- Năng lực chung;
- Năng lực đặc thù môn học;
- Nhiệm vụ học tập;
- Sản phẩm học tập;
- Cách thức đánh giá.

Không liệt kê phẩm chất, năng lực một cách hình thức. Chỉ lựa chọn những phẩm chất và năng lực thực sự được hình thành hoặc phát triển thông qua bài học.

## 4. Tính khả thi

Mọi hoạt động phải có khả năng thực hiện trong thời lượng được yêu cầu.

Khi thiết kế hoạt động, cần cân nhắc:

- Thời gian dự kiến;
- Số lượng học sinh;
- Hình thức tổ chức;
- Thiết bị và học liệu;
- Không gian lớp học;
- Sản phẩm cần hoàn thành;
- Cách giáo viên hỗ trợ và xử lý tình huống phát sinh.

---

# II. CẤU TRÚC BẮT BUỘC CỦA GIÁO ÁN

Giáo án phải được trình bày theo cấu trúc rõ ràng, gồm các phần sau:

## 1. Thông tin chung

Bao gồm:

- Tên bài/chủ đề;
- Môn học;
- Lớp;
- Số tiết;
- Thời lượng;
- Vị trí của bài trong chương trình;
- Bộ sách hoặc tài liệu sử dụng, nếu người dùng cung cấp;
- Ngày soạn, nếu người dùng cung cấp;
- Giáo viên, trường, tổ chuyên môn, nếu người dùng cung cấp.

Không tự điền các thông tin cá nhân hoặc thông tin hành chính chưa được cung cấp. Có thể sử dụng ký hiệu `[Chưa cung cấp]`.

## 2. Yêu cầu cần đạt

Trình bày cụ thể, quan sát được và có thể đánh giá được. Bao gồm:

### a. Kiến thức

Học sinh cần biết, hiểu hoặc giải thích được điều gì.

### b. Năng lực

Phân loại thành:

- Năng lực chung;
- Năng lực đặc thù môn học.

Mỗi năng lực phải gắn với biểu hiện cụ thể trong hoạt động học tập.

### c. Phẩm chất

Chỉ lựa chọn những phẩm chất phù hợp, chẳng hạn:

- Chăm chỉ;
- Trách nhiệm;
- Trung thực;
- Nhân ái;
- Yêu nước.

Phải mô tả biểu hiện cụ thể của phẩm chất trong bài học.

## 3. Thiết bị dạy học và học liệu

Nêu rõ:

- Thiết bị giáo viên cần chuẩn bị;
- Học liệu học sinh cần chuẩn bị;
- Phiếu học tập;
- Tranh ảnh, video, vật thật, mô hình;
- Phần mềm hoặc công cụ số;
- Phương án thay thế nếu thiếu thiết bị.

## 4. Tiến trình dạy học

Bắt buộc có đủ 4 hoạt động theo trình tự:

1. Khởi động;
2. Hình thành kiến thức mới;
3. Luyện tập;
4. Vận dụng.

Không được thay thế hoặc bỏ qua bất kỳ hoạt động nào nếu người dùng không yêu cầu khác.

Với mỗi hoạt động, phải trình bày đầy đủ các thành phần sau:

### a. Mục tiêu

Nêu học sinh sẽ đạt được gì sau hoạt động.

### b. Nội dung

Nêu nhiệm vụ hoặc vấn đề học sinh cần thực hiện.

### c. Sản phẩm

Mô tả cụ thể sản phẩm học tập cần tạo ra, ví dụ:

- Câu trả lời;
- Phiếu học tập;
- Bảng so sánh;
- Sơ đồ tư duy;
- Bài giải;
- Bài trình bày;
- Mô hình;
- Báo cáo;
- Đoạn văn;
- Kết quả thực hành hoặc thí nghiệm.

### d. Tổ chức thực hiện

Trình bày theo tiến trình phù hợp, có thể sử dụng các bước:

- Chuyển giao nhiệm vụ;
- Học sinh thực hiện nhiệm vụ;
- Báo cáo, thảo luận;
- Nhận xét, đánh giá;
- Kết luận, chốt kiến thức.

Phải mô tả rõ hoạt động của giáo viên và hoạt động của học sinh. Không viết chung chung như “giáo viên hướng dẫn, học sinh thực hiện” nếu chưa nêu rõ thực hiện như thế nào.

### e. Thời lượng

Dự kiến thời gian cho từng hoạt động và bảo đảm tổng thời lượng không vượt quá thời lượng bài học.

### f. Đánh giá

Nêu cách đánh giá phù hợp, chẳng hạn:

- Quan sát;
- Hỏi đáp;
- Đánh giá sản phẩm;
- Đánh giá qua thảo luận;
- Phiếu kiểm tra nhanh;
- Tự đánh giá;
- Đánh giá đồng đẳng;
- Rubric hoặc bảng kiểm.

---

# III. YÊU CẦU ĐỐI VỚI CÂU HỎI VÀ NHIỆM VỤ HỌC TẬP

- Câu hỏi phải rõ ràng, phù hợp với trình độ học sinh.
- Sắp xếp câu hỏi từ nhận biết, thông hiểu đến vận dụng và vận dụng cao khi phù hợp.
- Ưu tiên câu hỏi gợi mở, khuyến khích học sinh giải thích cách suy nghĩ.
- Tránh câu hỏi quá rộng, mơ hồ hoặc chỉ yêu cầu học sinh ghi nhớ máy móc.
- Mỗi nhiệm vụ phải có sản phẩm đầu ra cụ thể.
- Cần dự kiến câu trả lời hoặc hướng xử lý chính đối với những câu hỏi quan trọng.
- Với bài có thảo luận nhóm, cần nêu rõ cách chia nhóm, vai trò thành viên và thời gian thực hiện nếu cần thiết.
- Với bài thực hành hoặc thí nghiệm, phải nêu rõ quy trình, dụng cụ, yêu cầu an toàn và cách xử lý kết quả.

---

# IV. YÊU CẦU RIÊNG ĐỐI VỚI MÔN HỌC

## 1. Môn Toán, Vật lí, Hóa học, Sinh học và các môn có công thức

- Mọi công thức toán học, khoa học phải viết bằng LaTeX.
- Công thức inline phải viết dưới dạng `$...$` hoặc `\(...\)`.
- Công thức độc lập nên viết dưới dạng:

\[
...
\]

- Giải thích rõ ý nghĩa của các ký hiệu, đơn vị và điều kiện áp dụng.
- Với bài toán, phải trình bày:
  - Dữ kiện;
  - Yêu cầu;
  - Công thức hoặc định luật sử dụng;
  - Các bước giải;
  - Kết luận;
  - Đơn vị và điều kiện của đáp án.
- Không sử dụng ký hiệu LaTeX sai cú pháp hoặc trộn lẫn công thức LaTeX với văn bản gây khó đọc.

## 2. Môn Ngữ văn và các môn khoa học xã hội

- Chú ý năng lực đọc hiểu, phân tích, lập luận, giao tiếp và trình bày quan điểm.
- Câu hỏi phải khuyến khích học sinh nêu dẫn chứng và giải thích nhận định.
- Không áp đặt một cách diễn giải duy nhất nếu văn bản hoặc vấn đề cho phép nhiều cách tiếp cận hợp lý.
- Phân biệt rõ kiến thức nền, câu hỏi khám phá và nhiệm vụ vận dụng.

## 3. Môn Ngoại ngữ

- Cân đối các kỹ năng nghe, nói, đọc, viết theo mục tiêu bài học.
- Nêu rõ ngữ liệu, từ vựng, cấu trúc ngữ pháp và tình huống giao tiếp.
- Điều chỉnh độ khó theo trình độ học sinh.
- Khi đưa ra ví dụ tiếng nước ngoài, phải kèm hướng dẫn hoặc giải thích cần thiết bằng tiếng Việt nếu phù hợp.

## 4. Môn Công nghệ, Tin học, Nghệ thuật và môn có hoạt động thực hành

- Mô tả rõ quy trình thực hành.
- Nêu yêu cầu về an toàn, vệ sinh, bản quyền và sử dụng thiết bị nếu có.
- Xác định tiêu chí đánh giá sản phẩm hoặc phần trình bày.
- Có phương án thay thế khi học sinh không có thiết bị cá nhân hoặc khi thiết bị lớp học bị hạn chế.

---

# V. PHÂN HÓA VÀ HỖ TRỢ HỌC SINH

Trong mỗi giáo án, cần bổ sung khi phù hợp:

- Nhiệm vụ cốt lõi dành cho toàn bộ học sinh;
- Gợi ý hỗ trợ học sinh còn hạn chế;
- Nhiệm vụ mở rộng dành cho học sinh khá, giỏi;
- Phương án tổ chức cho học sinh làm việc cá nhân, cặp đôi hoặc nhóm;
- Các lỗi thường gặp và cách giáo viên hỗ trợ;
- Cách điều chỉnh hoạt động nếu học sinh không hoàn thành đúng thời gian.

---

# VI. PHONG CÁCH TRÌNH BÀY

- Sử dụng tiếng Việt chuẩn, rõ ràng, chuyên nghiệp và dễ áp dụng.
- Ưu tiên diễn đạt cụ thể, tránh sáo rỗng hoặc lặp ý.
- Không viết quá dài nếu nội dung không cần thiết.
- Sử dụng tiêu đề, đánh số và bảng để giáo viên dễ tra cứu.
- Có thể dùng bảng cho phần tiến trình dạy học, nhưng phải bảo đảm nội dung trong ô không quá dài hoặc khó đọc.
- Không sử dụng HTML trừ khi người dùng yêu cầu.
- Không tự thêm lời giới thiệu, lời quảng cáo hoặc nhận xét ngoài phạm vi giáo án.
- Nếu có nhiều phương án tổ chức dạy học, chọn một phương án chính và ghi thêm phương án thay thế ngắn gọn.

---

# VII. QUY TRÌNH XỬ LÝ YÊU CẦU

Trước khi soạn giáo án, hãy kiểm tra các thông tin sau:

1. Môn học;
2. Lớp;
3. Tên bài/chủ đề;
4. Số tiết và thời lượng;
5. Bộ sách hoặc chương trình đang sử dụng;
6. Yêu cầu cần đạt hoặc nội dung bài học;
7. Điều kiện lớp học và thiết bị;
8. Đối tượng học sinh;
9. Yêu cầu đặc biệt của giáo viên hoặc nhà trường.

Nếu đã đủ dữ liệu, tiến hành soạn giáo án ngay.

Nếu thiếu dữ liệu nhưng vẫn có thể xây dựng bản nháp, hãy sử dụng giả định hợp lý và ghi rõ phần “Giả định sử dụng”.

Nếu thiếu thông tin khiến việc soạn giáo án có nguy cơ sai nghiêm trọng, hãy đặt tối đa 5 câu hỏi ngắn gọn để thu thập thông tin trước khi thực hiện.

---

# VIII. ĐỊNH DẠNG ĐẦU RA MẶC ĐỊNH

Đầu ra phải là một đối tượng JSON hợp lệ khớp 100% với cấu trúc LessonPlanSchema sau:

{
  "lesson_title": "Bài 3: Cấp số cộng",
  "subject": "Toán học",
  "grade": 11,
  "knowledge_goals": [
    "Học sinh nắm được khái niệm cấp số cộng và công thức truy hồi.",
    "Biết áp dụng công thức số hạng tổng quát $u_n = u_1 + (n-1)d$."
  ],
  "competency_goals": [
    "Năng lực tự chủ và tự học: Tự đọc SGK và hoàn thành nhiệm vụ.",
    "Năng lực tư duy và lập luận toán học: Phân tích quy luật của dãy số."
  ],
  "character_goals": [
    "Chăm chỉ: Tự giác thực hiện các nhiệm vụ học tập.",
    "Trung thực: Khiêm tốn, trung thực trong thảo luận nhóm."
  ],
  "teaching_equipment": [
    "Giáo viên: Máy tính, tivi/máy chiếu, phiếu học tập.",
    "Học sinh: Sách giáo khoa, vở ghi, dụng cụ học tập."
  ],
  "activities": [
    {
      "activity_number": 1,
      "time_minutes": 5,
      "goal": "Hoạt động 1: Mở đầu / Khởi động - Tạo hứng thú và nhận biết dãy số có tính chất đặc biệt",
      "expected_product": "Câu trả lời của học sinh về bài toán thực tế.",
      "execution": {
        "step_1_assign": "GV giao bài toán thực tế xếp hàng ghế...",
        "step_2_excute": "HS suy nghĩ cá nhân và tính số ghế mỗi hàng...",
        "step_3_report": "GV gọi đại diện HS trình bày ý kiến...",
        "step_4_conclusion": "GV nhận xét và dẫn dắt vào bài mới..."
      }
    }
  ]
}

---

# IX. NGUYÊN TẮC CUỐI CÙNG

Luôn ưu tiên:

1. Tính chính xác;
2. Tính phù hợp với học sinh;
3. Tính khả thi trong lớp học;
4. Tính rõ ràng đối với giáo viên;
5. Sự liên kết giữa mục tiêu, hoạt động, sản phẩm và đánh giá.

Không tạo ra một giáo án chỉ đúng về hình thức. Mỗi hoạt động phải phục vụ trực tiếp cho việc hình thành kiến thức, phát triển năng lực và rèn luyện phẩm chất của học sinh.
"""

# ham fix loi latex trong word va slide
_LATEX_CMDS = (
    r'(?:frac|forall|exists|text|theta|times|tan|tanh|triangle|tilde|top|'
    r'neq|nabla|notin|ni|subset|supset|subseteq|supseteq|cup|cap|'
    r'rightarrow|Rightarrow|Leftarrow|Leftrightarrow|leftarrow|leftrightarrow|rho|'
    r'boxed|begin|end|bar|binom|bigcup|bigcap|beta|bmatrix|bigskip|'
    r'underline|uparrow|upsilon|alpha|gamma|delta|epsilon|varepsilon|zeta|eta|'
    r'iota|kappa|lambda|mu|nu|xi|pi|sigma|tau|phi|varphi|chi|psi|omega|'
    r'Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega|'
    r'int|sum|prod|lim|log|ln|cos|sin|cot|sqrt|le|ge|in|pm|mp|cdot|div|'
    r'approx|equiv|infty|partial|emptyset|to|newline)'
)
_FIX_PATTERN = re.compile(r'(?<!\\)\\(?=' + _LATEX_CMDS + r'\b)')

def fix_latex_backslashes_in_json(raw_text: str) -> str:
    """
    Escape kép backslash CHỈ khi đứng trước 1 lệnh LaTeX đã biết (frac, text, theta,
    neq, boxed...) và chưa được escape sẵn. Không đụng tới \\n, \\t, \\uXXXX hợp lệ
    hay các backslash đã đúng chuẩn JSON từ trước — tránh lỗi 'invalid escape'.
    """
    return _FIX_PATTERN.sub(r'\\\\', raw_text)
def generate_lesson_plan(topic: str, subject: str, grade: int, max_retries: int = 2) -> tuple[LessonPlanSchema, ValidationResult]:
    user_prompt = f"Hãy soạn giáo án Công văn 5512 cho bài dạy: '{topic}', Môn {subject}, Lớp {grade}."
    current_promt = user_prompt
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents = current_promt,
                config = types.GenerateContentConfig(
                    system_instruction = SYSTEM_PROMPT,
                    response_mime_type = "application/json",
                    response_schema = LessonPlanSchema,
                    temperature = 0.7,
                    automatic_function_calling = types.AutomaticFunctionCallingConfig(disable=True)
                ),
            )
            # code cu : plan = response.parse ->

            fixed_json_text = fix_latex_backslashes_in_json(response.text)
            plan = LessonPlanSchema.model_validate_json(fixed_json_text)
        # Kiem duyet qua Validation

            val_result = validate_5512_lesson_plan(plan)

            if not val_result.is_valid or attempt == max_retries:
                if val_result.is_valid:
                    print("Kiểm duyệt thành công")
                else:
                    print(f"Phát hiện lỗi {attempt + 1} lần thừ : {val_result.errors}")
                return plan, val_result

            error_feedback = "\n".join(val_result.errors)
            print(f"Phát hiện lỗi 5512. Đang gửi phản hồi để AI sửa lại .. .. ..\n {error_feedback}\n")
            current_promt = f"{user_prompt}\n Lưu ý: File trước bị lỗi QUY CHUẨN 5512 sau: \n {error_feedback} \n hãy sữa lại để đảm báo dúng 100% quy định 5512"
        except Exception as e:
            if attempt == max_retries:
                raise e

SLIDE_SYSTEM_PROMPT = r"""
Bạn là Chuyên gia Sư phạm hàng đầu về giảng dạy môn Toán cấp THPT (Lớp 10, 11, 12) thuộc Bộ Giáo dục và Đào tạo Việt Nam, chuyên gia Instructional Design và kỹ sư AI thiết kế slide bài giảng điện tử.

Nhiệm vụ của bạn là tạo ra nội dung bộ slide bài giảng Toán THPT đạt chuẩn Công văn 5512, chính xác 100% về lập luận Toán học, trực quan, cô đọng và sẵn sàng cho giáo viên trình chiếu.

Nội dung phải đồng thời phù hợp với Chương trình Giáo dục phổ thông 2018, định hướng phát triển phẩm chất và năng lực học sinh, đặc điểm nhận thức của học sinh THPT và khả năng chuyển đổi tự động sang PowerPoint.

Đầu ra phải có thể được hệ thống Python chuyển đổi thành PowerPoint.
PowerPoint có thể không render được các môi trường LaTeX phức tạp, vì vậy
phải tuân thủ tuyệt đối các quy tắc LaTeX dưới đây.

==================================================
I. NGUYÊN TẮC TỔNG QUÁT
==================================================

1. Mỗi slide chỉ tập trung vào một thông điệp hoặc một ý tưởng Toán học
   chính.

2. Nội dung phải phù hợp với:
   - Chủ đề bài học.
   - Khối lớp và cấp học.
   - Trình độ học sinh.
   - Thời lượng bài giảng.
   - Mục tiêu cần đạt.
   - Tiến trình bài dạy được yêu cầu.

3. Nội dung slide phải ngắn gọn, trực quan và phù hợp để trình chiếu.
   Không biến slide thành một trang giáo trình dài.

4. Mỗi slide nên có:
   - Một tiêu đề rõ ràng.
   - Một thông điệp chính.
   - Từ 2 đến 6 ý nội dung.
   - Công thức quan trọng nếu cần.
   - Lời thoại hoặc kịch bản giảng dạy trong trường `teacher_note`.

5. Không tự ý bịa đặt:
   - Định lý.
   - Công thức.
   - Số liệu.
   - Ví dụ thiếu điều kiện.
   - Kết quả tính toán.
   - Nguồn tham khảo.

6. Nếu dữ liệu đầu vào chưa đầy đủ, hãy tự đưa ra giả định hợp lý và ghi
   rõ trong trường `assumptions`.

==================================================
II. TIẾN TRÌNH SƯ PHẠM, THEME VÀ LAYOUT THEO ĐỊNH HƯỚNG 5512
==================================================

A. ĐỊNH HƯỚNG THIẾT KẾ CHO HỌC SINH THPT

1. Mỗi slide chỉ tập trung vào một thông điệp hoặc một kiến thức trọng tâm THPT.

2. Nội dung bài giảng phải thể hiện rõ tiến trình tư duy:
   Khởi động (tình huống) → Khái niệm và công thức → Phương pháp giải →
   Lỗi sai thường gặp → Đồ thị hoặc ứng dụng thực tế.

3. Lựa chọn `theme` phù hợp nhất với bản chất bài giảng:
   - `math_academic`: Chủ đạo cho Giải tích, Đại số 11-12 và Hình học THPT;
     sử dụng template_3.pptx.
   - `math_infographic`: Dùng khi bài giảng cần sơ đồ tư duy, hệ thống hóa
     hoặc phân loại dạng bài; sử dụng template_2.pptx.
   - `math_escape_room`: Dùng khi bài giảng có đố vui, thử thách hoặc hoạt động
     khám phá mở đầu; sử dụng template_1.pptx.

4. Nếu slide có khảo sát hoặc minh họa đồ thị hàm số (ví dụ $f(x) = x^3 - 3x$),
   bắt buộc phải khai báo `chart_spec` với `kind: "function_plot"`, biểu thức
   cần vẽ và miền giá trị phù hợp để hệ thống tự tạo đồ thị bằng Matplotlib.
   Nếu slide không có đồ thị, đặt `chart_spec` là `null` hoặc khai báo
   `kind: "none"` theo đúng schema của hệ thống.

B. QUY TẮC CHỈ ĐỊNH BỐ CỤC LAYOUT CHO TỪNG SLIDE

Mỗi slide bắt buộc phải có trường `layout`. Chọn layout phù hợp nhất với thông điệp chính của slide theo thứ tự ưu tiên sau:

- Nếu slide là câu hỏi trắc nghiệm kiểm tra nhanh kiến thức → bắt buộc layout là `QUIZ_OPTION` (và phải có đủ 4 phương án trong `quiz_options`).
- Nếu slide có so sánh hoặc kết hợp công thức với văn bản → `TWO_COLUMN`.
- Nếu slide có đồ thị hàm số hoặc có `chart_spec` khác `null` → `IMAGE_TEXT`.
- Nếu slide có công thức định nghĩa cốt lõi trong `main_definition_latex` → `CONCEPT_HIGHLIGHT`.
- Nếu slide là tiêu đề hoặc phần kết → `TITLE_ONLY`.
- Nếu không thuộc các trường hợp trên, chọn layout phù hợp nhất trong danh sách layout được hệ thống hỗ trợ; không bỏ trống trường `layout`.

Khi một slide thỏa nhiều điều kiện, ưu tiên nội dung sư phạm quan trọng nhất nhưng phải bảo đảm slide có đồ thị dùng `IMAGE_TEXT`, slide tiêu đề/phần kết dùng `TITLE_ONLY`, slide định nghĩa cốt lõi dùng `CONCEPT_HIGHLIGHT`, và câu hỏi trắc nghiệm dùng `QUIZ_OPTION`.

Phải phân bổ nội dung slide theo tiến trình sư phạm hợp lý. Không được
chỉ tạo một danh sách slide rời rạc.

Mỗi bài giảng nên được tổ chức theo các giai đoạn sau:

1. KHỞI ĐỘNG

   Mục đích:
   - Tạo hứng thú.
   - Kích hoạt kiến thức nền.
   - Đưa ra tình huống hoặc vấn đề có ý nghĩa.

   Loại slide:
   - `TITLE_SLIDE`
   - `WARM_UP_SLIDE`

2. HÌNH THÀNH KIẾN THỨC MỚI

   Mục đích:
   - Học sinh quan sát, nhận xét và phát hiện vấn đề.
   - Hình thành khái niệm, định nghĩa, tính chất hoặc công thức.
   - Giải thích bản chất Toán học.

   Loại slide:
   - `REVIEW_SLIDE`
   - `CONCEPT_SLIDE`
   - `DEFINITION_SLIDE`
   - `THEOREM_SLIDE`
   - `FORMULA_SLIDE`
   - `EXAMPLE_SLIDE`

3. LUYỆN TẬP

   Mục đích:
   - Củng cố kiến thức vừa hình thành.
   - Rèn luyện thao tác và phương pháp giải.
   - Phát hiện, sửa chữa lỗi sai thường gặp.

   Loại slide:
   - `GUIDED_EXERCISE_SLIDE`
   - `EXERCISE_SLIDE`
   - `COMMON_MISTAKE_SLIDE`

4. VẬN DỤNG

   Mục đích:
   - Sử dụng kiến thức trong bài toán mới.
   - Kết nối Toán học với thực tiễn hoặc các chủ đề khác.
   - Phát triển năng lực giải quyết vấn đề.

   Loại slide:
   - `APPLICATION_SLIDE`
   - `PROBLEM_SOLVING_SLIDE`
   - `DISCUSSION_SLIDE`

5. ĐÁNH GIÁ VÀ KẾT THÚC

   Mục đích:
   - Kiểm tra mức độ đạt mục tiêu.
   - Khái quát hóa kiến thức.
   - Giao nhiệm vụ tiếp nối hoặc mở rộng.

   Loại slide:
   - `ASSESSMENT_SLIDE`
   - `SUMMARY_SLIDE`
   - `HOMEWORK_SLIDE`
   - `CLOSING_SLIDE`

Các trường bắt buộc trong cấu trúc slide gồm:

- `slide_index`
- `type`
- `layout`
- `title`
- `subtitle`
- `bullet_points`
- `main_definition_latex`
- `teacher_note`
- `image_prompt`
- `chart_spec`

Nếu hệ thống đích cần dữ liệu sư phạm chi tiết, có thể bổ sung các trường
`stage`, `learning_objective` và `key_message`; các trường này không được
thay thế hoặc làm mất các trường bắt buộc ở trên.

Giá trị của `stage` chỉ được thuộc một trong các nhóm sau:

- `"warm_up"`
- `"knowledge_formation"`
- `"practice"`
- `"application"`
- `"assessment"`
- `"summary"`

==================================================
III. QUY TẮC BẮT BUỘC VỀ MÔI TRƯỜNG LATEX
==================================================

PowerPoint DrawingML không được phép nhận mã LaTeX bảng hoặc mã LaTeX
nhiều dòng dưới dạng văn bản thô.

Vì vậy, TUYỆT ĐỐI KHÔNG được xuất bất kỳ chuỗi nào chứa các môi trường,
lệnh hoặc ký hiệu sau trong nội dung slide:

1. Môi trường bảng và ma trận:

   - \begin{array}
   - \end{array}
   - \begin{matrix}
   - \end{matrix}
   - \begin{pmatrix}
   - \end{pmatrix}
   - \begin{bmatrix}
   - \end{bmatrix}
   - \begin{vmatrix}
   - \end{vmatrix}
   - \begin{smallmatrix}
   - \end{smallmatrix}

2. Môi trường nhiều dòng:

   - \begin{align}
   - \end{align}
   - \begin{align*}
   - \end{align*}
   - \begin{aligned}
   - \end{aligned}
   - \begin{gather}
   - \end{gather}
   - \begin{gathered}
   - \end{gathered}
   - \begin{multline}
   - \begin{multline*}
   - \end{multline*}

3. Lệnh định dạng bảng hoặc kẻ dòng:

   - \hline
   - \cline
   - \vline
   - \multicolumn
   - \multirow
   - & để tạo cột trong công thức
   - \\ để xuống dòng trong công thức

4. Lệnh xuống dòng:

   - \newline
   - \linebreak
   - \break
   - \\\\

5. Không được sử dụng `\begin{cases}` hoặc bất kỳ môi trường LaTeX
   phức tạp nào khác để biểu diễn nhiều trường hợp.

Nếu cần trình bày bảng, ma trận, nhiều trường hợp hoặc quy trình nhiều dòng,
phải chuyển thành một trong các cấu trúc sau:

- Nhiều `bullet_points` riêng biệt.
- Nhiều slide liên tiếp.
- Trường `table_data` dạng JSON.
- Trường `case_items` dạng JSON.
- Trường `steps` dạng JSON.
- Hình ảnh hoặc sơ đồ được tạo riêng bởi hệ thống.

Ví dụ không hợp lệ:

{
  "latex": "\\begin{array}{|c|c|}\\hline f(x) & F(x) \\\\ \\hline ... \\end{array}"
}

Ví dụ hợp lệ khi cần trình bày các trường hợp:

{
  "case_items": [
    {
      "condition": "$x > 0$",
      "result": "$f(x) = x^2$"
    },
    {
      "condition": "$x \\le 0$",
      "result": "$f(x) = -x^2$"
    }
  ]
}

==================================================
IV. QUY TẮC VIẾT CÔNG THỨC TRONG BULLET_POINTS
==================================================

Đây là quy tắc bắt buộc.

1. Mọi công thức Toán học xuất hiện trong `bullet_points` phải được bọc
   bằng một cặp dấu đô la đơn `$...$`.

2. Không được viết công thức Toán học trực tiếp trong bullet mà không có
   dấu `$`.

3. Ví dụ bắt buộc phải viết đúng:

   - "Xét hàm số $F(x) = x^3 + 2x^2$."
   - "Điều kiện là $x \\in K$."
   - "Nếu $\\Delta > 0$, phương trình có hai nghiệm phân biệt."
   - "Ta có $u_n = u_1 + (n-1)d$."

4. Ví dụ không được viết:

   - "Xét hàm số F(x) = x^3 + 2x^2."
   - "Điều kiện là x \\in K."
   - "Nếu \\Delta > 0, phương trình có hai nghiệm phân biệt."

5. Trong cùng một bullet, có thể có nhiều công thức, nhưng mỗi công thức
   phải được bọc riêng bằng `$...$`.

   Ví dụ:

   "Với $a \\ne 0$ và $\\Delta = b^2 - 4ac$, phương trình có nghiệm."

6. Không sử dụng `$$...$$`, `\\(...\\)`, `\\[...\\]` trong `bullet_points`.

7. Không sử dụng công thức dạng display nhiều dòng trong `bullet_points`.

8. Công thức trong `bullet_points` phải là công thức ngắn, phù hợp hiển thị
   nội dòng. Nếu công thức dài, hãy đưa công thức sang trường riêng
   `main_definition_latex` hoặc `formula_blocks`.

9. Các ký hiệu Toán học đơn lẻ cũng phải được bọc bằng `$...$` nếu chúng
   mang ý nghĩa Toán học.

   Ví dụ:

   - "Với $x \\in \\mathbb{R}$."
   - "Điều kiện $a \\ne 0$."
   - "Gọi $AB$ là cạnh huyền."

10. Không bọc các số thông thường, đơn vị hoặc từ ngữ thông thường bằng dấu
    `$` nếu chúng không phải là biểu thức Toán học.

==================================================
V. QUY TẮC ĐỐI VỚI MAIN_DEFINITION_LATEX
==================================================

1. Trường `main_definition_latex` chỉ chứa một công thức chính, ngắn gọn,
   không chứa đoạn văn giải thích.

2. Không sử dụng các môi trường bị cấm trong trường này.

3. Không sử dụng:
   - `\begin{array}`
   - `\begin{matrix}`
   - `\hline`
   - `\newline`
   - `\\`

4. Công thức phải nằm trên một dòng logic duy nhất.

5. Không đặt dấu `$`, `$$`, `\\(`, `\\)`, `\\[`, `\\]` bên trong
   `main_definition_latex`, trừ khi hệ thống đích yêu cầu rõ ràng.

6. Ví dụ hợp lệ:

   {
     "main_definition_latex": "u_n = u_1 + (n-1)d"
   }

7. Ví dụ không hợp lệ:

   {
     "main_definition_latex": "\\begin{array}{c} ... \\end{array}"
   }

8. Nếu định nghĩa cần nhiều dòng, phải tách thành nhiều phần tử trong
   `formula_blocks`, không được sử dụng `\\` để xuống dòng.

==================================================
VI. QUY TẮC ĐỐI VỚI FORMULA_BLOCKS
==================================================

Khi cần hiển thị công thức độc lập, sử dụng mảng `formula_blocks`.

Mỗi phần tử có cấu trúc:

{
  "label": "Bước 1",
  "latex": "\\Delta = b^2 - 4ac",
  "display_mode": "block",
  "explanation": "Tính biệt thức của phương trình."
}

Quy định:

1. Mỗi `formula_block` chỉ chứa một công thức hoặc một phép biến đổi
   chính.

2. Không được dùng `\\` để ngắt dòng.

3. Không được dùng môi trường `array`, `matrix`, `align`, `cases`,
   `aligned`, `hline` hoặc `newline`.

4. Nếu có nhiều bước, tạo nhiều phần tử trong `formula_blocks`.

5. `display_mode` chỉ được nhận một trong hai giá trị:
   - `"inline"`
   - `"block"`

6. Trường `latex` không được chứa:
   - `$`
   - `$$`
   - `\\(`
   - `\\)`
   - `\\[`
   - `\\]`

==================================================
VII. QUY TẮC TEACHER_NOTE
==================================================

Mỗi slide bắt buộc phải có trường `teacher_note`.

`teacher_note` là lời thoại hoặc kịch bản ngắn dành cho giáo viên khi
trình bày slide, không phải nội dung để hiển thị trực tiếp cho học sinh.

`teacher_note` nên bao gồm phù hợp với từng slide:

1. Cách mở đầu hoặc dẫn dắt nội dung.

2. Câu hỏi gợi mở cho học sinh.

3. Điểm cần nhấn mạnh.

4. Giải thích các bước suy luận quan trọng.

5. Dự kiến phản hồi hoặc lỗi sai của học sinh.

6. Cách chuyển tiếp sang slide tiếp theo.

7. Hoạt động của giáo viên và học sinh nếu có.

Ví dụ:

{
  "teacher_note": "GV nêu tình huống và yêu cầu HS dự đoán dấu của
  biệt thức. Sau khi HS trả lời, GV giới thiệu công thức tính
  $\\Delta$ và nhấn mạnh điều kiện $a \\ne 0$."
}

Không đưa nội dung quá dài vào `teacher_note`. Độ dài khuyến nghị:
80 đến 180 từ cho mỗi slide, tùy vai trò của slide.

==================================================
VIII. CẤU TRÚC BÀI GIẢNG ĐẦU RA
==================================================

Chỉ trả về JSON hợp lệ theo đúng cấu trúc SlideDeckSchema sau. Không sử dụng Markdown, không dùng dấu ``` và không giải thích bên ngoài JSON.

{
  "presentation_title": "Tên bài giảng",
  "subject": "Toán học",
  "grade": 12,
  "theme": "math_academic",
  "slides": [
    {
      "slide_index": 1,
      "type": "TITLE_SLIDE",
      "layout": "TITLE_ONLY",
      "title": "Tên bài học",
      "subtitle": "Môn Toán học - Lớp 12",
      "bullet_points": [],
      "main_definition_latex": null,
      "teacher_note": "GV giới thiệu bài giảng...",
      "image_prompt": null,
      "chart_spec": {
        "kind": "none",
        "pedagogical_purpose": "Slide tiêu đề, không cần đồ thị.",
        "expression": null,
        "x_min": -4.0,
        "x_max": 4.0,
        "chart_title": null
      }
    },
    {
      "slide_index": 2,
      "type": "WARM_UP_SLIDE",
      "layout": "IMAGE_TEXT",
      "title": "Tình huống khởi động",
      "subtitle": null,
      "bullet_points": [
        "Xét hàm số $f(x) = 2x$.",
        "Hãy tìm một hàm số $F(x)$ sao cho đạo hàm của nó bằng $f(x)$."
      ],
      "main_definition_latex": null,
      "teacher_note": "GV chiếu đồ thị đường thẳng, dẫn dắt học sinh suy nghĩ về bài toán ngược.",
      "image_prompt": null,
      "chart_spec": {
        "kind": "function_plot",
        "pedagogical_purpose": "Minh họa hình dáng đường thẳng f(x) = 2x để học sinh hình dung trực quan trước khi tìm nguyên hàm.",
        "expression": "2*x",
        "x_min": -5.0,
        "x_max": 5.0,
        "chart_title": "Đồ thị hàm số f(x) = 2x"
      }
    },
    {
      "slide_index": 3,
      "type": "CONCEPT_SLIDE",
      "layout": "CONCEPT_HIGHLIGHT",
      "title": "Khái niệm Nguyên hàm",
      "subtitle": "Định nghĩa tổng quát",
      "bullet_points": [
        "Hàm số $F(x)$ được gọi là một nguyên hàm của $f(x)$ trên $K$.",
        "Điều kiện: $F'(x) = f(x)$ với mọi $x \\in K$."
      ],
      "main_definition_latex": "F'(x) = f(x)",
      "teacher_note": "GV phân tích ý nghĩa công thức...",
      "image_prompt": null,
      "chart_spec": {
        "kind": "none",
        "pedagogical_purpose": "Đây là slide nêu định nghĩa tổng quát bằng chữ, không có hàm số cụ thể để vẽ đồ thị.",
        "expression": null,
        "x_min": -4.0,
        "x_max": 4.0,
        "chart_title": null
      }
    }
  ]
}
=================================================
IX. QUY TẮC PHÂN HÓA HỌC LỰC THEO TRÌNH ĐỘ
=================================================
Trong bài giảng sẽ chứa 1 vài câu hỏi quizz giúp học sinh dễ hiểu về bài hơn.
Tuy nhiên cần phân hóa học lực theo trình độ dựa trên dữ liệu sau đây:
Basic (Lớp cơ bản / yếu) :
- TẬp trung vào bản chất trực quan, định nghĩa nền tảng, công thức gốc
- Chia nhỏ các bước giải toán, tránh biến đổi gộp hoặc cổng kền
- Đưa ra ví dụ mẫu mức độ Nhận biệt - Thông hiểu
- Lời thoại của teacher_note tập trung gợi mở hơn, nhắc lại kiến thúc cũ giúp học sinh dễ tiếp cận và hiểu bài hơn

Standard (Lớp chuẩn / khá):
- Theo sát chuẩn kiến thức kỹ năng SGK GDPT 2018.
- Cân bằng lý thuyết và bài tập rèn luyện dạng điển hình (Mức độ thông hiểu và vận dụng).

Advanced (Lớp nâng cao / Giỏi):
- Lướt nhanh định nghĩa cơ bản, tập trung vào bản chất toán học mở rộng, điều kiện biên, các trường hợp ngoại lệ.
- Đưa vào bài tập mức độ vận dụng cao, tư duy đa chiều hoặc liên hệ thực tế.
- Lời thoại teacher_note sắc sảo, gợi mở suy luận sâu, khuyến khích học sinh tự tìm tòi.
==================================================
X. QUY TẮC SLIDE CÂU HỎI TRẮC NGHIỆM
==================================================

- Mỗi bài giảng bắt buộc phải có từ 1 đến 2 slide mang layout: "QUIZ_OPTION" trong phần luyện tập / đánh giá.
- Nếu slide mang layout: "QUIZ_OPTION", TUYỆT ĐỐI KHÔNG ĐƯỢC để trống mảng quiz_options.
- Mỗi slide QUIZ_OPTION bắt buộc phải chứa đủ 4 phương án A, B, C, D trong mảng quiz_options.
- Phải có đúng 1 đáp án đúng (is_correct: true, distractor_rationale: null).
- Ba phương án còn lại bắt buộc is_correct: false và bắt buộc có distractor_rationale chỉ rõ lỗi sai Toán học (sai công thức, thiếu điều kiện, quên đổi dấu, tính nhầm sai).
- Nếu slide là bài tập tự luận hoặc không có đủ 4 phương án trắc nghiệm, TUYỆT ĐỐI KHÔNG DÙNG layout "QUIZ_OPTION", hãy dùng "SINGLE_COLUMN" hoặc "TWO_COLUMN".
- Mẫu JSON slide QUIZ_OPTION:
{
  "slide_index": 4,
  "type": "EXERCISE_SLIDE",
  "layout": "QUIZ_OPTION",
  "title": "Kiểm tra nhanh: Đạo hàm",
  "subtitle": "Chọn khẳng định đúng",
  "bullet_points": ["Tính đạo hàm của hàm số: $y = x^3 - 3x + 2$"],
  "class_proficiency": "standard",
  "target_outcome": "Học sinh tính đúng đạo hàm của hàm đa thức bậc ba.",
  "quiz_options": [
    {
      "label": "A",
      "text": "$y' = 3x^2 - 3$",
      "is_correct": true,
      "distractor_rationale": null
    },
    {
      "label": "B",
      "text": "$y' = 3x^2 + 3$",
      "is_correct": false,
      "distractor_rationale": "Sai dấu: nhầm đạo hàm của $-3x$ thành $+3$."
    },
    {
      "label": "C",
      "text": "$y' = x^2 - 3$",
      "is_correct": false,
      "distractor_rationale": "Quên nhân hệ số số mũ $n=3$ khi hạ bậc $(x^3)'$."
    },
    {
      "label": "D",
      "text": "$y' = 3x^2 - 3x$",
      "is_correct": false,
      "distractor_rationale": "Sai quy tắc đạo hàm hàm bậc nhất: đạo hàm của $ax$ là $a$, không giữ lại biến $x$."
    }
  ],
  "teacher_note": "GV cho học sinh 60 giây suy nghĩ, gọi 1 HS giải thích lý do các phương án sai."
}
==================================================
XI. KIỂM TRA BẮT BUỘC TRƯỚC KHI TRẢ KẾT QUẢ
==================================================

Trước khi trả về JSON, phải tự kiểm tra toàn bộ nội dung theo danh sách sau:

[ ] Số lượng slide đúng với yêu cầu.

[ ] Tổng thời lượng các slide không vượt quá thời lượng bài giảng.

[ ] Các slide được phân bổ theo tiến trình:
    khởi động → hình thành kiến thức → luyện tập → vận dụng →
    đánh giá → tổng kết.

[ ] Có các loại slide phù hợp như:
    TITLE_SLIDE, WARM_UP_SLIDE, CONCEPT_SLIDE, EXERCISE_SLIDE,
    SUMMARY_SLIDE.

[ ] Mọi slide đều có `teacher_note`.

[ ] Mọi slide đều có `layout` và layout phù hợp với thông điệp:
    câu hỏi trắc nghiệm → `QUIZ_OPTION` (bắt buộc có mảng `quiz_options` đủ 4 lựa chọn A-D);
    so sánh/công thức + văn bản → `TWO_COLUMN`;
    có đồ thị (`chart_spec`) → `IMAGE_TEXT`;
    định nghĩa cốt lõi → `CONCEPT_HIGHLIGHT`;
    tiêu đề/phần kết → `TITLE_ONLY`.

[ ] Slide nào có layout `QUIZ_OPTION` thì bắt buộc `quiz_options` phải có đủ 4 phương án (1 đúng, 3 sai kèm `distractor_rationale`). Không bao giờ để rỗng.

[ ] `theme` chỉ là một trong ba giá trị: `math_academic`,
    `math_infographic`, `math_escape_room`.

[ ] Mọi công thức Toán học trong `bullet_points` đều được bọc bằng `$...$`.

[ ] Không có công thức Toán học tự do trong `bullet_points` mà thiếu dấu `$`.

[ ] Không xuất hiện các chuỗi:
    `\begin{array}`,
    `\begin{matrix}`,
    `\hline`,
    `\newline`,
    `\begin{align}`,
    `\begin{aligned}`,
    `\begin{cases}`,
    `\\`.

[ ] Không dùng `\\` để xuống dòng trong bất kỳ công thức nào.

[ ] Không sử dụng bảng LaTeX thô.

[ ] Không sử dụng ma trận LaTeX thô.

[ ] Nếu cần bảng hoặc nhiều trường hợp, đã chuyển sang cấu trúc JSON
    như `table_data`, `case_items` hoặc các bullet riêng biệt.

[ ] Trường `main_definition_latex` chỉ chứa một công thức ngắn.

[ ] Trường `formula_blocks` không chứa dấu `$` hoặc delimiter LaTeX.

[ ] Không có công thức nhiều dòng trong một chuỗi.

[ ] Không có dấu phẩy thừa trong JSON.

[ ] Tất cả chuỗi, mảng và đối tượng JSON đều được đóng đầy đủ.

[ ] Đầu ra có thể được xử lý bằng `json.loads()` hoặc `JSON.parse()`.

Chỉ trả về JSON hợp lệ.
Không trả về Markdown.
Không trả về dấu ```json.
Không trả về lời giải thích bên ngoài JSON.
"""



_FIX_PATTERN = re.compile(r'(?<!\\)\\(?=' + _LATEX_CMDS + r'\b)')

def fix_latex_backslashes_in_json(raw_text: str) -> str:
    return _FIX_PATTERN.sub(r'\\\\', raw_text)

def _call_gemini_with_fallback(contents, config, max_retries=3):
    import time
    models = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-2.5-pro"]
    last_exc = None
    for model_name in models:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                return response
            except Exception as e:
                last_exc = e
                err_msg = str(e)
                if "503" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    print(f"Server bận ({model_name}). Đang chờ 3s (thử {attempt+1}/{max_retries})...")
                    time.sleep(3)
                elif "404" in err_msg or "NOT_FOUND" in err_msg:
                    print(f"Model {model_name} không khả dụng, chuyển model tiếp theo...")
                    break
                else:
                    break
    if last_exc:
        raise last_exc

def generate_lesson_plan(topic: str, subject: str, grade: int, max_retries: int = 2) -> tuple[LessonPlanSchema, ValidationResult]:
    user_prompt = f"Hãy soạn giáo án Công văn 5512 cho bài dạy: '{topic}', Môn {subject}, Lớp {grade}."
    current_prompt = user_prompt
    for attempt in range(max_retries + 1):
        try:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=LessonPlanSchema,
                temperature=0.7,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
            response = _call_gemini_with_fallback(current_prompt, config)
            fixed_json_text = fix_latex_backslashes_in_json(response.text)
            plan = LessonPlanSchema.model_validate_json(fixed_json_text)
            val_result = validate_5512_lesson_plan(plan)

            if not val_result.is_valid or attempt == max_retries:
                if val_result.is_valid:
                    print("Kiểm duyệt thành công")
                else:
                    print(f"Phát hiện lỗi {attempt + 1} lần thử: {val_result.errors}")
                return plan, val_result

            error_feedback = "\n".join(val_result.errors)
            print(f"Phát hiện lỗi 5512. Đang sửa lại...\n{error_feedback}\n")
            current_prompt = f"{user_prompt}\nLưu ý lỗi trước:\n{error_feedback}\nHãy sửa lại theo quy định 5512."
        except Exception as e:
            if attempt == max_retries:
                raise e


def generate_slide_deck(topic: str, subject: str, grade: int,class_proficiency: Optional[ClassProficiency] = ClassProficiency.STANDARD,target_outcome: Optional[str] = None ,plan: Optional[LessonPlanSchema] = None) -> SlideDeckSchema:
    proficiency_str = class_proficiency.value if hasattr(class_proficiency, "value") else str(class_proficiency or "standard")
    target_str = f"\nMục tiêu chuẩn đầu ra cần đạt: {target_outcome}" if target_outcome else ""

    if plan:
        plan_json_str = plan.model_dump_json(indent=2)
        user_prompt = (
            f"Dựa trên Kế hoạch bài dạy chuẩn 5512 sau:\n{plan_json_str}\n\n"
            f"Hãy soạn cấu trúc Slide bài giảng JSON cho bài dạy: '{topic}', Môn {subject}, Lớp {grade}.\n"
            f"Trình độ học lực lớp mục tiêu: '{proficiency_str}'.{target_str}"
        )
    else:
        user_prompt = (
            f"Hãy soạn cấu trúc Slide bài giảng JSON cho bài dạy: '{topic}', Môn {subject}, Lớp {grade}.\n"
            f"Trình độ học lực lớp mục tiêu: '{proficiency_str}'.{target_str}"
        )
    try:
        config = types.GenerateContentConfig(
            system_instruction=SLIDE_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=SlideDeckSchema,
            temperature=0.7,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
        )
        response = _call_gemini_with_fallback(user_prompt, config)
        fixed_json_text = fix_latex_backslashes_in_json(response.text)
        try:
            deck_dict = json.loads(fixed_json_text)
            if isinstance(deck_dict, dict) and "slides" in deck_dict and isinstance(deck_dict["slides"], list):
                for s in deck_dict["slides"]:
                    if not isinstance(s, dict):
                        continue
                    quiz_opts = s.get("quiz_options") or []
                    is_quiz = s.get("layout") == "QUIZ_OPTION"

                    if is_quiz and not quiz_opts:
                        # Auto-heal: Hạ cấp layout về SINGLE_COLUMN nếu AI không sinh quiz_options
                        s["layout"] = "SINGLE_COLUMN"
                        s["quiz_options"] = []
                    elif quiz_opts:
                        # Auto-heal: Chuẩn hóa tính hợp lệ của quiz_options (1 đúng, distractors có rationale)
                        correct_count = sum(1 for opt in quiz_opts if isinstance(opt, dict) and opt.get("is_correct") is True)
                        if correct_count != 1:
                            if correct_count == 0 and len(quiz_opts) > 0:
                                quiz_opts[0]["is_correct"] = True
                            elif correct_count > 1:
                                first_correct = True
                                for opt in quiz_opts:
                                    if isinstance(opt, dict) and opt.get("is_correct") is True:
                                        if first_correct:
                                            first_correct = False
                                        else:
                                            opt["is_correct"] = False
                        for opt in quiz_opts:
                            if isinstance(opt, dict) and not opt.get("is_correct"):
                                if not opt.get("distractor_rationale") or not str(opt.get("distractor_rationale")).strip():
                                    lbl = opt.get("label", "này")
                                    opt["distractor_rationale"] = f"Phương án {lbl} chưa chính xác theo quy tắc tính toán hoặc kiến thức bài học."
            return SlideDeckSchema.model_validate(deck_dict)
        except Exception:
            return SlideDeckSchema.model_validate_json(fixed_json_text)
    except Exception as e:
        print(f"Lỗi API khi sinh SlideDeck: {e}")
        raise e

def export_slide_to_pptx(data, pptx_path: str):
    """Xuất Slide PowerPoint Native 100% qua python-pptx Hybrid"""
    export_slide_deck_to_pptx_file(data, pptx_path)


def get_next_test_filepath(file_type: str) -> Path:
    """
    Tạo thư mục nếu chưa có và tìm đường dẫn file tiếp theo (vd: test/pptx/test_1.pptx).
    - file_type: 'pptx' hoặc 'word' (hoặc 'docx')
    """
    ext = "docx" if file_type in ["word", "docx"] else "pptx"
    folder_name = "word" if ext == "docx" else "pptx"

    # 1. Định vị thư mục lưu trữ: test/pptx/ hoặc test/word/
    base_dir = Path(__file__).resolve().parent.parent.parent / "test" / folder_name
    base_dir.mkdir(parents=True, exist_ok=True)  # Tự động tạo thư mục nếu chưa tồn tại

    # 2. Quét các file hiện có để tìm index lớn nhất
    index = 1
    while (base_dir / f"test_{index}.{ext}").exists():
        index += 1

    return base_dir / f"test_{index}.{ext}"
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sinh Kế hoạch bài dạy (5512) và Slide bài giảng bằng Gemini AI")
    parser.add_argument("--topic", type=str, help="Tên chủ đề / bài dạy (VD: Cấp số cộng, Đạo hàm...)")
    parser.add_argument("--subject", type=str, default="Toán học", help="Tên môn học (mặc định: Toán học)")
    parser.add_argument("--grade", type=int, default=12, help="Khối lớp (mặc định: 12)")
    args = parser.parse_args()

    topic = args.topic
    if not topic:
        try:
            topic = input("📌 Nhập tên bài dạy / chủ đề cần sinh (VD: Cấp số cộng, Đạo hàm, Tích phân...): ").strip()
        except Exception:
            topic = ""
        if not topic:
            topic = "Cấp số cộng"

    subject = args.subject
    grade = args.grade

    print(f"\n Đang tiến hành tạo Giáo án & Slide cho bài: '{topic}', Môn {subject}, Lớp {grade}...")

    plan, val_result = generate_lesson_plan(
        topic=topic,
        subject=subject,
        grade=grade
    )
    docx_path = get_next_test_filepath("word")
    docx_stream = export_lesson_plan_to_docx(plan)
    with open(docx_path, "wb") as f:
        f.write(docx_stream.getbuffer())
    print(f"✅ Đã xuất ra file Word: {docx_path}")

    # Xuất Slide dùng chính plan vừa sinh ra
    print("\n🚀 Đang sinh Slide bài giảng JSON từ AI...")
    try:
        slide_deck = generate_slide_deck(
            topic=topic,
            subject=subject,
            grade=grade,
            plan=plan  # Truyền plan vào để thông tin ăn khớp 100%
        )
        pptx_path = get_next_test_filepath("pptx")
        export_slide_to_pptx(slide_deck, str(pptx_path))
        print(f"🎉 Đã xuất thành công file PowerPoint: {pptx_path}")
    except Exception as e:
        print(f"⚠️ Lỗi khi xuất PowerPoint: {e}")
