# Domain-agnostic rule engine.
#
# Knows nothing about ints, strings, sums, or matching. Its whole job is:
#   - iterate a collection
#   - test each item against a predicate
#   - accumulate (filter, count, reduce)
#
# Concrete domains (sum-service, matcher-service) extend this by:
#   1. subclassing Rule to describe their own rules
#   2. injecting a RuleEngine instance and calling its operations
#
# This file deliberately has no dependency on any domain service.

from __future__ import annotations

from typing import (
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    TypeVar,
)

from pydantic import BaseModel, ValidationError

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
T = TypeVar("T")
Predicate = Callable[[T], bool]
Reducer = Callable[[T, T], T]


# ---------------------------------------------------------------------------
# Rule base
#
# A rule is *data* that knows how to become a predicate. Concrete rules
# subclass this and narrow `kind` to a Literal so Pydantic can build a
# discriminated union per domain.
# ---------------------------------------------------------------------------
class Rule(BaseModel):
    kind: str

    def to_predicate(self) -> Predicate:
        raise NotImplementedError(
            f"{type(self).__name__} must implement to_predicate()"
        )


# ---------------------------------------------------------------------------
# RuleEngine
#
# Stateless, generic. Injected into domain services. Any T works.
# ---------------------------------------------------------------------------
class RuleEngine(Generic[T]):
    """Pure operations over a collection + predicate.

    Every method is side-effect free with respect to the engine itself,
    which is why it can be shared, injected, or mocked freely.
    """

    def filter(self, items: Iterable[T], predicate: Predicate) -> List[T]:
        return [item for item in items if predicate(item)]

    def count(self, items: Iterable[T]) -> Dict[T, int]:
        counts: Dict[T, int] = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1
        return counts

    def reduce(
        self,
        items: Iterable[T],
        predicate: Predicate,
        op: Reducer,
        init: T,
    ) -> T:
        acc = init
        for item in items:
            if predicate(item):
                acc = op(acc, item)
        return acc


# ---------------------------------------------------------------------------
# Shared error-display helper
# ---------------------------------------------------------------------------
def show_errors(label: str, exc: ValidationError) -> None:
    errs = exc.errors(include_url=False)
    print(f"rejected ({label}): {len(errs)} error(s)")
    for err in errs:
        loc = ".".join(str(p) for p in err["loc"]) or "<root>"
        print(f"  - [{err['type']}] {loc}: {err['msg']}")