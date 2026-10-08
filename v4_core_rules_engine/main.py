from __future__ import annotations

import sys
from typing import Sequence

from pydantic import ValidationError

from cli import build_parser, parse_request
from core_rules_engine import RuleEngine
from demos import matcher_demo, sum_demo
from services import build_service
from sum_service import SumInput


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    request = parse_request(argv, parser)
    print(f"\nRequest received: {request}")

    # # -- let Pydantic validate the whole thing at once --
    # payload = SumInput(integers=integers, rule=IntRuleAdapter.validate_python({"kind": "evens"}))
    # try:
    #     payload = SumInput(integers=integers, rule=rule_dict)
    # except ValidationError as e:
    #     print("invalid input:\n", e, file=sys.stderr)
    #     return 2
    # print(f"\nPayload: {payload}")
    # -- validate the payload --
    try:
        payload = SumInput(integers=request.integers, rule=request.rule)
    except ValidationError as e:
        print("Error: Invalid input:\n", e, file=sys.stderr)
        return 2

    rule = payload.rule
    condition = rule.to_predicate()

    if request.verbose:
        print(f"\nIntegers : {payload.integers}")
        print(f"Service : {request.service}")
        print(f"Rule     : {type(rule).__name__}({rule.model_dump()})")
        print(f"Condition: {condition}")

    # -- compose and run --  
    engine: RuleEngine[int] = RuleEngine()
    service = build_service(request.service, engine)
    total = service.sum_by_condition(payload.integers, condition)

    print(f"\nTotal: {total}")
    print("\n---------- END ----------\n")
    return 0


if __name__ == "__main__":
    print("\n--------------------------")
    print("\n--- RULES ENGINE v.1.0 ---")
    print("\n--------------------------")
    raise SystemExit(main())