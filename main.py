# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "tqdm>=4.67.3",
# ]
# ///
from sys import exit
from collections import defaultdict
from datetime import date
from os import PathLike
from pathlib import Path
from time import sleep
from tkinter.filedialog import askdirectory
from typing import Callable, Iterable, NoReturn
from tqdm import tqdm

type FileName = str
type Days = dict[str, list[FileName]]
type Months = dict[str, Days]
type Years = dict[str, Months]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

class DateParser:
    input_dir: str | PathLike

    def __init__(self, 
                 input_dir: str | PathLike | None = None, 
                 output_dir: str | PathLike = r"output/",
                 exclude: Iterable[str | PathLike] = ()) -> None:
        self._input_dir = Path(input_dir) if input_dir is not None else Path.cwd()
        self._output_dir = Path(output_dir).absolute()
        self._exclude = {Path(p).name for p in exclude} | {self._output_dir}

    def parse(self) -> Path:
        self._date_tree = self._create_date_tree()
        return self._build_result_tree()

    def _create_date_tree(self) -> Years:
        days_dd_generator: Callable[[], Days] = lambda: defaultdict(list)
        months_dd_generator: Callable[[], Months] = lambda: defaultdict(days_dd_generator)
        result: Years = defaultdict(months_dd_generator)

        self.__list_iterdir = list(self._input_dir.iterdir())
        with tqdm(total=len(self.__list_iterdir), colour="#ff44ff", desc="Парсим парсим парсим^^", leave=False, ascii=True) as pbar:
            for file in self.__list_iterdir:
                if file.name in self._exclude: continue
                year, month, day, *_ = date.fromtimestamp(file.stat().st_birthtime).timetuple()
                year, month, day = str(year), MONTHS[month-1], str(day)
                result[year][month][day].append(file.as_posix())
                pbar.update()
                sleep(.05)
        
        return result

    def _build_result_tree(self) -> Path:
        with tqdm(total=len(self.__list_iterdir), colour="#ff44ff", desc="Копируем копируем^^", leave=False, ascii=True) as pbar:
            for year in self._date_tree:
                for month in self._date_tree[year]:
                    for day in self._date_tree[year][month]:
                        for file in self._date_tree[year][month][day]:
                            target_dir = self._output_dir / year / month / day
                            target_dir.mkdir(parents=True, exist_ok=True)  
                            Path(file).copy_into(target_dir, preserve_metadata=True)
                            pbar.update()
        return self._output_dir
    

def clear_input (s):
    return "".join(s.split()).lower()

def dir_get_and_check(msg: str, default: str | None = None) -> Path | NoReturn:
    while True:
        dir = input(msg) or default
        if clear_input(dir) == "gui()":
            dir = askdirectory(title="Введите путь до папки")
        if not dir: 
            msg = "Ты ничего не ввёл( ещё раз\n>"
            continue
        dir = Path(dir)

        if dir.exists() and not dir.is_dir():
            msg = "Это не папка( ещё раз\n>"
        else:
            break
    
    return dir

if __name__ == "__main__":     
    try:
        input_dir = dir_get_and_check('Введи путь до папки, из которой будем копировать\n(напиши "gui()" без кавычек, чтобы открыть окошко с вводом папки)\n> ')
        output_dir = dir_get_and_check('Введи путь до папки, в которую будете копировать (если она не существует, то она сама создастся)\n(по умолчанию "output")> ', "output")
        
        if output_dir.exists() and list(output_dir.iterdir()):
            if clear_input(input("Вы хотите, чтобы папки и файлы возможно перезаписалися?\n(y/n) > ")) == "n":
                print("Тогда сохраните её или используйте другую папку")
                sleep(5)
                exit()
        DateParser(input_dir, output_dir).parse()
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        print("Ошибка(((")
        print(e)
        sleep(5)
