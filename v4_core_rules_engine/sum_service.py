# Domain service for integer filtering and summation.
#
# Composition:
#   - Depends on RuleEngine[int], injected via the constructor.
#   - Owns the int rule catalogue (ExcludeRule, EvensRule, ...).
#   - Owns the SumInput container (validation + precedence resolution).
#
# Does NOT know about the matcher service, and does not import it.

from __future__ import annotations

from functools import partial
import operator
from turtle import numinput
from typing import Annotated, Callable, List, Literal, Optional, Union

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    TypeAdapter,
    field_validator,
    validate_call,
)
from pydantic_core import PydanticCustomError

from core_rules_engine import Predicate, Rule, RuleEngine, show_errors

# ---------------------------------------------------------------------------
# Factories and predicates
# ---------------------------------------------------------------------------
onlyEvens: Condition = lambda integer: integer % 2 == 0
onlyOdds: Condition = lambda integer: integer % 2 == 1

sumExcluding: Callable[[int], Condition] = (
    lambda integerToExclude: (lambda integer: integer != integerToExclude)
)

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
# Validate shared input once, up front
# ---------------------------------------------------------------------------
# payload = numinput(integers=integers, condition=sumExcludingTwo)
# payload = SumInput(integers=integers, rule=IntRuleAdapter.validate_python({"kind": "evens"}))
# integers = payload.integers   # coerced + validated

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Condition = Predicate[int]
IntList = List[int]

# ---------------------------------------------------------------------------
# A condition described as data (JSON-friendly) rather than a live function
# ---------------------------------------------------------------------------
class ByName(BaseModel):
    kind: Literal["exclude", "include", "evens", "odds"]
    value: int = 2

    def to_condition(self) -> Condition:
        match self.kind:
            case "exclude": return lambda n: n != self.value
            case "include": return lambda n: n == self.value
            case "evens":   return lambda n: n % 2 == 0
            case "odds":    return lambda n: n % 2 == 1

# ---------------------------------------------------------------------------
# Int rule catalogue
# ---------------------------------------------------------------------------
class ExcludeRule(Rule):
    kind: Literal["exclude"]
    value: int

    def to_predicate(self) -> Condition:
        return lambda n: n != self.value


class IncludeRule(Rule):
    kind: Literal["include"]
    value: int

    def to_predicate(self) -> Condition:
        return lambda n: n == self.value


class EvensRule(Rule):
    kind: Literal["evens"]

    def to_predicate(self) -> Condition:
        return lambda n: n % 2 == 0


class OddsRule(Rule):
    kind: Literal["odds"]

    def to_predicate(self) -> Condition:
        return lambda n: n % 2 == 1


class GreaterThanRule(Rule):
    kind: Literal["greater_than"]
    threshold: int

    def to_predicate(self) -> Condition:
        return lambda n: n > self.threshold


class LessThanRule(Rule):
    kind: Literal["less_than"]
    threshold: int

    def to_predicate(self) -> Condition:
        return lambda n: n < self.threshold


class DivisibleByRule(Rule):
    kind: Literal["divisible_by"]
    divisor: int

    def to_predicate(self) -> Condition:
        return lambda n: n % self.divisor == 0


class IntInSetRule(Rule):
    kind: Literal["int_in_set"]
    values: List[int]

    def to_predicate(self) -> Condition:
        return lambda n: n in self.values


# ---------------------------------------------------------------------------
# Discriminated union — routes on `kind`
# ---------------------------------------------------------------------------
IntRule = Annotated[
    Union[
        ExcludeRule,
        IncludeRule,
        EvensRule,
        OddsRule,
        GreaterThanRule,
        LessThanRule,
        DivisibleByRule,
        IntInSetRule,
    ],
    Field(discriminator="kind"),
]

IntRuleAdapter = TypeAdapter(IntRule)


# ---------------------------------------------------------------------------
# Container model
#
# Precedence for the active predicate:
#     condition > rule > default (evens)
# ---------------------------------------------------------------------------
class SumInput(BaseModel):
    integers: IntList = Field(
        ...,
        min_length=1,
        description="The list of integers to filter and sum.",
        examples=[[1, 2, 3, 4]],
    )
    rule: Optional[IntRule] = Field(
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
        if self.condition is not None:
            return self.condition
        if self.rule is not None:
            return self.rule.to_predicate()
        return lambda n: n % 2 == 0   # default: evens


# ---------------------------------------------------------------------------
# SumService (DI: RuleEngine[int] is injected)
# ---------------------------------------------------------------------------
class SumService:

    def __init__(self, engine: RuleEngine[int]) -> None:
        self._engine = engine

    @validate_call
    def sum_by_condition(self, integers: IntList, condition: Condition) -> int:
        return self._engine.reduce(integers, condition, operator.add, 0)

    @validate_call
    def sum_by_rule(self, integers: IntList, rule: IntRule) -> int:
        return self.sum_by_condition(integers, rule.to_predicate())

    @validate_call
    def sum_from_input(self, payload: SumInput) -> int:
        return self.sum_by_condition(payload.integers, payload.resolve_condition())