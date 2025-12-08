from abc import ABC, abstractmethod
from functools import wraps
import inspect
from inspect import isabstract, Parameter, Signature
from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules
import re
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Generic, Iterable, List, TypeVar

C = TypeVar("C", bound="ChallengeWrapper")
T = TypeVar("T")


class Example(Generic[T]):
    def __init__(self, input_str: str, result: T, skip: bool = False, **kwargs):
        self.input_str: str = input_str
        self.result: T = result
        self.skip: bool = skip
        self.kwargs: dict[str, Any] = kwargs


class Challenge(Generic[T]):
    def __init__(self, day: int, part: int, func: Callable[[Path], T], examples: Iterable[Example[T]] = ()):
        self.day: int = day
        self.part: int = part
        self.func: Callable[[Path], T] = func
        self.examples: list[Example[T]] = list(examples)
        self.__name__ = func.__name__

    def __call__(self, *args, **kwargs) -> T:
        return self.func(*args, **kwargs)

    def validate(self, example: Example):
        tmpfile = NamedTemporaryFile("w", delete=False)
        try:
            tmpfile.write(example.input_str)
            tmpfile.close()
            result = self.func(Path(tmpfile.name), **example.kwargs)
            if result != example.result:
                raise ValueError(f"Day {self.day} Part {self.part} {self.func.__name__}: example "
                                 f"expected {example.result!r} but got {result!r}")
        finally:
            Path(tmpfile.name).unlink()

    def validate_examples(self):
        for e in self.examples:
            if not e.skip:
                self.validate(e)

    def __str__(self):
        return self.__name__


CHALLENGES: dict[int, dict[int, Challenge[Any]]] = {}


class ChallengeWrapper(ABC):
    wrappers: list[type["ChallengeWrapper"]]

    def __init__(self, func: Callable[..., Any], signature: Signature):
        self.func: Callable[..., Any] = func
        self.signature: Signature = signature

    def __init_subclass__(cls, **kwargs):
        if isabstract(cls):
            return
        if not hasattr(ChallengeWrapper, "wrappers"):
            setattr(ChallengeWrapper, "wrappers", [])
        elif ChallengeWrapper.wrappers is None:
            ChallengeWrapper.wrappers = []
        ChallengeWrapper.wrappers.append(cls)

    @abstractmethod
    def __call__(self, *args, **kwargs) -> Callable[[Path], Any]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def wrap(cls: type[C], func: Callable[..., Any], signature: Signature) -> C | None:
        raise NotImplementedError


class SingleParamChallengeWrapper(Generic[T], ChallengeWrapper, ABC):
    def __init__(self, func: Callable[[T], Any], signature: Signature, param: Parameter):
        super().__init__(func=func, signature=signature)
        self.param = param

    def __call__(self, *args, **kwargs) -> Callable[[Path], Any]:
        @wraps(self.func)
        def wrapper(path: Path, **kwargs2) -> Any:
            return self.func(self.convert(path), **kwargs2)

        return wrapper

    @abstractmethod
    def convert(self, path: Path) -> T:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def validate(cls, param: Parameter) -> bool:
        raise NotImplementedError()

    @classmethod
    def wrap(cls: type[C], func: Callable[..., Any], signature: Signature) -> C | None:
        required_args = [
            param
            for param in signature.parameters.values()
            if param.default is inspect.Parameter.empty
        ]
        if len(required_args) != 1:
            return None
        param = required_args[0]
        if cls.validate(param):
            return cls(func=func, signature=signature, param=param)
        else:
            return None


class PathWrapper(SingleParamChallengeWrapper[str | Path]):
    @classmethod
    def validate(cls, param: Parameter) -> bool:
        return param.name == "path" or param.annotation is Path or (param.annotation is str and param.name != "data")

    def convert(self, path: Path) -> str | Path:
        if self.param.annotation is str:
            return str(path)
        else:
            return path


class LinesWrapper(SingleParamChallengeWrapper[list[str]]):
    def convert(self, path: Path) -> list[str]:
        with open(path, "r") as f:
            return f.readlines()

    @classmethod
    def validate(cls, param: Parameter) -> bool:
        return param.name == "lines" or param.annotation is List or param.annotation is list \
            or param.annotation == [str]


class DataWrapper(SingleParamChallengeWrapper[str]):
    def convert(self, path: Path) -> str:
        with open(path, "r") as f:
            return f.read()

    @classmethod
    def validate(cls, param: Parameter) -> bool:
        return param.name == "data" and (param.annotation is None or param.annotation is str)


def challenge(day: int, part: int | None = None):
    if day in CHALLENGES:
        existing_day = CHALLENGES[day]
    else:
        existing_day = {}
        CHALLENGES[day] = existing_day
    if part is None:
        part = len(existing_day)
    elif part in existing_day:
        raise ValueError(f"Day {day} part {part} is already assigned to {existing_day[part].__name__}")

    def wrapper(func: Callable[[Any], T]) -> Challenge[T]:
        sig = inspect.signature(func)
        for w in ChallengeWrapper.wrappers:
            wrapped = w.wrap(func=func, signature=sig)
            if wrapped is not None:
                c = Challenge(day=day, part=part, func=wrapped())
                existing_day[part] = c
                return c
        raise TypeError(f"Unexpected parameter: {func!s}{sig!s}")

    return wrapper


def example(input_str: str, result: T, skip: bool = False, **kwargs) -> Callable[[Challenge[T]], Challenge[T]]:
    def wrapper(func: Challenge[T]) -> Challenge[T]:
        if not isinstance(func, Challenge):
            raise TypeError(f"@example can only be used on a Challenge"
                            f"or a function annotated with @challenge, not {func!r}")
        func.examples = [Example(input_str=input_str, result=result, skip=skip, **kwargs)] + func.examples
        return func

    return wrapper


def regex(
        pattern: re.Pattern | str
) -> Callable[[Callable[[list[re.Match | None]], T]], Callable[[list[str]], T]]:
    if isinstance(pattern, str):
        pattern = re.compile(pattern=pattern)

    def wrapper(func: Callable[[list[re.Match[str] | None]], T]) -> Callable[[list[str]], T]:
        def converter(lines: list[str]) -> T:
            return func([
                pattern.match(line)
                for line in lines
            ])

        return converter

    return wrapper


# Automatically load all modules in the `aoc2023` package
package_dir = Path(__file__).resolve().parent
for (_, module_name, _) in iter_modules([str(package_dir)]):  # type: ignore
    # import the module and iterate through its attributes
    if module_name != "__main__":
        module = import_module(f"{__name__}.{module_name}")
