from functools import partial
from typing import Callable, List

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_validator,
    validate_call,
    TypeAdapter,
)
from pydantic_core import PydanticCustomError 


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Condition = Callable[[int], bool]
IntList = List[int]
IntListAdapter = TypeAdapter(IntList)


# ---------------------------------------------------------------------------
# Validated input model
# ---------------------------------------------------------------------------
class SumInput(BaseModel):
    integers: IntList = Field(
        ...,
        min_length=1,
        description="The list of integers to filter and sum.",
        examples=[[1, 2, 3, 4]],
    )
    condition: Condition = Field(
        default=lambda n: "2" not in str(n),
        description="Predicate deciding which integers get summed.",
    )

    @field_validator("integers")
    @classmethod
    def no_duplicates(cls, v: IntList) -> IntList:
        if len(v) != len(set(v)):
            # ValueError → Pydantic wraps it in ValidationError
            raise ValueError("duplicates not allowed")
        return v

    @field_validator("condition")
    @classmethod
    def condition_returns_bool(cls, v: Condition) -> Condition:
        try:
            result = v(1)
        except Exception as e:
            # ValueError → wrapped
            raise ValueError(f"condition raised on probe input: {e}") from e
        if not isinstance(result, bool):
            # PydanticCustomError → wrapped, and gives us a stable `type=` code
            raise PydanticCustomError(
                "condition_not_bool",
                "condition must return bool, got {got}",
                {"got": type(result).__name__},
            )
        return v


# ---------------------------------------------------------------------------
# SumClass
# ---------------------------------------------------------------------------
class SumClass:

    @validate_call
    def sumOfNumbers1(self, integers: IntList) -> int:
        numberSum: int = 0
        for integer in integers:
            if "2" not in str(integer):
                numberSum = numberSum + integer
        return numberSum

    @validate_call
    def sumOfNumbers1b(self, integers: IntList, condition: Condition) -> int:
        numberSum: int = 0
        for integer in integers:
            if condition(integer):
                numberSum = numberSum + integer
        return numberSum

    @validate_call
    def sumOfNumbers2(self, integers: IntList) -> int:
        return [sum(integer for integer in integers if "2" not in str(integer))][0]

    @validate_call
    def sumOfNumbers2b(self, integers: IntList, condition: Condition) -> int:
        return sum(integer for integer in integers if condition(integer))

    @validate_call
    def sumOfNumbers3(self, integers: IntList) -> int:
        return [sum(integer for integer in integers if integer != 2)][0]

    @validate_call
    def sumOfNumbers4(self, integers: IntList) -> int:
        return sum(integer for integer in integers if integer != 2)
 
    sumOfNumbers5: Callable[[IntList, Condition], int] = staticmethod(
        validate_call(
            lambda integers: sum(integer for integer in integers if integer != 2)
        )
    ) 

    sumOfNumbers6 = staticmethod(
        lambda integers, condition: sum(
            n for n in IntListAdapter.validate_python(integers)
            if condition(n)
        )
    )


# ---------------------------------------------------------------------------
# Error-display helper — aggregates every validation error
# ---------------------------------------------------------------------------
def show_errors(label: str, exc: ValidationError) -> None:
    errs = exc.errors(include_url=False)
    print(f"rejected ({label}): {len(errs)} error(s)")
    for err in errs:
        loc = ".".join(str(p) for p in err["loc"]) or "<root>"
        print(f"  - [{err['type']}] {loc}: {err['msg']}")


# ---------------------------------------------------------------------------
# Runtime data
# ---------------------------------------------------------------------------
sumObj = SumClass()

integers: IntList = [1, 2, 3, 4]

sumExcludingTwo: Condition = lambda integer: integer != 2
sumExcludingTwoB: Condition = lambda integer: "2" not in str(integer)

sumExcludingFactory: Callable[[int], Condition] = (
    lambda integerToExclude: (lambda integer: integer != integerToExclude)
)

sumExcludingPredicate: Callable[[int, int], bool] = (
    lambda integer, integerToExclude: integer != integerToExclude
)
sumIncludingPredicate: Callable[[int, int], bool] = (
    lambda integer, integerToExclude: integer == integerToExclude
)

onlyEvens: Condition = lambda integer: integer % 2 == 0
onlyOdds: Condition = lambda integer: integer % 2 == 1

# partial pre-binds integerToExclude=2 by keyword (positional would bind `integer`)
sumExcludingPredicateWithCondition: Condition = partial(
    sumExcludingPredicate, integerToExclude=2
)
sumIncludingPredicateWithCondition: Condition = partial(
    sumIncludingPredicate, integerToExclude=2
)


# ---------------------------------------------------------------------------
# Validate shared input once, up front
# ---------------------------------------------------------------------------
payload = SumInput(integers=integers, condition=sumExcludingTwo)
integers = payload.integers

# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # --- happy path ------------------------------------------------------
    print(sumObj.sumOfNumbers1(integers))                                     # 8
    print(sumObj.sumOfNumbers1b(integers, sumExcludingTwo))                   # 8
    print(sumObj.sumOfNumbers2(integers))                                     # 8
    print(sumObj.sumOfNumbers2b(integers, sumExcludingTwo))                   # 8
    print(sumObj.sumOfNumbers3(integers))                                     # 8
    print(sumObj.sumOfNumbers4(integers))                                     # 8
    print(sumObj.sumOfNumbers5(integers))                                     # 8
    print(sumObj.sumOfNumbers6(integers, sumExcludingTwo))                    # 8
    print(sumObj.sumOfNumbers6(integers, sumExcludingTwoB))                   # 8
    print(sumObj.sumOfNumbers6(integers, sumExcludingFactory(2)))             # 8
    print(sumObj.sumOfNumbers6(integers, sumExcludingPredicateWithCondition)) # 8

    print(sumObj.sumOfNumbers6(integers, sumIncludingPredicateWithCondition)) # 2

    print(sumObj.sumOfNumbers6(integers, onlyEvens))                          # 6
    print(sumObj.sumOfNumbers6(integers, onlyOdds))                           # 4

    # --- coercion --------------------------------------------------------
    print(SumInput(integers=["1", "2", "3"], condition=onlyEvens).integers)   # [1, 2, 3]

    # --- aggregated error demos ------------------------------------------
    print("\n--- validation errors (aggregated) ---")

    # 1. duplicates
    try:
        SumInput(integers=[1, 1, 2], condition=onlyEvens)
    except ValidationError as e:
        show_errors("duplicates", e)

    # 2. condition returns non-bool
    try:
        SumInput(integers=[1, 2, 3], condition=lambda n: n)  # returns int
    except ValidationError as e:
        show_errors("non-bool condition", e)

    # 3. both problems at once — Pydantic reports every error
    try:
        SumInput(integers=[1, 1, 2], condition=lambda n: n)
    except ValidationError as e:
        show_errors("duplicates + non-bool condition", e)

    # 4. @validate_call catches a bad list at the method boundary
    try:
        sumObj.sumOfNumbers6([1, 2, "three"], onlyEvens)  # type: ignore[list-item]
    except ValidationError as e:
        show_errors("validate_call bad list", e)

    # 5. empty list (min_length=1)
    try:
        SumInput(integers=[], condition=onlyEvens)
    except ValidationError as e:
        show_errors("empty list", e)