from enum import Enum, EnumType, auto
from typing import TYPE_CHECKING

from .borders_manipulator import BorderSubPattern

if TYPE_CHECKING:
    import re


class __CasefoldEnumType(EnumType):
    def __call__(cls: type[Enum], value: str | Enum) -> Enum:  # ty: ignore[invalid-method-override]
        if isinstance(value, Enum):
            return value
        for name, member in cls.__members__.items():
            if name.casefold() == value.casefold():
                return member
        casefolded_names = tuple(name.casefold() for name in cls.__members__)
        msg = f"{value} is not an enum or not a string in {casefolded_names}"
        raise ValueError(msg)


class CasefoldEnum(Enum, metaclass=__CasefoldEnumType):
    @staticmethod
    def _generate_next_value_[*PS](
        name: str, *_args: PS.args, **_kwargs: PS.kwargs
    ) -> str:
        return name.casefold()


class MATError(Exception):
    pass


class MissingArgsTreatment(CasefoldEnum):
    UNCHANGE = auto()
    REMOVE = auto()
    ELLIPSIS = auto()
    ERROR = auto()
    DONT_LOG = auto(), "\x1e"

    def treat(self, missing_arg: re.Match, orig_borders: str) -> str:
        match self:
            case MissingArgsTreatment.UNCHANGE:
                left, right = BorderSubPattern.paired_borders(orig_borders)
                return f"{left}{missing_arg.group(1)}{right}"
            case MissingArgsTreatment.REMOVE:
                return ""
            case MissingArgsTreatment.ELLIPSIS:
                return "..."
            case MissingArgsTreatment.ERROR:
                msg = f"{missing_arg.group(1)} is not an argument of the {{}}"
                raise MATError(msg)
            case MissingArgsTreatment.DONT_LOG:
                return self.value[1]
            case _:
                msg = f"Unexpected value of {type(self).__name__}"
                raise TypeError(msg)
