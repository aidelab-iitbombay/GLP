# src/glp/core.py
"""
Core structures for Goal Linear Programming (GLP).

Contains:
- GoalSense, ConstraintSense enums
- Goal, Constraint dataclasses
- GLPModel (wrapper over PuLP)
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

import pulp
from pulp import LpVariable

from glp.constraint import Constraint
from glp.enums import ConstraintSense
from glp.goal import Goal

# ============================================================================
# UTILS
# ============================================================================


def _sanitize_name(name: str) -> str:
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
    Central GLP model wrapper around PuLP.
    Handles:
    - variable registry
    - goal registry
    - dev vars
    - constraint registry
    - weighted goal programming solve
    """

    def __init__(self, name: str = "glp", minimize: bool = True):
        self.name = name
        self.problem = pulp.LpProblem(
            name, pulp.LpMinimize if minimize else pulp.LpMaximize
        )

        self.variables: Dict[str, pulp.LpVariable] = {}
        self.goals: Dict[str, Goal] = {}
        self.constraints: Dict[str, Constraint] = {}
        self.dev_vars: Dict[str, Tuple[pulp.LpVariable, pulp.LpVariable]] = {}

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
    # CONSTRAINT API
    # ----------------------------------------------------------------------
    def add_constraint(self, c: Constraint) -> None:
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
    # GOAL API (creates deviation vars)
    # ----------------------------------------------------------------------
    def add_goal(self, g: Goal) -> Tuple[LpVariable, LpVariable]:
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
    # SOLVE: Weighted Goal Programming
    # ----------------------------------------------------------------------
    def solve_weighted(
        self,
        goal_weights: Optional[Dict[str, Tuple[float, float]]] = None,
        cost_expr: Optional[pulp.LpAffineExpression] = None,
        cost_weight: float = 0.0,
    ) -> Dict[str, Any]:

        terms = []

        # (1) cost term
        if cost_expr is not None and cost_weight != 0:
            terms.append(cost_weight * cost_expr)

        # (2) weighted deviations
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
        return f"GLPModel(vars={len(self.variables)}, goals={len(self.goals)})"
