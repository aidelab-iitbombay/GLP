# OPD Waiting-Time Targets – Toy Dataset

Small synthetic dataset for testing a Goal Linear Programming (GLP) implementation on an outpatient waiting-time target problem.

Source paper: https://indjst.org/articles/setting-up-waiting-time-targets-for-out-patients-using-fuzzy-linear-programming

This toy dataset adapts the problem described in the paper (which uses fuzzy linear programming) for a classical goal programming setup.

Data description

Files in this directory (expected):
- groups.csv — per-group patient counts and optional minimum service proportion.
- waiting_goals.csv — service-level goals (group, time band, target proportion, tolerance, weight).
- capacity.* — capacity information (Total_Slots, etc.). May be provided as JSON/YAML/CSV depending on your workflow.

groups table

- Group: Aggregate patient category (e.g. Punctual, Late).
- Patients: Number of patients on the waiting list for the upcoming OPD session in that group.
- Min_Service_Prop (optional): Minimum proportion of each group that must be scheduled overall (within the 45-minute horizon).

waiting_goals table

Each row corresponds to one service-level goal.
- Group: Group to which the goal applies (Punctual / Late).
- Time_Band: Waiting-time threshold in minutes (e.g. 30 or 45).
- Target_Prop: Target proportion of that group’s patients that should be examined within Time_Band.
- Tolerance: Optional metadata for weighted GP implementations to indicate acceptable deviation.
- Weight: Importance of this goal in the weighted GP objective. Larger values give the corresponding goal higher priority in trade-offs.

capacity dict

- Total_Slots: Maximum number of patients that can be scheduled in the upcoming session (within the 45-minute horizon), enforcing the overall capacity constraint.
- Additional keys (optional): You may include other capacity-related parameters such as 'Slot_Length', 'Available_Doctors', or session-specific modifiers.

Notes

- This README is intended as human-readable documentation for the toy dataset. Use the provided CSV/YAML/JSON files in this directory as input to GLP/goal-programming experiments or unit tests.
- If you want me to push a specific README content variant, or include/modify the example CSV files themselves, tell me the exact changes and I will update them in the same commit.
