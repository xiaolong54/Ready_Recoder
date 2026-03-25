from dataclasses import dataclass
from datetime import datetime
from queue import Queue, Empty
from typing import List


@dataclass
class LogEvent:
    timestamp: str
    level: str
    message: str
    source: str = "GUI"


class ThemeState:
    def __init__(self, mode: str = "dark", light_theme: str = "flatly", dark_theme: str = "cyborg"):
        self.light_theme = light_theme
        self.dark_theme = dark_theme
        self.mode = "dark" if mode not in ("light", "dark") else mode

    def set_mode(self, mode: str) -> None:
        if mode in ("light", "dark"):
            self.mode = mode

    def toggle(self) -> str:
        self.mode = "light" if self.mode == "dark" else "dark"
        return self.mode

    @property
    def current_theme(self) -> str:
        return self.dark_theme if self.mode == "dark" else self.light_theme


class NavigationState:
    def __init__(self, pages: List[str], current: str):
        self.pages = list(pages)
        self.current = current if current in self.pages else self.pages[0]

    def switch(self, page: str) -> bool:
        if page not in self.pages:
            return False
        self.current = page
        return True


class LogBuffer:
    def __init__(self, max_events: int = 1000):
        self.max_events = max_events
        self.events: List[LogEvent] = []
        self.queue: Queue = Queue()

    def emit(self, level: str, message: str, source: str = "GUI") -> None:
        event = LogEvent(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            level=(level or "INFO").upper(),
            message=message,
            source=source,
        )
        self.queue.put(event)

    def drain(self) -> List[LogEvent]:
        drained: List[LogEvent] = []
        while True:
            try:
                event = self.queue.get_nowait()
            except Empty:
                break
            self.events.append(event)
            drained.append(event)

        overflow = len(self.events) - self.max_events
        if overflow > 0:
            self.events = self.events[overflow:]

        return drained

    def clear(self) -> None:
        self.events.clear()
        while True:
            try:
                self.queue.get_nowait()
            except Empty:
                break

    def filtered(self, level: str = "ALL") -> List[LogEvent]:
        normalized = (level or "ALL").upper()
        if normalized == "ALL":
            return list(self.events)
        return [event for event in self.events if event.level == normalized]

    def recent(self, limit: int = 10) -> List[LogEvent]:
        if limit <= 0:
            return []
        return self.events[-limit:]
