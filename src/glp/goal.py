from dataclasses import dataclass
from typing import Any

from glp.enums import GoalSense


@dataclass
class Goal:
    """
    Represents a goal-programming objective component.

    Attributes:
        name: Identifier for the goal. Used for reporting and analysis.
        expression: The quantity whose deviation from 'target' is considered.
            Can be a symbolic expression or any object supported by the modeling layer.
        target: The target value the expression should attain or relate to.
        sense: A GoalSense describing which deviations are penalized
            (e.g., ATTAIN, MINIMIZE_UNDER, MINIMIZE_OVER).
        weight: Non-negative weight applied to this goal’s deviation in the objective.
        priority: Lexicographic priority (integer >= 1). Lower numbers typically
            indicate higher priority in preemptive goal programming.

    Notes:
        - This class validates weight non-negativity, priority type/range,
          and the sense enum in __post_init__.
        - Interpretation of 'sense':
            * ATTAIN: penalize both under- and over-target deviations.
            * MINIMIZE_UNDER: prefer value <= target; penalize over-target deviations.
            * MINIMIZE_OVER: prefer value >= target; penalize under-target deviations.
    """

    name: str
    expression: Any
    target: float
    sense: GoalSense = GoalSense.ATTAIN
    weight: float = 1.0
    priority: int = 1

    def __post_init__(self) -> None:
        """
        Validate field values after initialization.

        Ensures that:
        - 'weight' is non-negative.
        - 'priority' is an integer >= 1.
        - 'sense' is an instance of GoalSense.

        Raises:
            ValueError: If any validation fails.
        """
        if self.weight < 0:
            raise ValueError("Goal.weight cannot be negative.")
        if not isinstance(self.priority, int) or self.priority < 1:
            raise ValueError("priority must be integer >= 1")
        if not isinstance(self.sense, GoalSense):
            raise ValueError("sense must be GoalSense enum")
