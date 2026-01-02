import os
import sys

import pulp
import pytest

# Ensure src is on path when running tests from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from glp.constraint import Constraint
from glp.core import GLPModel
from glp.enums import ConstraintSense, GoalSense
from glp.goal import Goal

# ----------------------------
# Basic Core Component Tests
# ----------------------------


def test_goal_dataclass_defaults_and_validation() -> None:
    """Check Goal dataclass default values and weight validation."""
    x = pulp.LpVariable("x", lowBound=0)
    g = Goal(name="protein", expression=2 * x, target=50.0)
    assert g.name == "protein"
    assert g.weight == 1.0
    assert g.priority == 1
    assert g.sense == GoalSense.ATTAIN

    # negative weight -> should raise ValueError
    with pytest.raises(ValueError):
        Goal(name="bad", expression=1 * x, target=10.0, weight=-1.0)


def test_constraint_dataclass_and_validation() -> None:
    """Check Constraint dataclass creation."""
    x = pulp.LpVariable("y", lowBound=0)
    c = Constraint(name="cap", expression=3 * x, sense=ConstraintSense.LE, rhs=100)
    assert c.name == "cap"
    assert c.sense == ConstraintSense.LE
    assert c.rhs == 100


def test_glpmodel_add_variable_and_constraint_and_goal() -> None:
    """Ensure GLPModel variable, constraint, and goal additions work correctly."""
    model = GLPModel(name="test_model")
    # add variables
    v1 = model.add_variable("rice", low_bound=0.0)
    v2 = model.add_variable("lentils", low_bound=0.0)
    assert "rice" in model.variables
    assert "lentils" in model.variables
    assert isinstance(v1, pulp.LpVariable)

    # add constraint: 10*rice + 5*lentils <= 100
    expr = 10 * v1 + 5 * v2
    c = Constraint(
        name="cap_total", expression=expr, sense=ConstraintSense.LE, rhs=100.0
    )
    model.add_constraint(c)
    assert any("cap_total" in name for name in model.problem.constraints.keys())

    # add goal: protein = 50 (where protein = 2*rice + 10*lentils)
    protein_expr = 2 * v1 + 10 * v2
    goal = Goal(name="protein_goal", expression=protein_expr, target=50.0)
    n_var, p_var = model.add_goal(goal)
    assert "n_protein_goal" in model.variables
    assert "p_protein_goal" in model.variables
    assert any(
        "goal_link_protein_goal" in name for name in model.problem.constraints.keys()
    )


def test_duplicate_goal_name_raises() -> None:
    """Check duplicate goal names raise an error."""
    model = GLPModel("dup_test")
    v = model.add_variable("a", low_bound=0)
    g1 = Goal(name="g", expression=1 * v, target=10.0)
    model.add_goal(g1)
    g2 = Goal(name="g", expression=1 * v, target=5.0)
    with pytest.raises(ValueError):
        model.add_goal(g2)


# ----------------------------
# Weighted Goal Programming (WGP) Test
# ----------------------------


def test_simple_wgp_two_goals() -> None:
    """
    Small representative Weighted Goal Programming (WGP) problem:
        Variables: x1 >= 0, x2 >= 0
        Goals:
            g1: x1 + x2 = 10
            g2: x1 = 7
        Weights: equal weights for all deviations
    Expected optimal solution:
        x1 = 7, x2 = 3  (both goals satisfied exactly)
        All deviations = 0
        Objective = 0
    """
    model = GLPModel(name="test_wgp")
    x1 = model.add_variable("x1", low_bound=0.0)
    x2 = model.add_variable("x2", low_bound=0.0)

    # Define goals
    g1 = Goal(
        name="g1", expression=x1 + x2, target=10.0, sense=GoalSense.ATTAIN, weight=1.0
    )
    g2 = Goal(name="g2", expression=x1, target=7.0, sense=GoalSense.ATTAIN, weight=1.0)

    model.add_goal(g1)
    model.add_goal(g2)

    # Solve Weighted Goal Programming model
    res = model.solve_weighted()

    # Check solver status
    assert res["status"] in ("Optimal", "Optimal Solution Found")

    # Check variable results
    vars_out = res["variables"]
    assert pytest.approx(vars_out["x1"], rel=1e-6) == 7.0
    assert pytest.approx(vars_out["x2"], rel=1e-6) == 3.0

    # Check deviations (should be all zero)
    devs = res["deviations"]
    for n_val, p_val in devs.values():
        assert pytest.approx(n_val, rel=1e-6) == 0.0
        assert pytest.approx(p_val, rel=1e-6) == 0.0

    # Objective should be ~0
    assert pytest.approx(res["objective"], rel=1e-6) == 0.0


# if __name__ == "__main__":
#     unittest.main()
