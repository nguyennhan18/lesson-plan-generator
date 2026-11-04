"""Bounded, killable jobs. Importing this module never starts a process."""
import multiprocessing as mp
import threading
import time


class JobError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _entry(connection, operation, payload):
    try:
        # Linux release workers have hard memory/CPU ceilings in addition to the parent deadline.
        import sys
        if sys.platform.startswith("linux"):
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(1536*1024*1024,1536*1024*1024))
            resource.setrlimit(resource.RLIMIT_CPU,(20,20))
        if operation.startswith("math."):
            from lessonai.services.math_worker import execute
        elif operation.startswith("ingest."):
            from lessonai.services.uploads import execute
        else:
            raise JobError("job_unsupported", "Tác vụ chưa được hỗ trợ")
        connection.send({"result": execute(operation, payload)})
    except Exception as error:
        connection.send({"error": {"code": getattr(error, "code", "job_failed"),
                                   "message": str(error)[:500]}})
    finally:
        connection.close()


class JobRunner:
    def __init__(self, concurrency=2, capacity=10):
        self._slots = threading.BoundedSemaphore(concurrency)
        self._capacity = threading.BoundedSemaphore(capacity)
        self._lock = threading.RLock()
        self._processes = set()
        self._closed = False

    def run(self, operation, payload, *, timeout=5, wait_timeout=1):
        deadline = time.monotonic() + timeout
        if not self._capacity.acquire(blocking=False):
            raise JobError("job_busy", "Hàng đợi đã đầy, vui lòng thử lại")
        acquired = False
        process = parent = child = None
        try:
            acquired = self._slots.acquire(timeout=min(wait_timeout, timeout))
            if not acquired:
                raise JobError("job_busy", "Các tác vụ đang bận, vui lòng thử lại")
            context = mp.get_context("spawn")
            parent, child = context.Pipe(duplex=False)
            process = context.Process(target=_entry, args=(child, operation, payload), daemon=True)
            with self._lock:
                if self._closed:
                    raise JobError("job_unavailable", "Bộ xử lý đã dừng")
                process.start()
                self._processes.add(process)
            child.close()
            if not parent.poll(max(0, deadline - time.monotonic())):
                raise JobError("job_timeout", "Tác vụ vượt thời hạn; chưa thể kiểm chứng")
            try:
                result = parent.recv()
            except EOFError as error:
                raise JobError("job_crashed", "Bộ xử lý đã dừng trước khi có kết quả") from error
            if "error" in result:
                raise JobError(**result["error"])
            return result["result"]
        finally:
            if process is not None and process.pid is not None:
                process.join(timeout=0.1)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=0.5)
                if process.is_alive():
                    process.kill()
                    process.join(timeout=0.5)
                with self._lock:
                    self._processes.discard(process)
                process.close()
            for connection in (parent, child):
                if connection is not None:
                    connection.close()
            if acquired:
                self._slots.release()
            self._capacity.release()

    def close(self):
        with self._lock:
            self._closed = True
            for process in list(self._processes):
                if process.is_alive():
                    process.terminate()


_runner = None
_runner_lock = threading.Lock()


def get_runner():
    global _runner
    with _runner_lock:
        if _runner is None or _runner._closed:
            _runner = JobRunner()
        return _runner


def close_runner():
    with _runner_lock:
        if _runner is not None:
            _runner.close()
