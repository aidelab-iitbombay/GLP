from dataclasses import dataclass
from typing import Any

from .enums import GoalSense


@dataclass(frozen=True)
class Goal:
    """
    Class to define a single goal
    """

    name: str
    expression: Any
    target: float
    sense: GoalSense
    weight: float = 1.0
    priority: int = 1
