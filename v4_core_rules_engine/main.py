from functools import partial
from typing import Callable

from core_rules_engine import RuleEngine, show_errors
from matcher_service import MatcherService, SelectionInput, StrRuleAdapter
from sum_service import IntRuleAdapter, SumInput, SumService, onlyEvens

from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Matcher Demo — composition root for this service
# ---------------------------------------------------------------------------

def matcher_demo() -> None:
    engine: RuleEngine[str] = RuleEngine()
    matcher = MatcherService(engine)

    animal_list = ["wolf", "cat", "wolf pack", "wolf", "wolves", "wolf"]
    cars_list = ["Ford", "Volvo", "BMW"]

    print("--- match by condition ---")
    print(matcher.match_by_condition(animal_list, lambda x: "wol" in x))
    print(matcher.match_by_condition(animal_list, lambda x: x in {"wolf", "wolves"}))

    print("\n--- match by attributes ---")
    print(matcher.match_by_attributes(animal_list, {"wolf"}))
    print(matcher.match_by_attributes(animal_list, {"wolf", "wolves"}))
    print(matcher.match_by_attributes(cars_list, {"ford"}))

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

    x = [car for car in cars if "F" not in car]
    print(x)

    integers = [12, 22, 56, 78, 123, 900]

    # Equals 2
    x = [integer for integer in integers if integer == 2]
    print(x, len(x))

    # Contains 2
    x = [integer for integer in integers if "2" in str(integer)]
    print(x, len(x))

    # Even (modulus)
    x = [integer for integer in integers if integer % 2 == 0]
    print(x, len(x))

    print("\n--- END ---\n")

# ---------------------------------------------------------------------------
# Sum Demo — composition root for this service
# ---------------------------------------------------------------------------
def sum_demo() -> None:
    engine: RuleEngine[int] = RuleEngine()
    sums = SumService(engine)

    integers = [1, 2, 3, 4, 5, 6]

    print("--- sum by rule ---")
    examples = [
        {"kind": "exclude", "value": 2},
        {"kind": "include", "value": 2},
        {"kind": "evens"},
        {"kind": "odds"},
        {"kind": "greater_than", "threshold": 3},
        {"kind": "less_than", "threshold": 3},
        {"kind": "divisible_by", "divisor": 3},
        {"kind": "int_in_set", "values": [1, 4, 5]},
    ]
    for raw in examples:
        rule = IntRuleAdapter.validate_python(raw)
        total = sums.sum_by_rule(integers, rule)
        print(f"{type(rule).__name__:20s} {raw!s:45s} -> {total}")

    print("\n--- sum by condition ---")
    print(sums.sum_by_condition(integers, lambda n: n != 2))
    print(sums.sum_by_condition(integers, lambda n: "2" not in str(n)))

    print("\n--- via SumInput ---")
    payload = SumInput(integers=integers, rule=IntRuleAdapter.validate_python({"kind": "evens"}))
    print(sums.sum_from_input(payload))

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
        SumInput(integers=[], condition=onlyEvens)
    except ValidationError as e:
        show_errors("empty list", e)

    print("\n--- END ---\n")


if __name__ == "__main__":
    matcher_demo()
    sum_demo()