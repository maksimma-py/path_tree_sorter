import sys
from getpass import getpass
from mimetypes import guess_file_type
from pathlib import Path
from tkinter.filedialog import askdirectory
from typing import TYPE_CHECKING, Final

from parser import PathTreeParser

if TYPE_CHECKING:
    from collections.abc import Iterable
    from os import PathLike

type PathType = tuple[str, ...] | str


class FileTypeMap:
    """Map for path keys and file type values with path formatting."""

    def __init__(self) -> None:
        """Initialize an object."""
        self._dict = {}

    def set_format_return(self, path: Path, value: str | PathType) -> PathType:
        """
        Act like function wrapper for __setitem__ with formatting input.

        Args:
            path (Path): input formatting path key
            value (str | PathType): input value for self[path]

        Returns:
            PathType: formatted path

        """
        if isinstance(value, str):
            value = (value,)
        self[path] = value
        return value

    def get(self, path: Path) -> PathType | None:
        """
        Act like function wrapper for __getitem__.

        Args:
            path (Path): input path

        Returns:
            PathType | None: value of self[path]

        """
        return self[path]

    def __getitem__(self, path: Path) -> PathType | None:
        return self._dict.get(path.absolute().as_posix())

    def __setitem__(self, path: Path, value: str | PathType) -> None:
        if isinstance(value, str):
            value = tuple(value.split())
        self._dict[path.absolute().as_posix()] = value

    def __contains__(self, path: Path) -> bool:
        return path.absolute().as_posix() in self._dict


class PathTypeSizeParser(PathTreeParser):
    """Subclass of PathTreeParser."""

    FILE_SIZE_CLASSES: Final = {
        r"tiny": 1_000,
        r"very small": 10_000,
        r"small": 100_000,
        r"moderate": 1_000_000,
        r"medium": 10_000_000,
        r"large": 100_000_000,
        r"very large": 1_000_000_000,
        r"huge": 10_000_000_000,
        r"massive": float("inf"),
    }

    METHOD_2_TYPE: Final = {
        "is_dir": "directory",
        "is_mount": "mount",
        "is_block_device": "block device",
        "is_char_device": "character device",
        "is_fifo": "fifo",
        "is_socket": "socket",
    }

    def __init__(
        self,
        input_dir: str | PathLike,
        output_dir: str | PathLike = r"output/",
        exclude: Iterable[str] = (),
    ) -> None:
        """
        Initialize an object of this class.

        Args:
            input_dir (str | PathLike): input directory
            output_dir (str | PathLike, optional): output directory. Defaults to r"output/".
            exclude (Iterable[str | PathLike], optional): excluded paths and glob-patterns. Defaults to ().

        """
        super().__init__(input_dir, output_dir, exclude)
        self._memo: FileTypeMap = FileTypeMap()

    def generate_key(self, path: str | PathLike) -> tuple[str, ...]:
        """
        Generate a tuple of strings for the tree branch with path type and subjective size.

        Args:
            path (str | PathLike): input path

        Returns:
            tuple[str]: output string's tuple

        """
        path = Path(path)
        file_type = self.get_path_type(path)
        size = self.get_path_subjective_size(path)
        return *file_type, size

    def get_path_type(self, path: Path) -> PathType:
        """
        Choice closest.

        Args:
            path (Path): _description_

        Returns:
            PathType: _description_

        """
        attempts = [
            self._memo.get,
            self._try_get_symlink,
            self._try_get_file,
            self._try_get_other,
        ]
        for attempt in attempts:
            if (res := attempt(path)) is not None:
                return self._memo.set_format_return(path, res)
        return ("unknown",)

    @staticmethod
    def _try_get_file(path: Path) -> PathType | None:
        if not path.is_file():
            return None

        if path.suffix.endswith(".lnk"):
            return "windows link"

        if (guess := guess_file_type(path)[0]) is not None:
            return tuple(guess.split("/"))

        return "unknown file"

    def _try_get_symlink(self, path: Path) -> PathType | None:
        if not path.is_symlink():
            return None

        self._memo[path] = "link"
        src_type = self.get_path_type(path.readlink())

        if src_type == ("link",):
            return self._memo.set_format_return(path, "recursive link")

        is_not_link = src_type and src_type[0] != "link"
        if is_not_link:
            src_type = ("link", *src_type)
        return src_type

    def _try_get_other(self, path: Path) -> PathType | None:
        for method, type_ in self.METHOD_2_TYPE.items():
            if hasattr(path, method) and getattr(path, method)():
                return type_
        return None

    def get_path_subjective_size(self, path: Path) -> str:
        """
        Rate a path size based on self.FILE_SIZE_CLASSES.

        Args:
            path (Path): file which size is rating

        Returns:
            str: size rate

        """
        size = (
            self._get_dir_size(path) if path.is_dir() else path.stat().st_size
        )
        for subjective_size, v in self.FILE_SIZE_CLASSES.items():
            if size <= v:
                return subjective_size
        return "unknown"

    def _get_dir_size(self, path: Path) -> int:
        return sum(
            sp.stat().st_size if sp.is_file() else self._get_dir_size(sp)
            for sp in path.iterdir()
        )


# ruff: disable[T201]
if __name__ == "__main__":
    try:
        print("Укажи папку из которой будем копировать файлы в дерево")
        input_dir = askdirectory(mustexist=True)
        print("Укажи папку в которую будем копировать")
        output_dir = askdirectory()
        print("Выполняем...")
        result_dir = PathTypeSizeParser(input_dir, output_dir).parse()
        print(f"Готово! Дерево было сохранено в {result_dir}")
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:  # noqa: BLE001
        print(f"Произошла ошибка!\n{e}")
    finally:
        getpass("Нажми Enter для выхода")
# ruff: enable[T201]
