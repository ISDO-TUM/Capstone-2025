import datetime as dt
from typing import Any
import logging

logger = logging.getLogger(__name__)


def _coerce_date_to_year(value: Any) -> Any:
    """
    Convert YYYY-MM-DD strings to int(year) so they compare naturally
    (“2025-06-02” ≥ 2024 → True).
    """
    if isinstance(value, str) and value.count("-") == 2:
        try:
            return dt.datetime.strptime(value, "%Y-%m-%d").year
        except ValueError:
            # fall through – treat as string
            pass
    return value


def _matches(field_value: Any, op: str, target: Any) -> bool:
    """
    Returns True if `field_value <op> target` is satisfied.
    Supported ops: '>', '>=', '<', '<=', '==', 'in', 'not in'
    """
    field_value = _coerce_date_to_year(field_value)

    # Convert lists to sets for "in" / "not in"
    if op in {"in", "not in"}:
        if not isinstance(target, (list, set, tuple)):
            target = [target]
        target_set = {str(x) for x in target}
        result = str(field_value) in target_set
        return result if op == "in" else not result

    # Numeric / lexicographic comparisons
    try:
        if op == ">":
            return float(field_value) > float(target)
        if op == ">=":
            return float(field_value) >= float(target)
        if op == "<":
            return float(field_value) < float(target)
        if op == "<=":
            return float(field_value) <= float(target)
        if op == "==":
            return str(field_value).lower() == str(target).lower()
    except (TypeError, ValueError):
        return False

    logger.warning("Unknown operator '%s' – returning False", op)
    return False
