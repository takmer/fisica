from typing import Any


class Pin:
    IN: int
    OUT: int
    PULL_DOWN: int

    def __init__(self, id: int, mode: int, pull: int | None = ...) -> None: ...
    def value(self, value: int | None = ...) -> int: ...
