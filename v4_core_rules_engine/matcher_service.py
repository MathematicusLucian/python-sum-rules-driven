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


# ---------------------------------------------------------------------------
# Demo — composition root for this service
# ---------------------------------------------------------------------------
def main() -> None:
    engine: RuleEngine[str] = RuleEngine()
    matcher = MatcherService(engine)

    animal_list = ["wolf", "cat", "wolf pack", "wolf", "wolves", "wolf"]

    print("--- match by condition ---")
    print(matcher.match_by_condition(animal_list, lambda x: "wol" in x))
    print(matcher.match_by_condition(animal_list, lambda x: x in {"wolf", "wolves"}))

    print("\n--- match by attributes ---")
    print(matcher.match_by_attributes(animal_list, {"wolf"}))
    print(matcher.match_by_attributes(animal_list, {"wolf", "wolves"}))

    print("\n--- match by rule ---")
    examples = [
        {"kind": "substring", "value": "wol"},
        {"kind": "str_in_set", "values": {"wolf", "wolves"}},
    ]
    for raw in examples:
        rule = StrRuleAdapter.validate_python(raw)
        result = matcher.match_by_rule(animal_list, rule)
        print(f"{type(rule).__name__:15s} {raw!s:45s} -> {result}")

    print("\n--- via SelectionInput ---")
    payload = SelectionInput(items=animal_list, predicate=lambda x: "wol" in x)
    print(matcher.match_from_input(payload))

    print("\n--- count ---")
    print(matcher.count_items(animal_list))

    print("\n--- validation errors (aggregated) ---")
    try:
        SelectionInput(items=[], predicate=lambda x: "wol" in x)
    except ValidationError as e:
        show_errors("empty list", e)

    try:
        SelectionInput(items=animal_list, predicate=lambda x: x)  # str, not bool
    except ValidationError as e:
        show_errors("non-bool predicate", e)


if __name__ == "__main__":
    main()