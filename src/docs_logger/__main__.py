from dataclasses import dataclass
from typing import Self

from src import DocsLoggerConfig, loguru_logger
from src.docs_logger.logger import docs_logger


@dataclass(slots=True, repr=False)
class IPhone:
    version: str = ""
    color: str = ""
    os: str = ""

    def __repr__(self) -> str:
        return (
            f"{self.color.capitalize()} IPhone {self.version} with {self.os}"
        )


@docs_logger(
    docs_logger_config=DocsLoggerConfig(
        docs_loggerize_subclasses=True,
        docsless_format_str="",
        missing_args_treatment="remove",
    ),
)
class IPhoneBuilder:
    def __init__(self, name: str) -> None:
        """Initialize `name` builder"""
        super().__init__()
        self._name = name

    def init_iphone(self, version: str) -> Self:
        """Initialize IPhone `version`"""
        self._iphone = IPhone()
        self._iphone.version = version
        return self

    def color_iphone(self, color: str) -> Self:
        """Color iphone with `color`"""
        self._iphone.color = color
        return self

    def install_os(self, os: str) -> Self:
        """Install `os` `lalala` in IPhone"""
        self._iphone.os = os
        return self

    def get_iphone(self) -> IPhone:
        """Getting `lalala.__class__`"""
        return self._iphone


class AnthennaIPhoneBuilder(IPhoneBuilder):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._anthenna = False

    def add_anthenna(self) -> Self:
        """Adding anthenna"""
        self._anthenna = True
        return self

    def remove_anthenna(self) -> Self:
        """Removing anthenna"""
        self._anthenna = False
        return self

    def __repr__(self) -> str:
        iphone = self.get_iphone()
        if self._anthenna:
            return f"{iphone!r} (with anthenna)"
        return f"{iphone!r}"


def main() -> None:
    loguru_logger.opt(raw=True).debug(
        f"""{
            AnthennaIPhoneBuilder("Bob")
            .init_iphone("15 Pro Max")
            .color_iphone("red")
            .install_os("IOS X")
            .add_anthenna()!r
        }\n"""
    )


if __name__ == "__main__":
    main()
