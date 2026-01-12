---
title: 'PyGuLP: A Python package for Weighted Goal Linear Programming'
tags:
  - Python
  - optimization
  - linear programming
  - goal programming
  - decision support
  - health
  - public health
authors:
  - name: Kshitij Vaidya
    orcid: 0000-0000-0000-0000
    equal-contrib: true
    affiliation: 1
  - name: Roomani Srivastava
    orcid: 0000-0001-8183-109X
    equal-contrib: true
    affiliation: 1
  - name: Ishan Pandit
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Kshitij Jadhav
    corresponding: true
    orcid: 0000-0001-9795-8335
    affiliation: 1
affiliations:
  - name: AIDE Lab, Koita Centre for Digital Health, Indian Institute of Technology Bombay, India
    index: 1
date: 2 January 2026
bibliography: paper.bib
---

# Summary
Resource allocation is a key factor in several day-to-day activities, planning and even policy making. This is often expressed in terms of multiple targets rather than a single objective. In health and public health, planners may need to simultaneously cover specific areas, where public programs need to be implemented, adhere to recommended standards, and control costs under fixed resource constraints. Similar target-driven decision problems arise in environmental sciences, infrastructure planning, education, nutrition etc. In such settings, improving performance with respect to one target often requires accepting a trade-off with others.
Traditional linear programming frameworks are well suited to optimizing a single objective subject to feasibility constraints, but they usually fail in solving problems with conflicting objectives such as providing a protein rich diet at lower costs. Goal Linear Programming (GLP) extends linear programming by allowing targets to be modelled explicitly and by minimizing deviations from those targets. Among GLP variants, Weighted Goal Linear Programming (WGP) offers a transparent and interpretable formulation in which the relative importance of competing targets is encoded through priority weights.
**PyGuLP** is a lightweight Python package that implements WGP using standard linear programming constructs. Users define decision variables, feasibility constraints, and a set of goals expressed as linear functions with target values. For each goal, the package automatically introduces under- and over-deviation variables and constructs the corresponding goal-linking constraints. The resulting linear program minimizes a weighted sum of deviations and is solved using established linear solvers. PyGuLP makes goal-based optimization accessible to applied researchers while preserving full control over the underlying optimization model.

# Statement of Need
Linear programming provides efficient tools for expressing feasibility constraints and optimizing a single scalar objective. When analysts face problems involving multiple objectives, common practice is to rely on multi-objective linear programming techniques such as weighted sum scalarization, $\epsilon$-constraint formulations, Pareto-based analyses, and interval-based multi-objective linear programming. In weighted sum approaches, multiple objectives are combined into a single objective function using weights defined by the user [@halffmann2022exact] where the relation between objective weights and the achieved outcomes are indirect and problem-dependent, making it difficult to interpret how a given choice of weights translates into target attainment. $\epsilon$-constraint methods designate one objective for optimization while converting others into constraints with prescribed bounds; this can lead to infeasibility when targets cannot be simultaneously satisfied [@tantawy2009multiple]. Interval-based multi-objective linear programming represents objectives or parameters as ranges rather than fixed values [@RivazSaeidi2021IntervalMOLP], shifting uncertainty handling into the optimization formulation but still requiring feasibility to be defined through hard bounds that may not align with aspirational targets [halffmann2022exact]. Pareto-based approaches aim to enumerate or approximate the set of non-dominated solutions; a non-dominated solution is one for which no objective can be improved without worsening at least one other objective. This places the burden on the decision maker to explore and select a “best compromise” solution from a potentially large solution set [halme1989nondominated].
These approaches blur an important conceptual distinction between feasibility requirements (constraints) that must be satisfied and aspiration targets (goals) that may be violated at a known and acceptable cost. In contrast, GLP introduces deviation variables that explicitly quantify under- and over-achievement relative to specified targets, allowing infeasible aspiration levels to be accommodated in a controlled and interpretable manner. This explicit representation of deviations aligns more naturally in the context of decision making, where targets serve as guiding benchmarks rather than strict constraints [@charnes1957; @orumie2014].

# State of the Field
Although the theoretical foundations of goal programming are well established in the operations research literature [@charnes1957; @orumie2014; @nagarajan2022], practical implementations are typically reported as part of individual case studies rather than as reusable, general-purpose software. Goal Programming has been used across multiple domains which require dynamic target handling. Examples include; diet planning, manpower planning and resource allocation in hospitals [@KwakLee1997LinearGP_HR]. Beyond health, financial problems such as deciding insurance premiums [gleason1977goal; @gonzalez2020goal] or environmental planning for reduced emissions limits coupled with conservation goals [@mamun2015application; @abella2023land] have used GLP to balance such goals.
However, unlike linear programming there is no open-source tool that can implement this seamlessly. Analysts often implement goal programming models using spreadsheet-based workflows [@goh2019optimizing], proprietary modelling environments, or problem-specific code written for a single study. A case in point is the commercial optimization platform FICO-Xpress [@FICOXpressOptimizationDocsOverview] which has been used to apply GLP in diet optimization and test different achievement functions [gerdessen2015diet]. However, GLP model construction often remains a manual, error-prone process, and these solutions are not open-source. These choices make models harder to audit, reproduce as well as scale effectively. PyGuLP addresses this gap by providing a standardized, reusable software workflow for weighted goal linear programming. 

# Software Design
## Design Philosophy and Architecture
PyGuLP is designed to formalize and standardize how weighted goal programming models are constructed and solved in applied research. The package provides a consistent structure for separating feasibility constraints from aspirational goals or targets, reflecting the distinction emphasized in the goal programming literature but often implemented manually in practice. For each goal, PyGuLP systematically introduces deviation variables and constructs the corresponding goal-linking constraint, ensuring that under- and over-achievement are represented explicitly. The resulting optimization problem remains a linear program and is solved using established solvers through the PuLP ecosystem. By returning achieved values and deviations in a structured form, PyGuLP supports interpretation, comparison across scenarios, and reuse across problem settings. 

# Mathematical formulation
PyGuLP implements Weighted Goal Linear Programming using a standard linear formulation.
Let  
`x` denote a vector of decision variables subject to a set of linear feasibility constraints.
Each goal `k = 1, ..., K` is defined by a linear expression `Z_k(x)` and a target value `T_k`. To measure deviations from the target, PyGuLP introduces under and over deviation variables `d-_k` and `d+_k` and constructs the goal-linking equation:

Z_k(x) + d-_k - d+_k = T_k

The weighted goal programming objective minimizes the total deviation across all goals:

minimize sum_k w_k * (d-_k + d+_k)

where `w_k >= 0` is the weight assigned to goal `k`. Larger weights enforce closer adherence to the corresponding target. This formulation preserves linearity and allows trade-offs between competing targets to be expressed transparently.


# Implementation and Future Aspects
PyGuLP supports reproducibility and alignment with best practices in optimization-based decision support, while making goal programming interpretable even to inter-disciplinary teams with non-specialists in optimization.
While the current package is intended for programmatic use by researchers, its formulation is designed to support future extensions, including higher-level interfaces aimed at enabling domain experts without programming backgrounds to formulate and explore goal-based optimization models.


# References

