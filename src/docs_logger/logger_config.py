from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .borders_manipulator import BordersManipulator
from .missing_args_treatment import MissingArgsTreatment

if TYPE_CHECKING:
    from collections.abc import Collection


@dataclass(slots=True)
class DocsLoggerConfig:
    borders: str = "``"
    format_str: str = "{docs}"

    missing_args_treatment: MissingArgsTreatment | str = "unchange"
    docsless_format_str: str = "Calling {func_obj.__qualname__}..."

    logger_level: str | int = "DEBUG"
    logger_catch: bool = True

    ignore: Collection[str] = field(default_factory=set)
    ignore_from_types: Collection[type] = field(default_factory=set)
    always_include: Collection[str] = field(
        default_factory=lambda: {"__init__"}
    )

    docs_loggerize_subclasses: bool = False

    borders_manipulator: BordersManipulator = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.ignore = set(self.ignore)
        for t in self.ignore_from_types:
            self.ignore |= set(dir(t))
        self.ignore -= set(self.always_include)

        mat = self.missing_args_treatment
        self.missing_args_treatment = MissingArgsTreatment(mat)

        self.borders_manipulator = BordersManipulator(self.borders)
