# 📦 GLP – Goal Linear Programming Package (Draft)

A minimal and clean **Goal Programming (GP)** / **Goal Linear Programming (GLP)** package implemented on top of **PuLP**, designed to help solve multi-objective optimization problems such as dietary planning, resource allocation, etc.

This draft version demonstrates:

* Creating **decision variables**
* Creating **soft goals with deviation variables**
* Adding **hard constraints**
* Solving **Weighted Goal Programming (WGP)** problems

The core implementation is located in:

```
src/glp/core.py
```

---

## 🧠 What is Goal Programming?

Traditional optimization maximizes or minimizes one objective.
**Goal Programming** instead **minimizes deviation from targets**, recognizing that in real-world systems you cannot satisfy every requirement fully.

For each goal:

```
expression + n - p = target
```

Where:

| Symbol       | Meaning                               |
| ------------ | ------------------------------------- |
| `expression` | linear function of decision variables |
| `n`          | negative deviation (underachievement) |
| `p`          | positive deviation (overachievement)  |
| `target`     | desired aspiration level              |

### **Weighted GP Objective**

```
Minimize  Σ (weight_i * (n_i + p_i))
```

---

## 📁 Project Structure

```
project_root/
│
├── src/
│   └── glp/
│       ├── core.py          # main GP engine
│       └── __init__.py
│
├── tests/
│
└── demo_minimal_diet.py     # example usage script
```

---

## 🛠 Core API Usage

### **Create a Model**

```python
from glp.core import GLPModel

model = GLPModel("diet_model", minimize=True)
```

---

### **Add Decision Variables**

```python
x = model.add_variable("Rice", low_bound=0)
y = model.add_variable("Dal", low_bound=0)
```

---

### **Add Soft Goals**

```python
from glp.core import Goal, GoalSense

energy_expr = 3*x + 10*y
goal_energy = Goal(name="energy",
                   expression=energy_expr,
                   target=50,
                   weight=1.0,
                   sense=GoalSense.ATTAIN)

model.add_goal(goal_energy)
```

This automatically adds:

```
energy_expr + n_energy - p_energy = 50
```

---

### **Add Hard Constraints**

```python
from glp.core import Constraint, ConstraintSense

c = Constraint(name="max_food",
               expression=x + y,
               sense=ConstraintSense.LE,
               rhs=20)

model.add_constraint(c)
```

---

### **Solve Weighted Goal Programming**

```python
result = model.solve_weighted()
```

Extract results:

```python
print(result["status"])
print(result["variables"])
print(result["deviations"])
```

---

## 🎯 Who can use this package?

| User                       | Use case                                            |
| -------------------------- | --------------------------------------------------- |
| Researchers                | Multi-objective models with conflicting constraints |
| Nutrition & health experts | Realistic diet planning                             |
| Operations researchers     | Allocation / distribution planning                  |
| Students                   | Learning GP concepts                                |
