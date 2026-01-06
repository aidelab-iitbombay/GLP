from dataclasses import dataclass
from typing import Any

from glp.enums import ConstraintSense


@dataclass
class Constraint:
    """
    Represents a single algebraic constraint.

    Attributes:
        name: Identifier for the constraint. Useful for reporting and debugging.
        expression: The left-hand side expression of the constraint. This can be
            a symbolic expression, an expression tree, or any object understood
            by the modeling layer consuming this dataclass.
        sense: The relational direction of the constraint, as a ConstraintSense.
        rhs: The numeric right-hand side against which the expression is compared.

    Notes:
        - This class does not evaluate expressions; it only carries structure.
        - Validation in __post_init__ ensures type safety for 'sense' and 'rhs'.
    """

    name: str
    expression: Any
    sense: ConstraintSense
    rhs: float

    def __post_init__(self) -> None:
        """
        Validate field types after initialization.

        Ensures that:
        - 'sense' is a ConstraintSense instance.
        - 'rhs' is numeric (int or float).

        Raises:
            ValueError: If 'sense' is not a ConstraintSense or 'rhs' is not numeric.
        """
        if not isinstance(self.sense, ConstraintSense):
            raise ValueError("sense must be ConstraintSense")
        if not isinstance(self.rhs, (int, float)):
            raise ValueError("rhs must be numeric")
