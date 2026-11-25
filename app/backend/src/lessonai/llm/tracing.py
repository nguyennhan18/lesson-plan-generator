"""Langfuse v5 Full Observability cho Role-Based Prompt Chaining & LLM Gateway (feature/ban-lam-viec).

Nguyên tắc thiết kế:
- Tracing chỉ là tầng quan sát (Observability): mọi lỗi của SDK/mạng đều được bắt và ghi log nhẹ,
  không bao giờ làm gián đoạn luồng sinh bài giảng hay làm mất Bản soạn của giáo viên.
- Hỗ trợ phân cấp chuẩn Langfuse v5:
  * `chain`      : Toàn bộ pipeline của một API (Workbench Outline v3 / Outline v2 / Lesson Plan / Slide Deck), gom theo `session_id`.
  * `retriever`  : Bước truy xuất ngữ cảnh sư phạm Pedagogical RAG đã duyệt.
  * `agent`      : Từng vai trò chuyên biệt trong chuỗi Prompt Chaining (kèm `prompt_name` & `prompt_version`).
  * `generation` : Từng lần gọi model cụ thể trong `LLMGateway` (kèm `usage_details` input/output/total tokens).
  * `evaluator`  : Các cổng kiểm định Deterministic Gates (Workbench contract, 5512, `outline_contract`, `KINDS` 3D, `block_errors`, `source_refs` SHA-256).
- Tự động tắt gọi mạng khi thiếu khóa, khi `LANGFUSE_TRACING_ENABLED=false`, hoặc khi chạy dưới `pytest`
  (trừ khi test chủ động bơm mock client qua `set_client_for_testing`).
"""

from __future__ import annotations

import os
import sys
from contextlib import ExitStack, contextmanager
from typing import Any, Dict, Iterator, List, Optional

_client: Any = None
_initialized = False
_testing_override = False


def _enabled() -> bool:
    if _testing_override:
        return _client is not None
    if "pytest" in sys.modules:
        return False
    if os.getenv("LANGFUSE_TRACING_ENABLED", "true").strip().lower() in {"0", "false", "no"}:
        return False
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def _get_client() -> Any:
    global _client, _initialized
    if _testing_override:
        return _client
    if _initialized:
        return _client
    _initialized = True
    if not _enabled():
        return None
    try:
        from langfuse import Langfuse

        base_url = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST")
        _client = Langfuse(base_url=base_url) if base_url else Langfuse()
    except Exception as exc:  # noqa: BLE001 - tracing must never break generation
        print(f"[Langfuse] Tắt tracing do lỗi khởi tạo: {exc}")
        _client = None
    return _client


def set_client_for_testing(mock_client: Any = None) -> None:
    """Cho phép unit test bơm mock Langfuse client để kiểm chứng cây observation mà không gọi mạng."""
    global _client, _initialized, _testing_override
    _client = mock_client
    _initialized = True
    _testing_override = mock_client is not None


