from dataclasses import dataclass
from typing import Literal, TypeVar, cast

T = TypeVar("T")


@dataclass(frozen=True)
class ResultSuccess[T]:
    value: T
    success: Literal[True] = True
    message: str = "Ok"


@dataclass(frozen=True)
class ResultError[T]:
    message: str
    success: Literal[False] = False


Result = ResultSuccess[T] | ResultError[T]


class Res:
    @staticmethod
    def ok(value: T, message: str = "Ok") -> Result[T]:
        return ResultSuccess(value=value, message=message)

    @staticmethod
    def err(message: str) -> Result[T]:
        return cast(Result[T], ResultError(message=message))
