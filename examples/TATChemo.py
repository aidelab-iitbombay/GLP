import pandas as pd
import pulp

from pygulp.constraint import Constraint
from pygulp.core import GLPModel
from pygulp.enums import ConstraintSense
from pygulp.goal import Goal

# 1. Data
units = pd.DataFrame(
    {
        "Unit": ["Triage", "Consultation", "Infusion"],
        "Staff_Type": ["Nurse", "Doctor", "Nurse"],
        "Min_Staff": [1, 1, 2],
        "Max_Staff": [3, 4, 5],
        "Staff_Cost_per_Hour": [20.0, 80.0, 25.0],
    }
)

patient_classes = pd.DataFrame(
    {
        "Class": ["Chemo_Long", "Chemo_Short", "Followup"],
        "Daily_Volume": [10, 20, 30],
        "Base_TAT": [360.0, 240.0, 120.0],
        "TAT_Target": [270.0, 180.0, 90.0],
        "Priority_Weight": [3.0, 2.0, 1.0],
    }
)

tat_sensitivity = pd.DataFrame(
    {
        "Class": ["Chemo_Long"] * 3 + ["Chemo_Short"] * 3 + ["Followup"] * 3,
        "Unit": ["Triage", "Consultation", "Infusion"] * 3,
        "Gamma": [
            3.0,
            10.0,
            12.0,  # Chemo_Long
            1.0,
            6.0,
            6.0,  # Chemo_Short
            0.5,
            3.0,
            2.0,  # Followup
        ],
    }
)

config_options = pd.DataFrame(
    {
        "Option_ID": [
            "INF_TEMPLATE_BASE",
            "INF_TEMPLATE_EXTENDED",
            "INF_OVERFLOW_BEDS",
        ],
        "Option_Type": [
            "Infusion_Template",
            "Infusion_Template",
            "Capacity_AddOn",
        ],
        "Description": [
            "Baseline infusion day: 8-hour day, standard chair schedule.",
            "Extended infusion day: 10-hour day, more evenly spread starts.",
            "Open 2 overflow infusion beds for the day.",
        ],
        "Extra_Nurse_Hours": [
            0.0,  # baseline
            8.0,  # one extra nurse for 8 hours
            4.0,  # additional monitoring time for overflow beds
        ],
        "Fixed_Cost": [
            0.0,
            400.0,
            200.0,
        ],
        "Infusion_Capacity_Factor": [
            1.00,
            1.25,
            1.10,
        ],
    }
)

global_params = {
    "Base_Hours_Per_Day": 8.0,
    "Max_Daily_Budget": 6000.0,
    "Min_Service_Prop": {
        "Chemo_Long": 0.6,
        "Chemo_Short": 0.5,
        "Followup": 0.4,
    },
}

# 2. Helpers

U = units["Unit"].tolist()
C = patient_classes["Class"].tolist()
K = config_options["Option_ID"].tolist()

min_staff = units.set_index("Unit")["Min_Staff"].to_dict()
max_staff = units.set_index("Unit")["Max_Staff"].to_dict()
staff_cost = units.set_index("Unit")["Staff_Cost_per_Hour"].to_dict()

base_tat = patient_classes.set_index("Class")["Base_TAT"].to_dict()
tat_target = patient_classes.set_index("Class")["TAT_Target"].to_dict()
priority = patient_classes.set_index("Class")["Priority_Weight"].to_dict()
daily_vol = patient_classes.set_index("Class")["Daily_Volume"].to_dict()

gamma = tat_sensitivity.set_index(["Class", "Unit"])["Gamma"].to_dict()

opt_type = config_options.set_index("Option_ID")["Option_Type"].to_dict()
opt_fixed = config_options.set_index("Option_ID")["Fixed_Cost"].to_dict()
opt_extra_nurse_hours = config_options.set_index("Option_ID")[
    "Extra_Nurse_Hours"
].to_dict()

base_hours = float(global_params["Base_Hours_Per_Day"])
budget = float(global_params["Max_Daily_Budget"])
min_service_prop = global_params["Min_Service_Prop"]

infusion_nurse_cost = staff_cost["Infusion"]
templates = [k for k in K if opt_type[k] == "Infusion_Template"]

# Capacity assumption (patients per infusion nurse-hour)
patients_per_nurse_hour = 2.0


# 3. Model (using pygulp)

m = GLPModel(name="Outpatient_GLPP", minimize=True)

# Staff variables (integer counts per unit)
x = {
    u: m.add_variable(
        f"x_staff_{u}", low_bound=min_staff[u], up_bound=max_staff[u], cat="Integer"
    )
    for u in U
}

# Binary configuration variables
z = {k: m.add_variable(f"z_{k}", low_bound=0, up_bound=1, cat="Binary") for k in K}

# Service proportion per class (access), bounded by min required and 1
p = {
    c: m.add_variable(
        f"p_service_{c}", low_bound=min_service_prop[c], up_bound=1, cat="Continuous"
    )
    for c in C
}

# TAT per class (derived)
TAT = {c: m.add_variable(f"TAT_{c}", low_bound=0, cat="Continuous") for c in C}

# ---------------------------------------------
# 4. Constraints
# ---------------------------------------------

