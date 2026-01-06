# 📦 PyGuLP — Python Package for Goal Linear Programming

**PyGuLP** is a Python package for **Goal Linear Programming (GLP)** with an initial focus on **Weighted Goal Programming (WGP)**.

The package is intended for **multi-target linear optimization problems**, where several desired outcomes must be balanced simultaneously under linear constraints. Such problems commonly arise in health and public health planning, environmental management, resource allocation, and policy analysis. The package itself is **domain-agnostic** and can be applied wherever linear models with multiple targets are appropriate.

---

## What is Goal Linear Programming?

Goal Linear Programming (GLP) is an extension of classical Linear Programming (LP) that allows multiple, potentially conflicting targets to be handled within a single linear optimization model.

In standard LP, a problem is formulated to optimize a single objective function subject to a set of constraints. In many real-world planning problems, however, the central question is not how to optimize one quantity, but how to **achieve several targets as closely as possible** while still satisfying feasibility conditions.

GLP addresses this by introducing **deviation variables** that explicitly measure how far the achieved solution deviates from each target. The objective function then minimizes these deviations according to their relative importance.

---

## Conceptual overview

Traditional linear optimization optimizes a single objective function subject to a set of constraints.

GLP makes these trade-offs explicit by introducing *deviation variables* that measure how far the achieved solution departs from each target, and by minimizing these deviations according to their relative importance.

---

## Goals, expressions, and deviation variables

Each goal in a GLP model specifies:

- what quantity is being measured  
- what value is desired  
- how important it is to meet that value  

To formalize this, GLP constructs the following relationship for each goal:


expression + d- - d+ = target

where:

- **expression** is a linear function of decision variables  
- **target** is the desired aspiration level  
- **d-** measures under-achievement of the target  
- **d+** measures over-achievement of the target  

The deviation variables satisfy:

    d- >= 0,   d+ >= 0


Only one of `d-` or `d+` will be positive in an optimal solution, indicating whether the achieved value falls below or exceeds the target.

---

## What is meant by an expression?

An **expression** defines how the achieved value of a goal is computed from the model’s decision variables.

Formally, an expression is a **linear combination of decision variables**:

    expression = a1*x1 + a2*x2 + ... + an*xn

where:

- x1, x2, ..., xn are decision variables
- a1, a2, ..., an are known coefficients


The expression represents the achieved value of a quantity of interest as implied by the current choice of decision variables. The goal-linking equation then compares this achieved value to the specified target and measures any mismatch using deviation variables.

Expressions do not encode priorities or penalties. They only define *how the model computes a quantity*. Trade-offs are handled entirely through deviation variables and their associated weights.

Expressions can be as complex as multiple decision variable with associated co-efficients as shown above or as simple as a sum of two decision variables.

---

## Weights and the optimization objective

Weights quantify the relative importance of goals.

In Weighted Goal Programming (as implemented in version 0.0.1), the optimization problem minimizes the weighted sum of deviations across all goals:

minimize sum( w * (d- + d+) )
where:

- **w** is the non-negative weight assigned to a goal  
- larger weights enforce closer adherence to the corresponding target  

Weights do not affect feasibility. They only determine how the solver trades off deviations between competing goals.

This formulation preserves linearity and keeps priorities explicit and interpretable.

---

## Core modeling elements

### Decision variables

Decision variables represent the quantities the model is allowed to choose. They are standard linear programming variables and may be:

- continuous  
- integer  
- binary  

Decision variables define the degrees of freedom of the optimization problem.

---

### Constraints

Constraints restrict the feasible region of the problem and must be satisfied
by all solutions.

They take the standard linear form:

a1x1 + a2x2 + ... + an*xn <= / = / >= b

where `x1..xn` are decision variables and `a1..an` are fixed coefficients.

Constraints represent non-negotiable conditions such as limits, capacities, or
regulatory bounds. Constraints define feasibility and do not introduce deviation
variables.

---

### Goals

Goals represent desired outcomes or aspiration levels that the model attempts to achieve as closely as possible.

