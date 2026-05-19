from functools import wraps
from types import FunctionType
from typing import TYPE_CHECKING, Self, overload

from src import loguru_logger

from .formatter import DocsFormatter
from .logger_config import DocsLoggerConfig

if TYPE_CHECKING:
    from collections.abc import Callable

    from .fcallable import FCallable


class docs_logger[**PS, R, NC]:  # noqa: N801
    type DO = FCallable[PS, R] | type[NC]

    def __new__[**NPS](
        cls,
        decorated_obj: Self | DO | None = None,
        *,
        docs_logger_config: DocsLoggerConfig | None = None,  # ruff: ignore[ARG004]
    ) -> Self:
        if isinstance(decorated_obj, docs_logger):
            return decorated_obj
        return super().__new__(cls)

    def __init__(
        self,
        decorated_obj: Self | DO | None = None,
        *,
        docs_logger_config: DocsLoggerConfig | None = None,
    ) -> None:
        if isinstance(decorated_obj, docs_logger):
            return

        self._config = docs_logger_config or DocsLoggerConfig()
        if decorated_obj:
            self.decorated_obj = self.__call__(decorated_obj)

    @overload
    def __call__(self, obj: type[NC], /) -> type[NC]: ...

    @overload
    def __call__(self, obj: FCallable[PS, R], /) -> FCallable[PS, R]: ...

    @overload
    def __call__(self, obj: Self, /) -> DO: ...

    @overload
    def __call__(self, *args: PS.args, **kwargs: PS.kwargs) -> R: ...

    def __call__(self, *args, **kwargs):
        if not getattr(self, "decorated_obj", None):
            if not args:
                msg = f"Empty call of {type(self).__name__}"
                raise AttributeError(msg)

            obj = args[0]

            if isinstance(obj, (FunctionType, type)):
                self.decorated_obj = self.decorate(obj)
                return self.decorated_obj

            if isinstance(obj, docs_logger):
                return obj.decorated_obj

            msg = "Decorated object is not callable or a class"
            raise TypeError(msg)

        return self.decorated_obj(*args, **kwargs)

    def decorate(self, decorated_obj: DO) -> type[NC] | Callable[PS, R]:
        if isinstance(decorated_obj, type):
            return self._decorate_type(decorated_obj)

        if self._validate_function(decorated_obj.__name__):
            return self._decorate_function(decorated_obj)

        msg = "Decorated object is not a functon or a class"
        raise AttributeError(msg)

    def _validate_function(self, name: str) -> bool:
        return name not in self._config.ignore

    def _decorate_type(self, type_: type[NC]) -> type[NC]:
        for attr_name, attr_obj in vars(type_).items():
            is_valid_function = isinstance(
                attr_obj, FunctionType
            ) and self._validate_function(attr_name)

            if is_valid_function:
                decorated_function = self._decorate_function(
                    attr_obj, attr_name
                )
                setattr(type_, attr_name, decorated_function)

        if self._config.docs_loggerize_subclasses:

            @classmethod
            def __init_subclass__(cls, **kwargs) -> None:  # noqa: ANN001, ANN003, N807
                super(type_, cls).__init_subclass__(**kwargs)
                docs_logger(cls, docs_logger_config=self._config)

            type_.__init_subclass__: Callable = __init_subclass__

        return type_

    def _decorate_function(
        self, call: FCallable[PS, R], potentional_name: str | None = None
    ) -> Callable[PS, R]:
        if getattr(call, "__docs_logger_decorated__", False):
            return call
        setattr(call, "__docs_logger_decorated__", True)  # noqa: B010
        docs_formatter = DocsFormatter(call, self._config, potentional_name)
        patched_logger = loguru_logger.patch(
            docs_formatter.format_args.patcher_for_loguru
        )
        level = self._config.logger_level
        dont_log = not docs_formatter.msg or docs_formatter.mat_dont_log()

        if dont_log:
            return call

        @wraps(call)
        def wrapper(*args: PS.args, **kwargs: PS.kwargs) -> R:
            msg = docs_formatter.format_msg_from_args(*args, **kwargs)
            patched_logger.log(level, msg)
            return call(*args, **kwargs)

        catcher = (
            loguru_logger.catch() if self._config.logger_catch else lambda x: x
        )
        return catcher(wrapper)
