"""
Mô-đun LLM Gateway Đa Nhà Cung Cấp & Tự Động Chuyển Mạch Dự Phòng (Auto-Fallback)

Kiến trúc & Tối ưu hóa:
- Đảm bảo tính sẵn sàng cao (High Availability), triệt tiêu điểm nghẽn đơn lẻ (Zero SPOF).
- Hỗ trợ đa nhà cung cấp: Google Gemini, Groq Cloud LPU, OpenRouter API.
- Chuẩn hóa Model Google: gemini-2.0-flash (Ưu tiên 1) -> gemini-1.5-flash -> gemini-1.5-pro.
- Cơ chế Exponential Backoff khi chạm trần 429 / RESOURCE_EXHAUSTED (nghỉ 4s -> 8s).
- Tương thích Pydantic V2 BaseModel, tự động làm sạch Markdown và sửa lỗi escape LaTeX.
"""

import os
import re
import json
import time
from typing import Type, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path

# Nạp biến môi trường từ .env
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BACKEND_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Nạp OpenAI Client cho Groq và OpenRouter
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Nạp Google GenAI Client chính thức
try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

T = TypeVar("T", bound=BaseModel)

# Regex tìm và sửa lỗi thiếu escape cho các lệnh LaTeX phổ biến trong toán THPT
_LATEX_CMDS = r'(?:sqrt|frac|vec|mathbf|perp|alpha|beta|gamma|Delta|pi|approx|le|ge|neq|in|subset|cap|cup|times)'
_FIX_PATTERN = re.compile(r'(?<!\\)\\(?=' + _LATEX_CMDS + r'\b)')

def fix_latex_backslashes(raw_text: str) -> str:
    r"""
    Tự động chuyển đổi các dấu gạch chéo ngược đơn (\sqrt) thành dấu thoát kép (\\sqrt)
    trong chuỗi JSON để bảo vệ trình phân tích cú pháp json.loads không bị ném ngoại lệ.
    """
    return _FIX_PATTERN.sub(r'\\\\', raw_text)


