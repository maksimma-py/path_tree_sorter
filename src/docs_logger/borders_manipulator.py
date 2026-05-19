import contextlib
import re
from collections.abc import Callable
from re import compile as rc
from typing import Final

from src import loguru_logger

type Repl = str | Callable[[re.Match], str]
type PairedBorders = tuple[str, str] | tuple[()]


class BorderSubPattern:
    POSSIBLE_FORMAT_PARAMS: Final[tuple[tuple[str, str], ...]] = (
        ("l", "r"),
        ("left", "right"),
        ("s", "e"),
        ("start", "end"),
        ("f", "l"),
        ("first", "last"),
    )

    def __init__(
        self, name: str, pattern: str | re.Pattern[str], repl: Repl
    ) -> None:
        self._name = name
        self._pattern = pattern
        self._repl = repl

    def substitute(self, string: str, borders: str | None = None) -> str:
        if isinstance(self._pattern, re.Pattern):
            return re.sub(self._pattern, self._repl, string)

        escaped_borders = self.escaped_paired_borders(borders)

        if not (isinstance(borders, str) and escaped_borders):
            msg = f"{type(self).__name__} should have either a pattern of type re.Pattern or borders of type str"
            raise TypeError(msg)

        return self._get_substituted_pattern(
            self._pattern, escaped_borders, string
        )

    def _get_substituted_pattern(
        self, pattern: str, escaped_borders: tuple[str, str], string: str
    ) -> str:
        try:
            formatted_pattern = pattern.format(*escaped_borders)
            return re.sub(formatted_pattern, self._repl, string)
        except KeyError:
            pass

        for params in self.POSSIBLE_FORMAT_PARAMS:
            kwargs = dict(zip(params, escaped_borders, strict=True))
            with contextlib.suppress(KeyError):
                formatted_pattern = pattern.format(*escaped_borders, **kwargs)
                loguru_logger.info(
                    "\n\n\tFounded params {} in {}\n", params, self
                )
                return re.sub(formatted_pattern, self._repl, string)
        raise KeyError(pattern)

    def escaped_paired_borders(
        self, borders: str | None = None
    ) -> PairedBorders:
        if borders is None or not (
            paired_borders := self.paired_borders(borders)
        ):
            return ()
        left, right = paired_borders
        return re.escape(left), re.escape(right)

    @staticmethod
    def paired_borders(borders: str) -> PairedBorders:
        if not borders:
            return ()
        if len(borders) == 1:
            left = right = borders[0]
        else:
            left, right, *_ = borders

        return left, right

    def __repr__(self) -> str:
        return f'{self._name}(r"{self._pattern}" -> r"{self._repl}")'


class BordersManipulator:
    BORDER_SUB_PATTERNS: Final[list[BorderSubPattern]] = [
        BorderSubPattern("EmptyUnescaped", r"(?<!\\){}(?<!\\){}", r""),
        BorderSubPattern("Unescaped", r"(?<!\\){}(.*?)(?<!\\){}", r"{\1}"),
        BorderSubPattern("EscapedBraces", rc(r"\\\{(.*?)\\\}"), r"{{\1}}"),
        BorderSubPattern("Escaped", r"\\({})(.*?)\\({})", r"\1\2\3"),
    ]

    def __init__(self, borders: str) -> None:
        self._borders = borders
        self._docs = 0

    def sub_borders_in(self, docs: str) -> str:
        for bsp in self.BORDER_SUB_PATTERNS:
            docs = bsp.substitute(docs, self._borders)

        return docs
