import sys
import threading
import time
from typing import List, Literal, Set

from core.i18n import _tr
from core.types.color import Color

SpinnerColor = Literal["white", "red", "green", "yellow"]


class Spinner:
    # Keep track of every running spinner so a KeyboardInterrupt can stop all
    # of them before the interpreter shuts down.
    _registry: Set["Spinner"] = set()

    def __init__(
        self,
        message: str = "",
        interval: float = 0.2,
    ) -> None:
        msg = message or _tr("Loading")
        self.message = _tr("{} ...").format(msg)
        self.interval = interval
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._thread = threading.Thread(target=self._animate, daemon=True)

    def _animate(self) -> None:
        animation: List[str] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(self.interval)
                continue
            for char in animation:
                if self._pause_event.is_set() or self._stop_event.is_set():
                    break
                sys.stdout.write(f"\r{Color.GREEN}{char}{Color.RST} {self.message}")
                sys.stdout.flush()
                time.sleep(self.interval)
        sys.stdout.write("\r" + " " * (len(self.message) + 1) + "\r")
        sys.stdout.flush()

    def start(self) -> None:
        self._stop_event.clear()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._animate, daemon=True)
            self._thread.start()
        Spinner._registry.add(self)

    def pause(self) -> None:
        """Pause animation and clear the current spinner line.

        Clearing the line is essential: if a child process (for example
        ``sudo apt-get``) writes a password prompt to the terminal, the prompt
        must appear on a blank line instead of being overwritten by the
        spinner frame.
        """
        self._pause_event.set()
        sys.stdout.write("\r" + " " * (len(self.message) + 1) + "\r")
        sys.stdout.flush()

    def resume(self) -> None:
        self._pause_event.clear()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join()
        Spinner._registry.discard(self)

    @classmethod
    def stop_all(cls) -> None:
        """Stop every spinner that is still registered."""
        for spinner in list(cls._registry):
            spinner.stop()
