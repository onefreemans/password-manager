import threading
import os


_timer = None
_lock = threading.Lock()


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def reset(timeout=600):
    global _timer

    def _on_timeout():
        clear_console()
        print("\nВы неактивны более 10 минут. Программа завершена.")
        os._exit(0)

    with _lock:
        if _timer:
            _timer.cancel()
        _timer = threading.Timer(timeout, _on_timeout)
        _timer.daemon = True
        _timer.start()