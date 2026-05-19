import inspect
import re
from annotationlib import Format
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Self

from .borders_manipulator import BorderSubPattern
from .missing_args_treatment import MATError, MissingArgsTreatment

if TYPE_CHECKING:
    from collections.abc import Mapping

    from loguru import Record

    from .fcallable import FCallable
    from .logger_config import DocsLoggerConfig


@dataclass(slots=True, frozen=True)
class RecordFile:
    name: str
    path: str


@dataclass(slots=True, frozen=True)
class FormatArgs[**P, R]:
    func_obj: FCallable[P, R]
    function: str
    file: RecordFile
    line: int
    module: str
    name: str
    docs: str = ""

    @classmethod
    def from_function(
        cls: type[Self], func_obj: FCallable, name: str | None = None
    ) -> Self:
        function = name or func_obj.__name__

        module = inspect.getmodule(func_obj)
        module = func_obj.__module__ if module is None else module.__name__
        name = f"{module}::{func_obj.__qualname__.rpartition(".")[0]}"

        file_path = Path(inspect.getabsfile(func_obj))
        file = RecordFile(file_path.name, file_path.as_posix())

        line = inspect.getsourcelines(func_obj)[1]

        return cls(func_obj, function, file, line, module, name)

    def patcher_for_loguru(self, record: Record) -> None:
        record["function"] = self.function
        record["file"].name = self.file.name
        record["file"].path = self.file.path
        record["line"] = self.line
        record["module"] = self.module
        record["name"] = self.name


class DocsFormatter[**P, R]:
    def __init__(
        self,
        f: FCallable[P, R],
        config_: DocsLoggerConfig,
        name: str | None = None,
    ) -> None:
        self._f = f
        self._config = config_
        self._name = name or f.__name__

        self.sig = inspect.signature(f, annotation_format=Format.STRING)
        self.format_args = FormatArgs.from_function(f, name)

        self.braced_docs = self._braced_docs(f)
        self.msg = (
            config_.format_str
            if self.braced_docs
            else config_.docsless_format_str
        )

    def _braced_docs(self, f: FCallable) -> str:
        docs = inspect.getdoc(f)
        if docs is None:
            return ""
        bm = self._config.borders_manipulator
        docs_first_line = docs.splitlines()[0]
        return bm.sub_borders_in(docs_first_line)

    def format_msg_from_args(self, *args: P.args, **kwargs: P.kwargs) -> str:
        bound_args = self.sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        dict_doc_format_args = asdict(
            replace(self.format_args, docs=self._format_docs(bound_args))
        )

        return self.msg.format(**dict_doc_format_args)

    def mat_dont_log(self) -> bool:
        missing_marker = MissingArgsTreatment.DONT_LOG.value[1]
        return missing_marker in self._treat_missing_args_in_docs(
            dict.fromkeys(self.sig.parameters, "dummy")
        )

    def _format_docs(self, bound_args: inspect.BoundArguments) -> str:
        arguments = bound_args.arguments
        treated_docs = self._treat_missing_args_in_docs(arguments)
        return treated_docs.format(**arguments)

    def _treat_missing_args_in_docs(self, args: Mapping) -> str:
        def _missing_args_repl(match: re.Match) -> str:
            possible_endings = re.escape("[.:!")
            root_part_pattern = re.compile(rf"[^{possible_endings}]+")
            root_part = root_part_pattern.match(match.group(1))

            if root_part and root_part.group() in args:
                return match.group()

            mat = self._config.missing_args_treatment
            borders = self._config.borders
            return MissingArgsTreatment(mat).treat(match, borders)

        try:
            return BorderSubPattern(
                "MissingArguments", re.compile(r"{(.*?)}"), _missing_args_repl
            ).substitute(self.braced_docs)
        except MATError as e:
            new_msg = e.args[0].format(self._name)
            raise ValueError(new_msg) from MATError().with_traceback(
                e.__traceback__
            )
