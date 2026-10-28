---
title: "Top-Conference Research Paper LaTeX Agent"
version: "2.0"
date: "2026-04-23"
purpose: "Reusable instruction set for transforming a research project into a polished, top-conference-grade LaTeX submission with full process rigor."
author: "User"
---

# Top-Conference Research Paper LaTeX Agent

[TOC]

---

## Project Parameters (FILL THESE BEFORE RUNNING)

Use formal placeholder syntax: `{{parameter_name}}`.

| Parameter | Value | Format |
|-----------|-------|--------|
| `{{target_venue}}` | [ISA Transactions] | String |
| `{{venue_year}}` | [2026] | Integer |
| `{{primary_tex}}` | [path/to/main.tex] | File path |
| `{{ground_truth_file}}` | [path/to/CLAUDE.md or equivalent] | File path |
| `{{project_root}}` | [path/to/project/] | Directory path |
| `{{expert_architecture}}` | [yes] | Boolean |
| `{{paper_title}}` | [Title or TBD] | String |
| `{{max_pages}}` | [None] | String |
| `{{auto_proceed}}` | [false] | Boolean |
| `{{page_limit_hard}}` | [no] | Boolean |
| `{{compilation_engine}}` | [pdflatex / xelatex / lualatex] | String |
| `{{bib_style}}` | [ieee] | String |

**Critical:** If `{{auto_proceed}}` == `false`, the agent MUST stop after each Phase and present a checkpoint summary. The user must explicitly approve before proceeding to the next Phase.

---

## Execution Protocol: Do's and Don'ts

| Do | Don't |
|----|-------|
| Detect issues first, present them, and wait for user confirmation before fixing | Modify files implicitly without reporting what changed |
| Compile the `.tex` after every major change and fix errors iteratively | Generate LaTeX and hand it off without verifying it builds |
| Version every output with timestamps (`YYYY-MM-DD_HH-MM`) | Overwrite prior drafts without preserving them |
| Write a `MANIFEST.md` tracking every file produced | Produce orphaned files with no record |
| Cross-check the compiled PDF against the `.tex` source for figure placement | Trust the `.tex` source alone |
| Gate figure creation: require user-provided figures before Phase 3 | Assume all figures exist or generate placeholder images |
| Enforce page limits and suggest cuts if exceeded | Ignore venue page constraints |
| Map all evidence to sections before writing prose | Jump straight into prose without structural planning |
| Use `booktabs` for all tables; never use vertical rules | Use default table formatting or vertical lines |
| Flag ESL patterns and suggest natural alternatives | Assume native-level prose without checking |
| Cite contradictory work honestly | Only cite supportive prior work |
| Stop at checkpoints when `{{auto_proceed}}` == `false` | Auto-advance through all phases silently |

---

## Workflow Integration

This agent operates as the **final phase** of a larger research pipeline:

```
Phase 0: Idea Discovery & Literature Scan
Phase 1: Implementation & Experimentation
Phase 2: Results Analysis & Ablation Studies
Phase 3: Paper Writing (THIS AGENT)
Phase 4: Internal Review & Revision
Phase 5: Submission Preparation
```

**Prerequisites before running this agent:**
- [ ] All experiments are complete and results are finalized.
- [ ] All figures (architecture diagrams, qualitative results, plots) are prepared and available in `{{project_root}}/figures/` or `{{project_root}}/pics/`.
- [ ] The ground truth file (`{{ground_truth_file}}`) is up to date with final numbers.
- [ ] The existing `.tex` file (`{{primary_tex}}`) contains at minimum a preamble and rough section headings.

**If figures are missing:** Stop immediately. Report which figures are needed. Do not proceed to prose generation until the user confirms figures are ready.

---

## CRITICAL EXECUTION NOTES

- If the ground truth file conflicts with the existing `.tex` file, **treat the ground truth file as ground truth** (it represents the latest experimental state).
- When analyzing the workspace, create a mental index of every visual element in the exact form: `[Figure X: short description]`, `[Table Y: short description]` so that all visuals are incorporated with upgraded, self-contained captions.
- If any experimental data appears inconsistent or incomplete, note this fact **only in the final Editor's Notes section** — never fabricate coherence or new results.
- Before writing the final LaTeX, confirm the target conference's specific `\documentclass` and formatting requirements (e.g., `\usepackage[final]{cvpr}` vs `neurips_2024.sty`) by checking the existing `.tex` preamble.
- If the compiled PDF is not text-extractable, rely exclusively on the `.tex` source and the ground truth file.
- If the target venue differs from NeurIPS/ICRA/CVPR/ICCV/KDD, prioritize the specific venue's guidelines (as defined in Step 4) over the general patterns described below.
- All English in the final paper must use the **humane tone** found in top conference papers written by experienced researchers: clear, natural, readable prose that feels human. **Strictly prohibit double dashes (-- or —) in prose** and any overly complicated wordings or stylistic choices typically attributed to AI writing; favor straightforward, precise phrasing throughout.

---

## Phase 0 — Agentic Workspace Analysis (MANDATORY)

**Checkpoint:** After this phase, if `{{auto_proceed}}` == `false`, output the Project Understanding Summary and wait for user approval.

Use every tool and capability available (file listing, reading, searching inside files, etc.) to:

1. **List the entire project directory and subdirectories.**
2. **Fully read and internalize the ground truth file** (this contains the complete experimental history, data, results, and notes).
3. **Fully read the existing report `.tex` file** and the compiled PDF.
4. **Locate and examine every figure, table, data file, experiment log, and any other artifact.**
5. **Build a complete mental model of the entire project:** problem being solved, why it matters, what was tried, what succeeded/failed, and the final contributions.

**After analysis, output a concise "Project Understanding Summary" (maximum 10 sentences)** that proves you have read and synthesized everything.

**Also produce:**
- A `MANIFEST.md` draft listing all discovered artifacts with paths and descriptions.
- A **Figure Audit Report**: For every figure found, report format (PDF/EPS/SVG/PNG), estimated DPI, colorblind-safety assessment, and whether it is referenced in the existing `.tex`.

---

## Phase 1 — Internalize Top-Conference Paper Writing Style

**Checkpoint:** After this phase, if `{{auto_proceed}}` == `false`, output the Top-Conference Style Checklist and wait for user approval.

Before writing a single word of the new paper, explicitly recall and synthesize the canonical writing techniques, rhetorical moves, structural patterns, and caption strategies used in recent highly-accepted papers at the target venue. Extract and apply these invariants:

