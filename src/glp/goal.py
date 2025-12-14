from dataclasses import dataclass
from typing import Any

from glp.enums import GoalSense


@dataclass
class Goal:
    name: str
    expression: Any
    target: float
    sense: GoalSense = GoalSense.ATTAIN
    weight: float = 1.0
    priority: int = 1

    def __post_init__(self) -> None:
        if self.weight < 0:
            raise ValueError("Goal.weight cannot be negative.")
        if not isinstance(self.priority, int) or self.priority < 1:
            raise ValueError("priority must be integer >= 1")
        if not isinstance(self.sense, GoalSense):
            raise ValueError("sense must be GoalSense enum")