def strip_markdown_json_fence(text: str) -> str:
    """
    Làm sạch các khối suy luận <think>...</think> và đoạn bọc markdown ```json ... ```
    do một số LLMs (như Qwen, DeepSeek, Gemini) tự ý thêm vào.
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Trích xuất đối tượng JSON ngoài cùng nếu còn sót văn bản dẫn nhập/kết luận
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace : last_brace + 1]
    return text.strip()


class ProviderRoute:
    """
    Đại diện cho một tuyến gọi LLM cụ thể (Provider + Model + Endpoint).
    """
    def __init__(
        self,
        provider_id: str,
        model_name: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.provider_id = provider_id      # "google", "groq", "openrouter"
        self.model_name = model_name        # Tên model cụ thể
        self.base_url = base_url            # Endpoint OpenAI-compatible nếu dùng
        self.api_key = api_key              # API Key tương ứng

    def __repr__(self) -> str:
        return f"<ProviderRoute [{self.provider_id.upper()}]: {self.model_name}>"


class LLMGateway:
    """
    Bộ định tuyến và quản lý chuyển mạch LLM đa nhà cung cấp có cơ chế Auto-Fallback & Backoff.
    """
    google_client: Any = None
    groq_client: Any = None
    openrouter_client: Any = None

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")

        # Lưu lại lịch sử chuyển mạch để phục vụ log và kiểm thử Chaos Testing
        self.transition_history: List[Dict[str, Any]] = []
        self._cached_groq_models: Optional[List[str]] = None
        self._cached_google_models: Optional[List[str]] = None
        # Danh sách đen (Blacklist) chứa các model đã bị ngừng hỗ trợ (404) hoặc không tương thích trong phiên chạy
        self._dead_models: set[str] = set()

        # Khởi tạo Google GenAI Client
        self.google_client: Any = None
        if self.gemini_key and genai is not None:
            try:
                self.google_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                print(f"[LLM Gateway] Cảnh báo khởi tạo Google GenAI Client: {e}")

        # Khởi tạo Groq OpenAI-compatible Client
        self.groq_client: Any = None
        if self.groq_key and OpenAI is not None:
            try:
                self.groq_client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=self.groq_key,
                    timeout=20.0
                )
            except Exception as e:
                print(f"[LLM Gateway] Cảnh báo khởi tạo Groq Client: {e}")

        # Khởi tạo OpenRouter Client
        self.openrouter_client: Any = None
        if self.openrouter_key and OpenAI is not None:
            try:
                self.openrouter_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.openrouter_key,
                    timeout=25.0
                )
            except Exception as e:
                print(f"[LLM Gateway] Cảnh báo khởi tạo OpenRouter Client: {e}")

    def refresh_keys(self):
        """Cập nhật lại các API Key từ biến môi trường nếu có sự thay đổi trong lúc chạy."""
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")

        if self.gemini_key and genai is not None and not self.google_client:
            try:
                self.google_client = genai.Client(api_key=self.gemini_key)
            except Exception:
                pass

        if self.groq_key and OpenAI is not None and not self.groq_client:
            try:
                self.groq_client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=self.groq_key, timeout=20.0)
            except Exception:
                pass

        if self.openrouter_key and OpenAI is not None and not self.openrouter_client:
            try:
                self.openrouter_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=self.openrouter_key, timeout=25.0)
            except Exception:
                pass

    def get_available_groq_models(self) -> List[str]:
        """Tự động truy vấn và lọc các Text-Generation LLM thực tế từ Groq API, loại bỏ Audio/Guardrails."""
        if self._cached_groq_models is not None:
            return [m for m in self._cached_groq_models if f"groq:{m}" not in self._dead_models]
        if not self.groq_client:
            return []
        try:
            res = self.groq_client.models.list()
            excluded_keywords = (
                "guard", "whisper", "orpheus", "tts", "audio",
                "vision", "embed", "moderation", "safeguard", "playai", "allam"
            )
            models = []
            for m in getattr(res, "data", []):
                mid = getattr(m, "id", "")
                if mid and not any(kw in mid.lower() for kw in excluded_keywords):
                    models.append(mid)

            def _groq_priority(model_id: str) -> int:
                ml = model_id.lower()
                if "llama-3.3" in ml or "llama-4" in ml or "llama-3.1-70b" in ml:
                    return 0
                if "qwen" in ml:
                    return 1
                if "deepseek" in ml:
                    return 2
                if "llama" in ml:
                    return 3
                if "gemma" in ml or "mixtral" in ml:
                    return 4
                return 5

            models.sort(key=_groq_priority)
            if models:
                print(f"[LLM Gateway] 🔍 Đã lọc {len(models)} model sinh văn bản Groq khả dụng: {models[:5]}")
                self._cached_groq_models = models
                return [m for m in models if f"groq:{m}" not in self._dead_models]
        except Exception:
            pass
        return []

    def get_available_google_models(self) -> List[str]:
        """Tự động truy vấn và lọc các model Gemini sinh văn bản đang hoạt động, loại bỏ model ngừng hỗ trợ (2.5) và TTS/Image."""
        if self._cached_google_models is not None:
            return [m for m in self._cached_google_models if f"google:{m}" not in self._dead_models]
        if not self.google_client:
            return []
        try:
            excluded_keywords = (
                "embedding", "aqa", "tts", "image", "imagen", "veo",
                "vision", "audio", "live", "robotics", "computer-use",
                "learnlm", "2.5-flash", "2.5-pro", "2.0-flash-exp", "1.5-", "1.0-"
            )
            models = []
            for m in self.google_client.models.list():
                raw = getattr(m, "name", "")
                clean = raw.replace("models/", "")
                if "gemini" in clean.lower() and not any(kw in clean.lower() for kw in excluded_keywords):
                    models.append(clean)

            def _google_priority(model_id: str) -> int:
                ml = model_id.lower()
                if ml == "gemini-flash-latest":
                    return 0
                if "gemini-3" in ml and "flash" in ml and "preview" not in ml:
                    return 1
                if "gemini-3" in ml and "flash" in ml:
                    return 2
                if "flash" in ml and "lite" not in ml:
                    return 3
                if "pro" in ml and "preview" not in ml:
                    return 4
                return 5

            models.sort(key=_google_priority)
            if models:
                print(f"[LLM Gateway] 🔍 Đã lọc {len(models)} model sinh văn bản Google khả dụng: {models[:5]}")
                self._cached_google_models = models
                return [m for m in models if f"google:{m}" not in self._dead_models]
        except Exception:
            pass
        return []

    def get_active_routes(self, task_type: str = "lesson_plan") -> List[ProviderRoute]:
        """
        Xác định danh sách các tuyến ưu tiên (Routing Matrix) dựa theo task_type
        và các API Key thực tế đang có sẵn trong môi trường.
        """
        self.refresh_keys()
        routes: List[ProviderRoute] = []

        # Lấy danh sách model Google thực tế hoặc fallback
        google_models = self.get_available_google_models()
        if not google_models:
            google_models = [
                m for m in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
                if f"google:{m}" not in self._dead_models
            ]

        # Lấy danh sách model Groq thực tế hoặc fallback
        groq_models = self.get_available_groq_models()
        if not groq_models:
            groq_models = [
                m for m in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
                if f"groq:{m}" not in self._dead_models
            ]

        if task_type == "lesson_plan":
            # 1. Soạn Kế hoạch bài dạy 5512
            if self.gemini_key:
                for m in google_models[:2]:
                    routes.append(ProviderRoute("google", m, api_key=self.gemini_key))
            if self.groq_key:
                for m in groq_models[:2]:
                    routes.append(ProviderRoute("groq", m, "https://api.groq.com/openai/v1", self.groq_key))
            if self.openrouter_key and "openrouter:deepseek/deepseek-chat" not in self._dead_models:
                routes.append(ProviderRoute("openrouter", "deepseek/deepseek-chat", "https://openrouter.ai/api/v1", self.openrouter_key))
            if self.gemini_key and len(google_models) > 2:
                for m in google_models[2:4]:
                    routes.append(ProviderRoute("google", m, api_key=self.gemini_key))

        elif task_type == "slide":
            # 2. Sinh cấu trúc Slide bài giảng (Ưu tiên Groq nếu có, sau đó Google)
            if self.groq_key:
                for m in groq_models[:2]:
                    routes.append(ProviderRoute("groq", m, "https://api.groq.com/openai/v1", self.groq_key))
            if self.gemini_key:
                for m in google_models[:2]:
                    routes.append(ProviderRoute("google", m, api_key=self.gemini_key))
            if self.openrouter_key and "openrouter:deepseek/deepseek-chat" not in self._dead_models:
                routes.append(ProviderRoute("openrouter", "deepseek/deepseek-chat", "https://openrouter.ai/api/v1", self.openrouter_key))

        elif task_type == "chat":
            # 3. Chat Trợ giảng Co-pilot
            if self.groq_key:
                for m in groq_models[:2]:
                    routes.append(ProviderRoute("groq", m, "https://api.groq.com/openai/v1", self.groq_key))
            if self.gemini_key:
                for m in google_models[:2]:
                    routes.append(ProviderRoute("google", m, api_key=self.gemini_key))
            if self.openrouter_key and "openrouter:deepseek/deepseek-chat" not in self._dead_models:
                routes.append(ProviderRoute("openrouter", "deepseek/deepseek-chat", "https://openrouter.ai/api/v1", self.openrouter_key))

        elif task_type == "math_code":
            # 4. Sinh mã nguồn hình học / đồ thị
            if self.openrouter_key and "openrouter:qwen/qwen-2.5-coder-32b-instruct" not in self._dead_models:
                routes.append(ProviderRoute("openrouter", "qwen/qwen-2.5-coder-32b-instruct", "https://openrouter.ai/api/v1", self.openrouter_key))
            if self.groq_key and groq_models:
                routes.append(ProviderRoute("groq", groq_models[0], "https://api.groq.com/openai/v1", self.groq_key))
            if self.gemini_key and google_models:
                routes.append(ProviderRoute("google", google_models[0], api_key=self.gemini_key))

        else:
            # Tuyến mặc định an toàn
            if self.gemini_key and google_models:
                routes.append(ProviderRoute("google", google_models[0], api_key=self.gemini_key))
            if self.groq_key and groq_models:
                routes.append(ProviderRoute("groq", groq_models[0], "https://api.groq.com/openai/v1", self.groq_key))

        return [r for r in routes if f"{r.provider_id}:{r.model_name}" not in self._dead_models]

    def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        response_schema: Type[T],
        task_type: str = "lesson_plan",
        temperature: float = 0.7
    ) -> T:
        """
        Thực thi sinh dữ liệu có cấu trúc Pydantic Schema qua chuỗi Fallback thông minh.
        Tích hợp Exponential Backoff 4s -> 8s khi gặp lỗi 429/RESOURCE_EXHAUSTED.
        Tự động chuyển mạch tức thời sang Provider tiếp theo (Google -> Groq -> OpenRouter).
        """
        routes = self.get_active_routes(task_type)
        if not routes:
            raise ValueError(
                "Không tìm thấy API Key nào khả dụng! Vui lòng cấu hình ít nhất GEMINI_API_KEY hoặc GROQ_API_KEY trong tệp .env"
            )

        last_error = None
        start_time = time.time()

        for idx, route in enumerate(routes):
            attempt_start = time.time()

            # Hỗ trợ tối đa 2 lần thử nội bộ trên từng route có kèm Exponential Backoff nếu chạm trần 429
            max_route_attempts = 2 if route.provider_id == "google" else 1

            for route_attempt in range(max_route_attempts):
                try:
                    print(f"[LLM Gateway] 🚀 Đang định tuyến tới [{route.provider_id.upper()}]: Model '{route.model_name}' (Tác vụ: '{task_type}' | Lần {route_attempt + 1})...")

                    # ================= 1. XỬ LÝ QUA GOOGLE GENAI SDK =================
                    if route.provider_id == "google" and self.google_client is not None and genai_types is not None:
                        config = genai_types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_mime_type="application/json",
                            response_schema=response_schema,
                            temperature=temperature,
                            automatic_function_calling=genai_types.AutomaticFunctionCallingConfig.model_validate({"disable": True})
                        )
                        res = self.google_client.models.generate_content(
                            model=route.model_name,
                            contents=prompt,
                            config=config
                        )
                        raw_text = res.text or ""
                        clean_text = strip_markdown_json_fence(fix_latex_backslashes(raw_text))
                        result = response_schema.model_validate_json(clean_text)

                        latency = round(time.time() - attempt_start, 2)
                        self.transition_history.append({
                            "provider": route.provider_id,
                            "model": route.model_name,
                            "status": "success",
                            "latency_sec": latency
                        })
                        print(f"[LLM Gateway] ✅ Thành công với [{route.provider_id.upper()}]: '{route.model_name}' trong {latency}s")
                        return result

                    # ================= 2. XỬ LÝ QUA GROQ CLOUD LPU =================
                    elif route.provider_id == "groq" and self.groq_client is not None:
                        schema_json = json.dumps(response_schema.model_json_schema(), ensure_ascii=False)
                        messages = [
                            {
                                "role": "system",
                                "content": (
                                    f"{system_prompt}\n\nQUY TẮC BẮT BUỘC:\n"
                                    f"Chỉ trả về duy nhất chuỗi JSON hợp lệ tuân thủ chính xác Schema sau:\n{schema_json}\n"
                                    "Tuyệt đối không bọc trong ```json, không xuất thẻ <think> và không có bất kỳ ký tự nào ngoài JSON."
                                )
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                        try:
                            completion = self.groq_client.chat.completions.create(
                                model=route.model_name,
                                messages=messages,
                                response_format={"type": "json_object"},
                                temperature=temperature
                            )
                            raw_text = completion.choices[0].message.content or "{}"
                        except Exception as groq_err:
                            err_text = str(groq_err).lower()
                            if "failed to generate json" in err_text or "failed_generation" in err_text or "json_validate_failed" in err_text:
                                print(f"[LLM Gateway] 🔧 Groq json_object bị từ chối do thẻ suy luận/cú pháp, đang thử lại chế độ tự làm sạch JSON trên '{route.model_name}'...")
                                completion = self.groq_client.chat.completions.create(
                                    model=route.model_name,
                                    messages=messages,
                                    temperature=temperature
                                )
                                raw_text = completion.choices[0].message.content or "{}"
                            else:
                                raise groq_err

                        clean_text = strip_markdown_json_fence(fix_latex_backslashes(raw_text))
                        result = response_schema.model_validate_json(clean_text)

                        latency = round(time.time() - attempt_start, 2)
                        self.transition_history.append({
                            "provider": route.provider_id,
                            "model": route.model_name,
                            "status": "success",
                            "latency_sec": latency
                        })
                        print(f"[LLM Gateway] ✅ Thành công với [{route.provider_id.upper()}]: '{route.model_name}' trong {latency}s")
                        return result

                    # ================= 3. XỬ LÝ QUA OPENROUTER =================
                    elif route.provider_id == "openrouter" and self.openrouter_client is not None:
                        schema_json = json.dumps(response_schema.model_json_schema(), ensure_ascii=False)
                        messages = [
                            {
                                "role": "system",
                                "content": (
                                    f"{system_prompt}\n\nQUY TẮC:\n"
                                    f"Chỉ trả về JSON thuần túy theo Schema:\n{schema_json}"
                                )
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                        completion = self.openrouter_client.chat.completions.create(
                            model=route.model_name,
                            messages=messages,
                            response_format={"type": "json_object"},
                            temperature=temperature
                        )
                        raw_text = completion.choices[0].message.content or "{}"
                        clean_text = strip_markdown_json_fence(fix_latex_backslashes(raw_text))
                        result = response_schema.model_validate_json(clean_text)

                        latency = round(time.time() - attempt_start, 2)
                        self.transition_history.append({
                            "provider": route.provider_id,
                            "model": route.model_name,
                            "status": "success",
                            "latency_sec": latency
                        })
                        print(f"[LLM Gateway] ✅ Thành công với [{route.provider_id.upper()}]: '{route.model_name}' trong {latency}s")
                        return result

                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    err_lower = err_str.lower()
                    is_rate_limit = any(term in err_lower for term in ["429", "resource_exhausted", "ratelimit", "quota"])
                    is_dead_model = any(
                        term in err_lower
                        for term in [
                            "404", "not_found", "no longer available", "does not exist",
                            "not a valid model", "decommissioned", "model_not_found",
                            "reduce the length of the messages"
                        ]
                    )

                    if is_dead_model:
                        self._dead_models.add(f"{route.provider_id}:{route.model_name}")
                        print(f"[LLM Gateway] 🚫 Đã loại bỏ vĩnh viễn model không khả dụng [{route.provider_id.upper()}: {route.model_name}] khỏi danh sách định tuyến.")

                    # NẾU GẶP 429 TRÊN GOOGLE: THỰC HIỆN EXPONENTIAL BACKOFF (4s -> 8s)
                    if is_rate_limit and not is_dead_model and route.provider_id == "google" and route_attempt < max_route_attempts - 1:
                        backoff_sec = 4.0 if route_attempt == 0 else 8.0
                        print(f"[LLM Gateway] ⏳ Phát hiện Quota Limit 429 trên [{route.model_name}]. Đang thực hiện Exponential Backoff ({backoff_sec}s)...")
                        time.sleep(backoff_sec)
                        continue  # Thử lại trên chính model này sau khi đợi

                    # Nếu lỗi khác hoặc đã hết lần thử backoff: Ghi log và nhảy sang route tiếp theo
                    latency = round(time.time() - attempt_start, 2)
                    self.transition_history.append({
                        "provider": route.provider_id,
                        "model": route.model_name,
                        "status": "failed",
                        "error": err_str[:120],
                        "latency_sec": latency
                    })
                    print(f"[LLM Gateway] ⚠️ Tuyến [{route.provider_id.upper()}: {route.model_name}] gặp lỗi: {err_str[:120]}")
                    print("[LLM Gateway] 🔄 Đang tự động chuyển mạch sang tuyến dự phòng kế tiếp...")
                    time.sleep(0.3)
                    break

        total_elapsed = round(time.time() - start_time, 2)
        raise RuntimeError(
            f"Toàn bộ {len(routes)} tuyến LLM đều không phản hồi sau {total_elapsed}s. Lỗi cuối cùng: {last_error}"
        )

    def generate_text(
        self,
        prompt: str,
        system_prompt: str,
        task_type: str = "chat",
        temperature: float = 0.6
    ) -> str:
        """
        Thực thi sinh văn bản tự do (Conversational / Co-pilot) qua chuỗi Fallback đa nhà cung cấp.
        Ưu tiên tốc độ phản hồi cực nhanh của Groq LPU, sau đó đến Gemini và OpenRouter.
        """
        routes = self.get_active_routes(task_type)
        if not routes:
            raise ValueError("Không tìm thấy tuyến LLM khả dụng cho tác vụ sinh văn bản.")

        last_error = None
        for route in routes:
            attempt_start = time.time()
            try:
                if route.provider_id == "google" and self.google_client is not None and genai_types is not None:
                    config = genai_types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=temperature,
                        max_output_tokens=1000
                    )
                    res = self.google_client.models.generate_content(
                        model=route.model_name,
                        contents=prompt,
                        config=config
                    )
                    if res and res.text:
                        latency = round(time.time() - attempt_start, 2)
                        self.transition_history.append({
                            "provider": route.provider_id,
                            "model": route.model_name,
                            "status": "success",
                            "latency_sec": latency
                        })
                        return res.text.strip()

                elif route.provider_id == "groq" and self.groq_client is not None:
                    completion = self.groq_client.chat.completions.create(
                        model=route.model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=temperature,
                        max_tokens=1000
                    )
                    text = completion.choices[0].message.content
                    if text:
                        latency = round(time.time() - attempt_start, 2)
                        self.transition_history.append({
                            "provider": route.provider_id,
                            "model": route.model_name,
                            "status": "success",
                            "latency_sec": latency
                        })
                        return text.strip()

                elif route.provider_id == "openrouter" and self.openrouter_client is not None:
                    completion = self.openrouter_client.chat.completions.create(
                        model=route.model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=temperature,
                        max_tokens=1000
                    )
                    text = completion.choices[0].message.content
                    if text:
                        latency = round(time.time() - attempt_start, 2)
                        self.transition_history.append({
                            "provider": route.provider_id,
                            "model": route.model_name,
                            "status": "success",
                            "latency_sec": latency
                        })
                        return text.strip()
            except Exception as e:
                last_error = e
                latency = round(time.time() - attempt_start, 2)
                self.transition_history.append({
                    "provider": route.provider_id,
                    "model": route.model_name,
                    "status": "failed",
                    "error": str(e)[:120],
                    "latency_sec": latency
                })
                continue

        raise RuntimeError(f"Không thể sinh văn bản phản hồi từ các tuyến LLM: {last_error}")


# Khởi tạo Singleton Gateway dùng chung cho toàn bộ ứng dụng
llm_gateway = LLMGateway()