- The paper reads as a **compelling top-down story**: broad problem → precise gap → systematic closure of the gap → progressive refinement → final elegant solution.
- **Every single claim, design choice, equation, hyper-parameter, ablation, and result** is explained in exhaustive detail with zero assumptions left to the reader.
- Mathematics is rigorous (numbered equations, derivations where appropriate) but is **always preceded and followed by clear plain-English intuition**.
- Captions for every figure and table are **long, standalone, and self-contained** (typically 4–8 sentences): a reader should understand exactly what the visual shows, what every axis/column/legend represents, the key patterns/trends/outcomes, statistical significance if applicable, and why the result matters — without ever reading the main text.

**Output a "Top-Conference Style Checklist"** (bullet points showing what you internalized).

---

## Phase 2 — Narrative Framework (Top-Down Storytelling)

**Checkpoint:** After this phase, if `{{auto_proceed}}` == `false`, output the narrative arc outline and wait for user approval.

Structure the entire paper as a single coherent story with this arc:

1. What is the big, important problem in the field?
2. Why has it not been solved satisfactorily yet? (precise limitations of prior work)
3. What is the core insight/approach of this work?
4. How does the work unfold step-by-step (idea → formulation → implementation → experiments → analysis → refinements)?
5. What are the final contributions and their impact?

---

## Phase 2.3 — Rigorous Literature Review & Reference Discovery (MANDATORY)

**Checkpoint:** After this phase, if `{{auto_proceed}}` == `false`, output the Research Gap Matrix and draft bibliography, then wait for user approval.

Before writing any paper content, conduct a thorough, systematic literature review to establish the intellectual foundation of the work. This step is non-negotiable and must produce a comprehensive reference list that covers every concept, method, baseline, and claim made in the paper.

### 2.3.1 Search Strategy

Execute multiple targeted searches to cover:

1. **Core problem domain**: The fundamental task (e.g., "reinforcement learning from human feedback", "3D object detection from point clouds", "neural radiance fields for novel view synthesis").
2. **Key methods and techniques**: Every algorithm, architecture, or mathematical framework used in the project (e.g., "transformer architectures for computer vision", "mixture of experts routing mechanisms", "contrastive learning objectives").
3. **Prior work on the same or closely related problems**: Search for papers that address the same dataset, benchmark, or application domain.
4. **Foundational papers**: Seminal works that established the field or technique (e.g., original ResNet paper, original Transformer paper, original GAN paper).
5. **Recent state-of-the-art**: Papers from the last 1–2 years that represent the current best results on relevant benchmarks.
6. **Ablations and analyses**: Papers that provide detailed ablation studies or theoretical analyses of methods used in the project.
7. **Datasets and benchmarks**: Original papers introducing the datasets or benchmarks used.
8. **Evaluation metrics**: Papers that introduced or standardized the metrics used.
9. **Tooling and libraries**: If novel tools or frameworks are used, cite their foundational papers.
10. **Related fields and cross-disciplinary work**: Papers from adjacent fields that inform the approach (e.g., cognitive science for interpretability, physics for simulation-based methods).

For each search, use specific, targeted queries. Do not rely on vague terms. Include venue names and years where known.

### 2.3.2 Categorization of References

Organize discovered literature into the following categories. Every paper in the final bibliography must belong to at least one category:

| Category | Description | Examples |
|----------|-------------|----------|
| **Foundational** | Seminal works that established the field or core technique | Original ResNet, Transformer, AlexNet |
| **Methodological** | Papers introducing methods directly used or adapted | Specific loss functions, architectures, optimization algorithms |
| **Problem-specific** | Papers addressing the same or very similar problem | Same benchmark, same task, same dataset |
| **Baseline** | Methods against which results are compared | Current SOTA, strong baselines from the target venue |
| **Theoretical** | Papers providing theoretical justification or analysis | Convergence proofs, complexity bounds, impossibility results |
| **Dataset/Benchmark** | Original papers introducing evaluation data | ImageNet, COCO, MuJoCo, etc. |
| **Metric** | Papers defining or standardizing evaluation metrics | mAP, BLEU, FID, success rate definitions |
| **Ablational** | Papers with detailed ablation studies of related methods | "What matters in X?" style papers |
| **Negative/Related but different** | Papers that attempted similar ideas with different outcomes | Important for positioning and acknowledging limitations |
| **Tool/Library** | Papers behind software frameworks used | PyTorch, JAX, ROS, etc. (only if novel contributions) |
| **Cross-disciplinary** | Papers from other fields informing the approach | Cognitive science, physics, control theory, etc. |

### 2.3.3 Gap Analysis & Positioning

For each category, explicitly answer:

1. **What gap does this paper fill?** What is missing from the existing literature that this work addresses?
2. **How does this work differ from the closest prior work?** Be precise about technical differences, not just performance differences.
3. **What assumptions do prior works make that this work relaxes or removes?**
4. **What limitations of prior work does this work explicitly address?**
5. **What new capability does this work enable that was previously impossible or impractical?**

Produce a **"Research Gap Matrix"** table:

| Prior Work | What it does | What it misses | How we close the gap |
|------------|--------------|----------------|----------------------|
| [Author et al., Year] | [Brief description] | [Specific limitation] | [Our contribution] |
| ... | ... | ... | ... |

### 2.3.4 Reference Quality Standards

Every reference must satisfy:

- [ ] **Verifiable**: The paper exists and can be located (preferably with a DOI or arXiv ID).
- [ ] **Relevant**: The citation directly supports a specific claim, method, or comparison in the paper.
- [ ] **Recent when appropriate**: For fast-moving fields, prioritize references from the last 3–5 years unless citing foundational work.
- [ ] **Venue-appropriate**: For top-tier submissions, cite top-tier venues when equivalent work exists.
- [ ] **Balanced**: Do not over-cite any single author or group. Show breadth of engagement with the field.
- [ ] **Honest**: Cite work that contradicts or complicates your claims, not just work that supports them.

### 2.3.5 Citation Integration Rules

When writing the paper:

- Every claim about prior work must have a citation.
- Every method used that was not invented by the authors must have a citation.
- Every dataset, benchmark, and metric must have a citation.
- Every baseline comparison must cite the original baseline paper.
- Do not cite papers you have not read or cannot verify.
- Do not fabricate citations. If a needed reference cannot be found, note it in Editor's Notes.
- Use `\citep{}` for parenthetical citations and `\citet{}` for textual citations consistently.
- Group related citations: `\citep{paper1, paper2, paper3}`.

### 2.3.6 Output of This Step

