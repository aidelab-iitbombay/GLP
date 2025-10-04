from enum import Enum


class ConstraintSense(Enum):
    LE = "<="
    GE = ">="
    EQ = "=="
    LT = "<"
    GT = ">"


class GoalSense(Enum):
    ATTAIN = "attain"  # Value is equal to the target
    MINIMIZE_UNDER = "minimize_under"  # Value is <= target
    MINIMIZE_OVER = "minimize_over"  # Value is >= target