# TAT linkage: TAT_c = Base_TAT_c - sum_u Gamma[c,u]*(x_u - MinStaff_u)
for c in C:
    tat_link_expr = (
        TAT[c]
        - base_tat[c]
        + pulp.lpSum(gamma.get((c, u), 0.0) * (x[u] - min_staff[u]) for u in U)
    )
    m.add_constraint(
        Constraint(
            name=f"link_TAT_{c}",
            expression=tat_link_expr,
            sense=ConstraintSense.EQ,
            rhs=0.0,
        )
    )

# Exactly one infusion template
m.add_constraint(
    Constraint(
        name="one_infusion_template",
        expression=pulp.lpSum(z[k] for k in templates),
        sense=ConstraintSense.EQ,
        rhs=1.0,
    )
)

# Cost composition
staff_hours_cost = pulp.lpSum(staff_cost[u] * x[u] * base_hours for u in U)
fixed_option_cost = pulp.lpSum(opt_fixed[k] * z[k] for k in K)
extra_nurse_cost = pulp.lpSum(
    opt_extra_nurse_hours[k] * infusion_nurse_cost * z[k] for k in K
)
total_cost_expr = staff_hours_cost + fixed_option_cost + extra_nurse_cost

# Budget cap
m.add_constraint(
    Constraint(
        name="budget_cap",
        expression=total_cost_expr,
        sense=ConstraintSense.LE,
        rhs=budget,
    )
)

# Infusion capacity: served <= rate * hours * effective staff
served_patients = pulp.lpSum(p[c] * daily_vol[c] for c in C)
effective_infusion_staff = x["Infusion"] + pulp.lpSum(
    (opt_extra_nurse_hours[k] / base_hours) * z[k] for k in K
)
capacity_expr = (
    served_patients - patients_per_nurse_hour * base_hours * effective_infusion_staff
)
m.add_constraint(
    Constraint(
        name="infusion_capacity",
        expression=capacity_expr,
        sense=ConstraintSense.LE,
        rhs=0.0,
    )
)


# 5. Goals

# TAT goals: penalize only positive deviation above target (p-var)
goal_weights = {}
for c in C:
    m.add_goal(
        Goal(
            name=f"TAT_target_{c}",
            expression=TAT[c],
            target=tat_target[c],
            weight=priority[c],
        )
    )
    goal_weights[f"TAT_target_{c}"] = (0.0, priority[c])  # (under-weight, over-weight)

# Access goals: drive p_service -> 1, penalize only shortfall (n-var)
lambda_access = 1.0
for c in C:
    m.add_goal(
        Goal(
            name=f"Access_{c}",
            expression=p[c],
            target=1.0,
            weight=lambda_access * priority[c],
        )
    )
    goal_weights[f"Access_{c}"] = (lambda_access * priority[c], 0.0)


# 6. Solve

lambda_cost = 1e-3
result = m.solve_weighted(
    goal_weights=goal_weights, cost_expr=total_cost_expr, cost_weight=lambda_cost
)


# 7. Report

print(f"Status: {result['status']}")
print(f"Objective value: {result['objective']:.2f}")

# Compute cost value from solution
staff_hours_cost_val = sum(
    staff_cost[u] * result["variables"][f"x_staff_{u}"] * base_hours for u in U
)
fixed_option_cost_val = sum(opt_fixed[k] * result["variables"][f"z_{k}"] for k in K)
extra_nurse_cost_val = sum(
    opt_extra_nurse_hours[k] * infusion_nurse_cost * result["variables"][f"z_{k}"]
    for k in K
)
total_cost_val = staff_hours_cost_val + fixed_option_cost_val + extra_nurse_cost_val
print(f"Total cost: {total_cost_val:.2f} (budget {budget:.2f})\n")

print("Staffing decisions:")
for u in U:
    print(f"  {u}: {result['variables'][f'x_staff_{u}']}")

print("\nSelected options:")
for k in K:
    print(f"  {k}: {int((result['variables'][f'z_{k}'] or 0) > 0.5)}")

print("\nClass outcomes:")
for c in C:
    p_val = result["variables"][f"p_service_{c}"]
    tat_val = result["variables"][f"TAT_{c}"]
    served_val = p_val * daily_vol[c]
    d_tat_plus = result["deviations"][f"TAT_target_{c}"][1]
    access_shortfall = result["deviations"][f"Access_{c}"][0]
    print(
        f"  {c}: p={p_val:.3f}, served={served_val:.1f}, "
        f"TAT={tat_val:.1f}, d_TAT+={d_tat_plus:.1f}, "
        f"access_shortfall={access_shortfall:.3f}"
    )

print("\nCapacity check:")
served_total = sum(result["variables"][f"p_service_{c}"] * daily_vol[c] for c in C)
effective_staff_val = result["variables"]["x_staff_Infusion"] + sum(
    (opt_extra_nurse_hours[k] / base_hours) * result["variables"][f"z_{k}"] for k in K
)
capacity_rhs = patients_per_nurse_hour * base_hours * effective_staff_val
print(f"  Served patients: {served_total:.2f}")
print(f"  Effective infusion staff: {effective_staff_val:.2f}")
print(f"  Capacity RHS: {capacity_rhs:.2f}")
