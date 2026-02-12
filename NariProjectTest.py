import os
import sys

import pandas as pd
from pulp import LpBinary, LpMinimize, LpProblem, LpStatus, LpVariable, lpSum

# Ensure local glp package is importable
sys.path.append("/Users/kshitijvaidya/glpPackage/src")
from glp.enums import GoalSense
from glp.goal import Goal


def main():
    region_key = "NT_NV"
    region = region_key.split("_")[0]
    cost_col = f"Cost_{region}"

    # Adjust the path to the Excel file as needed
    excel_path = "/Users/kshitijvaidya/glpPackage/tests/Master_Nutrient_Value_Cost.xlsx"
    if not os.path.exists(excel_path):
        excel_path = "Master_Nutrient_Value_Cost.xlsx"  # fallback to CWD

    EAR = {
        "Energy": 2130.0,
        "Protein": 36.0,
        "Visible_Fat": 30.0,
        "Carbohydrate": 290.0,
        "Total_Dietary_Fibre": 30.0,
        "Vitamin_A": 390.0,
        "Vitamin_B1": 1.4,
        "Vitamin_B2": 2.0,
        "Vitamin_B3": 12.0,
        "Pyridoxine": 1.6,
        "Folic_Acid": 180.0,
        "Vitamin_C": 55.0,
        "Iron": 15.0,
        "Calcium": 800.0,
        "Zinc": 11.0,
    }

    limits = {
        "NT_NV": {
            "Cereals": {"LL": 100, "UL": 280},
            "Pulses": {"LL": 15, "UL": 15},
            "GLV": {"LL": 35, "UL": 200},
            "OV": {"LL": 50, "UL": 150},
            "Fruits": {"LL": 50, "UL": 100},
            "RT": {"LL": 25, "UL": 100},
            "Condi": {"LL": 5, "UL": 10},
            "Nuts": {"LL": None, "UL": None},
            "Sugars": {"LL": 2.5, "UL": 20},
            "Mushrooms": {"LL": None, "UL": None},
            "Milk": {"LL": 20, "UL": 20},
            "Meat": {"LL": 50, "UL": 100},
            "Fish": {"LL": 50, "UL": 100},
            "Poultry": {"LL": 50, "UL": 100},
            "Oils": {"LL": 15, "UL": 25},
        }
    }

    # Load Excel
    df = pd.read_excel(excel_path)

    # If Food_Group not provided, derive from Food_Item
    if "Food_Group" not in df.columns and "Food_Item" in df.columns:
        df["Food_Group"] = df["Food_Item"].str.split("_").str[0]

    # Keep columns: Food_Item + nutrients + costs
    food_names = df.iloc[:, 0]
    numeric_data = df.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    # Convert per 100g to per gram
    numeric_data = numeric_data / 100.0
    final_df = pd.concat([food_names, numeric_data], axis=1)

    # Remove Windows-only cost column if present (not needed on Mac)
    for col in list(final_df.columns):
        if col.startswith("Cost_") and col != cost_col:
            final_df = final_df.drop(columns=col)

    # Drop some items as per notebook
    final_df = final_df[~final_df["Food_Item"].str.startswith("Poultry")]
    final_df = final_df[~final_df["Food_Item"].str.startswith("Meat")]
    final_df.reset_index(drop=True, inplace=True)

    # Constants: Garlic 5g, Tamarind 20g
    garlic_amt = 5
    tamarind_amt = 20
    if "Condi_Garlic" in final_df["Food_Item"].values:
        garlicNutrients = (
            final_df.loc[final_df["Food_Item"] == "Condi_Garlic"]
            .drop(columns=["Food_Item"])
            .T
            * garlic_amt
        )
    else:
        garlicNutrients = pd.DataFrame()
    if "Fruits_Tamarind" in final_df["Food_Item"].values:
        tamarindNutrients = (
            final_df.loc[final_df["Food_Item"] == "Fruits_Tamarind"]
            .drop(columns=["Food_Item"])
            .T
            * tamarind_amt
        )
    else:
        tamarindNutrients = pd.DataFrame()

    # Adjust EAR for constants
    for key in list(EAR.keys()):
        if not garlicNutrients.empty and key in garlicNutrients.index:
            EAR[key] -= float(garlicNutrients.loc[key].values[0])
        if not tamarindNutrients.empty and key in tamarindNutrients.index:
            EAR[key] -= float(tamarindNutrients.loc[key].values[0])

    # Remove constants from optimization df
    remove_foods = [
        "Condi_Garlic",
        "Fruits_Tamarind",
        "Milk_Cow_Milk",
        "Milk_Milk_Powder",
        "Milk_Paneer",
        "Milk_Curd",
        "Cereals_Flatened_Rice",
        "Cereals_Rice_Powder",
        "Cereals_Maida",
    ]
    final_df = final_df[~final_df["Food_Item"].isin(remove_foods)].copy()
    if "Food_Group" not in final_df.columns:
        final_df["Food_Group"] = final_df["Food_Item"].str.split("_").str[0]

    # Weights
    weights = {
        "Cost": 10.0,
        "Energy": 1.0,
        "Protein": 1.0,
        "Visible_Fat": 1.0,
        "Carbohydrate": 1.0,
        "Total_Dietary_Fibre": 1.0,
        "Vitamin_A": 1.0,
        "Vitamin_B1": 1.0,
        "Vitamin_B2": 1.0,
        "Vitamin_B3": 1.0,
        "Pyridoxine": 1.0,
        "Folic_Acid": 1.0,
        "Vitamin_C": 1.0,
        "Iron": 1.0,
        "Calcium": 1.0,
        "Zinc": 1.0,
    }

    # Build model
    model = LpProblem(name=f"{region_key}_food_basket", sense=LpMinimize)
    food_items = final_df["Food_Item"].tolist()

    # Decision vars and selection vars
    food_vars = {food: LpVariable(food, lowBound=0) for food in food_items}
    selection_vars = {
        food: LpVariable(f"{food}_selected", cat=LpBinary) for food in food_items
    }

    # Big-M per food from group UL
    big_M_per_food = {}
    for food in food_items:
        group = final_df.loc[final_df["Food_Item"] == food, "Food_Group"].values[0]
        group_limits = limits[region_key].get(group, {})
        upper_limit = group_limits.get("UL")
        big_M_per_food[food] = upper_limit if upper_limit is not None else 1000.0

    # Link selection and quantity
    min_amt = 5.0
    for food in food_items:
        model += (
            food_vars[food] >= min_amt * selection_vars[food],
            f"{food}_min_amt_link",
        )
        model += (
            food_vars[food] <= big_M_per_food[food] * selection_vars[food],
            f"{food}_selection_link",
        )

    # Group selection constraints
    cereal_items = [f for f in food_items if f.startswith("Cereals")]
    if "Cereals_Rice" in cereal_items:
        other_cereal_items = [f for f in cereal_items if f != "Cereals_Rice"]
        rice_amount = food_vars["Cereals_Rice"]
        other_cereal_amount = (
            lpSum(food_vars[f] for f in other_cereal_items) if other_cereal_items else 0
        )
        total_cereal = rice_amount + other_cereal_amount
        model += rice_amount == 0.8 * total_cereal, "Rice_80pct_Cereals"
        if other_cereal_items:
            model += other_cereal_amount == 0.2 * total_cereal, "Others_20pct_Cereals"
        model += lpSum(selection_vars[f] for f in cereal_items) == 2, "Only_two_cereals"

    glv_items = [f for f in food_items if f.startswith("GLV")]
    if glv_items:
        model += lpSum(selection_vars[f] for f in glv_items) == 1, "Other_GLV_Atleast_1"

    condi_items = [
        f for f in food_items if f.startswith("Condi") and f != "Condi_Garlic"
    ]
    if condi_items:
        model += (
            lpSum(selection_vars[f] for f in condi_items) == 1,
            "Other_Condi_Atleast_1",
        )

    fruit_items = [
        f for f in food_items if f.startswith("Fruits") and f != "Fruits_Tamarind"
    ]
    if fruit_items:
        model += (
            lpSum(selection_vars[f] for f in fruit_items) == 1,
            "Other_Fruit_Atleast_1",
        )

    pulse_items = [f for f in food_items if f.startswith("Pulses")]
    if pulse_items:
        model += lpSum(selection_vars[f] for f in pulse_items) == 1, "One_Pulse"

    ov_items = [f for f in food_items if f.startswith("OV")]
    if ov_items:
        model += lpSum(selection_vars[f] for f in ov_items) == 2, "OV_Exactly_2"
        common_ov_amount = LpVariable("common_OV_amount", lowBound=0)
        ov_UL = limits[region_key]["OV"]["UL"]
        model += 2 * common_ov_amount <= ov_UL, "OV_Total_UL"
        bigM = 150.0
        for f in ov_items:
            model += food_vars[f] <= common_ov_amount, f"{f}_le_common_amount"
            model += food_vars[f] <= bigM * selection_vars[f], f"{f}_le_bigM"
            model += (
                food_vars[f] >= common_ov_amount - (1 - selection_vars[f]) * bigM,
                f"{f}_ge_common_or_0",
            )

    rt_items = [f for f in food_items if f.startswith("RT")]
    if rt_items:
        model += lpSum(selection_vars[f] for f in rt_items) == 1, "RT_only_1"

    fish_items = [f for f in food_items if f.startswith("Fish")]
    if fish_items:
        model += lpSum(selection_vars[f] for f in fish_items) == 1, "Fish_only_1"

    # Build nutrient expressions and Goals (using glp)
    goals = {}
    deviation_vars = {}
    for nutrient in EAR.keys():
        expr = lpSum(
            final_df[nutrient].iloc[i] * food_vars[final_df["Food_Item"].iloc[i]]
            for i in range(len(final_df))
        )
        goal = Goal(
            name=nutrient,
            expression=expr,
            target=EAR[nutrient],
            sense=GoalSense.ATTAIN,
            weight=weights.get(nutrient, 1.0),
            priority=1,
        )
        goals[nutrient] = goal
        deviation_vars[nutrient] = {
            "under": LpVariable(f"{nutrient}_under", lowBound=0),
            "over": LpVariable(f"{nutrient}_over", lowBound=0),
        }
        # Goal constraints
        model += (
            goal.expression
            + deviation_vars[nutrient]["under"]
            - deviation_vars[nutrient]["over"]
            == goal.target,
            f"{nutrient}_goal_attain",
        )

    # Group LL/UL bounds
    for group, bounds in limits[region_key].items():
        group_items = final_df[final_df["Food_Item"].str.startswith(group)][
            "Food_Item"
        ].tolist()
        if not group_items:
            continue
        if bounds["LL"] is not None:
            model += (
                lpSum(food_vars[f] for f in group_items) >= bounds["LL"],
                f"{group}_LL",
            )
        if bounds["UL"] is not None:
            model += (
                lpSum(food_vars[f] for f in group_items) <= bounds["UL"],
                f"{group}_UL",
            )

    # Objective: cost + weighted goal deviations
    cost_sum = lpSum(
        final_df[cost_col].iloc[i] * food_vars[final_df["Food_Item"].iloc[i]]
        for i in range(len(final_df))
        if cost_col in final_df.columns
    )
    model += weights["Cost"] * cost_sum + lpSum(
        goals[n].weight * (deviation_vars[n]["under"] + deviation_vars[n]["over"])
        for n in goals.keys()
    )

    # Solve
    model.solve()

    # Output
    print("Status:", LpStatus[model.status])
    total_cost = sum(
        (food_vars[f].varValue or 0.0)
        * float(final_df.loc[final_df["Food_Item"] == f, cost_col].values[0])
        for f in food_items
        if cost_col in final_df.columns
    )
    print("Total Cost (Rs):", round(total_cost, 2))
    print("\nOptimized Food Basket (grams):")
    for f in food_items:
        val = food_vars[f].varValue
        if val and val > 0:
            print(f"  {f}: {val:.1f}g")


if __name__ == "__main__":
    main()