A goal consists of:

- a linear expression  
- a numeric target value  
- a goal sense (attainment in version 0.0.1)  
- a weight indicating importance  

Goals may be under- or over-achieved, with deviations explicitly measured by `d-` and `d+` and penalized in the objective.

In version **0.0.1**, all goals are linked using the attainment form:

expression + d- - d+ = target

The direction and magnitude of deviation are governed entirely by the weights.

---

### Weights

Weights quantify the relative importance of goals.

A higher weight implies that the optimization prioritizes bringing the achieved value closer to the target, allowing less deviation relative to other goals. Weights do not affect feasibility; they only govern trade-offs among goals.

---

## Current features (Version 0.0.1)

- Weighted Goal Programming (WGP)
- Automatic creation of under- and over-deviation variables (d-, d+)
- Automatic construction of goal-linking constraints
- Constraints with senses: ≤, =, ≥
- Optional inclusion of a linear cost term in the objective
- Transparent linear programming backend via PuLP
- Deterministic solving with the CBC solver

---

## Solver support

PyGuLP uses **PuLP** as its modeling layer.

- Default solver: **CBC** (bundled with PuLP)

---

## Output

The solver returns a structured result containing:

- solver status  
- decision variable values  
- per-goal deviations (\( d^{-}, d^{+} \))  
- final objective value  

This structure supports diagnostics, scenario comparison, and sensitivity analysis.

---

## Installation

```bash
pip install glp
```

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

## Essential classes

### GLPModel

`GLPModel` is the central wrapper around a PuLP `LpProblem`. It maintains registries for decision variables, constraints, goals, and deviation variables.

Key responsibilities include:

- registering decision variables
- adding feasibility constraints
- adding goals and constructing deviation variables
- building and solving the weighted goal programming objective

### Goal

A `Goal` defines one target to be approached:

- `name`: unique identifier  
- `expression`: PuLP linear expression  
- `target`: numeric target value  
- `weight`: importance (nonnegative)  

Defaults:

- `weight = 1.0`
- `priority = 1`
- `sense = GoalSense.ATTAIN`

The target is treated as a fixed aspiration level, with deviations captured by
d^- and d^+.

### Constraint

A `Constraint` defines a feasibility restriction:

- `name`: unique identifier  
- `expression`: PuLP linear expression  
- `sense`: <=, =, or >=  
- `rhs`: numeric right-hand side  

---

## Quick start

### Create a model

    from glp.core import GLPModel
    model = GLPModel("example_model")

### Add decision variables

    x = model.add_variable("Rice", low_bound=0)
    y = model.add_variable("Dal", low_bound=0)

Variables may be continuous, integer, or binary via the `cat` argument.

### Add constraints

    from glp.constraint import Constraint
    from glp.enums import ConstraintSense

    budget = Constraint(
        name="budget",
        expression=2*x + 3*y,
        sense=ConstraintSense.LE,
        rhs=100
    )

    model.add_constraint(budget)

### Add goals

    from glp.goal import Goal
    from glp.enums import GoalSense

    energy_goal = Goal(
        name="energy",
        expression=5*x + 10*y,
        target=200,
        sense=GoalSense.ATTAIN,
        weight=1.0
    )

    model.add_goal(energy_goal)

When a goal is added, GLP automatically creates the deviation variables d^- and
d^+ and the corresponding goal-linking constraint.

### Solve the model

    result = model.solve_weighted()


## Inspecting results
    result["status"]
    result["variables"]
    result["deviations"]
    result["objective"]


Each entry in `result["deviations"]` is a tuple:

    (d_minus, d_plus)

indicating under- and over-achievement of the corresponding goal.

---

## Typical use cases

- Health and public health planning  
- Environmental and resource allocation  
- Coverage versus cost trade-offs  
- Policy target balancing  
- Teaching and research in optimization  

---

## Reproducibility and transparency

- All models are standard linear programs
- No heuristics or hidden transformations
- Full access to the underlying PuLP model
- Deterministic solutions given solver settings

---

## License

MIT License
