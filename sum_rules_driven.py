from functools import partial
from typing import Annotated, Callable, List, Literal, Optional, Union

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
# Rule classes (each is one menu item)
# ---------------------------------------------------------------------------
class ExcludeRule(BaseModel):
    kind: Literal["exclude"]
    value: int

    def to_condition(self) -> Condition:
        return lambda n: n != self.value


class IncludeRule(BaseModel):
    kind: Literal["include"]
    value: int

    def to_condition(self) -> Condition:
        return lambda n: n == self.value


class EvensRule(BaseModel):
    kind: Literal["evens"]

    def to_condition(self) -> Condition:
        return lambda n: n % 2 == 0


class OddsRule(BaseModel):
    kind: Literal["odds"]

    def to_condition(self) -> Condition:
        return lambda n: n % 2 == 1


class GreaterThanRule(BaseModel):
    kind: Literal["greater_than"]
    threshold: int

    def to_condition(self) -> Condition:
        return lambda n: n > self.threshold


class LessThanRule(BaseModel):
    kind: Literal["less_than"]
    threshold: int

    def to_condition(self) -> Condition:
        return lambda n: n < self.threshold


class DivisibleByRule(BaseModel):
    kind: Literal["divisible_by"]
    divisor: int

    def to_condition(self) -> Condition:
        return lambda n: n % self.divisor == 0


class InSetRule(BaseModel):
    kind: Literal["in_set"]
    values: List[int]

    def to_condition(self) -> Condition:
        return lambda n: n in self.values


# ---------------------------------------------------------------------------
# Discriminated union — routes on `kind`
# ---------------------------------------------------------------------------
AnyRule = Annotated[
    Union[
        ExcludeRule,
        IncludeRule,
        EvensRule,
        OddsRule,
        GreaterThanRule,
        LessThanRule,
        DivisibleByRule,
        InSetRule,
    ],
    Field(discriminator="kind"),
]

RuleAdapter = TypeAdapter(AnyRule)


# ---------------------------------------------------------------------------
# Container model
#   - `rule` is the primary, optional input (defaults to "evens")
#   - `condition` is an optional live callable (overrides `rule` if given)
#   - `resolve_condition()` returns whichever is active
# ---------------------------------------------------------------------------
class SumInput(BaseModel):
    integers: IntList = Field(
        ...,
        min_length=1,
        description="The list of integers to filter and sum.",
        examples=[[1, 2, 3, 4]],
    )
    rule: Optional[AnyRule] = Field(
        default=None,
        description="A rule as data (kind + fields). Optional.",
    )
    condition: Optional[Condition] = Field(
        default=None,
        description="A live predicate. Overrides `rule` when provided.",
    )

    @field_validator("integers")
    @classmethod
    def no_duplicates(cls, v: IntList) -> IntList:
        if len(v) != len(set(v)):
            raise ValueError("duplicates not allowed")
        return v

    @field_validator("condition")
    @classmethod
    def condition_returns_bool(cls, v: Optional[Condition]) -> Optional[Condition]:
        if v is None:
            return v
        try:
            result = v(1)
        except Exception as e:
            raise ValueError(f"condition raised on probe input: {e}") from e
        if not isinstance(result, bool):
            raise PydanticCustomError(
                "condition_not_bool",
                "condition must return bool, got {got}",
                {"got": type(result).__name__},
            )
        return v

    def resolve_condition(self) -> Condition:
        """Return the effective predicate, from `condition` or `rule`."""
        if self.condition is not None:
            return self.condition
        if self.rule is not None:
            return self.rule.to_condition()
        # fallback default
        return lambda n: n % 2 == 0   # evens


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

    # fixed annotation: only one arg
    sumOfNumbers5: Callable[[IntList], int] = staticmethod(
        validate_call(
            lambda integers: sum(integer for integer in integers if integer != 2)
        )
    )

    # keep the adapter-based version, but it's fine
    sumOfNumbers6 = staticmethod(
        lambda integers, condition: sum(
            n for n in IntListAdapter.validate_python(integers)
            if condition(n)
        )
    )

    @validate_call
    def sumOfNumbers6b(self, integers: IntList, condition: Condition) -> int:
        return sum(n for n in integers if condition(n))


# ---------------------------------------------------------------------------
# Error-display helper
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

sumExcludingPredicateWithCondition: Condition = partial(
    sumExcludingPredicate, integerToExclude=2
)
sumIncludingPredicateWithCondition: Condition = partial(
    sumIncludingPredicate, integerToExclude=2
)


# ---------------------------------------------------------------------------
# Validate shared input once, up front
#   - now works because `rule` is optional
# ---------------------------------------------------------------------------
payload = SumInput(integers=integers, condition=sumExcludingTwo)
integers = payload.integers


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    sumObj = SumClass()
    integers = [1, 2, 3, 4, 5, 6]

    # --- rule-driven examples ---
    examples = [
        {"kind": "exclude", "value": 2},
        {"kind": "include", "value": 2},
        {"kind": "evens"},
        {"kind": "odds"},
        {"kind": "greater_than", "threshold": 3},
        {"kind": "less_than", "threshold": 3},
        {"kind": "divisible_by", "divisor": 3},
        {"kind": "in_set", "values": [1, 4, 5]},
    ]

    for raw in examples:
        rule = RuleAdapter.validate_python(raw)
        cond = rule.to_condition()
        total = sumObj.sumOfNumbers6(integers, cond)
        print(f"{type(rule).__name__:20s} {raw!s:45s} → {total}")

    # --- happy path ---
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

    # --- coercion ---
    print(SumInput(integers=["1", "2", "3"], condition=onlyEvens).integers)   # [1, 2, 3]

    # --- aggregated error demos ---
    print("\n--- validation errors (aggregated) ---")

    try:
        SumInput(integers=[1, 1, 2], condition=onlyEvens)
    except ValidationError as e:
        show_errors("duplicates", e)

    try:
        SumInput(integers=[1, 2, 3], condition=lambda n: n)
    except ValidationError as e:
        show_errors("non-bool condition", e)

    try:
        SumInput(integers=[1, 1, 2], condition=lambda n: n)
    except ValidationError as e:
        show_errors("duplicates + non-bool condition", e)

    try:
        sumObj.sumOfNumbers6([1, 2, "three"], onlyEvens)
    except ValidationError as e:
        show_errors("validate_call bad list", e)

    try:
        SumInput(integers=[], condition=onlyEvens)
    except ValidationError as e:
        show_errors("empty list", e)


if __name__ == "__main__":
    main()