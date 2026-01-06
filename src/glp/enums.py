from enum import Enum


class ConstraintSense(Enum):
    """
    Relational senses for constraints.

    Each member maps to the corresponding mathematical operator represented
    as a string. These are commonly used to annotate constraints of the form
    expression (sense) rhs.

    Members:
    - LE: "<="  Left-hand side must be less than or equal to the right-hand side.
    - GE: ">="  Left-hand side must be greater than or equal to the right-hand side.
    - EQ: "=="  Left-hand side must be equal to the right-hand side.
    - LT: "<"   Left-hand side must be strictly less than the right-hand side.
    - GT: ">"   Left-hand side must be strictly greater than the right-hand side.
    """

    LE = "<="
    GE = ">="
    EQ = "=="
    LT = "<"
    GT = ">"


class GoalSense(Enum):
    """
    Goal semantics for goal programming.

    These senses describe how deviations from a target are interpreted and
    penalized in a goal-programming model.

    Members:
    - ATTAIN: "attain"
        Aim to match the target value as closely as possible (both under- and
        over-target deviations may be penalized).
    - MINIMIZE_UNDER: "minimize_under"
        Prefer values at or below the target (value <= target). Typically
        interpreted as penalizing over-target (positive) deviations only.
    - MINIMIZE_OVER: "minimize_over"
        Prefer values at or above the target (value >= target). Typically
        interpreted as penalizing under-target (negative) deviations only.
    """

    ATTAIN = "attain"  # Value is equal to the target
    MINIMIZE_UNDER = "minimize_under"  # Value is <= target
    MINIMIZE_OVER = "minimize_over"  # Value is >= target
