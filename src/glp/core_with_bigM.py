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
    s = re.sub(r"\W+", "_", name.strip())
    s = re.sub(r"_+", "_", s)
    if not s:
        raise ValueError("Invalid name after sanitization")
    return s


# ============================================================================
# 🆕 ELASTIC CONSTRAINT (BIG-M FEASIBILITY)
# ============================================================================

class ElasticConstraint:
    """
    Represents an elastic (soft) constraint using Big-M feasibility relaxation.
    """

    def __init__(
        self,
        name: str,
        expression: Any,
        sense: ConstraintSense,
        rhs: float,
        penalty: float = 1e5,
    ):
        if penalty <= 0:
            raise ValueError("penalty must be positive")

        self.name = name
        self.expression = expression
        self.sense = sense
        self.rhs = rhs
        self.penalty = penalty


# ============================================================================
# GLP MODEL
# ============================================================================

class GLPModel:
    """
    Central GLP model wrapper around PuLP.

    Handles:
    - variable registry
    - variable groups
    - goal registry
    - deviation variables
    - constraint registry
    - elastic (Big-M) feasibility constraints
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
        self.variable_groups: Dict[str, List[str]] = {}

        # 🆕 Big-M / Elastic constraint storage
        self.elastic_constraints: Dict[str, ElasticConstraint] = {}
        self.violation_vars: Dict[str, pulp.LpVariable] = {}

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
        Add a single decision variable.
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
        Add multiple variables at once.
        Optionally assign them to a group.
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
        Add existing variables to a named group.
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
        Add collective lower/upper bounds for a group of variables.
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
    # 🆕 ELASTIC CONSTRAINT API (BIG-M)
    # ----------------------------------------------------------------------
    def add_elastic_constraint(self, c: ElasticConstraint) -> LpVariable:
        """
        Add a Big-M elastic (feasibility) constraint.
        """

        if c.name in self.elastic_constraints:
            raise ValueError(f"elastic constraint '{c.name}' exists")

        safe = _sanitize_name(c.name)

        v = pulp.LpVariable(f"v_{safe}", lowBound=0)
        self.variables[f"v_{safe}"] = v

        if c.sense == ConstraintSense.LE:
            constr = c.expression <= c.rhs + v
        elif c.sense == ConstraintSense.GE:
            constr = c.expression >= c.rhs - v
        elif c.sense == ConstraintSense.EQ:
            constr = c.expression + v == c.rhs
        else:
            raise ValueError("invalid constraint sense")

        self.problem.addConstraint(constr, name=f"elastic_{safe}")

        self.elastic_constraints[c.name] = c
        self.violation_vars[c.name] = v

        return v

    # ----------------------------------------------------------------------
    # GOAL API
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
    # SOLVE: WEIGHTED GOAL PROGRAMMING + BIG-M
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

        # (2) goal deviations
        for gname, g in self.goals.items():
            n, p = self.dev_vars[gname]

            if goal_weights and gname in goal_weights:
                w_minus, w_plus = goal_weights[gname]
            else:
                w_minus = g.weight
                w_plus = g.weight

            terms.append(w_minus * n)
            terms.append(w_plus * p)

        # (3) 🆕 elastic constraint penalties (Big-M)
        for cname, c in self.elastic_constraints.items():
            terms.append(c.penalty * self.violation_vars[cname])

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
        return (
            f"GLPModel(vars={len(self.variables)}, "
            f"goals={len(self.goals)}, "
            f"groups={len(self.variable_groups)})"
        )
