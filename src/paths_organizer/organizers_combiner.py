from collections import UserList
from pathlib import Path
from typing import TYPE_CHECKING

from .paths_organizer import PathsOrganizer

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence


class Organizers(UserList[PathsOrganizer]):
    def __iter__(self) -> Iterator[PathsOrganizer]:
        for organizer in self.data:
            if isinstance(organizer, OrganizersCombiner):
                yield from organizer.organizers
            yield organizer

    def __len__(self) -> int:
        return len(tuple(iter(self)))


class OrganizersCombiner(PathsOrganizer):
    def __init__(
        self,
        input_dir: Path,
        output_dir: Path = Path("output/"),
        exclude: Sequence[str] = (),
        organizers: Sequence[PathsOrganizer] = (),
    ) -> None:
        super().__init__(input_dir, output_dir, exclude)
        self.organizers = Organizers(organizers)

    def generate_branch(self, path: Path) -> Sequence[str]:
        res = []
        for organizer in self.organizers:
            res.extend(organizer.generate_branch(path))
        return res
