import contextlib
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable
from os import PathLike
from pathlib import Path
from typing import Final

type Tree = dict[tuple[str, ...], list[Path]]
type StrPathLike = str | PathLike


class PathTreeParser[K: (str | Iterable[str])](ABC):
    """The abstract class for creating structured directory trees of paths."""

    ESCAPED_DELIMITER: Final[re.Pattern] = re.compile(
        r"\\(?P<delimiter>[\., \t])"
    )
    UNESCAPED_DELIMITER: Final[re.Pattern] = re.compile(
        r"(?<!\\)(?P<delimiter>[\., \t])"
    )

    def __init__(
        self,
        input_dir: StrPathLike,
        output_dir: StrPathLike = r"output/",
        exclude: Iterable[str] = (),
    ) -> None:
        """
        PathTreeParser constructor.

        Args:
            input_dir (StrPathLike): path to input directory
            output_dir (StrPathLike, optional): path for output directory. Defaults to r"output/".
            exclude (Iterable[StrPathLike], optional): excluding files and glob-patterns. Defaults to ().

        Raises:
            ValueError: when input_dir is not an existing directory

        """
        if not (input_dir := Path(input_dir)).is_dir():
            msg = "input_dir should be a path to dir"
            raise ValueError(msg)
        self._input_dir = input_dir
        self._output_dir = Path(output_dir).absolute()
        self._exclude = set(exclude) | {self._output_dir.as_posix()}

    @abstractmethod
    def generate_key(self, path: StrPathLike) -> K:
        """
        Abstract method for key generator of subclasses.

        Args:
            path (StrPathLike): path to file

        Returns:
            K: generated key

        """
        return NotImplemented

    def filter(self, path: Path) -> bool:
        """
        Check path in input directory.

        Args:
            path (Path): checking path

        Returns:
            bool: checking result

        """
        return all(not path.match(ex) for ex in self._exclude)

    def parse(self) -> Path:
        """
        Build a tree based on keys generator and filter.

        Returns:
            Path: path to output tree

        """
        self._date_tree = self._create_tree()
        return self._build_result_tree()

    def _create_tree(self) -> Tree:
        res = defaultdict(list)
        accepted_paths = {
            p for p in self._input_dir.iterdir() if self.filter(p)
        }
        for file in accepted_paths:
            key = self._uniform_key(self.generate_key(file))
            res[key].append(file)
        return dict(res)

    def _build_result_tree(self) -> Path:
        for branch, files in self._date_tree.items():
            target_dir = self._output_dir.joinpath(*branch)
            target_dir.mkdir(parents=True, exist_ok=True)

            for file in map(Path, files):
                if not target_dir.joinpath(file.name).exists():
                    with contextlib.suppress(Exception):
                        file.copy_into(target_dir, preserve_metadata=True)
        return self._output_dir

    @classmethod
    def _uniform_key(cls, key: str | Iterable[str]) -> tuple[str, ...]:
        if isinstance(key, str):
            key = (
                cls.ESCAPED_DELIMITER.sub(r"\g<delimiter>", k)
                for k in cls.UNESCAPED_DELIMITER.split(key)
                if k and cls.UNESCAPED_DELIMITER.fullmatch(k) is None
            )
        return tuple(key)
