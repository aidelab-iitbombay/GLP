# 📦 GLP — Goal Linear Programming (Weighted Goal Programming)

**GLP** is a lightweight Python package for **Goal Linear Programming (GLP)** with a focus on **Weighted Goal Programming (WGP)**, built on top of **PuLP**.

The package is designed for researchers and practitioners who need to solve **multi-objective linear optimization problems** where several targets must be balanced simultaneously under hard constraints—common in health, public health, nutrition, and resource allocation problems.

---

## What this package provides

Version **0.0.1** implements:

- **Weighted Goal Programming (WGP)**
- Automatic creation of **under- and over-deviation variables**
- Support for goal types:
  - equality / attainment
  - minimizing under-achievement
  - minimizing over-achievement
- Explicit separation of:
  - **hard constraints** (must be satisfied)
  - **soft goals** (targets that may be violated with penalty)
- Linear programming backend via **PuLP**
- Default open-source solver: **CBC**
- Structured solution output:
  - decision variable values
  - per-goal deviations
  - objective value and solver status

The implementation is intentionally minimal, transparent, and fully linear.

---

## Installation

```bash
pip install glp
