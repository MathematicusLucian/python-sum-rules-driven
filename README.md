# Rule-Based Sum and Selection Examples

## Overview

This repo contains two related examples:

1. **`sum_rule_engine.py`** — the attached Pydantic + callable-rule file for filtering and summing integers.
2. **`matcher_rule_engine.py`** — the simple selection/counting functions, plus a structured Pydantic/rule-based variant.

Together they show two ends of the same design space:

- **Simple functions** for small, one-off problems.
- **Data-driven rule engines** for configurable, validated, extensible behaviour.

The same principles appear in both, but the trade-offs differ. The simpler file is often the better default. The structured file is useful when rules come from JSON, an API, a database, or a user interface.

---

## Core Ideas

Both files revolve around a few small concepts:

- **Predicate** — `Callable[[T], bool]`, e.g. `lambda n: n != 2`.
- **Rule** — a data object that knows how to turn itself into a predicate, e.g. `ExcludeRule.to_condition()`.
- **Adapter** — `TypeAdapter` parses raw dict/list data into a typed rule.
- **Container** — `SumInput` / `SelectionInput` validates input and resolves the active predicate.
- **Service** — `SumClass` / `AnimalSelector` performs operations using an injected predicate.
- **Composition root** — `main()` wires everything together and handles I/O.

---

## Design Principles

DRY (Don't Repeat Yourself) is about having a **single source of truth**, not about eliminating every repeated line.

Where it shows up:

- `rule.to_condition()` centralises predicate creation for each rule.
- `resolve_condition()` centralises precedence: explicit condition > rule > default.
- `count_items()` uses `counts.get(item, 0) + 1` instead of branching duplicate increment logic.
- `select_by_condition()` is generic over any predicate, so filtering logic is written once.
- `TypeAdapter` avoids repeating parsing and validation for each rule type.
- `show_errors()` centralises error formatting.

Caveat: DRY can be overdone. In the simple animal file, three small functions are clearer than a generic framework. Repetition is sometimes cheaper than the wrong abstraction.

---

## SOLID

### S — Single Responsibility

Each unit has one reason to change:

- `ExcludeRule`, `IncludeRule`, `EvensRule`, etc. each model one rule and convert it to a predicate.
- `SumInput` validates input and resolves the active condition.
- `SumClass` performs summation.
- `show_errors` formats validation errors.
- `AnimalSelector` methods each do one operation: select by condition, select by attributes, count items.
- `SelectionInput` validates and resolves predicates.

### O — Open/Closed

The rule engines are open for extension but closed for modification:

- Add a new rule by creating a new `BaseModel` subclass and adding it to the `AnyRule` union. Existing rules are untouched.
- In the simple animal file, add a new predicate by passing a new lambda. `select_by_condition` does not change.

### L — Liskov Substitution

Rule objects and predicates are substitutable:

- Every rule exposes `to_condition()` returning a `Condition`.
- Every predicate is a `Callable[[T], bool]`.
- `partial`, lambdas, set membership, and rule-derived conditions can all be used wherever a predicate is expected.

### I — Interface Segregation

Interfaces are small and focused:

- `Condition = Callable[[int], bool]`
- `Predicate = Callable[[Item], bool]`
- Separate methods for selection by condition vs selection by attributes vs counting, rather than one god method.

### D — Dependency Inversion

High-level code depends on abstractions, not concrete rules:

- `SumClass` depends on `Condition`, not on `ExcludeRule`.
- `AnimalSelector` depends on `Predicate`, not on `SubstringRule`.
- `SumInput` can accept a live callable or a data rule; the caller decides.

---

## Other Principles

- **KISS** — simple functions are often enough. The elaborate rule engine is justified only when rules are configurable, validated, or external.
- **YAGNI** — do not build a rule engine for a one-off filter. The simple `animal_selector.py` is the better default.
- **Composition over inheritance** — rules compose into predicates; there is no deep class hierarchy.
- **Strategy pattern** — each rule is a strategy for filtering.
- **Adapter pattern** — `RuleAdapter`, `rule.to_condition()`, and `TypeAdapter` adapt raw data into behaviour.
- **Data-driven design** — rules are data, e.g. `{"kind": "exclude", "value": 2}`, validated and converted to behaviour.
- **Functional core, imperative shell** — pure predicates and list comprehensions; `main()` handles I/O.
- **Validation at boundaries** — Pydantic checks types, duplicates, and bool-returning predicates.
- **Fail fast, aggregate errors** — `ValidationError` collects multiple issues; `show_errors` prints them.

---

## Architectural Concepts

- **Layering**
  - Domain/rules: Pydantic models.
  - Application/service: `SumClass`, `AnimalSelector`.
  - Boundary/adapters: `TypeAdapter`, `validate_call`.
  - Composition root: `main`.

- **Discriminated union** — the `kind` field routes to the correct rule model.

- **Dependency injection** — predicates and conditions are passed into service methods.

- **Precedence resolution** — `condition` overrides `rule`; `allowed` overrides `rule` in the animal variant.

- **Runtime validation** — `@validate_call` validates method arguments; `BaseModel` validates payloads.

- **Testability** — pure functions are easy to test; rules can be instantiated without I/O.

---

## File-by-File Notes

### `sum_rule_engine.py`

- Rule models: `ExcludeRule`, `IncludeRule`, `EvensRule`, `OddsRule`, `GreaterThanRule`, `LessThanRule`, `DivisibleByRule`, `InSetRule`.
- `AnyRule` is a discriminated union on `kind`.
- `SumInput` holds `integers`, optional `rule`, optional `condition`; validates no duplicates and bool-returning condition; `resolve_condition()` picks the active predicate.
- `SumClass` demonstrates multiple sum implementations: loop, generator, list wrapper, staticmethod, adapter-based, and `validate_call`.
- `main()` shows rule-driven examples, happy paths, coercion, and error aggregation.
- Design note: comments in `main()` may be stale after `integers` changes. Update expected outputs when data changes.

### `animal_selector.py`

- Simple version:
  - `select_by_condition(items, predicate)`
  - `select_by_attributes(items, allowed)`
  - `count_items(items)`
- Structured version:
  - `SubstringRule`, `InSetRule`, `AnyRule`, `RuleAdapter`
  - `SelectionInput` with `items`, `rule`, `predicate`, `allowed`; `resolve_predicate()`
  - `AnimalSelector` with `select_by_condition`, `select_by_attributes`, `count_items`
- Design note: the structured version intentionally mirrors the sum file. For real work, prefer the simple version unless you need config-driven rules.

---

## When to Use Which

| Need | Use |
|------|-----|
| One-off filter/count | Simple functions |
| User/JSON-configurable rules | Pydantic rule models + `TypeAdapter` |
| Strong boundary validation | Pydantic + `validate_call` |
| Maximum clarity for small scripts | KISS, no framework |
| Extensible rule set | Open/Closed rule classes |

---

## Testing Guidance

- Test predicates directly.
- Test `resolve_condition()` / `resolve_predicate()` precedence.
- Test invalid inputs raise `ValidationError`.
- Test `count_items` with duplicates, empty lists, and mixed types.
- For the rule engine, test each rule’s `to_condition()` and the discriminated-union parsing.

---

## Conclusion

The two files show two ends of the same design space. The sum file is a small, validated, extensible rule engine. The animal selector file shows how the same ideas apply to strings, but also reminds us that simple functions are often the right answer.

Use DRY and SOLID to manage change, not to add ceremony. The best design is the simplest one that meets the requirement and can evolve safely.