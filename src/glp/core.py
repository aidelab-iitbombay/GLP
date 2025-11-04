# src/glp/core.py
"""Core datatypes and model container for a Goal Linear Programming (GLP) package.

This module provides:
- GoalSense, ConstraintSense enums
- Goal and Constraint dataclasses
- GLPModel: a thin wrapper around pulp.LpProblem to manage variables, goals,
  deviation variables and constraints in a consistent API.

Notes Expressions used for goals/constraints should be PuLP linear expressions (e.g., sums of pulp.LpVariable multiplied by constants).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import re
import pulp

# ----------------------
# Enums
# ----------------------
class GoalSense(Enum):
    """
    Indicates the sense/type of a goal.

    ATTAIN: aim to attain (two-sided) the target — both under/over deviations tracked.
    MINIMIZE_UNDER: focus on minimizing underachievement (e.g., meet minimums).
    MINIMIZE_OVER: focus on minimizing overachievement (e.g., not exceed a budget).
    """

    ATTAIN = "ATTAIN"
    MINIMIZE_UNDER = "MINIMIZE_UNDER"
    MINIMIZE_OVER = "MINIMIZE_OVER"

class ConstraintSense(Enum):
    """Sense for a hard constraint."""

    LE = "<="
    GE = ">="
    EQ = "=="
    LT = "<"
    GT = ">"

# ----------------------
# Dataclasses
# ----------------------
@dataclass
class Goal:
    """
    Representation of a soft goal (aspiration) in GLP.

    Attributes:
        name: Unique identifier for the goal.
        expression: A PuLP linear expression representing the left-hand side (f(x)).
                    Typically an `pulp.LpAffineExpression`.
        target: The aspiration/target value (right-hand side).
        sense: The GoalSense (ATTAIN, MINIMIZE_UNDER, MINIMIZE_OVER).
        weight: The weight used in weighted goal programming (default 1.0).
        priority: Integer priority level (1 = highest by default).
    """

    name: str
    expression: Any
    target: float
    sense: GoalSense = GoalSense.ATTAIN
    weight: float = 1.0
    priority: int = 1

    def __post_init__(self) -> None:
        # Basic validation
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Goal.name must be a non-empty string.")
        if not isinstance(self.priority, int) or self.priority < 1:
            raise ValueError("Goal.priority must be an integer >= 1.")
        if not isinstance(self.weight, (int, float)) or self.weight < 0:
            raise ValueError("Goal.weight must be a non-negative number.")
        if not isinstance(self.sense, GoalSense):
            raise ValueError("Goal.sense must be a GoalSense enum member.")


@dataclass
class Constraint:
    """
    Representation of a hard constraint.

    Attributes:
        name: Unique identifier for the constraint.
        expression: Left-hand side expression (PuLP affine expression).
        sense: ConstraintSense (LE, GE, EQ).
        rhs: Right-hand side numeric value of the constraint.
    """

    name: str
    expression: Any
    sense: ConstraintSense
    rhs: float

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Constraint.name must be a non-empty string.")
        if not isinstance(self.sense, ConstraintSense):
            raise ValueError("Constraint.sense must be a ConstraintSense enum member.")
        if not isinstance(self.rhs, (int, float)):
            raise ValueError("Constraint.rhs must be numeric.")


# ----------------------
# GLPModel
# ----------------------
def _sanitize_name(name: str) -> str:
    """Return a safe PuLP-compatible name (letters, numbers, underscore)."""
    # Replace whitespace and non-alphanum with underscore, collapse underscores.
    s = re.sub(r"\W+", "_", name.strip())
    s = re.sub(r"_+", "_", s)
    if not s:
        raise ValueError("Name cannot be sanitized to a valid identifier.")
    return s


class GLPModel:
    """
    Main class to define and manage a Goal Programming model.

    This class wraps around PuLP's `LpProblem` to:
    - Add variables, goals, and constraints
    - Handle deviation variables for each goal
    - Prepare the structure for solving Goal Programming problems

    Example usage (conceptual):
        model = GLPModel("diet")
        x1 = model.add_variable("rice", low_bound=0.0)
        x2 = model.add_variable("lentils", low_bound=0.0)
        # Create a PuLP expression for protein: 2*x1 + 10*x2
        expr = 2 * x1 + 10 * x2
        goal = Goal(name="protein", expression=expr, target=50.0)
        model.add_goal(goal)
    """

    def __init__(self, name: str = "glp_problem", minimize: bool = True) -> None:
        """
        Initialize a new GLPModel instance.

        Args:
            name: Problem name.
            minimize: If True, problem sense = minimize; else maximize.
        """
        self.name = name
        self.problem = pulp.LpProblem(name, pulp.LpMinimize if minimize else pulp.LpMaximize)

        # Internal registries
        self.variables: Dict[str, pulp.LpVariable] = {}
        self.goals: Dict[str, Goal] = {}
        self.constraints: Dict[str, Constraint] = {}
        # mapping: goal_name -> (n_dev_var, p_dev_var)
        self.dev_vars: Dict[str, Tuple[pulp.LpVariable, pulp.LpVariable]] = {}

    # ----------------------
    # Variable API
    # ----------------------
    def add_variable(
        self,
        name: str,
        low_bound: Optional[float] = 0.0,
        up_bound: Optional[float] = None,
        cat: str = "Continuous",
    ) -> pulp.LpVariable:
        """
        Create and register a pulp.LpVariable.

        Args:
            name: variable name (will be sanitized).
            low_bound: lower bound (float or None).
            up_bound: upper bound (float or None).
            cat: category string: "Continuous", "Integer", or "Binary".

        Returns:
            The created pulp.LpVariable stored in self.variables.
        """
        if name in self.variables:
            # Return existing variable (idempotent) — you can choose to raise instead.
            return self.variables[name]

        safe = _sanitize_name(name)

        cat_map = {
            "CONTINUOUS": pulp.LpContinuous,
            "CONT": pulp.LpContinuous,
            "INTEGER": pulp.LpInteger,
            "INT": pulp.LpInteger,
            "BINARY": pulp.LpBinary,
            "BIN": pulp.LpBinary,
        }
        cat_key = (cat or "Continuous").upper()
        pulp_cat = cat_map.get(cat_key)
        if pulp_cat is None:
            raise ValueError("Unknown variable category. Choose Continuous, Integer, or Binary.")

        # Create variable. Use `lowBound` / `upBound` names compatible with PuLP.
        var = pulp.LpVariable(safe, lowBound=low_bound, upBound=up_bound, cat=pulp_cat)
        self.variables[name] = var
        return var

    # ----------------------
    # Constraint API
    # ----------------------
    def add_constraint(self, constraint: Constraint) -> None:
        """
        Add a hard constraint to the internal PuLP problem.

        The constraint is converted to the appropriate PuLP relational operator.

        Raises:
            ValueError: if constraint name already exists, or expression type is invalid.
        """
        if constraint.name in self.constraints:
            raise ValueError(f"Constraint with name '{constraint.name}' already exists.")
        # Basic type-check for expressions: accept PuLP LpAffineExpression or LpVariable or numeric.
        if not isinstance(constraint.expression, (pulp.LpAffineExpression, pulp.LpVariable, int, float)):
            # allow any expression that implements __add__/__mul__, but strongly prefer PuLP expressions.
            # For stricter behavior, uncomment the next line:
            # raise TypeError("Constraint.expression must be a PuLP linear expression or LpVariable.")
            pass

        safe_name = _sanitize_name(constraint.name)
        # Build and add actual PuLP constraint
        if constraint.sense == ConstraintSense.LE:
            pulp_constr = constraint.expression <= constraint.rhs
        elif constraint.sense == ConstraintSense.GE:
            pulp_constr = constraint.expression >= constraint.rhs
        elif constraint.sense == ConstraintSense.EQ:
            pulp_constr = constraint.expression == constraint.rhs
        else:
            raise ValueError("Unsupported constraint sense.")

        # Add to problem with human-readable name
        self.problem.addConstraint(pulp_constr, name=safe_name)
        self.constraints[constraint.name] = constraint

    # ----------------------
    # Goal API
    # ----------------------
    def add_goal(self, goal: Goal) -> Tuple[pulp.LpVariable, pulp.LpVariable]:
        """
        Register a Goal and create its deviation variables and linking constraint.

        Adds:
            - two nonnegative deviation variables: n_<goal>, p_<goal>
            - linking equality: goal.expression + n - p == goal.target

        Raises:
            ValueError: if a goal with the same name already exists, or invalid expression.
        Returns:
            Tuple of (n_dev_var, p_dev_var)
        """
        if goal.name in self.goals:
            raise ValueError(f"Goal with name '{goal.name}' already exists.")

        # Basic expression validation (prefer PuLP expressions)
        if not isinstance(goal.expression, (pulp.LpAffineExpression, pulp.LpVariable, int, float)):
            # We allow flexibility but warn via exception for clarity in this core implementation:
            raise TypeError(
                "Goal.expression must be a PuLP linear expression (LpAffineExpression) or LpVariable or numeric."
            )

        safe = _sanitize_name(goal.name)
        n_name = f"n_{safe}"
        p_name = f"p_{safe}"

        # Create non-negative deviation variables (continuous)
        # Use unique naming in the model registry to avoid collision with user vars:
        if n_name in self.variables or p_name in self.variables:
            # collision is unlikely due to sanitization, but handle defensively
            raise ValueError(f"Deviation variable name collision for goal '{goal.name}'.")

        n_var = pulp.LpVariable(n_name, lowBound=0.0, cat=pulp.LpContinuous)
        p_var = pulp.LpVariable(p_name, lowBound=0.0, cat=pulp.LpContinuous)

        # Register dev vars in the same registry (under original goal.name to preserve user-level keys)
        self.variables[n_name] = n_var
        self.variables[p_name] = p_var

        # Create linking constraint: expression + n - p == target
        linking_name = f"goal_link_{safe}"
        linking_expr = goal.expression + n_var - p_var == float(goal.target)

        # Add constraint to PuLP problem
        self.problem.addConstraint(linking_expr, name=linking_name)

        # Save goal and deviation mapping
        self.goals[goal.name] = goal
        self.dev_vars[goal.name] = (n_var, p_var)

        # Return deviation variables for further usage (if caller wants to include them in objective)
        return (n_var, p_var)
    
    # NEW: Weighted Goal Programming Solver Implementation
    
    # def solve_weighted_goal_programming(self) -> Tuple[Dict[str, float], float]:
    #     """
    #     🆕 Solves a Weighted Goal Programming (WGP) model.
    #     Objective:
    #         Minimize Σ (w_i⁻ * n_i + w_i⁺ * p_i)
    #     Returns:
    #         Tuple[Dict[str, float], float]: (variable_values, objective_value)
    #     """
    #     # Build the weighted deviation-based objective
    #     objective_terms = []
    #     for goal_name, (goal, n_dev, p_dev) in self.goals.items():
    #         # Each goal contributes weighted deviations
    #         objective_terms.append(goal.weight * (n_dev + p_dev))

    #     self.model += pulp.lpSum(objective_terms), "Weighted_Objective"

    #     # Solve using PuLP's default solver
    #     self.model.solve(pulp.PULP_CBC_CMD(msg=False))

    #     # Collect results
    #     variable_values = {v.name: v.varValue for v in self.model.variables()}
    #     objective_value = pulp.value(self.model.objective)
    #     return variable_values, objective_value

    def solve_weighted(
        self,
        goal_weights: Optional[Dict[str, Tuple[float, float]]] = None,
        cost_expr: Optional[pulp.LpAffineExpression] = None,
        cost_weight: float = 0.0,
        solver: Optional[pulp.PULP_CBC_CMD] = None,
        keep_existing_objective: bool = False,
    ) -> Dict[str, Any]:
        """Build and solve a Weighted Goal Programming (WGP) objective.

        Objective (general form):
            Minimize  cost_weight * cost_expr
                    + Σ_goals (w_minus[g] * n_g + w_plus[g] * p_g)

        Args:
            goal_weights: mapping goal_name -> (w_minus, w_plus).
                          If None, uses goal.weight for both sides.
            cost_expr: optional PuLP linear expression for cost term (e.g., Σ c_i x_i)
            cost_weight: multiplier for the cost term (default 0.0)
            solver: optional PuLP solver object; if None, uses default CBC solver.
            keep_existing_objective: if True, do not overwrite any objective already set.

        Returns:
            dict with keys:
                - "status": pulp.LpStatus[problem.status]
                - "objective": numeric objective value (or None if infeasible)
                - "variables": mapping variable_name -> value
                - "deviations": mapping goal_name -> (n_value, p_value)
        """
        # Build objective
        if not keep_existing_objective:
            # Remove existing objective by resetting problem.objective (PuLP quirk)
            # PuLP doesn't provide a direct reset; we add a new objective assignment below.
            pass

        # Use provided solver or default
        if solver is None:
            solver = pulp.PULP_CBC_CMD(msg=False)

        # Assemble weighted deviation sum
        weighted_devs = []
        for gname, goal in self.goals.items():
            if gname not in self.dev_vars:
                raise RuntimeError(f"Goal '{gname}' has no registered deviation variables.")
            n_var, p_var = self.dev_vars[gname]
            if goal_weights and gname in goal_weights:
                w_minus, w_plus = goal_weights[gname]
            else:
                # default: use goal.weight for both sides
                w_minus = float(goal.weight)
                w_plus = float(goal.weight)
            weighted_devs.append(w_minus * n_var)
            weighted_devs.append(w_plus * p_var)

        # cost term
        obj_terms = []
        if cost_expr is not None and cost_weight != 0.0:
            obj_terms.append(cost_weight * cost_expr)

        if weighted_devs:
            obj_terms.append(pulp.lpSum(weighted_devs))

        if not obj_terms:
            raise RuntimeError("No objective terms defined for WGP. Provide goals or cost term.")

        objective = pulp.lpSum(obj_terms)

        # set objective
        self.problem += objective

        # Solve
        result = self.problem.solve(solver)

        status = pulp.LpStatus[self.problem.status]
        obj_value = None
        if status == "Optimal" or status == "Optimal Solution Found":
            try:
                obj_value = pulp.value(self.problem.objective)
            except Exception:
                obj_value = None

        # Collect variable values
        var_values: Dict[str, float] = {}
        for name, var in self.variables.items():
            try:
                var_values[name] = float(var.value())
            except Exception:
                var_values[name] = None

        # Collect deviations
        dev_values: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
        for gname in self.goals.keys():
            n_var, p_var = self.dev_vars[gname]
            n_val = float(n_var.value()) if n_var.value() is not None else None
            p_val = float(p_var.value()) if p_var.value() is not None else None
            dev_values[gname] = (n_val, p_val)

        return {
            "status": status,
            "objective": obj_value,
            "variables": var_values,
            "deviations": dev_values,
        }

    # ----------------------
    # Utility / Introspection
    # ----------------------
    def get_deviation_vars(self, goal_name: str) -> Tuple[pulp.LpVariable, pulp.LpVariable]:
        """Return (n_dev, p_dev) for a registered goal."""
        if goal_name not in self.dev_vars:
            raise KeyError(f"No deviation variables found for goal '{goal_name}'.")
        return self.dev_vars[goal_name]

    def __repr__(self) -> str:
        return f"GLPModel(name={self.name}, vars={len(self.variables)}, goals={len(self.goals)}, constraints={len(self.constraints)})"