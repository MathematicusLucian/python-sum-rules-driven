from functools import partial
from typing import Callable, List

from pydantic import BaseModel, Field, field_validator, validate_call


# ---------------------------------------------------------------------------
# Type aliases (make the signatures read nicer)
# ---------------------------------------------------------------------------
Condition = Callable[[int], bool]
IntList = List[int]


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
            raise ValueError("duplicates not allowed")
        return v

    @field_validator("condition")
    @classmethod
    def condition_returns_bool(cls, v: Condition) -> Condition:
        # Pydantic already guarantees callable; this checks it behaves as a predicate.
        try:
            result = v(1)
        except Exception as e:
            raise ValueError(f"condition raised on probe input: {e}") from e
        if not isinstance(result, bool):
            raise TypeError(f"condition must return bool, got {type(result).__name__}")
        return v


# ---------------------------------------------------------------------------
# SumClass — every method type-annotated, entry points validated
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

    # Lambdas as class attributes — annotate the variable, not the lambda.
    sumOfNumbers5: Callable[[IntList], int] = (
        lambda integers: sum(integer for integer in integers if integer != 2)
    )

    sumOfNumbers6: Callable[[IntList, Condition], int] = (
        lambda integers, condition: sum(
            integer for integer in integers if condition(integer)
        )
    )


# ---------------------------------------------------------------------------
# Runtime data
# ---------------------------------------------------------------------------
sumObj = SumClass()

integers: IntList = [1, 2, 3, 4]

# --- named condition callables (kept as plain typed variables) ------------
sumExcludingTwo: Condition = lambda integer: integer != 2
sumExcludingTwoB: Condition = lambda integer: "2" not in str(integer)

# factory returning a Condition
sumExcluding: Callable[[int], Condition] = (
    lambda integerToExclude: (lambda integer: integer != integerToExclude)
)

# two-arg predicates (candidates for partial)
sumExcludingFactory: Callable[[int, int], bool] = (
    lambda integer, integerToExclude: integer != integerToExclude
)
sumIncludingFactory: Callable[[int, int], bool] = (
    lambda integer, integerToExclude: integer == integerToExclude
)

onlyEvens: Condition = lambda integer: integer % 2 == 0
onlyOdds: Condition = lambda integer: integer % 2 == 1

# partial pre-binds the keyword integerToExclude=2.
# (Passing 2 positionally would bind it to `integer` instead — symmetric here,
#  but a trap for asymmetric predicates like `>`.)
sumExcludingCondition: Condition = partial(sumExcludingFactory, integerToExclude=2)
sumIncludingCondition: Condition = partial(sumIncludingFactory, integerToExclude=2)


# ---------------------------------------------------------------------------
# Validate the shared input once, up front
# ---------------------------------------------------------------------------
payload = SumInput(integers=integers, condition=sumExcludingTwo)
integers = payload.integers   # coerced + validated
# (payload.condition is validated too, but we still pass different conditions below.)


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------
print(sumObj.sumOfNumbers1(integers))                           # 8
print(sumObj.sumOfNumbers1b(integers, sumExcludingTwo))         # 8
print(sumObj.sumOfNumbers2(integers))                           # 8
print(sumObj.sumOfNumbers2b(integers, sumExcludingTwo))         # 8
print(sumObj.sumOfNumbers3(integers))                           # 8
print(sumObj.sumOfNumbers4(integers))                           # 8
print(sumObj.sumOfNumbers5(integers))                           # 8
print(sumObj.sumOfNumbers6(integers, sumExcludingTwo))          # 8
print(sumObj.sumOfNumbers6(integers, sumExcludingTwoB))         # 8
print(sumObj.sumOfNumbers6(integers, sumExcluding(2)))          # 8
print(sumObj.sumOfNumbers6(integers, sumExcludingCondition))    # 8

print(sumObj.sumOfNumbers6(integers, sumIncludingCondition))    # 2

print(sumObj.sumOfNumbers6(integers, onlyEvens))                # 6
print(sumObj.sumOfNumbers6(integers, onlyOdds))                 # 4


# ---------------------------------------------------------------------------
# Optional: what Pydantic now catches for you
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Coercion: strings → ints
    print(SumInput(integers=["1", "2", "3"], condition=onlyEvens).integers)  # [1, 2, 3]

    # 2. Custom validator: duplicates
    try:
        SumInput(integers=[1, 1, 2], condition=onlyEvens)
    except Exception as e:
        print("rejected (duplicates):", e)

    # 3. Custom validator: condition must return bool
    try:
        SumInput(integers=[1, 2, 3], condition=lambda n: n)  # returns int, not bool
    except Exception as e:
        print("rejected (non-bool condition):", e)

    # 4. @validate_call catches a bad list at the method boundary
    try:
        sumObj.sumOfNumbers6([1, 2, "three"], onlyEvens)
    except Exception as e:
        print("validate_call rejected:", e)