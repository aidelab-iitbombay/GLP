# tests/test_core.py
import pytest
import pulp

from glp.core import Goal, Constraint, GLPModel, GoalSense, ConstraintSense


def test_goal_dataclass_defaults_and_validation():
    # basic instantiation
    x = pulp.LpVariable("x", lowBound=0)
    g = Goal(name="protein", expression=2 * x, target=50.0)
    assert g.name == "protein"
    assert g.weight == 1.0
    assert g.priority == 1
    assert g.sense == GoalSense.ATTAIN

    # negative weight -> ValueError
    with pytest.raises(ValueError):
        Goal(name="bad", expression=1 * x, target=10.0, weight=-1.0)


def test_constraint_dataclass_and_validation():
    x = pulp.LpVariable("y", lowBound=0)
    c = Constraint(name="cap", expression=3 * x, sense=ConstraintSense.LE, rhs=100)
    assert c.name == "cap"
    assert c.sense == ConstraintSense.LE
    assert c.rhs == 100


def test_glpmodel_add_variable_and_constraint_and_goal():
    model = GLPModel(name="test_model")
    # add variables
    v1 = model.add_variable("rice", low_bound=0.0)
    v2 = model.add_variable("lentils", low_bound=0.0)
    assert "rice" in model.variables
    assert "lentils" in model.variables
    assert isinstance(v1, pulp.LpVariable)

    # add a constraint: 10*rice + 5*lentils <= 100
    expr = 10 * v1 + 5 * v2
    c = Constraint(name="cap_total", expression=expr, sense=ConstraintSense.LE, rhs=100.0)
    model.add_constraint(c)
    # check that constraint name exists in PuLP problem constraints (sanitized)
    assert any("cap_total" in name for name in model.problem.constraints.keys())

    # add goal: protein = 50 (where protein = 2*rice + 10*lentils)
    protein_expr = 2 * v1 + 10 * v2
    goal = Goal(name="protein_goal", expression=protein_expr, target=50.0)
    n_var, p_var = model.add_goal(goal)
    # check dev vars are registered (sanitized names stored in variables mapping)
    assert "n_protein_goal" in model.variables
    assert "p_protein_goal" in model.variables
    # check linking constraint exists
    assert any("goal_link_protein_goal" in name for name in model.problem.constraints.keys())


def test_duplicate_goal_name_raises():
    model = GLPModel("dup_test")
    v = model.add_variable("a", low_bound=0)
    g1 = Goal(name="g", expression=1 * v, target=10.0)
    model.add_goal(g1)
    # second add should raise
    g2 = Goal(name="g", expression=1 * v, target=5.0)
    with pytest.raises(ValueError):
        model.add_goal(g2)
