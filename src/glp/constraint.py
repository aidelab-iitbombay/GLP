from dataclasses import dataclass
from typing import Any

from glp.enums import ConstraintSense


@dataclass
class Constraint:
    name: str
    expression: Any
    sense: ConstraintSense
    rhs: float

    def __post_init__(self) -> None:
        if not isinstance(self.sense, ConstraintSense):
            raise ValueError("sense must be ConstraintSense")
        if not isinstance(self.rhs, (int, float)):
            raise ValueError("rhs must be numeric")
