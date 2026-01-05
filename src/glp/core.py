# src/glp/core.py
"""
Core structures for Goal Linear Programming (GLP).

This module provides the fundamental building blocks to formulate and solve
Goal Linear Programming problems using PuLP, including:

- Decision variable management
- Variable grouping and group-level bounds
- Goal definitions with deviation variables
- Hard constraints
- Weighted Goal Programming solver

This file is intentionally minimal and generic, forming the foundation
for higher-level problem-specific models (e.g., diet optimization).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple, Iterable, List

import pulp
from pulp import LpVariable

from glp.constraint import Constraint
from glp.enums import ConstraintSense
from glp.goal import Goal


# ============================================================================
# UTILS
# ============================================================================

def _sanitize_name(name: str) -> str:
    """
    Sanitize a user-provided name to make it safe for PuLP.

    Replaces non-alphanumeric characters with underscores and ensures
    the resulting name is valid for use as a PuLP variable or constraint.

    Parameters
    ----------
    name : str
        Original name provided by the user.

    Returns
    -------
    str
        Sanitized name compatible with PuLP.

    Raises
    ------
    ValueError
        If the name cannot be sanitized into a valid identifier.
    """
    s = re.sub(r"\W+", "_", name.strip())
    s = re.sub(r"_+", "_", s)
    if not s:
        raise ValueError("Invalid name after sanitization")
    return s


# ============================================================================
# GLP MODEL
# ============================================================================

class GLPModel:
    """
    Core Goal Linear Programming (GLP) model.

    This class wraps a PuLP ``LpProblem`` and provides a structured API to:

    - Add decision variables (individually or in groups)
    - Organize variables into named groups
    - Apply collective lower/upper bounds to groups of variables
    - Define goals with deviation variables (under- and over-achievement)
    - Add hard constraints
    - Solve the model using Weighted Goal Programming

    The design is intentionally generic and problem-agnostic, allowing
    this core model to be reused across diverse optimization problems.
    """

    def __init__(self, name: str = "glp", minimize: bool = True):
        """
        Initialize a GLP model.

        Parameters
        ----------
        name : str, optional
            Name of the optimization problem.
        minimize : bool, optional
            Whether the objective should be minimized (default True).
        """
        self.name = name
        self.problem = pulp.LpProblem(
            name, pulp.LpMinimize if minimize else pulp.LpMaximize
        )

        self.variables: Dict[str, pulp.LpVariable] = {}
        self.goals: Dict[str, Goal] = {}
        self.constraints: Dict[str, Constraint] = {}
        self.dev_vars: Dict[str, Tuple[pulp.LpVariable, pulp.LpVariable]] = {}
        self.variable_groups: Dict[str, List[str]] = {}

    # ----------------------------------------------------------------------
    # VARIABLE API
    # ----------------------------------------------------------------------
    def add_variable(
        self,
        name: str,
        low_bound: Optional[float] = 0,
        up_bound: Optional[float] = None,
        cat: str = "Continuous",
    ) -> pulp.LpVariable:
        """
        Add a single decision variable to the model.

        If a variable with the same name already exists, the existing variable
        is returned.

        Parameters
        ----------
        name : str
            Name of the decision variable.
        low_bound : float, optional
            Lower bound for the variable (default is 0).
        up_bound : float, optional
            Upper bound for the variable (default is None).
        cat : str, optional
            Variable category: "Continuous", "Integer", or "Binary".

        Returns
        -------
        pulp.LpVariable
            The created (or existing) PuLP variable.
        """

        if name in self.variables:
            return self.variables[name]

        safe = _sanitize_name(name)

        cat_map = {
            "CONTINUOUS": pulp.LpContinuous,
            "INTEGER": pulp.LpInteger,
            "BINARY": pulp.LpBinary,
        }
        pulp_cat = cat_map.get(cat.upper(), pulp.LpContinuous)

        var = pulp.LpVariable(safe, lowBound=low_bound, upBound=up_bound, cat=pulp_cat)
        self.variables[name] = var
        return var

    # ----------------------------------------------------------------------
    # MULTI-VARIABLE API
    # ----------------------------------------------------------------------
    def add_variables(
        self,
        names: Iterable[str],
        low_bound: Optional[float] = 0,
        up_bound: Optional[float] = None,
        cat: str = "Continuous",
        group: Optional[str] = None,
    ) -> Dict[str, pulp.LpVariable]:
        """
        Add multiple decision variables at once.

        All variables share the same bounds and category. Optionally, the
        variables can be assigned to a named group for later group-level
        operations (e.g., collective bounds).

        Parameters
        ----------
        names : iterable of str
            Names of the variables to be added.
        low_bound : float, optional
            Lower bound for all variables.
        up_bound : float, optional
            Upper bound for all variables.
        cat : str, optional
            Variable category ("Continuous", "Integer", "Binary").
        group : str, optional
            Name of a variable group to assign these variables to.

        Returns
        -------
        dict
            Mapping from variable name to PuLP variable.
        """

        created = {}
        for name in names:
            created[name] = self.add_variable(
                name,
                low_bound=low_bound,
                up_bound=up_bound,
                cat=cat,
            )

        if group is not None:
            self.add_to_group(group, names)

        return created

    # ----------------------------------------------------------------------
    # GROUP MANAGEMENT
    # ----------------------------------------------------------------------
    def add_to_group(self, group: str, variables: Iterable[str]) -> None:
        """
        Add existing variables to a named variable group.

        Variable groups allow collective operations such as applying
        group-level lower and upper bounds.

        Parameters
        ----------
        group : str
            Name of the group.
        variables : iterable of str
            Names of variables to add to the group.

        Raises
        ------
        KeyError
            If any variable does not exist in the model.
        """

        if group not in self.variable_groups:
            self.variable_groups[group] = []

        for var in variables:
            if var not in self.variables:
                raise KeyError(f"Variable '{var}' not found in model")
            if var not in self.variable_groups[group]:
                self.variable_groups[group].append(var)

    # ----------------------------------------------------------------------
    # GROUP BOUNDING
    # ----------------------------------------------------------------------
    def add_group_bounds(
        self,
        group: str,
        lower: Optional[float] = None,
        upper: Optional[float] = None,
    ) -> None:
        """
        Apply collective lower and/or upper bounds to a group of variables.

        Internally, this creates constraints of the form:
            sum(group_variables) >= lower
            sum(group_variables) <= upper

        Parameters
        ----------
        group : str
            Name of the variable group.
        lower : float, optional
            Collective lower bound for the group.
        upper : float, optional
            Collective upper bound for the group.

        Raises
        ------
        KeyError
            If the specified group does not exist.
        """

        if group not in self.variable_groups:
            raise KeyError(f"Group '{group}' not defined")

        vars_in_group = [self.variables[v] for v in self.variable_groups[group]]
        total = pulp.lpSum(vars_in_group)

        if lower is not None:
            self.problem += total >= lower, f"{group}_LL"

        if upper is not None:
            self.problem += total <= upper, f"{group}_UL"

    # ----------------------------------------------------------------------
    # CONSTRAINT API
    # ----------------------------------------------------------------------
    def add_constraint(self, c: Constraint) -> None:
        """
        Add a hard constraint to the model.

        Hard constraints must always be satisfied; infeasible models will
        fail unless relaxed externally.

        Parameters
        ----------
        c : Constraint
            Constraint object defining the expression, sense, and RHS.

        Raises
        ------
        ValueError
            If a constraint with the same name already exists.
        """

        if c.name in self.constraints:
            raise ValueError(f"constraint '{c.name}' exists")

        safe = _sanitize_name(c.name)

        if c.sense == ConstraintSense.LE:
            constr = c.expression <= c.rhs
        elif c.sense == ConstraintSense.GE:
            constr = c.expression >= c.rhs
        elif c.sense == ConstraintSense.EQ:
            constr = c.expression == c.rhs
        else:
            raise ValueError("invalid constraint sense")

        self.problem.addConstraint(constr, name=safe)
        self.constraints[c.name] = c

    # ----------------------------------------------------------------------
    # GOAL API
    # ----------------------------------------------------------------------
    def add_goal(self, g: Goal) -> Tuple[LpVariable, LpVariable]:
        """
        Add a goal to the model and create its deviation variables.

        For a goal of the form:
            expression ≈ target

        The following linking constraint is added:
            expression + n - p = target

        where:
            n = under-achievement deviation (>= 0)
            p = over-achievement deviation (>= 0)

        These deviation variables are later penalized in the objective
        during Weighted Goal Programming.

        Parameters
        ----------
        g : Goal
            Goal definition including expression, target, and weight.

        Returns
        -------
        tuple
            (negative_deviation_variable, positive_deviation_variable)

        Raises
        ------
        ValueError
            If a goal with the same name already exists.
        """

        if g.name in self.goals:
            raise ValueError(f"goal '{g.name}' exists")

        safe = _sanitize_name(g.name)

        n_var = pulp.LpVariable(f"n_{safe}", lowBound=0)
        p_var = pulp.LpVariable(f"p_{safe}", lowBound=0)

        self.variables[f"n_{safe}"] = n_var
        self.variables[f"p_{safe}"] = p_var

        linking = g.expression + n_var - p_var == float(g.target)
        self.problem.addConstraint(linking, name=f"goal_link_{safe}")

        self.goals[g.name] = g
        self.dev_vars[g.name] = (n_var, p_var)

        return n_var, p_var

    # ----------------------------------------------------------------------
    # SOLVE: WEIGHTED GOAL PROGRAMMING
    # ----------------------------------------------------------------------
    def solve_weighted(
        self,
        goal_weights: Optional[Dict[str, Tuple[float, float]]] = None,
        cost_expr: Optional[pulp.LpAffineExpression] = None,
        cost_weight: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Solve the model using Weighted Goal Programming (WGP).

        The objective minimized is:
            cost_weight * cost_expr
            + sum(w_minus * n_i + w_plus * p_i) over all goals

        Parameters
        ----------
        goal_weights : dict, optional
            Mapping: goal_name -> (weight_under, weight_over).
            If not provided, each goal's default weight is used.
        cost_expr : pulp.LpAffineExpression, optional
            Linear expression representing cost or another primary objective.
        cost_weight : float, optional
            Weight applied to the cost expression.

        Returns
        -------
        dict
            Dictionary containing:
            - status: solver status string
            - variables: values of all decision and deviation variables
            - deviations: (n, p) values for each goal
            - objective: final objective value
        """

        terms = []

        if cost_expr is not None and cost_weight != 0:
            terms.append(cost_weight * cost_expr)

        for gname, g in self.goals.items():
            n, p = self.dev_vars[gname]

            if goal_weights and gname in goal_weights:
                w_minus, w_plus = goal_weights[gname]
            else:
                w_minus = g.weight
                w_plus = g.weight

            terms.append(w_minus * n)
            terms.append(w_plus * p)

        if not terms:
            raise RuntimeError("No objective terms provided")

        self.problem += pulp.lpSum(terms)

        solver = pulp.PULP_CBC_CMD(msg=False)
        self.problem.solve(solver)

        status = pulp.LpStatus[self.problem.status]

        var_vals = {
            name: (None if v.value() is None else float(v.value()))
            for name, v in self.variables.items()
        }

        dev_vals = {
            gname: (
                float(self.dev_vars[gname][0].value()),
                float(self.dev_vars[gname][1].value()),
            )
            for gname in self.goals
        }

        obj = None
        try:
            obj = float(pulp.value(self.problem.objective))
        except Exception:
            pass

        return {
            "status": status,
            "variables": var_vals,
            "deviations": dev_vals,
            "objective": obj,
        }

    # ----------------------------------------------------------------------
    def __repr__(self) -> str:
        """
        Return a concise string representation of the GLPModel.
        """
        return (
            f"GLPModel(vars={len(self.variables)}, "
            f"goals={len(self.goals)}, "
            f"groups={len(self.variable_groups)})"
        )