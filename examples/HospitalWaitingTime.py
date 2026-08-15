import pandas as pd

from pygulp.constraint import Constraint
from pygulp.core import GLPModel
from pygulp.enums import ConstraintSense, GoalSense
from pygulp.goal import Goal

# --- 1. Data Setup (from your notebook) ---
groups = pd.DataFrame(
    {
        "Group": ["Punctual", "Late"],
        "Patients": [120, 60],
        "Min_Service_Prop": [0.5, 0.2],
    }
)

waiting_goals = pd.DataFrame(
    {
        "Group": ["Punctual", "Punctual", "Late", "Late"],
        "Time_Band": [30, 45, 30, 45],
        "Target_Prop": [0.95, 1.00, 0.30, 1.00],
        "Tolerance": [0.05, 0.00, 0.20, 0.00],  # Not used in weighted GP
        "Weight": [3.0, 1.0, 2.0, 1.0],
    }
)

capacity = {"Total_Slots": 150}

# Helper for quick lookups
group_stats = groups.set_index("Group").to_dict("index")

# --- 2. Build GLP Model ---
model = GLPModel(name="OPD_Waiting_Time_Optimization")

# --- 3. Decision Variables ---
# scheduled_{group}_{time} = patients of 'group' seen within 'time' minutes
decision_vars = {}
time_bands = [30, 45]

for group in groups["Group"]:
    for time in time_bands:
        var_name = f"scheduled_{group}_{time}"
        decision_vars[(group, time)] = model.add_variable(
            var_name, low_bound=0, cat="Integer"
        )

# --- 4. Hard Constraints ---

# A. Population Limits: scheduled(group,45) <= Patients(group)
for group in groups["Group"]:
    expr = decision_vars[(group, 45)]
    model.add_constraint(
        Constraint(
            name=f"Max_Pop_{group}",
            expression=expr,
            sense=ConstraintSense.LE,
            rhs=group_stats[group]["Patients"],
        )
    )

# B. Time Consistency: scheduled(group,30) <= scheduled(group,45)
for group in groups["Group"]:
    expr = decision_vars[(group, 30)] - decision_vars[(group, 45)]
    model.add_constraint(
        Constraint(
            name=f"Consistency_{group}_30_45",
            expression=expr,
            sense=ConstraintSense.LE,
            rhs=0.0,
        )
    )

# C. Global Capacity: sum scheduled(group,45) <= Total_Slots
total_scheduled_45 = sum(decision_vars[(g, 45)] for g in groups["Group"])
model.add_constraint(
    Constraint(
        name="Global_Capacity_Constraint",
        expression=total_scheduled_45,
        sense=ConstraintSense.LE,
        rhs=capacity["Total_Slots"],
    )
)

# D. Minimum Service Guarantee:
# scheduled(group,45) >= Min_Service_Prop * Patients(group)
for group in groups["Group"]:
    min_count = group_stats[group]["Patients"] * group_stats[group]["Min_Service_Prop"]
    model.add_constraint(
        Constraint(
            name=f"Min_Service_Req_{group}",
            expression=decision_vars[(group, 45)],
            sense=ConstraintSense.GE,
            rhs=min_count,
        )
    )

# --- 5. Goals ---
# For each waiting goal: scheduled(group,time) + n - p = target_val
# Penalize only underachievement via goal_weights[gname] = (weight, 0.0)
goal_weights = {}
for _, row in waiting_goals.iterrows():
    group = row["Group"]
    time = row["Time_Band"]
    weight = float(row["Weight"])
    target_val = float(row["Target_Prop"] * group_stats[group]["Patients"])

    gname = f"Goal_{group}_{time}"
    goal = Goal(
        name=gname,
        expression=decision_vars[(group, time)],
        target=target_val,
        sense=GoalSense.ATTAIN,
        weight=weight,
    )
    model.add_goal(goal)
    goal_weights[gname] = (weight, 0.0)  # (w_minus, w_plus)

# --- 6. Solve Weighted Goal Programming ---
result = model.solve_weighted(goal_weights=goal_weights)

# --- 7. Display Results ---
print(f"Status: {result['status']}")
print("-" * 30)

print("Scheduling Results:")
header = (
    f"{'Group':<10} | {'Time Band':<10} | {'Scheduled':<10} | "
    f"{'Target':<10} | {'Goal Met?'}"
)
print(header)
for _, row in waiting_goals.iterrows():
    group = row["Group"]
    time = row["Time_Band"]
    var_name = f"scheduled_{group}_{time}"
    actual = result["variables"][var_name]
    target = row["Target_Prop"] * group_stats[group]["Patients"]
    met = "YES" if actual is not None and actual >= target - 1e-6 else "NO"
    print(f"{group:<10} | {time:<10} | {actual:<10.0f} | {target:<10.0f} | {met}")

print("-" * 30)
total_punctual = result["variables"]["scheduled_Punctual_45"]
total_late = result["variables"]["scheduled_Late_45"]
print(
    "Total Punctual Scheduled: "
    f"{total_punctual} / {group_stats['Punctual']['Patients']}"
)
print(f"Total Late Scheduled:     {total_late} / {group_stats['Late']['Patients']}")
print(
    "Total Slots Used:         "
    f"{total_punctual + total_late} / {capacity['Total_Slots']}"
)