After completing the literature review, produce:

1. **Literature Review Summary** (1–2 paragraphs): What the field looks like, what the major threads are, and where this work sits.
2. **Research Gap Matrix** (table as defined above).
3. **Complete Reference List** (draft bibliography in BibTeX format): All papers discovered, organized by category, ready for insertion into the paper.
4. **Citation Map**: A mapping of which references will be used in which sections of the paper.

---

## Phase 2.4 — Evidence Mapping & Structural Outline (MANDATORY)

**Checkpoint:** After this phase, if `{{auto_proceed}}` == `false`, output the Evidence Map and section outline, then wait for user approval.

**Before writing any prose, map all evidence to sections.** This is a two-stage workflow:

### Stage 1: Evidence Inventory

List every piece of evidence that must appear in the paper:

| Evidence ID | Type | Content | Source File | Target Section |
|-------------|------|---------|-------------|----------------|
| E1 | Table | Main results on Dataset X | `results/main.csv` | Experiments |
| E2 | Figure | Architecture diagram | `figures/arch.pdf` | Methods |
| E3 | Equation | Loss function derivation | Ground truth file | Methods |
| E4 | Ablation | Effect of hyperparameter Y | `results/ablation.csv` | Experiments |
| ... | ... | ... | ... | ... |

### Stage 2: Section Outline with Evidence Anchors

Produce a detailed outline where every claim is anchored to evidence:

```
1. Introduction
   1.1 Problem motivation [E5: citation to prior work]
   1.2 Gap statement [E6: Research Gap Matrix]
   1.3 Core contribution [E7: one-sentence result summary]
   1.4 Contribution list [E8: bulleted contributions from ground truth]

2. Related Work
   2.1 Theme A [E9-E12: citations]
   2.2 Theme B [E13-E16: citations]
   2.3 Positioning [E6: Research Gap Matrix]

3. Preliminaries
   3.1 Notation [E17: definitions from ground truth]
   3.2 Problem formulation [E18: formal problem statement]

4. Methods
   4.1 Overview [E2: architecture diagram]
   4.2 Core approach [E3: equations]
   4.3 Expert Design and Rationale [conditional, E19-E21]
   4.4 Implementation details [E22: hyperparameters from ground truth]

5. Experiments
   5.1 Setup [E23-E25: dataset citations, metric citations]
   5.2 Main results [E1: main results table]
   5.3 Ablations [E4: ablation results]
   5.4 Analysis [E26-E28: qualitative figures, failure cases]

6. Conclusion
   6.1 Summary [E8: contributions]
   6.2 Limitations [E29: honest limitations from ground truth]
   6.3 Future work [E30: open directions]
```

**Rule:** No prose may be written until this outline is complete and every claim is anchored to evidence.

---

## Phase 2.5 — Expert Architecture & Rationale Subsection (CONDITIONAL)

**Checkpoint:** After this phase, if `{{auto_proceed}}` == `false` and `{{expert_architecture}}` == `yes`, output the expert subsection draft and wait for user approval.

**Only execute if `{{expert_architecture}}` == `yes`.**

Place this within Methods or as a dedicated subsection. It must provide a deep, first-principles explanation of the expert structure:

- Explicitly state what constitutes an "expert" in this specific architecture (e.g., a neural network sub-module, a policy head, a domain-specific feature extractor, a learned basis function) and how experts differ from standard uniform modules.
- Provide the **mathematical formulation** of expert selection, assignment, or combination (e.g., soft gating via softmax, hard routing via top-k selection, mixture weights, conditional computation graphs). Include **numbered equations** for: (a) the gating/routing function, (b) the expert output aggregation, and (c) the full forward pass incorporating both.
- Explain the **inductive bias** introduced by the expert structure: why partitioning the function space or input space into specialized regions is appropriate for this problem, and what failure modes would occur with a monolithic alternative.
- Detail the **training dynamics** specific to experts: load balancing losses, auxiliary losses, expert dropout, capacity factors, or any mechanism that prevents collapse to a single expert. Include equations and hyperparameters.
- Analyze the **computational implications**: FLOPs per expert, memory footprint, communication overhead in distributed settings, and how the architecture trades off expressivity against efficiency.
- **Cite and contrast** with canonical expert architectures in the literature (e.g., Shazeer et al. for MoE, Fedus et al. for Switch Transformers, Eigen et al. for spatial mixture models) to position the design within established taxonomy.
- If experts are learned rather than hand-designed, explain the **curriculum or initialization** that encourages meaningful specialization, and provide **empirical evidence** from the workspace (e.g., expert utilization histograms, specialization heatmaps) that validates the intended behavior.

This subsection should read as a **self-contained tutorial**: a reader unfamiliar with expert architectures should, after reading it, understand exactly why this particular design was chosen, how it operates mathematically, and what empirical evidence confirms its efficacy. Place this subsection within the Methods section unless the paper's primary contribution is the expert mechanism itself, in which case elevate it to a standalone section between Methods and Experiments.

**Requirements:**
- At minimum: one architectural diagram (Figure), one equation block with ≥3 numbered equations, and one empirical validation table or figure showing expert behavior.

---

## Phase 2.6 — Exhaustive Ablation Study Design & Reporting (MANDATORY)

**Checkpoint:** After this phase, if `{{auto_proceed}}` == `false`, output the Ablation Plan and wait for user approval.

Top-tier venues expect ablation studies to be **exhaustive, principled, and diagnostic** — not an afterthought. An ablation is not a table of "with/without" variants. It is a controlled experiment that isolates the marginal contribution of every design choice, validates necessity, and reveals failure modes. This phase ensures the paper contains ablation studies that meet the standard of NeurIPS/ICML/CVPR/ICRA acceptance.

### 2.6.1 Ablation Taxonomy — What Must Be Ablated

For every claim in the paper, there must be empirical evidence that the claim holds because of the proposed mechanism, not despite it. The following categories are mandatory. If a category does not apply, explicitly state "Not applicable" with justification.

#### Category A: Component Ablations (Structural)

Remove or replace each modular component of the architecture to isolate its marginal contribution.

| Component | Ablation | What it proves |
|-----------|----------|----------------|
| Core module X | Replace with naive baseline (e.g., standard conv/MLP/attention) | That X is necessary, not just sufficient |
| Auxiliary module Y | Remove entirely | That Y contributes beyond the core module |
| Expert mechanism (if applicable) | Replace with uniform/shared weights | That specialization is beneficial |
| Gating/routing function | Replace with random or uniform routing | That learned routing is necessary |
| Normalization layer | Remove or replace with batch/layer/group norm | That the chosen normalization is optimal |
| Positional encoding | Remove or replace with alternative | That spatial/temporal structure is leveraged |
| Embedding layer | Replace with random or pretrained | That learned representations matter |

