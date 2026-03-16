import threading
import time

value = 0
_started = False
_lock = threading.Lock()


def _heartbeat_loop():
    global value
    while True:
        with _lock:
            value += 1
        time.sleep(1)


def start_heartbeat():
    global _started
    with _lock:
        if _started:
            return
        _started = True
    heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    heartbeat_thread.start()
