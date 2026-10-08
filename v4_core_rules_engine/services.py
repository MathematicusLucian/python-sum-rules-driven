# SERVICE_REGISTRY + build_service()
from core_rules_engine import RuleEngine
from matcher_service import MatcherService
from sum_service import SumService

SERVICE_REGISTRY: dict[str, type] = {
    "matcher": MatcherService,
    "sum": SumService,
}


def build_service(name: str, engine: RuleEngine):
    try:
        cls = SERVICE_REGISTRY[name]
    except KeyError:
        raise SystemExit(f"error: unknown service {name!r}")
    return cls(engine)