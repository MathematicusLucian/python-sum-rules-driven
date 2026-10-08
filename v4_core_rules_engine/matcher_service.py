# Domain service for string filtering and counting.
#
# Composition:
#   - Depends on RuleEngine[str], injected via the constructor.
#   - Owns the str rule catalogue (SubstringRule, StrInSetRule).
#   - Owns the SelectionInput container.
#
# Does NOT know about the sum service, and does not import it.

from __future__ import annotations

from typing import Annotated, Callable, Dict, List, Literal, Optional, Set, Union

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    TypeAdapter,
    field_validator,
    validate_call,
)

from core_rules_engine import Predicate, Rule, RuleEngine, show_errors

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Item = str
ItemList = List[Item]
ItemPredicate = Predicate[Item]
AllowedSet = Set[Item]


# ---------------------------------------------------------------------------
# Str rule catalogue
# ---------------------------------------------------------------------------
class SubstringRule(Rule):
    kind: Literal["substring"]
    value: str

    def to_predicate(self) -> ItemPredicate:
        return lambda item: self.value in item


class StrInSetRule(Rule):
    kind: Literal["str_in_set"]
    values: AllowedSet

    def to_predicate(self) -> ItemPredicate:
        return lambda item: item in self.values


# ---------------------------------------------------------------------------
# Discriminated union — routes on `kind`
# ---------------------------------------------------------------------------
StrRule = Annotated[
    Union[SubstringRule, StrInSetRule],
    Field(discriminator="kind"),
]

StrRuleAdapter = TypeAdapter(StrRule)


# ---------------------------------------------------------------------------
# Container model
#
# Precedence for the active predicate:
#     predicate > allowed > rule > default (accept all)
# ---------------------------------------------------------------------------
class SelectionInput(BaseModel):
    items: ItemList = Field(
        ...,
        min_length=1,
        description="The list of strings to filter and count.",
        examples=[["wolf", "cat", "wolf pack"]],
    )
    rule: Optional[StrRule] = Field(
        default=None,
        description="A rule as data (kind + fields). Optional.",
    )
    predicate: Optional[ItemPredicate] = Field(
        default=None,
        description="A live predicate. Overrides `rule` when provided.",
    )
    allowed: Optional[AllowedSet] = Field(
        default=None,
        description="A set of allowed exact values. Overrides `rule` when provided.",
    )

    @field_validator("predicate")
    @classmethod
    def predicate_returns_bool(cls, v: Optional[ItemPredicate]) -> Optional[ItemPredicate]:
        if v is None:
            return v
        try:
            result = v("probe")
        except Exception as e:
            raise ValueError(f"predicate raised on probe input: {e}") from e
        if not isinstance(result, bool):
            raise ValueError("predicate must return bool")
        return v

    def resolve_predicate(self) -> ItemPredicate:
        if self.predicate is not None:
            return self.predicate
        if self.allowed is not None:
            return lambda item: item in self.allowed
        if self.rule is not None:
            return self.rule.to_predicate()
        return lambda item: True


# ---------------------------------------------------------------------------
# MatcherService (DI: RuleEngine[str] is injected)
# ---------------------------------------------------------------------------
class MatcherService:

    def __init__(self, engine: RuleEngine[str]) -> None:
        self._engine = engine

    @validate_call
    def match_by_condition(self, items: ItemList, predicate: ItemPredicate) -> ItemList:
        return self._engine.filter(items, predicate)

    @validate_call
    def match_by_attributes(self, items: ItemList, allowed: AllowedSet) -> ItemList:
        return self._engine.filter(items, lambda item: item in allowed)

    @validate_call
    def match_by_rule(self, items: ItemList, rule: StrRule) -> ItemList:
        return self._engine.filter(items, rule.to_predicate())

    @validate_call
    def match_from_input(self, payload: SelectionInput) -> ItemList:
        return self._engine.filter(payload.items, payload.resolve_predicate())

    @validate_call
    def count_items(self, items: ItemList) -> Dict[Item, int]:
        return self._engine.count(items)