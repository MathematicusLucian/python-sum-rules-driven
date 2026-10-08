import argparse
from functools import partial
import json
import sys
from typing import Callable, Sequence

from core_rules_engine import RuleEngine, show_errors
from matcher_service import MatcherService, SelectionInput, StrRuleAdapter
from sum_service import IntList, IntRuleAdapter, SumInput, SumService, onlyEvens

from pydantic import ValidationError

# Registry mapping name -> class
SERVICE_REGISTRY: dict[str, type] = {
    "matcher": MatcherService,
    "sum": SumService,
}

# ---------------------------------------------------------------------------
# Service factory
# ---------------------------------------------------------------------------
def build_service(name: str, engine: RuleEngine[int]):
    try:
        cls = SERVICE_REGISTRY[name]
    except KeyError:
        raise SystemExit(f"error: unknown service {name!r}")
    return cls(engine)

# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------
def parse_int_list(text: str) -> IntList:
    """Accept '1,2,3' or '[1,2,3]' and return a list of ints."""
    text = text.strip()
    if text.startswith("["):
        return json.loads(text)
    return [int(piece.strip()) for piece in text.split(",") if piece.strip()]


def build_rule_from_flags(args: argparse.Namespace) -> dict:
    """Turn --kind + rule-specific flags into a dict for Pydantic to validate."""
    if args.kind is None:
        raise SystemExit("error: --kind is required when --rule is not given")

    rule: dict = {"kind": args.kind}

    if args.kind in {"exclude", "include"}:
        if args.value is None:
            raise SystemExit(f"error: --value is required for kind '{args.kind}'")
        rule["value"] = args.value

    elif args.kind in {"greater_than", "less_than"}:
        if args.threshold is None:
            raise SystemExit(f"error: --threshold is required for kind '{args.kind}'")
        rule["threshold"] = args.threshold

    elif args.kind == "divisible_by":
        if args.divisor is None:
            raise SystemExit("error: --divisor is required for kind 'divisible_by'")
        rule["divisor"] = args.divisor

    elif args.kind == "in_set":
        if not args.values:
            raise SystemExit("error: --values is required for kind 'in_set'")
        rule["values"] = parse_int_list(args.values)

    # evens / odds need no extra flags
    return rule


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="main.py",
        description="Sum a list of integers, filtered by a named rule.",
        epilog=(
            "Examples:\n"
            "  count.py --integers '1,2,3,4' --service sum --kind evens\n"
            "  count.py --integers '1,2,3,4' --service sum --kind greater_than --threshold 2\n"
            "  count.py --integers '1,2,3,4' --service sum --kind in_set --values '1,4'\n"
            "  count.py --integers '1,2,3,4' --service sum --rule '{\"kind\": \"odds\"}'\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # integers: positional OR --integers
    p.add_argument(
        "integers_pos", nargs="?", default=None,
        help="Integers as CSV or JSON list (positional).",
    )
    p.add_argument(
        "--integers", dest="integers_flag", default=None,
        help="Integers as CSV or JSON list (flag form).",
    )

    # rule: raw JSON OR --kind + rule-specific flags
    p.add_argument(
        "--service", default=None,
        help='Full rule as JSON, e.g. \'{"service":"sum"}\'',
    )
    p.add_argument(
        "--rule", default=None,
        help='Full rule as JSON, e.g. \'{"kind":"greater_than","threshold":3}\'',
    )
    p.add_argument(
        "--kind",
        choices=[
            "exclude", "include", "evens", "odds",
            "greater_than", "less_than", "divisible_by", "in_set",
        ],
        default=None,
        help="Rule name (use with the rule-specific flag below).",
    )
    p.add_argument("--value", type=int, default=None,
                   help="For kind=exclude/include.")
    p.add_argument("--threshold", type=int, default=None,
                   help="For kind=greater_than/less_than.")
    p.add_argument("--divisor", type=int, default=None,
                   help="For kind=divisible_by.")
    p.add_argument("--values", default=None,
                   help="For kind=in_set, e.g. '1,4,5' or '[1,4,5]'.")

    p.add_argument("--verbose", "-v", action="store_true",
                   help="Show the parsed rule and condition kind.")

    return p

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

    x = [car for car in cars_list if "F" not in car]
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

def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    print(args)

    # -- resolve integers (flag wins over positional) --
    raw_integers = args.integers_flag or args.integers_pos
    if raw_integers is None: 
        matcher_demo()
        sum_demo() 
        parser.error("provide integers (positional or --integers)")
    try:
        print('\nAttempting to read args')
        integers = parse_int_list(raw_integers)
    except (ValueError, json.JSONDecodeError) as e:
        parser.error(f"could not parse integers {raw_integers!r}: {e}")

    # -- resolve the rule dict --
    if args.rule is not None:
        try:
            rule_dict = json.loads(args.rule)
        except json.JSONDecodeError as e:
            parser.error(f"--rule is not valid JSON: {e}")
    else:
        rule_dict = build_rule_from_flags(args)
    print(f"\nRules received: {rule_dict}")

    # -- let Pydantic validate the whole thing at once --
    payload = SumInput(integers=integers, rule=IntRuleAdapter.validate_python({"kind": "evens"}))
    try:
        payload = SumInput(integers=integers, rule=rule_dict)
    except ValidationError as e:
        print("invalid input:\n", e, file=sys.stderr)
        return 2
    print(f"\nPayload: {payload}")

    rule = payload.rule               # already the right concrete class
    condition = rule.to_predicate()
    if args.verbose:
        print(f"\nIntegers : {payload.integers}")
        print(f"\nRule     : {type(rule).__name__}({rule.model_dump()})")
        print(f"\nCondition: {condition}") 

    if args.service is None:
        raise SystemExit("error: --service is required when --rule is given") 
    print(f"\Service selected: {args.service}")

    engine: RuleEngine[int] = RuleEngine()
    service = build_service(args.service, engine)

    total = service.sum_by_condition(payload.integers, condition) # lambda n: n != 2)
    print(f"\nTotal: {total}")

    print("\n--- END ---\n")
    return 0

if __name__ == "__main__": 
    print("\n--- RULES ENGINE v.1.0 ---")
    print("\n--------------------------\n")
    raise SystemExit(main())