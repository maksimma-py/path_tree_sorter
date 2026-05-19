from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import FunctionType

    from ty_extensions import Intersection

    type FCallable[**P, R] = Intersection[Callable[P, R], FunctionType]
