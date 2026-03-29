import threading
import time
from concurrent.futures import ThreadPoolExecutor


class RequestsPerMinuteLimiter:
    def __init__(self, requests_per_minute, clock=time.monotonic, sleeper=time.sleep):
        self.interval_seconds = 60.0 / requests_per_minute
        self.clock = clock
        self.sleeper = sleeper
        self.lock = threading.Lock()
        self.next_allowed_at = 0.0

    def acquire(self):
        with self.lock:
            now = self.clock()
            if now < self.next_allowed_at:
                wait_time = self.next_allowed_at - now
                self.sleeper(wait_time)
                now = self.clock()

            self.next_allowed_at = max(now, self.next_allowed_at) + self.interval_seconds


def _get_rate_limiter(model):
    requests_per_minute = getattr(model, "requests_per_minute", None)
    if not requests_per_minute:
        return None

    limiter = getattr(model, "_promptbreeder_rate_limiter", None)
    if limiter is None:
        limiter = RequestsPerMinuteLimiter(requests_per_minute)
        setattr(model, "_promptbreeder_rate_limiter", limiter)

    return limiter


def chat_text(model, prompt, **kwargs):
    limiter = _get_rate_limiter(model)
    if limiter is not None:
        limiter.acquire()

    response = model.chat(message=prompt, **kwargs)
    return response.text


def batch_chat_text(model, prompts, max_workers=None, **kwargs):
    def run_chat(prompt):
        return chat_text(model, prompt, **kwargs)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(run_chat, prompts))
