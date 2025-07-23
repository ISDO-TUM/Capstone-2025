"""
Custom filter logic for agent-driven paper filtering in the Capstone project.

Responsibilities:
- Provides operator mapping and comparison logic for filtering papers by metadata
- Handles type coercion for dates and numeric/string comparisons
- Used by the agent and filtering tools to apply user-defined criteria
"""

from typing import Any
import logging
import operator
import re

logger = logging.getLogger(__name__)


_OPERATORS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
    "in": lambda x, vals: x in vals,
    "not in": lambda x, vals: x not in vals,
}

DATE_RE = re.compile(r"^\d{4}(-\d{2}-\d{2})?$")


def _coerce(val: Any):
    """
    Try to make comparison types compatible for filtering (e.g., convert date strings to year ints).
    Args:
        val (Any): The value to coerce.
    Returns:
        Any: The coerced value (int for dates, original otherwise).
    """
    if isinstance(val, str) and DATE_RE.match(val):
        # year or full date → int(year)
        return int(val[:4])
    return val


def _matches(field_val, op: str, target):
    """
    Compare a field value to a target using the specified operator.
    Args:
        field_val: The value from the paper metadata.
        op (str): The operator as a string (e.g., '>', 'in').
        target: The target value to compare against.
    Returns:
        bool: True if the comparison matches, False otherwise.
    Raises:
        ValueError: If the operator is not supported.
    """
    if op not in _OPERATORS:
        raise ValueError(f"Unsupported op '{op}'")
    return _OPERATORS[op](_coerce(field_val), _coerce(target))
