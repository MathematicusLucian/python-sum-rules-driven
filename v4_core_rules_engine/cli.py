# parser + helpers + resolve_request()
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Sequence

from sum_service import IntList


# ---------------------------------------------------------------------------
# Resolved request — the only thing main() has to know about
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Request:
    integers: IntList
    rule: dict
    service: str
    verbose: bool

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_int_list(text: str) -> IntList:
    """Accept '1,2,3' or '[1,2,3]' and return a list of ints."""
    text = text.strip()
    if text.startswith("["):
        return json.loads(text)
    return [int(piece.strip()) for piece in text.split(",") if piece.strip()]


def _rule_from_flags(args: argparse.Namespace) -> dict:
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

    p.add_argument("integers_pos", nargs="?", default=None,
                   help="Integers as CSV or JSON list (positional).")
    p.add_argument("--integers", dest="integers_flag", default=None,
                   help="Integers as CSV or JSON list (flag form).")

    p.add_argument("--service", default=None,
                   help="Service to run (e.g. 'sum').")   # <-- was wrong help text
    p.add_argument("--rule", default=None,
                   help='Full rule as JSON, e.g. \'{"kind":"greater_than","threshold":3}\'')
    p.add_argument(
        "--kind",
        choices=[
            "exclude", "include", "evens", "odds",
            "greater_than", "less_than", "divisible_by", "in_set",
        ],
        default=None,
        help="Rule name (use with the rule-specific flag below).",
    )
    p.add_argument("--value", type=int, default=None, help="For kind=exclude/include.")
    p.add_argument("--threshold", type=int, default=None, help="For kind=greater_than/less_than.")
    p.add_argument("--divisor", type=int, default=None, help="For kind=divisible_by.")
    p.add_argument("--values", default=None,
                   help="For kind=in_set, e.g. '1,4,5' or '[1,4,5]'.")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Show the parsed rule and condition kind.")

    return p


# ---------------------------------------------------------------------------
# The one public entry point
# ---------------------------------------------------------------------------
def parse_request(
    argv: Sequence[str] | None,
    parser: argparse.ArgumentParser | None = None,
) -> Request | None:
    """
    Parse argv into a validated Request.

    Returns None when no integers were supplied (caller should run demos).
    Calls parser.error(...) for invalid input, which exits the process.
    """
    parser = parser or build_parser()
    args = parser.parse_args(argv)

    raw_integers = args.integers_flag or args.integers_pos
    if raw_integers is None:
        return None

    try:
        integers = parse_int_list(raw_integers)
    except (ValueError, json.JSONDecodeError) as e:
        parser.error(f"could not parse integers {raw_integers!r}: {e}")

    if args.rule is not None:
        try:
            rule_dict = json.loads(args.rule)
        except json.JSONDecodeError as e:
            parser.error(f"--rule is not valid JSON: {e}")
    else:
        rule_dict = _rule_from_flags(args)

    if args.service is None:
        parser.error("--service is required when integers are given")

    return Request(
        integers=integers,
        rule=rule_dict,
        service=args.service,
        verbose=args.verbose,
    )