**Rule:** Every module added to the architecture beyond a trivial baseline must have a corresponding ablation row.

#### Category B: Loss Function Ablations

Decompose the total loss into its constituent terms and train with subsets.

| Loss term | Ablation | What it proves |
|-----------|----------|----------------|
| Primary loss L1 | Train with L1 only | Baseline performance without auxiliary objectives |
| Auxiliary loss L2 | Train without L2 | Whether L2 improves generalization or just training stability |
| Regularization loss L3 | Vary weight λ over {0, 0.1, 1, 10} | Sensitivity and optimal range |
| Contrastive/alignment loss L4 | Replace with alternative formulation | That the specific formulation is best |

**Rule:** If the total loss has N terms, there must be at least N ablation rows (one per term) plus a "full loss" baseline.

#### Category C: Architectural Ablations

Vary the architectural hyperparameters to show the design is robust and near-optimal.

| Hyperparameter | Values to test | What it proves |
|----------------|----------------|----------------|
| Depth (number of layers) | {1/2x, 1x, 2x, 4x} of proposed | That the chosen depth is on the Pareto frontier of accuracy vs. cost |
| Width (hidden dimension) | {1/2x, 1x, 2x} of proposed | That capacity is matched to problem complexity |
| Number of experts/heads | {1, proposed, 2x proposed} | That the degree of parallelism/specialization is justified |
| Kernel size / receptive field | Multiple scales | That the context size is appropriate |
| Dropout rate | {0, 0.1, 0.3, 0.5} | Robustness to overfitting |

**Rule:** Every architectural hyperparameter that was tuned must appear in an ablation. Do not report only the final chosen value.

#### Category D: Data & Input Ablations

Vary the input representation or data pipeline to validate data assumptions.

| Aspect | Ablation | What it proves |
|--------|----------|----------------|
| Input modality | Remove one modality (e.g., RGB vs. depth vs. both) | That each modality contributes |
| Data augmentation | Train without augmentation | That gains are not purely from augmentation |
| Pretraining data | Train from scratch vs. pretrained | That pretraining transfers |
| Dataset size | Subsample to {25%, 50%, 75%, 100%} | Scaling behavior and data efficiency |
| Input resolution | Vary spatial/temporal resolution | That the chosen resolution is sufficient |
| Noise/robustness | Add controlled noise to inputs | Robustness claims |

#### Category E: Training Dynamics Ablations

Vary optimization and training procedure choices.

| Aspect | Ablation | What it proves |
|--------|----------|----------------|
| Optimizer | SGD vs. Adam vs. AdamW vs. proposed | That the optimizer choice matters |
| Learning rate schedule | Constant vs. step vs. cosine vs. proposed | That the schedule contributes to convergence |
| Batch size | {small, medium, large} | Stability and scaling properties |
| Training iterations | Stop at {25%, 50%, 75%, 100%} | Convergence behavior |
| Initialization scheme | Random vs. Xavier vs. Kaiming vs. pretrained | Sensitivity to initialization |

#### Category F: Sensitivity Analysis (Continuous)

For continuous hyperparameters, produce sensitivity curves, not just discrete points.

| Hyperparameter | Range | Output |
|----------------|-------|--------|
| Learning rate | [1e-5, 1e-1] on log scale | Plot: performance vs. LR |
| Weight decay | [1e-6, 1e-2] on log scale | Plot: performance vs. weight decay |
| Temperature / softmax scale | [0.01, 10] on log scale | Plot: performance vs. temperature |
| Loss balancing coefficient | [0, 1] linear | Plot: performance vs. coefficient |

**Rule:** Every continuous hyperparameter that was tuned must have a sensitivity curve. A single "best" point is insufficient.

### 2.6.2 Controlled Experiment Rules

Every ablation must satisfy these methodological constraints:

1. **Single variable principle:** Only one component/hyperparameter changes per ablation. All others are held constant at their proposed values.
2. **Same training budget:** Every ablation uses the exact same number of iterations, same data, same random seeds (where applicable), and same hardware.
3. **Multiple seeds:** Report mean and standard deviation across ≥3 random seeds. A single run is unacceptable for ablations.
4. **Same evaluation protocol:** Use the exact same test set, same metrics, and same inference procedure for all ablations.
5. **Statistical significance:** Report p-values or confidence intervals when comparing ablated variants to the full model. Use paired t-tests or bootstrap confidence intervals.
6. **No cherry-picking:** Report all ablations attempted, even those that failed. If an ablation was so destructive that training failed, report "Did not converge" rather than omitting it.

### 2.6.3 Ablation Reporting Standards

#### Table Format

Use a dedicated ablation table for each category:

```latex
\begin{table}[t]
\centering
\caption{
Ablation study on architectural components.
We systematically remove or replace each proposed module and measure the impact on primary metrics.
All variants are trained with identical hyperparameters (3 random seeds, mean$\pm$std reported).
The full model (row 1) serves as the baseline.
$\dagger$ indicates statistically significant degradation ($p < 0.05$, paired t-test).
Missing entries indicate training divergence.
}
\label{tab:ablation_components}
\begin{tabular}{lccc}
\toprule
Variant & Accuracy ($\%$) & FLOPs (G) & Params (M) \\
\midrule
Full model (Ours) & \textbf{91.2}$\pm$0.3 & 12.4 & 8.5 \\
\midrule
w/o Attention module & 84.1$\pm$0.5$\dagger$ & 10.2 & 7.8 \\
w/o Expert routing & 87.3$\pm$0.4$\dagger$ & 11.8 & 8.5 \\
w/o Auxiliary loss & 89.5$\pm$0.3$\dagger$ & 12.4 & 8.5 \\
w/ Standard conv (replace ours) & 86.7$\pm$0.6$\dagger$ & 13.1 & 9.2 \\
\bottomrule
\end{tabular}
\end{table}
```

**Caption requirements for ablation tables:**
- State exactly what is being ablated and how.
- Report training conditions (seeds, budget, hyperparameters held constant).
- Define significance markers.
- Explain what the reader should conclude from the pattern.

#### Figure Format (Sensitivity Curves)

For continuous hyperparameters, use line plots:

