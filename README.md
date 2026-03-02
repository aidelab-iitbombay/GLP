# 📦 PyGuLP — Python Package for Goal Linear Programming

**PyGuLP** is a Python package for **Goal Linear Programming (GLP)** with an initial focus on **Weighted Goal Programming (WGP)**.

The package is designed for **multi-target linear optimization problems**, where several desired outcomes must be balanced simultaneously under linear constraints. Such problems commonly arise in health and public health planning, environmental management, resource allocation, and policy analysis.

PyGuLP is **domain-agnostic** and can be applied wherever linear models with multiple targets are appropriate.

Full documentation:  
https://www.kcdh.iitb.ac.in/~kshitij/browser/assets/glp-docs/index.html

---

## Installation

    pip install pygulp

### Dependencies

Required:
- pulp

Optional:
- pandas
- matplotlib

---

## Project structure

    src/glp/
    ├── core.py        # GLPModel and solver logic
    ├── goal.py        # Goal dataclass
    ├── constraint.py  # Constraint dataclass
    ├── enums.py       # GoalSense and ConstraintSense enums
    └── __init__.py

---

## What is Goal Linear Programming?

Goal Linear Programming (GLP) extends classical Linear Programming (LP) by allowing **multiple targets** to be handled within a single linear optimization model.

In standard LP, a problem optimizes one objective function subject to constraints. In many real-world planning problems, however, the task is to **approach several targets simultaneously** while maintaining feasibility.

GLP introduces **deviation variables** that explicitly measure how far the achieved solution deviates from each target. The objective then minimizes these deviations according to their relative importance.

---

## Goals, expressions, and deviation variables

Each goal specifies:

- what quantity is being measured
- what value is desired
- how important it is to meet that value

For each goal, GLP constructs:

    expression + d- - d+ = target

Where:

- expression — linear function of decision variables
- target — aspiration level
- d- — under-achievement
- d+ — over-achievement

With constraints:

    d- >= 0
    d+ >= 0

Only one of `d-` or `d+` is positive in an optimal solution.

---

## Weighted Goal Programming Objective

In Version 0.0.1, PyGuLP implements:

    minimize  Σ w * (d- + d+)

Where:

- w is a non-negative weight assigned to each goal
- larger weights enforce closer adherence to that target

Weights affect trade-offs but do not affect feasibility.

---

## Core modeling elements

### Decision Variables
Standard LP variables (continuous, integer, binary).

### Constraints
Feasibility restrictions of the form:

    a1x1 + a2x2 + ... + anxn <= / = / >= b

Constraints define feasibility only — they do not create deviation variables.

### Goals
Structured modeling objects consisting of:

- linear expression
- target value
- goal sense (ATTAIN in v0.1.2)
- weight

Deviation variables are created automatically when goals are added.

---

## Current features (Version 0.1.2)

- Weighted Goal Programming (WGP)
- Automatic creation of deviation variables (d-, d+)
- Automatic goal-linking constraint construction
- Standard LP constraints (≤, =, ≥)
- Optional linear cost term
- Transparent PuLP backend
- Deterministic CBC solver support

---

## Solver Support

PyGuLP uses **PuLP** as its modeling layer.

Default solver: **CBC** (bundled with PuLP)

---

## Minimal Multi-Goal Example

    from glp.core import GLPModel
    from glp.goal import Goal
    from glp.constraint import Constraint
    from glp.enums import ConstraintSense, GoalSense

    model = GLPModel("multi_goal_example")

    x = model.add_variable("Rice", low_bound=0)
    y = model.add_variable("Dal", low_bound=0)

    budget = Constraint(
        name="budget",
        expression=2*x + 3*y,
        sense=ConstraintSense.LE,
        rhs=100
    )
    model.add_constraint(budget)

    energy_goal = Goal(
        name="energy",
        expression=5*x + 10*y,
        target=200,
        sense=GoalSense.ATTAIN,
        weight=1.0
    )

    protein_goal = Goal(
        name="protein",
        expression=2*x + 8*y,
        target=50,
        sense=GoalSense.ATTAIN,
        weight=2.0
    )

    model.add_goal(energy_goal)
    model.add_goal(protein_goal)

    result = model.solve_weighted()

    print(result["status"])
    print(result["variables"])
    print(result["deviations"])
    print(result["objective"])

---

## Output Structure

The solver returns a structured dictionary containing:

- status
- variables
- deviations
- objective

Each deviation entry is:

    (d_minus, d_plus)

---

## Worked Multi-Goal Examples

More detailed worked examples are available here:

https://github.com/aidelab-iitbombay/GLP/tree/Worked_examples_using_GLP

---

## Typical Use Cases

- Health and public health planning
- Environmental and resource allocation
- Policy target balancing
- Coverage vs. cost trade-offs
- Teaching and research in optimization

---

## Reproducibility and Transparency

- All models remain standard linear programs
- No hidden transformations
- Full access to underlying PuLP model
- Deterministic solutions given solver settings

---

## License

MIT License
