from typing import Any
import logging
import operator
import re

logger = logging.getLogger(__name__)


_OPS = {
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
    """Try to make comparison types compatible."""
    if isinstance(val, str) and DATE_RE.match(val):
        # year or full date → int(year)
        return int(val[:4])
    return val


def _matches(field_val, op: str, target):
    if op not in _OPS:
        raise ValueError(f"Unsupported op '{op}'")
    return _OPS[op](_coerce(field_val), _coerce(target))