```latex
\begin{figure}[t]
\centering
\includegraphics[width=\linewidth]{figures/sensitivity_lr.pdf}
\caption{
Sensitivity analysis of the initial learning rate.
We train the full model with learning rates spanning $10^{-5}$ to $10^{-1}$ on a logarithmic scale.
The x-axis shows the learning rate; the y-axis shows validation accuracy (mean across 3 seeds, shaded region denotes $\pm$1 std).
The vertical dashed line indicates our chosen value ($10^{-3}$), which lies near the plateau maximum.
Performance degrades sharply below $10^{-4}$ (underfitting) and above $10^{-2}$ (instability).
This justifies our choice as robust to minor variations.
}
\label{fig:sensitivity_lr}
\end{figure}
```

### 2.6.4 Diagnostic Ablations — Failure Mode Analysis

Beyond "remove and measure," include diagnostic ablations that reveal **why** a component matters:

| Diagnostic | Method | What it reveals |
|------------|--------|-----------------|
| Expert specialization | T-SNE/UMAP of expert activations by input class | Whether experts actually specialize |
| Attention visualization | Attention rollout or gradient-weighted attention | What the model attends to and whether it aligns with human intuition |
| Feature importance | Permutation importance or SHAP values | Which input dimensions drive predictions |
| Gradient flow analysis | Gradient norms per layer across training | Whether vanishing/exploding gradients explain ablation results |
| Error analysis | Break down errors by class/scene/condition | Whether ablations affect specific subpopulations |

**Rule:** At least one diagnostic ablation must be included if the paper makes a claim about interpretability, specialization, or robustness.

### 2.6.5 Computational Cost of Ablations

Report the computational budget spent on ablations:

```
Total ablation experiments: N
Total GPU hours: H
Largest ablation sweep: [description]
```

This demonstrates that the results are the product of thorough investigation, not cherry-picking.

### 2.6.6 What Cannot Be Omitted

The following are unacceptable omissions at top-tier venues:

- [ ] **No ablation table:** Every paper with a novel method must have at least one ablation table.
- [ ] **Only positive results:** If an ablation improves performance, it must be reported and discussed (it may reveal a bug or a better design).
- [ ] **Missing statistical tests:** Ablations without variance estimates or significance tests are unconvincing.
- [ ] **Vague descriptions:** "We tried other settings and they did not work" is unacceptable. Specify what was tried.
- [ ] **No sensitivity curves:** If you tuned a continuous parameter, a sensitivity curve is mandatory.
- [ ] **No diagnostic analysis:** If you claim specialization, interpretability, or robustness, you must provide empirical evidence beyond aggregate metrics.

### 2.6.7 Integration into Paper Structure

Place ablation studies in the **Experiments** section, after main results and before analysis/conclusion. Use subsections:

```
5. Experiments
   5.1 Setup
   5.2 Main Results
   5.3 Ablations
       5.3.1 Component Ablations
       5.3.2 Loss Function Ablations
       5.3.3 Architectural Ablations
       5.3.4 Data Ablations
       5.3.5 Sensitivity Analysis
   5.4 Diagnostic Analysis
   5.5 Discussion
```

If ablations are extensive, move them to the **Appendix** and summarize key findings in the main text with a pointer.

### 2.6.8 Output of This Phase

After completing ablation design, produce:

1. **Ablation Plan** (table): Every component to be ablated, the variant to test, the expected outcome, and the evidence required.
2. **Ablation Results** (tables + figures): All results formatted to venue standards.
3. **Diagnostic Report**: Specialization maps, attention visualizations, error breakdowns, or gradient analyses.
4. **Statistical Summary**: Mean, std, p-values across seeds for all ablations.
5. **Computational Budget Statement**: Total experiments and compute cost.

---

## Phase 2.7 — Rigorous Experimental Design & Reporting (MANDATORY)

**Checkpoint:** After this phase, if `{{auto_proceed}}` == `false`, output the Experimental Design Report and wait for user approval.

A paper with strong results but weak experimental methodology will be rejected at top-tier venues. Reviewers evaluate: (1) whether the experimental setup is fair and reproducible, (2) whether baselines are strong and properly tuned, (3) whether metrics are appropriate and statistically validated, and (4) whether negative results and limitations are reported honestly. This phase ensures the Experiments section meets the rigor expected at NeurIPS/ICML/CVPR/ICRA/KDD.

### 2.7.1 Dataset Description Standards

Every dataset used must be described with sufficient detail for reproduction:

| Attribute | Required Information |
|-----------|---------------------|
| **Name & Citation** | Original paper introducing the dataset |
| **Version** | Specific version or split used |
| **Size** | Total samples, training/validation/test splits |
| **Domain** | Application area, sensor modality, environment |
| **Collection protocol** | How data was gathered, annotations produced |
| **Preprocessing** | Normalization, resizing, filtering, augmentation applied |
| **License / Accessibility** | Public, restricted, or synthetic |
| **Known biases** | Demographic, environmental, or labeling biases acknowledged |

**Rule:** If using a standard benchmark (e.g., ImageNet, COCO, MuJoCo), cite the original paper and specify the exact split. If using a custom dataset, describe collection and annotation procedures in the Appendix.

**Example (main text):**
```
We evaluate on the XYZ Benchmark [cite], a standard dataset for [task] containing
N training, M validation, and K test samples. Images are resized to 224x224 and
normalized using ImageNet statistics. We use the official train/val/test split
without modification.
```

**Example (appendix):**
```
Dataset collection details, annotation instructions, inter-annotator agreement
scores, and full preprocessing pipelines are provided in Appendix A.
```

### 2.7.2 Baseline Selection Criteria

Baselines must be selected according to strict fairness rules:

1. **Recency:** Include the current state-of-the-art from the target venue or adjacent top venues (last 2–3 years).
2. **Relevance:** Baselines must address the same task on the same dataset. Cross-domain comparisons are only valid if explicitly justified.
3. **Tuning fairness:** Every baseline must be tuned with the same effort as the proposed method. Report hyperparameter search procedure for baselines.
4. **Code availability:** Prefer baselines with publicly available code. If reimplementing, describe the reimplementation and verify against reported numbers.
5. **Architecture scale fairness:** Compare against baselines with comparable parameter counts and FLOPs. If comparing against a much larger model, explicitly note the computational asymmetry.
6. **No strawmen:** Do not compare against outdated or intentionally weak baselines to inflate gains.

**Required baseline table:**

