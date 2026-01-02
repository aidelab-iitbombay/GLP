---
title: 'GLP: A Python package for Weighted Goal Linear Programming'
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
---

# Summary

Many applied planning and policy problems are naturally expressed in terms of multiple targets rather than a single objective. In health and public health, planners may need to simultaneously meet service coverage thresholds, adhere to quality or equity benchmarks, and control costs under fixed resource constraints. Similar target-driven decision problems arise in environmental management, education planning, energy systems, and other public-sector domains. In such settings, improving performance with respect to one target often requires accepting controlled deviations from others.

Traditional linear programming frameworks are well suited to optimizing a single objective under constraints, but they provide limited direct support for problems where several aspiration levels must be balanced. Goal Programming (GP) extends linear programming by treating targets as soft goals and minimizing deviations from them. Among GP variants, Weighted Goal Linear Programming (WGLP) offers a transparent and interpretable formulation, allowing the relative importance of competing goals to be expressed explicitly through deviation weights.

`GLP` is a lightweight Python package that implements WGLP using standard linear programming constructs. Users define decision variables, hard feasibility constraints, and a set of goals expressed as linear functions with target values. For each goal, the package automatically introduces nonnegative under- and over-deviation variables and constructs the corresponding linking constraints. The resulting linear program minimizes a weighted sum of deviations and can be solved using established linear solvers via the PuLP ecosystem. By prioritizing transparency and minimal abstraction, `GLP` makes goal programming accessible to applied researchers while preserving full control over the underlying optimization model.

---

# Statement of need

Linear programming libraries provide mature and efficient tools for expressing constraints and optimizing a single scalar objective. When faced with multiple objectives, analysts often resort to ad-hoc scalarization approaches, such as weighted sums of objectives, which obscure the distinction between feasibility requirements and aspiration targets. In contrast, goal programming requires an explicit modeling structure: the introduction of deviation variables, the formulation of goal-linking constraints, and careful bookkeeping to ensure that under- and over-achievement are penalized appropriately.

Although the theoretical foundations of goal programming are well established in the operations research literature [@charnes1957; @orumie2014; @nagarajan2022], practical implementations are frequently bespoke and tightly coupled to individual case studies. In applied research domains, analysts often implement goal programming models manually in spreadsheets or custom scripts. Such implementations are difficult to audit, reuse, and systematically stress-test, and they can obscure the conceptual structure of the model for interdisciplinary teams that include non-specialists in optimization.

Target-driven formulations are particularly common in health and public-sector decision problems. For example, planning tasks may involve achieving recommended intake levels, minimum service coverage thresholds, or regulatory benchmarks while respecting budgets and capacity limits. In many cases, these targets function as aspirational guidelines rather than strict constraints, and perfect satisfaction of all targets is infeasible. Weighted goal programming provides a natural framework for such settings by allowing deviations to be traded off in a controlled and interpretable manner.

Similar modeling structures arise across a wide range of applications beyond health, including environmental planning, where emissions limits, conservation goals, and economic costs must be balanced, and in education or infrastructure planning, where access, quality, and expenditure targets coexist. The common feature across these domains is the need for a transparent mechanism to express priorities among competing goals while remaining within a linear optimization framework.

`GLP` addresses this need by providing a standardized software workflow for weighted goal programming. The package enforces a clear separation between hard feasibility constraints and soft goals, automatically constructs deviation variables and goal-linking constraints, and supports asymmetric penalties for under- and over-achievement. Results are returned in a structured form that reports achieved goal levels and deviations, facilitating diagnostic analysis and comparison across scenarios. By building directly on PuLP, `GLP` ensures compatibility with established solvers and preserves full visibility into the underlying linear program.

---

# Implementation and design philosophy

`GLP` is implemented entirely using linear programming constructs and relies exclusively on deterministic optimization solvers. The package introduces no heuristics or hidden transformations: all variables, constraints, and objectives remain explicit and inspectable through the underlying PuLP model. This design supports reproducibility, auditability, and alignment with established best practices in optimization-based decision support.

The implementation emphasizes a small and stable set of abstractions that can be composed to express a wide range of target-driven problems. While the current package is designed for programmatic use by researchers, the underlying abstractions are intended to support future extensions, including higher-level interfaces aimed at enabling domain experts without programming backgrounds to formulate and explore goal-based optimization models.

---

# Acknowledgements

The authors acknowledge support from the AI & Decision Lab and colleagues who provided feedback on model design, testing, and documentation. (Funding and sponsor involvement statements to be added as appropriate.)

# References
