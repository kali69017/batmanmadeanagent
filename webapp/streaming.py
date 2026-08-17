"""Server-Sent Events helpers."""
import json
import logging
import queue
import threading

from django.http import StreamingHttpResponse

logger = logging.getLogger(__name__)

_STOP = object()


def sse_response(job) -> StreamingHttpResponse:
    """Run `job(event_cb)` in a daemon thread and stream its events as SSE.

    `job` is any callable taking a single event callback that receives
    JSON-serializable dicts. Events are framed as `data: {json}\n\n`.

    When the client disconnects the worker thread is signalled to stop,
    preventing wasted LLM calls and releasing RUN_LOCK promptly.
    """
    q: "queue.Queue[dict | None]" = queue.Queue()
    stop_event = threading.Event()

    def worker():
        # Wrap q.put so the job can signal "stop" via _STOP sentinel.
        def emit(item):
            if stop_event.is_set():
                raise StopIteration("client disconnected")
            q.put(item)

        try:
            job(emit)
        except StopIteration:
            logger.info("SSE worker stopped: client disconnected")
        except Exception:
            logger.exception("SSE worker failed")
        finally:
            q.put(None)

    threading.Thread(target=worker, daemon=True).start()

    def event_source():
        try:
            while True:
                try:
                    item = q.get(timeout=1)
                except queue.Empty:
                    continue
                if item is None:
                    break
                yield f"data: {json.dumps(item, default=str)}\n\n"
        except GeneratorExit:
            # Client disconnected — signal the worker to stop.
            stop_event.set()

    return StreamingHttpResponse(event_source(), content_type="text/event-stream")