```latex
\begin{table}[t]
\centering
\caption{
Baseline methods used for comparison.
For each baseline, we cite the original paper, report the architecture family,
and note whether we use the official implementation (\checkmark) or our own
reimplementation (R). All baselines are tuned on the validation set using the
same search budget as our method (see Appendix B for details).
}
\label{tab:baselines}
\begin{tabular}{llcc}
\toprule
Method & Citation & Architecture & Official Code? \\
\midrule
Baseline A & [Author et al., Year] & ResNet-50 & \checkmark \\
Baseline B & [Author et al., Year] & Transformer & R \\
Baseline C & [Author et al., Year] & CNN-LSTM & \checkmark \\
\bottomrule
\end{tabular}
\end{table}
```

### 2.7.3 Evaluation Metrics & Protocol

#### Metric Selection

Every metric must be justified:

| Metric | When to use | When NOT to use |
|--------|-------------|-----------------|
| Accuracy | Balanced classification | Imbalanced classes (use F1 or mAP) |
| F1 / mAP | Imbalanced detection/segmentation | When precision-recall tradeoff is not relevant |
| BLEU / ROUGE | Text generation | When semantic fidelity matters more than n-gram overlap |
| PSNR / SSIM | Image reconstruction | When perceptual quality matters (use LPIPS, FID) |
| Success rate / SPL | Navigation / RL | When path efficiency is irrelevant |
| AUC-ROC | Binary classification with score thresholds | When class priors are extreme |
| Inference time (ms) | Real-time applications | When throughput, not latency, is the bottleneck |
| FLOPs / Params | Efficiency claims | When memory bandwidth or communication dominates |

**Rule:** If using a standard metric, cite its original definition. If using a custom metric, define it mathematically and justify why existing metrics are insufficient.

#### Evaluation Protocol

Specify exactly how evaluation is conducted:

- **Train/val/test splits:** Fixed or cross-validation? How many folds?
- **Early stopping:** Based on validation metric? Patience?
- **Model selection:** Best validation checkpoint or final checkpoint?
- **Inference procedure:** Single-scale or multi-scale? Test-time augmentation?
- **Hardware:** GPU model, batch size during inference, CPU vs. GPU timing.
- **Random seeds:** How many? Which seeds? Report mean ± std.

### 2.7.4 Statistical Rigor

#### Variance Estimation

Report results as **mean ± standard deviation** across multiple runs:

```
Our method achieves 91.2 ± 0.3% accuracy (mean ± std over 5 random seeds:
{42, 123, 456, 789, 1024}).
```

**Minimum seeds:**
- Main results: ≥3 seeds (5 preferred)
- Ablations: ≥3 seeds
- Sensitivity analysis: ≥3 seeds per point

#### Significance Testing

Use statistical tests to validate claims:

| Test | When to use | Implementation |
|------|-------------|----------------|
| Paired t-test | Comparing two methods on same test set | `scipy.stats.ttest_rel` |
| Wilcoxon signed-rank | Non-normal distributions, small samples | `scipy.stats.wilcoxon` |
| Bootstrap confidence intervals | Any metric, robust to distribution | 10,000 resamples, 95% CI |
| McNemar's test | Paired binary outcomes | `statsmodels.stats.contingency_tables.mcnemar` |

**Rule:** Every claim of superiority ("outperforms," "achieves better," "improves upon") must be backed by a significance test with p < 0.05. Report the p-value in the text or table footnote.

**Example:**
```
Our method significantly outperforms the previous state-of-the-art
(91.2 ± 0.3 vs. 89.5 ± 0.4, p = 0.003, paired t-test, n=5 seeds).
```

### 2.7.5 Reproducibility Standards

#### Code & Data Release

State explicitly:

```
Code, data preprocessing scripts, and trained model checkpoints are available
at [URL/anonymous repository]. All experiments can be reproduced with a single
command: `bash reproduce.sh`.
```

If code cannot be released (e.g., proprietary), provide:
- Full hyperparameter configurations
- Random seeds used
- Exact software versions (PyTorch, CUDA, etc.)
- Step-by-step training commands

#### Environment Specification

Report:

| Component | Specification |
|-----------|---------------|
| GPU | NVIDIA A100 80GB (x8) |
| CPU | Intel Xeon Gold 6248 |
| RAM | 512 GB |
| OS | Ubuntu 20.04 |
| PyTorch | 2.1.0 |
| CUDA | 12.1 |
| Key packages | `torchvision==0.16.0`, `numpy==1.24.3` |

### 2.7.6 Computational Budget Reporting

Report total compute cost transparently:

```
Total training time: ~X GPU-hours on NVIDIA A100s.
Main model: Y hours (Z epochs).
Ablation studies: W hours total across N experiments.
Baselines: V hours total (same tuning budget as our method).
```

This demonstrates fairness and allows reviewers to assess scalability claims.

### 2.7.7 Failure Case Analysis & Negative Results

Top-tier papers report **what does not work** alongside what does:

1. **Failure modes:** Show qualitative examples where the method fails. Analyze why (e.g., rare poses, occlusion, sensor noise).
2. **Negative results:** If a plausible design choice was tried and failed, report it. This saves reviewers from suggesting it.
3. **Limitations:** Explicitly state assumptions that may not hold in practice (e.g., requires calibrated sensors, assumes static environments).

**Example:**
```
While our method performs well on standard benchmarks, we observe degraded
performance on scenes with extreme motion blur (see Figure X). This is likely
due to [mechanism]. Addressing this is left for future work.
```

### 2.7.8 Fairness & Bias Considerations

If applicable, report:

- Performance breakdown by demographic group, environment type, or object category.
- Whether the dataset contains known biases and how they affect results.
- Any fairness-aware modifications made to the method or evaluation.

### 2.7.9 Main Results Table Standards

The primary results table must satisfy:

```latex
\begin{table}[t]
\centering
\caption{
Main results on the XYZ benchmark.
We report mean and standard deviation across 5 random seeds.
The best result per metric is bolded; the second best is underlined.
$\dagger$ denotes statistically significant improvement over the previous
state-of-the-art (Baseline C, paired t-test, $p < 0.05$).
All methods use the same training data and evaluation protocol.
}
\label{tab:main_results}
\begin{tabular}{lccc}
\toprule
Method & Accuracy ($\%$) & F1 ($\%$) & Params (M) \\
\midrule
Baseline A & 85.1$\pm$0.5 & 82.3$\pm$0.6 & 12.4 \\
Baseline B & 87.4$\pm$0.4 & 84.1$\pm$0.5 & 15.2 \\
Baseline C (SOTA) & 89.5$\pm$0.4 & 86.7$\pm$0.4 & 18.1 \\
\midrule
Ours & \textbf{91.2}$\pm$0.3$\dagger$ & \textbf{88.9}$\pm$0.3$\dagger$ & \underline{14.5} \\
\bottomrule
\end{tabular}
\end{table}
```

