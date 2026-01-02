# 📦 GLP — Goal Linear Programming (Weighted Goal Programming)

**GLP** is a lightweight Python package for **Goal Linear Programming (GLP)** with a focus on **Weighted Goal Programming (WGP)**, built on top of **PuLP**.

The package is designed for researchers and practitioners who need to solve **multi-objective linear optimization problems** where several targets must be balanced simultaneously under hard constraints—common in health, public health, nutrition, and resource allocation problems.

---
# What is Goal Linear Programming

**GLP** is a variant of Linear Programming which retains the linear structure of LP but allows conflicting constraints to be managed by introducing "deviational variables" and priority weights. Priority weights are values assigned to different goals of a GLP problem, where a higher weight implies that the model must prioritize that goal more by bringing its final value closest to the assigned goal.
## Conceptual overview

Traditional linear optimization optimizes a **single objective**.  
**Goal Programming** instead minimizes **deviations from desired targets**, recognizing that not all goals can usually be satisfied simultaneously.

For each goal, GLP constructs the relationship:

```
expression + n - p = target
```

Where:

| Term        | Meaning                                   |
|-------------|--------------------------------------------|
| expression  | Linear function of decision variables      |
| n           | Under-achievement (negative deviation)     |
| p           | Over-achievement (positive deviation)      |
| target      | Desired aspiration level                   |

### Weighted Goal Programming objective

The solver minimizes:

```
Σ (w- · n + w+ · p)
```

where weights reflect the relative importance of meeting each goal.

---

## Version **0.0.1** implements:

- **Weighted Goal Programming (WGP)**
- Automatic creation of **under- and over-deviation variables**
- Support for goal types:
  - equality / attainment to a value (target)
  - achieving lower than a value
  - achieving higher than a value
  - achieving percent of a value
Goals can be considered soft targets which can be under or over achieved based on certain weights assigned

## Constraints:

- The package builds constraints using the class
- Constraints can also be expreseed in terms of less than more than equal to
- A point explaining how are they different from goals

## Solver
- Linear programming backend via **PuLP**
- Default open-source solver: **CBC** (Can we change default solver, if so which are supported? )

## Output
- Structured solution output:
  - decision variable values
  - per-goal deviations
  - objective value and solver status
 
---
## Dependencies

- **pulp** (required)

Optional (for examples and analysis):

- **pandas**
- **matplotlib**

## Project structure

```
src/glp/
├── core.py        # GLPModel and solver logic
├── goal.py        # Goal dataclass
├── constraint.py  # Constraint dataclass
├── enums.py       # GoalSense and ConstraintSense enums
└── __init__.py
```
## Quick Start Guide
---
## Installation

```bash
pip install glp
```
---

## Core API

### Create a model

```python
from glp.core import GLPModel

model = GLPModel("diet_model")
```

---

### Add decision variables

```python
x = model.add_variable("Rice", low_bound=0)
y = model.add_variable("Dal", low_bound=0)
```

Variables may be continuous, integer, or binary via the `cat` argument.

---

### Add hard constraints

Hard constraints must always be satisfied.

```python
from glp.constraint import Constraint
from glp.enums import ConstraintSense

c = Constraint(
    name="budget",
    expression=2*x + 3*y,
    sense=ConstraintSense.LE,
    rhs=100
)

model.add_constraint(c)
```

---

### Add goals (soft constraints)

Goals define desired targets and allow deviations.

```python
from glp.goal import Goal
from glp.enums import GoalSense

goal_energy = Goal(
    name="energy",
    expression=5*x + 10*y,
    target=200,
    sense=GoalSense.ATTAIN,
    weight=1.0
)

model.add_goal(goal_energy)
```

Adding a goal automatically:

- creates deviation variables `n_energy` and `p_energy`
- adds the corresponding linking constraint to the model

---

### Solve a Weighted Goal Programming problem

```python
result = model.solve_weighted()
```

Optionally include a cost term in the objective:

```python
result = model.solve_weighted(
    cost_expr=2*x + 3*y,
    cost_weight=10.0
)
```

---

## Results

The solver returns a structured dictionary:

```python
{
    "status": "Optimal",
    "variables": {...},
    "deviations": {...},
    "objective": ...
}
```

### Decision variables

```python
result["variables"]["Rice"]
result["variables"]["Dal"]
```

### Goal deviations

```python
result["deviations"]["energy"]
# (under_deviation, over_deviation)
```

This makes it easy to diagnose which goals were met, underachieved, or exceeded.

---

## Typical use cases

GLP is suitable for problems such as:

- Diet and nutrition planning
- Health resource allocation
- Coverage vs cost trade-offs
- Policy target balancing
- Educational use in optimization courses

The package is **domain-agnostic**: users define their own variables, constraints, and goals.

---

## Reproducibility and transparency

- All models are standard linear programs
- No heuristics or hidden transformations
- Full access to the underlying PuLP model
- Solutions are deterministic given solver settings

---

## License

CCL - MIT
