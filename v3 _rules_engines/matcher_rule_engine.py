from typing import Annotated, Callable, Dict, List, Literal, Optional, Set, Union

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_validator,
    validate_call,
    TypeAdapter,
)

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Item = str
ItemList = List[Item]
Predicate = Callable[[Item], bool]
AllowedSet = Set[Item]

# ---------------------------------------------------------------------------
# Rule classes (each is one menu item)
# ---------------------------------------------------------------------------
class SubstringRule(BaseModel):
    kind: Literal["substring"]
    value: str

    def to_predicate(self) -> Predicate:
        return lambda item: self.value in item


class InSetRule(BaseModel):
    kind: Literal["in_set"]
    values: AllowedSet

    def to_predicate(self) -> Predicate:
        return lambda item: item in self.values


# ---------------------------------------------------------------------------
# Discriminated union — routes on `kind`
# ---------------------------------------------------------------------------
AnyRule = Annotated[
    Union[SubstringRule, InSetRule],
    Field(discriminator="kind"),
]

RuleAdapter = TypeAdapter(AnyRule)


# ---------------------------------------------------------------------------
# Container model
# ---------------------------------------------------------------------------
class SelectionInput(BaseModel):
    items: ItemList = Field(
        ...,
        min_length=1,
        description="The list of strings to filter and count.",
        examples=[["wolf", "cat", "wolf pack"]],
    )
    rule: Optional[AnyRule] = Field(
        default=None,
        description="A rule as data (kind + fields). Optional.",
    )
    predicate: Optional[Predicate] = Field(
        default=None,
        description="A live predicate. Overrides `rule` when provided.",
    )
    allowed: Optional[AllowedSet] = Field(
        default=None,
        description="A set of allowed exact values. Overrides `rule` when provided.",
    )

    @field_validator("predicate")
    @classmethod
    def predicate_returns_bool(cls, v: Optional[Predicate]) -> Optional[Predicate]:
        if v is None:
            return v
        try:
            result = v("probe")
        except Exception as e:
            raise ValueError(f"predicate raised on probe input: {e}") from e
        if not isinstance(result, bool):
            raise ValueError("predicate must return bool")
        return v

    def resolve_predicate(self) -> Predicate:
        if self.predicate is not None:
            return self.predicate
        if self.allowed is not None:
            return lambda item: item in self.allowed
        if self.rule is not None:
            return self.rule.to_predicate()
        return lambda item: True


# ---------------------------------------------------------------------------
# SelectorClass
# ---------------------------------------------------------------------------
class AnimalSelector:

    @validate_call
    def select_by_condition(self, items: ItemList, predicate: Predicate) -> ItemList:
        return [item for item in items if predicate(item)]

    @validate_call
    def select_by_attributes(self, items: ItemList, allowed: AllowedSet) -> ItemList:
        return [item for item in items if item in allowed]

    @validate_call
    def count_items(self, items: ItemList) -> Dict[Item, int]:
        counts: Dict[Item, int] = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1
        return counts


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
selector = AnimalSelector()

animal_list: ItemList = ['wolf', 'cat', 'wolf pack', 'wolf', 'wolves', 'wolf']

substring_wol: Predicate = lambda x: 'wol' in x
exact_wolves: Predicate = lambda x: x in {'wolf', 'wolves'}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    selector = AnimalSelector()
    animal_list = ['wolf', 'cat', 'wolf pack', 'wolf', 'wolves', 'wolf']

    print("--- simple function calls ---")
    print(selector.select_by_condition(animal_list, substring_wol))         # ['wolf', 'wolf pack', 'wolf', 'wolves', 'wolf']
    print(selector.select_by_condition(animal_list, exact_wolves))          # ['wolf', 'wolf', 'wolves', 'wolf']
    print(selector.select_by_attributes(animal_list, {'wolf'}))             # ['wolf', 'wolf', 'wolf']
    print(selector.select_by_attributes(animal_list, {'wolf', 'wolves'}))   # ['wolf', 'wolf', 'wolves', 'wolf']
    print(selector.count_items(animal_list))                                # {'wolf': 3, 'cat': 1, 'wolf pack': 1, 'wolves': 1}

    print("\n--- rule-driven examples ---")
    examples = [
        {"kind": "substring", "value": "wol"},
        {"kind": "in_set", "values": {"wolf", "wolves"}},
    ]
    for raw in examples:
        rule = RuleAdapter.validate_python(raw)
        pred = rule.to_predicate()
        result = selector.select_by_condition(animal_list, pred)
        print(f"{type(rule).__name__:15s} {raw!s:45s} → {result}")

    print("\n--- container model ---")
    payload = SelectionInput(items=animal_list, predicate=substring_wol)
    resolved = payload.resolve_predicate()
    print(selector.select_by_condition(payload.items, resolved))

    print("\n--- validation errors (aggregated) ---")
    try:
        SelectionInput(items=[], predicate=substring_wol)
    except ValidationError as e:
        show_errors("empty list", e)

    try:
        SelectionInput(items=animal_list, predicate=lambda x: x)  # returns str, not bool
    except ValidationError as e:
        show_errors("non-bool predicate", e)


if __name__ == "__main__":
    main()