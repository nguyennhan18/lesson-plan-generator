"""One process-wide lock for every Matplotlib renderer; no service imports."""

from functools import wraps
from threading import RLock

RENDER_LOCK = RLock()


def serialized_render(render):
    """Serialize full jobs and release only figures created by that job, on error too."""
    @wraps(render)
    def run(*args, **kwargs):
        with RENDER_LOCK:
            import matplotlib.pyplot as plt
            existing = set(plt.get_fignums())
            try:
                with plt.rc_context({
                    "font.sans-serif": ["Times New Roman", "Arial", "DejaVu Sans"],
                    "font.family": "serif", "axes.unicode_minus": False,
                }):
                    return render(*args, **kwargs)
            finally:
                for number in set(plt.get_fignums()) - existing:
                    plt.close(number)
    return run
