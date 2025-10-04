from dataclasses import dataclass
from typing import Any

from .enums import ConstraintSense


@dataclass(frozen=True)
class Constraint:
    """
    A data class to define a hard constraint
    """

    name: str
    expression: Any
    sense: ConstraintSense
    rhs: float
