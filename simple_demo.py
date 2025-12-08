import sys, os
sys.path.append(os.path.abspath("src"))

import pulp
from glp.core import GLPModel, Goal, GoalSense

# ======================
# STEP 1: FAKE SIMPLIFIED DATA
# ======================
import pandas as pd

data = {
    "Food_Item": [
        "Cereals_Rice", "Cereals_Wheat",
        "Pulses_Peas", "GLV_Spinach",
        "OV_Cabbage", "Fruits_Banana",
        "Oils_Mustard_Oil"
    ],
    "Food_Group": [
        "Cereals", "Cereals",
        "Pulses", "GLV",
        "OV", "Fruits",
        "Oils"
    ],
    "Cost_NT": [0.05, 0.04, 0.08, 0.03, 0.02, 0.06, 0.10],
    "Energy": [3.5, 3.3, 3.6, 0.2, 0.25, 0.9, 9.0],
    "Protein": [0.06, 0.12, 0.22, 0.02, 0.02, 0.01, 0.0],
}

df = pd.DataFrame(data)

# EAR Requirements
EAR = {"Energy": 2000, "Protein": 50}

# Group constraints (LL & UL)
limits = {
    "Cereals": {"LL": 200, "UL": 400},
    "Pulses": {"LL": 50, "UL": 80},
    "GLV": {"LL": 20, "UL": 200},
    "OV": {"LL": 30, "UL": 200},
    "Fruits": {"LL": 50, "UL": 150},
    "Oils": {"LL": 15, "UL": 30},
}

# ======================
# STEP 2: BUILD CORE MODEL
# ======================
model = GLPModel("Minimal_Diet_Example")

# Decision variables (grams/day)
food_vars = {food: model.add_variable(food, low_bound=0.0) for food in df["Food_Item"]}

# Goals for nutrients
for nutrient, target in EAR.items():
    expr = sum(df.loc[i, nutrient] * food_vars[df.loc[i, "Food_Item"]] for i in range(len(df)))
    g = Goal(name=nutrient, expression=expr, target=target, sense=GoalSense.ATTAIN, weight=1.0)
    model.add_goal(g)

# Group LL/UL constraints
for group, bounds in limits.items():
    items = df[df["Food_Group"] == group]["Food_Item"].tolist()
    total_group = sum(food_vars[f] for f in items)
    if bounds["LL"] is not None:
        model.problem += total_group >= bounds["LL"]
    if bounds["UL"] is not None:
        model.problem += total_group <= bounds["UL"]

# 80/20 Cereal Rule
rice = food_vars["Cereals_Rice"]
wheat = food_vars["Cereals_Wheat"]
total_cereal = rice + wheat
model.problem += rice == 0.8 * total_cereal
model.problem += wheat == 0.2 * total_cereal

# Cost expression
cost_expr = sum(df.loc[i, "Cost_NT"] * food_vars[df.loc[i, "Food_Item"]] for i in range(len(df)))

# ======================
# STEP 3: SOLVE WGP
# ======================
result = model.solve_weighted(cost_expr=cost_expr, cost_weight=10.0)

# ======================
# STEP 4: DISPLAY RESULTS
# ======================
print("\n=== MODEL STATUS ===")
print(result["status"])

print("\n=== OPTIMIZED FOOD BASKET ===")
for name, val in result["variables"].items():
    if val is not None and val > 0 and not name.startswith("n_") and not name.startswith("p_"):
        print(f"{name:20s}: {val:.1f} g")

# Nutrient totals
print("\n=== NUTRIENT TOTALS ===")
for nutrient in EAR.keys():
    expr = sum(df.loc[i, nutrient] * result["variables"][df.loc[i, "Food_Item"]] for i in range(len(df)))
    print(f"{nutrient:20s}: {expr:.2f}  ({expr / EAR[nutrient] * 100:.1f}% EAR)")