class ObservationHandle:
    """Tay cầm an toàn cho một span/chain/agent/retriever/evaluator đang mở."""

    def __init__(self, obs: Any = None):
        self._obs = obs

    def set_output(self, output: Any, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        if self._obs is None:
            return
        try:
            kwargs: Dict[str, Any] = {"output": output}
            if metadata:
                kwargs["metadata"] = metadata
            self._obs.update(**kwargs)
        except Exception as exc:  # noqa: BLE001
            print(f"[Langfuse] Bỏ qua lỗi cập nhật output span: {exc}")

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        if self._obs is None or not metadata:
            return
        try:
            self._obs.update(metadata=metadata)
        except Exception as exc:  # noqa: BLE001
            print(f"[Langfuse] Bỏ qua lỗi cập nhật metadata span: {exc}")

    def mark_warning(self, message: str, *, output: Any = None) -> None:
        if self._obs is None:
            return
        try:
            kwargs: Dict[str, Any] = {"level": "WARNING", "status_message": str(message)[:300]}
            if output is not None:
                kwargs["output"] = output
            self._obs.update(**kwargs)
        except Exception as exc:  # noqa: BLE001
            print(f"[Langfuse] Bỏ qua lỗi đánh dấu warning span: {exc}")

    def fail(self, error: BaseException | str) -> None:
        if self._obs is None:
            return
        try:
            self._obs.update(level="ERROR", status_message=str(error)[:300])
        except Exception as exc:  # noqa: BLE001
            print(f"[Langfuse] Bỏ qua lỗi đánh dấu fail span: {exc}")


class Generation:
    """Một lần gọi LLM trên một route trong LLMGateway; mọi phương thức an toàn khi tracing tắt."""

    def __init__(self, obs: Any = None):
        self._obs = obs

    def finish(
        self,
        output: Any = None,
        *,
        usage_details: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self._obs is None:
            return
        try:
            kwargs: Dict[str, Any] = {"output": output}
            if usage_details:
                kwargs["usage_details"] = usage_details
            if metadata:
                kwargs["metadata"] = metadata
            self._obs.update(**kwargs)
            self._obs.end()
        except Exception as exc:  # noqa: BLE001
            print(f"[Langfuse] Bỏ qua lỗi ghi generation: {exc}")

    def fail(self, error: BaseException | str) -> None:
        if self._obs is None:
            return
        try:
            self._obs.update(level="ERROR", status_message=str(error)[:300])
            self._obs.end()
        except Exception as exc:  # noqa: BLE001
            print(f"[Langfuse] Bỏ qua lỗi ghi lỗi generation: {exc}")


def extract_usage_details(response: Any, provider_id: str) -> Optional[Dict[str, int]]:
    """
    Trích xuất số lượng token thực tế (input, output, total) từ đối tượng phản hồi của
    Google GenAI (`usage_metadata`) hoặc Groq / OpenRouter (`usage`).
    """
    if response is None:
        return None
    try:
        if provider_id == "google":
            meta = getattr(response, "usage_metadata", None)
            if meta is None:
                return None
            inp = getattr(meta, "prompt_token_count", None)
            out = getattr(meta, "candidates_token_count", None)
            tot = getattr(meta, "total_token_count", None)
        else:
            usage = getattr(response, "usage", None)
            if usage is None:
                return None
            inp = getattr(usage, "prompt_tokens", None)
            out = getattr(usage, "completion_tokens", None)
            tot = getattr(usage, "total_tokens", None)

        usage_dict: Dict[str, int] = {}
        if isinstance(inp, int) and inp >= 0:
            usage_dict["input"] = inp
        if isinstance(out, int) and out >= 0:
            usage_dict["output"] = out
        if isinstance(tot, int) and tot >= 0:
            usage_dict["total"] = tot
        elif "input" in usage_dict and "output" in usage_dict:
            usage_dict["total"] = usage_dict["input"] + usage_dict["output"]

        return usage_dict if usage_dict else None
    except Exception:  # noqa: BLE001
        return None


def start_generation(
    *,
    name: str,
    provider: str,
    model: str,
    system_prompt: str,
    prompt: str,
    temperature: float,
    role_name: Optional[str] = None,
    prompt_name: Optional[str] = None,
    prompt_version: Optional[str] = None,
) -> Generation:
    client = _get_client()
    if client is None:
        return Generation()
    try:
        meta: Dict[str, Any] = {"provider": provider}
        if role_name:
            meta["role_name"] = role_name
        if prompt_name:
            meta["prompt_name"] = prompt_name
        if prompt_version:
            meta["prompt_version"] = prompt_version

        obs = client.start_observation(
            name=name,
            as_type="generation",
            model=model,
            version=prompt_version,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            model_parameters={"temperature": temperature},
            metadata=meta,
        )
        return Generation(obs)
    except Exception as exc:  # noqa: BLE001
        print(f"[Langfuse] Bỏ qua lỗi tạo generation: {exc}")
        return Generation()


@contextmanager
def _observe_context(
    name: str,
    *,
    as_type: str = "span",
    input_data: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
    version: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    is_root_chain: bool = False,
) -> Iterator[ObservationHandle]:
    client = _get_client()
    if client is None:
        yield ObservationHandle()
        return

    with ExitStack() as stack:
        obs_obj = None
        try:
            obs_cm = client.start_as_current_observation(
                name=name,
                as_type=as_type,
                input=input_data,
                metadata=metadata,
                version=version,
            )
            obs_obj = stack.enter_context(obs_cm)

            if is_root_chain and (session_id or tags or metadata):
                try:
                    from langfuse import propagate_attributes

                    prop_cm = propagate_attributes(
                        session_id=session_id,
                        tags=[t for t in (tags or []) if t],
                        metadata={k: str(v)[:200] for k, v in (metadata or {}).items() if v is not None},
                        trace_name=name,
                    )
                    stack.enter_context(prop_cm)
                except Exception:  # noqa: BLE001
                    pass
        except Exception as exc:  # noqa: BLE001
            print(f"[Langfuse] Bỏ qua lỗi mở observation '{name}': {exc}")
            obs_obj = None

        handle = ObservationHandle(obs_obj)
        try:
            yield handle
        except BaseException as exc:
            handle.fail(exc)
            raise


@contextmanager
def trace_chain(
    name: str,
    *,
    session_id: Optional[str] = None,
    lesson_id: Optional[str] = None,
    topic: Optional[str] = None,
    proficiency: Optional[str] = None,
    input_data: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Iterator[ObservationHandle]:
    """Root span `as_type='chain'` gom toàn bộ các vai trò của một pipeline và gắn `session_id`."""
    tags: List[str] = ["prompt-chain"]
    if lesson_id:
        tags.append(str(lesson_id))
    if proficiency:
        tags.append(f"proficiency:{proficiency}")

    merged_meta: Dict[str, Any] = {
        "lesson_id": lesson_id,
        "topic": topic,
        "proficiency": proficiency,
        **(metadata or {}),
    }
    with _observe_context(
        name,
        as_type="chain",
        input_data=input_data,
        metadata=merged_meta,
        session_id=session_id,
        tags=tags,
        is_root_chain=True,
    ) as handle:
        yield handle


@contextmanager
def observe_role(
    role_name: str,
    *,
    prompt_name: str,
    prompt_version: str,
    input_data: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Iterator[ObservationHandle]:
    """Span `as_type='agent'` đại diện cho một Vai trò (Role) trong chuỗi Prompt Chaining."""
    role_meta: Dict[str, Any] = {
        "role_name": role_name,
        "prompt_name": prompt_name,
        "prompt_version": prompt_version,
        **(metadata or {}),
    }
    with _observe_context(
        role_name,
        as_type="agent",
        input_data=input_data,
        metadata=role_meta,
        version=prompt_version,
    ) as handle:
        yield handle


@contextmanager
def observe_retriever(
    name: str,
    *,
    input_data: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Iterator[ObservationHandle]:
    """Span `as_type='retriever'` ghi nhận bước truy xuất ngữ cảnh sư phạm RAG."""
    with _observe_context(
        name,
        as_type="retriever",
        input_data=input_data,
        metadata=metadata,
    ) as handle:
        yield handle


@contextmanager
def observe_evaluator(
    name: str,
    *,
    input_data: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Iterator[ObservationHandle]:
    """Span `as_type='evaluator'` ghi nhận kết quả kiểm định tại các cổng Gate 1/2/3."""
    with _observe_context(
        name,
        as_type="evaluator",
        input_data=input_data,
        metadata=metadata,
    ) as handle:
        yield handle


@contextmanager
def trace_span(name: str, *, metadata: Optional[Dict[str, Any]] = None) -> Iterator[ObservationHandle]:
    """Span cha tổng quát gom chuỗi fallback giữa các provider trong LLMGateway."""
    with _observe_context(name, as_type="span", metadata=metadata) as handle:
        yield handle


def record_trace_score(
    name: str,
    value: float | str,
    *,
    data_type: Optional[str] = None,
    comment: Optional[str] = None,
) -> None:
    """Ghi điểm chất lượng tự động (Score) lên Trace hiện tại trên Langfuse."""
    client = _get_client()
    if client is None:
        return
    try:
        resolved_type = data_type or ("CATEGORICAL" if isinstance(value, str) else "NUMERIC")
        client.score_current_trace(
            name=name,
            value=value,
            data_type=resolved_type,
            comment=comment,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[Langfuse] Bỏ qua lỗi ghi score '{name}': {exc}")


def flush() -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.flush()
    except Exception:  # noqa: BLE001
        pass
