import contextlib
import shutil
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from environs import env

from src import DocsLoggerConfig, docs_logger

if TYPE_CHECKING:
    from collections.abc import Sequence

type Tree = dict[tuple[str, ...], list[Path]]


class PathsOrganizer(ABC):
    def __init__(
        self,
        input_dir: Path,
        output_dir: Path = Path("output/"),
        exclude: Sequence[str] = (),
    ) -> None:
        if not input_dir.is_dir():
            msg = "input_dir should be a path to dir"
            raise ValueError(msg)

        self._input_dir = input_dir
        self._output_dir = output_dir
        self._exclude = set(exclude) | {self._output_dir.absolute().as_posix()}

    @abstractmethod
    def generate_branch(self, path: Path) -> Sequence[str]:
        raise NotImplementedError

    def filter(self, path: Path) -> bool:
        return all(not path.match(ex) for ex in self._exclude)

    def parse(self) -> Path:
        self._date_tree = self._create_tree()
        return self._build_result_tree()

    def _create_tree(self) -> Tree:
        res = defaultdict(list)
        accepted_paths = filter(self.filter, self._input_dir.iterdir())
        for file in accepted_paths:
            key = self.generate_branch(file)
            res[key].append(file)
        return res

    def _build_result_tree(self) -> Path:
        for branch, files in self._date_tree.items():
            if not files:
                continue

            builded_branch = self._build_branch(branch, files)

            branch_is_empty = not tuple(builded_branch.iterdir())
            if branch_is_empty:
                self._trim(builded_branch)

        return self._output_dir

    @staticmethod
    def _trim(branch: Path) -> None:
        while len(tuple(branch.parent.iterdir())) <= 1:
            branch = branch.parent

        shutil.rmtree(branch)

    def _build_branch(
        self, branch: tuple[str, ...], files: list[Path]
    ) -> Path:
        target_dir = self._output_dir / Path(*branch)
        target_dir.mkdir(parents=True, exist_ok=True)

        for file in map(Path, files):
            if not target_dir.joinpath(file.name).exists():
                with contextlib.suppress(Exception):
                    file.copy_into(target_dir, preserve_metadata=True)
        return target_dir


env.read_env()
if env.bool("DEBUG", False):
    docs_logger_config = DocsLoggerConfig(docs_loggerize_subclasses=True)
    PathsOrganizer = docs_logger(docs_logger_config=docs_logger_config)(
        PathsOrganizer
    )
