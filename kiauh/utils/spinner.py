import sys
import threading
import time
from typing import List, Literal

from core.constants import (
    COLOR_GREEN,
    COLOR_RED,
    COLOR_WHITE,
    COLOR_YELLOW,
    RESET_FORMAT,
)

SpinnerColor = Literal["white", "red", "green", "yellow"]


class Spinner:
    def __init__(
        self,
        message: str = "Loading",
        color: SpinnerColor = "white",
        interval: float = 0.2,
    ) -> None:
        self.message = f"{message} ..."
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._animate)
        self._color = ""
        self._set_color(color)

    def _animate(self) -> None:
        animation: List[str] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        while not self._stop_event.is_set():
            for char in animation:
                sys.stdout.write(f"\r{self._color}{char}{RESET_FORMAT} {self.message}")
                sys.stdout.flush()
                time.sleep(self.interval)
                if self._stop_event.is_set():
                    break
        sys.stdout.write("\r" + " " * (len(self.message) + 1) + "\r")
        sys.stdout.flush()

    def _set_color(self, color: SpinnerColor) -> None:
        if color == "white":
            self._color = COLOR_WHITE
        elif color == "red":
            self._color = COLOR_RED
        elif color == "green":
            self._color = COLOR_GREEN
        elif color == "yellow":
            self._color = COLOR_YELLOW

    def start(self) -> None:
        self._stop_event.clear()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._animate)
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join()
