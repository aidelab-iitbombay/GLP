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
  - name: Author One
    orcid: 0000-0000-0000-0000
    corresponding: true
    affiliation: 1
  - name: Author Two
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Author Three
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Author Four
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: AIDE Lab, Koita Centre for Digital Health, Indian Institute of Technology Bombay, India
    index: 1
date: 2 January 2026
bibliography: paper.bib


# Summary

Resource allocation is a key factor in a number of day to day activities, planning and even policy making. This is more often than not expressed in terms of multiple targets rather than a single objective. In health and public health, planners may need to simultaneously cover specific areas, where public program needs to be implemented, adhere to recommended standards, and control costs under fixed resource constraints. Similar target-driven decision problems arise in environmental sciences, infrastructure planning, education, nutition etc. In such settings, improving performance with respect to one target often requires accepting a trade-off with others.

Traditional linear programming frameworks are well suited to optimizing a single objective subject to feasibility constraints, but they usually fail in solving problems with conflicting objectives such as providing a protein rich diet at lower costs. Goal Linear Programming (GLP) extends linear programming by allowing targets to be modeled explicitly and by minimizing deviations from those targets. Among GLP variants, Weighted Goal Linear Programming (WGP) offers a transparent and interpretable formulation in which the relative importance of competing targets is encoded through priority weights.

**PyGuLP** is a lightweight Python package that implements WGP using standard linear programming constructs. Users define decision variables, feasibility constraints, and a set of goals expressed as linear functions with target values. For each goal, the package automatically introduces under- and over-deviation variables and constructs the corresponding goal-linking constraints. The resulting linear program minimizes a weighted sum of deviations and is solved using established linear solvers. PyGuLP makes goal-based optimization accessible to applied researchers while preserving full control over the underlying optimization model.

# Statement of need

Linear programming libraries provide mature and efficient tools for expressing constraints and optimizing a single scalar objective. When analysts face problems involving multiple objectives, they often resort to ad-hoc scalarization approaches, such as weighted sums of objectives, which obscure the distinction between feasibility requirements and targets. In contrast, goal linear programming provides an explicit modeling structure with the introduction of deviation variables, the formulation of goals alongwith weight assignments.

Although the theoretical foundations of goal programming are well established in the operations research literature [@charnes1957; @orumie2014; @nagarajan2022], practical implementations are only seen coupled to individual case studies (Ref) and no generalized tool exists to implement this intutively. In applied domains, analysts often implement goal programming models manually in spreadsheets or custom scripts. Such implementations are difficult to audit, reuse, and systematically stress-test, and they can obscure the conceptual structure of the model for interdisciplinary teams that include non-specialists in optimization.

Target-driven formulations are particularly common in health and public-sector decision problems, where planners must balance recommended benchmarks, minimum coverage thresholds, and budgetary limits. In many cases, these targets function as aspirational guidelines rather than strict constraints, and perfect satisfaction of all targets is many times infeasible. Other examples of similar modelling needs may be; manpower planning and resource allocation to reduce patient waiting time or turn around time in hospitals. Similarly beyond health, fiancial problems such as deciding insurance premiums or environmental planning for reduced emissions limits coupled with conservation goals require tools to balance such goals. Across these domains, a common requirement is a transparent mechanism to express priorities among competing targets while remaining within a linear optimization framework. Weighted goal programming provides a natural framework for such settings by allowing deviations to be traded off in a controlled and interpretable manner.

PyGuLP addresses this need by providing a standardized, reusable software workflow for weighted goal linear programming. The package separates feasibility constraints from goals, automatically constructs deviation variables and goal-linking constraints, and returns results in a structured form that reports achieved goal levels and deviations. By building directly on PuLP, PyGuLP ensures compatibility with established solvers while preserving full visibility into the underlying linear program.

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

PyGuLP is implemented entirely using linear programming constructs and relies exclusively on deterministic optimization solvers. The package introduces no heuristics or hidden transformations: all decision variables, constraints, deviation variables, and objectives remain explicit and inspectable through the underlying PuLP model. This design supports reproducibility and alignment with best practices in optimization-based decision support.

While the current package is intended for programmatic use by researchers, its formulation is designed to support future extensions, including higher-level interfaces aimed at enabling domain experts without programming backgrounds to formulate and explore goal-based optimization models.


# Acknowledgements

The authors acknowledge support from TGI for providing data that enabled us to formulate and implement the GLP problem. The scale of the said nutrition prject was an impetus to develop this package.

# References