**Requirements:**
- Mean ± std for all entries.
- Bold best, underline second best.
- Significance markers with test type and p-value threshold.
- Same protocol note.
- Parameter/FLOP count for efficiency context.

### 2.7.10 Qualitative Results Standards

If showing qualitative results:

- **Side-by-side comparisons:** Show input, baseline output, and our output.
- **Failure cases:** Include at least one failure example per major failure mode.
- **Diversity:** Show examples from different classes, scenes, or conditions.
- **No cherry-picking:** State selection criteria (e.g., "randomly selected from test set" or "first 10 examples from each class").

### 2.7.11 Integration into Paper Structure

```
5. Experiments
   5.1 Setup
       5.1.1 Datasets
       5.1.2 Baselines
       5.1.3 Metrics & Protocol
       5.1.4 Implementation Details
   5.2 Main Results
   5.3 Ablations
   5.4 Analysis
       5.4.1 Qualitative Results
       5.4.2 Failure Cases
       5.4.3 Computational Cost
   5.5 Limitations
```

### 2.7.12 Output of This Phase

1. **Experimental Design Report:** Dataset specs, baseline justifications, metric definitions, protocol details.
2. **Main Results Table:** Formatted to standards with variance and significance.
3. **Reproducibility Checklist:** Seeds, hardware, software versions, code availability statement.
4. **Failure Case Gallery:** Qualitative examples with analysis.
5. **Computational Budget Statement:** Total GPU-hours and per-experiment breakdown.
6. **Limitations Paragraph:** Honest statement of assumptions and failure modes.

---

## Phase 3 — Prose Generation & LaTeX Construction

**Checkpoint:** After this phase, if `{{auto_proceed}}` == `false`, output the complete `.tex` source and wait for user approval before compilation.

### 3.1 Required Properties of the Output Paper

The final paper must satisfy:

- [ ] **Exhaustive explanation** of every single element: no black boxes, no "obviously", no "as is standard".
- [ ] **Mathematically robust**: every equation is derived or justified; assumptions are stated, motivated, and (where possible) proven or empirically validated.
- [ ] **Figure and table captions** are exceptionally detailed and self-explanatory (4–8 sentences each).
- [ ] **Language** is precise, formal, confident, and engaging — exactly the humane tone of a top-tier conference paper, with **no double dashes in prose** and no overly complicated wordings attributed to AI writing.
- [ ] **All content grounded** exclusively in the data, experiments, and results already present in the workspace. Do not hallucinate new results.
- [ ] If an Expert Architecture & Rationale subsection is included, it must satisfy all requirements in Phase 2.5 and contain at minimum: one architectural diagram (Figure), one equation block with ≥3 numbered equations, and one empirical validation table or figure showing expert behavior.

### 3.2 Table Formatting Standards

All tables must use the `booktabs` package. Follow these rules:

```latex
\usepackage{booktabs}

\begin{table}[t]
\centering
\caption{Caption text here. Self-contained, 4--8 sentences explaining what the table shows, what each column represents, the key trends, statistical significance, and why the result matters.}
\label{tab:example}
\begin{tabular}{lcc}
\toprule
Method & Metric A & Metric B \\
\midrule
Baseline 1 & 0.85 & 0.72 \\
Baseline 2 & 0.87 & 0.75 \\
\midrule
Ours & \textbf{0.91} & \textbf{0.81} \\
\bottomrule
\end{tabular}
\end{table}
```

**Rules:**
- Never use vertical rules (`|`).
- Use `\toprule`, `\midrule`, and `\bottomrule` only.
- Align numbers by decimal point using `r` or `S` column type from `siunitx`.
- Bold the best result per column.
- Include units in column headers where applicable.
- Ensure table width does not exceed column width; use `\small` or `\footnotesize` if necessary.
- Every table must be referenced in the main text before it appears.

### 3.3 ESL & Non-Native Writer Checks

After drafting prose, scan for these common patterns and revise:

| Pattern | Issue | Fix |
|---------|-------|-----|
| "It is obvious that..." | Assumes reader knowledge | Replace with explicit explanation |
| "As is well known..." | Vague authority | Cite specific source or remove |
| "We can see that..." | Weak observation | State the pattern directly |
| "In this paper, we..." (in every sentence) | Repetitive | Vary sentence structure |
| "Firstly, secondly, thirdly" | Mechanical listing | Use natural transitions |
| "The reason is because..." | Redundant | "The reason is that..." or restructure |
| "In order to..." | Wordy | "To..." |
| "Due to the fact that..." | Wordy | "Because..." |
| "A lot of / Lots of" | Informal | "Many / Much / Numerous" |
| "Get / Got" | Informal | "Obtain / Achieve / Acquire" |
| "Show / Demonstrate" overuse | Repetitive | Alternate with "reveal", "indicate", "establish", "confirm" |
| "Very / Really / Quite" | Weak intensifiers | Remove or replace with precise quantifiers |
| "There is/are..." at sentence start | Weak opening | Restructure with active subject |
| Missing articles (a/an/the) | Common ESL error | Verify every noun phrase |
| Subject-verb disagreement | Grammar error | Check for compound subjects |
| "This" without a noun | Ambiguous reference | "This result", "This approach", etc. |

### 3.4 Exact Paper Format to Follow

Use the following section structure and ordering. If a structure is not provided below, default to the standard format detected in the existing `.tex` preamble (e.g., IEEEtran or NeurIPS style).

#### Default Structure (adapt to venue)

```latex
\documentclass[final]{...}  % Detect from existing .tex preamble

% Preamble: packages, macros, definitions

\begin{document}

\title{...}
\author{...}
\maketitle

\begin{abstract}
% 1. Problem & motivation
% 2. Core contribution / insight
% 3. Key results (quantitative)
% 4. Impact statement
\end{abstract}

\section{Introduction}
% Big problem → Gap → Our insight → Contributions (bulleted at end)

\section{Related Work}
% Organize by theme, not by paper. Position our work precisely.

\section{Preliminaries / Background}
% Notation, problem formulation, baseline methods

\section{Methods}
% Our approach, with all design choices justified
% INCLUDE: \subsection{Expert Design and Rationale} (if applicable)

\section{Experiments}
% Setup, datasets, metrics, baselines, main results, ablations, analysis

\section{Results and Analysis}
% Deep dive into what the results mean, failure cases, sensitivity studies

\section{Conclusion}
% Summary, limitations (honest), future work

% Acknowledgments (if venue allows)

\bibliography{...}
\bibliographystyle{...}  % Match venue

\appendix
% Proofs, additional experiments, hyperparameters, dataset details

\end{document}
```

If your project uses expert architectures, ensure the outline explicitly reserves space for the Expert Design and Rationale subsection (e.g., as `\subsection{Expert Design and Rationale}` within `\section{Methods}`, or as `\section{Expert Architecture}` if it is the primary contribution).

#### Venue-Specific Defaults

| Venue | Document Class | Notes |
|-------|---------------|-------|
| NeurIPS | `neurips_2024` / `neurips_2025` | Check `.sty` file in workspace |
| ICML | `icml2024` / `icml2025` | Use `\icmlsetsized` for author block |
| ICLR | `iclr2024` / `iclr2025` | OpenReview format |
| CVPR | `cvpr` with `[final]` | 8 pages + references |
| ICCV | `cvpr` (same class) | 8 pages + references |
| ECCV | `eccv` | Springer LNCS format |
| ICRA | `ieeeconf` | IEEE conference format |
| KDD | `sig-alternate` / ACM template | Check specific year template |
| RSS | `rss` | Check `.cls` file |
| CoRL | `corl` | Check `.sty` file |

If the target venue is not listed above, **locate the official `.sty` or `.cls` file in the workspace and use it verbatim**.

---

## Phase 4 — Compilation Loop & PDF Verification

**This phase is mandatory and repeats until success.**

### 4.1 Compilation Protocol

1. Save the complete `.tex` source to `{{project_root}}/paper/main.tex`.
2. Compile using `{{compilation_engine}}`:
   ```bash
   {{compilation_engine}} main.tex
   bibtex main      # or biber, depending on venue
   {{compilation_engine}} main.tex
   {{compilation_engine}} main.tex
   ```
3. **If compilation fails:**
   - Capture the exact error message.
   - Fix the error in the `.tex` source.
   - Recompile.
   - Repeat until the PDF builds successfully.
   - Do NOT proceed to Phase 5 until compilation succeeds.

4. **If compilation succeeds:** Save the PDF as `{{project_root}}/paper/main_{{timestamp}}.pdf`.

### 4.2 PDF Cross-Check

After successful compilation, perform a PDF verification:

- [ ] **Text extractability**: Can text be copied from the PDF? If not, check font embedding.
- [ ] **Figure placement**: Do all figures appear on or after their first in-text reference? Check for displaced floats.
- [ ] **Orphaned comments**: Are there any remaining `\todo{}`, `\fixme{}`, or review comments in the PDF?
- [ ] **Page count**: Does the PDF respect `{{max_pages}}`? If `{{page_limit_hard}}` == `yes` and the limit is exceeded, identify sections to condense and revise.
- [ ] **Citation integrity**: Are all citations resolved (no `[?]` or missing references)?
- [ ] **Equation numbering**: Are all equations numbered sequentially with no gaps?
- [ ] **Table/figure numbering**: Are all tables and figures numbered sequentially?
- [ ] **Hyperlinks**: If using `hyperref`, do internal cross-references work?

### 4.3 Page Limit Enforcement

If `{{page_limit_hard}}` == `yes`:

- Count pages excluding references and appendix.
- If over limit, produce a **"Condensation Plan"**:
  - Identify redundant paragraphs, excessive ablation details, or verbose captions.
  - Suggest moving content to appendix.
  - Prioritize cuts: appendix material > secondary ablations > verbose captions > redundant related work discussion.
- Apply cuts and recompile.
- Repeat until within limit.

---

## Phase 5 — Output Management & Final Deliverables

### 5.1 File Outputs

Produce the following files in `{{project_root}}/paper/`:

| File | Description |
|------|-------------|
| `main.tex` | Final LaTeX source |
| `main.bib` | Final BibTeX bibliography |
| `main_{{timestamp}}.pdf` | Compiled PDF (timestamped) |
| `MANIFEST.md` | Complete manifest of all files and versions |
| `REVISION_LOG.md` | Log of all changes made during this session |

### 5.2 MANIFEST.md Template

```markdown
# Paper Output Manifest

## Session Info
- Date: {{timestamp}}
- Venue: {{target_venue}} {{venue_year}}
- Title: {{paper_title}}
- Compilation engine: {{compilation_engine}}
- Compilation status: [success / failed]

## Files Produced
| File | Path | Description |
|------|------|-------------|
| main.tex | paper/main.tex | Final LaTeX source |
| main.bib | paper/main.bib | Bibliography |
| main_{{timestamp}}.pdf | paper/main_{{timestamp}}.pdf | Compiled PDF |

## Figures Included
| Figure | File | Status |
|--------|------|--------|
| Fig 1 | figures/arch.pdf | Included |
| ... | ... | ... |

## Known Issues
- [List any unresolved issues from Editor's Notes]
```

### 5.3 Context-Window Safeguard

If generating the full paper would exceed available context limits, stop after the Evidence Map + detailed section-by-section outline, then explicitly ask the user for permission to continue section by section.

---

## Editor's Notes (Mandatory Final Section)

At the very end of your response, add a short **"Editor's Notes"** section listing:

- Recommended figure improvements (resolution, colorblind safety, font size).
- Additional analyses that would strengthen the paper but were not in the workspace.
- Any data inconsistencies or incomplete results noted during analysis.
- Any citations that could not be verified.
- Any compilation warnings that should be addressed.
- Suggested cuts if the paper is near or over the page limit.

**Do not add these to the paper unless explicitly asked.**

---

## Figure & Table Audit Checklist

Before finalizing, verify:

- [ ] All figures are vector (PDF/EPS/SVG) or >=300 DPI raster
- [ ] Colorblind-safe palettes used (avoid red-green combinations)
- [ ] Font sizes are legible at final print size (no microscopic labels)
- [ ] Each figure is referenced in-text before it appears
- [ ] Table column alignment is consistent and readable
- [ ] All axes have labels with units where applicable
- [ ] Error bars / confidence intervals shown where appropriate
- [ ] Legends are self-contained and do not require main text
- [ ] All tables use `booktabs` with no vertical rules
- [ ] Best results are bolded in tables
- [ ] Tables fit within column width

---

## END OF TEMPLATE

> **To use:** Fill the Project Parameters table at the top, paste this entire file into your chat, and the agent will execute Phases 0–5 autonomously with full checkpointing, compilation verification, and output management.
