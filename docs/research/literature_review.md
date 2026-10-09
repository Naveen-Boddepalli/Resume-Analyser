# Literature review and gap analysis

Status: every entry below was checked against the arXiv API and/or Crossref
(October 2026). Claims about a paper are limited to what its abstract or
published metadata states; the *Limitation* column is our reading of what the
paper's own setup implies, not a quotation. BibTeX keys refer to
[`paper/references.bib`](../../paper/references.bib).

## 1. Prior work, grouped by approach

### 1.1 Supervised person-job fit (deep models on interaction logs)

| Work (key) | Method | Data used | Limitation relevant to this project |
|---|---|---|---|
| Zhu et al. 2018 (`zhu2018pjfnn`) | CNN bipartite network over job/resume text; can point to satisfied requirement items | Large historical job-application logs | Needs large application histories that are not public |
| Qin et al. 2018 (`qin2018apjfnn`) | RNN + hierarchical ability-aware attention | Large historical application data | Same dependence on proprietary logs; explanation is learned attention, no check that it reflects the decision |
| Lavi et al. 2021 (`lavi2021consultantbert`) | Fine-tuned Siamese SBERT | >270,000 consultant-labelled resume-vacancy pairs | Needs a very large expert-labelled corpus; returns one similarity, no requirement-level evidence |
| Bhatia et al. 2019 (`bhatia2019endtoend`) | BERT sentence-pair classifier on parsed resumes | Resumes in LinkedIn and non-LinkedIn formats | Job description is *approximated* by the candidate's past experience text rather than real postings |

### 1.2 Augmentation and LLM-assisted representation learning

| Work (key) | Method | Limitation relevant to this project |
|---|---|---|
| Yu et al. 2024 (`yu2024confit`) | LLM data augmentation + contrastive learning; beats BM25 and OpenAI embeddings on nDCG@10 | Depends on an external LLM at training time and on interaction-labelled pairs; output is a single embedding similarity |
| Yu et al. 2025 (`yu2025confitv2`) | Hypothetical-resume embedding + runner-up hard negatives | Same dependence on generated text; no per-requirement explanation |
| Jouanneau et al. 2026 (`jouanneau2026longcontext`) | Late cross-attention re-ranker distilled from an LLM teacher; calibrated skill-fit scores | Needs an LLM teacher and large training set |

### 1.3 End-to-end screening pipelines

| Work (key) | Method | Limitation relevant to this project |
|---|---|---|
| Khelkhal & Lanasri 2025 (`khelkhal2025smarthiring`) | NER + embeddings, explainable pipeline | Abstract lists bias mitigation and fairness-aware modelling as *future directions*, i.e. not evaluated |
| Lo et al. 2025 (`lo2025multiagent`) | Multi-agent LLM with retrieval, compared with HR ratings | LLM-dependent scoring (cost, latency, run-to-run variation); no demographic audit described |

### 1.4 Skill extraction

| Work (key) | Contribution | Take-away for this project |
|---|---|---|
| Zhang et al. 2022 (`zhang2022skillspan`) | SkillSpan: 14.5K annotated sentences, hard/soft skills | Skill mentions are span-level and domain specific |
| Decorte et al. 2023 (`decorte2023xmlc`) | Skill linking as extreme multi-label classification with LLM-generated training data | Large ontologies need linking models; we use a transparent lexicon instead and say so |
| Nguyen et al. 2024 (`nguyen2024skillllm`) | In-context LLM skill extraction | LLMs handle complex mentions but lag supervised models |

### 1.5 Bias in automated screening

| Work (key) | Finding | Take-away |
|---|---|---|
| Bertrand & Mullainathan 2004 (`bertrand2004emily`) | Field experiment: identical resumes with white-sounding names received more callbacks | Counterfactual name swap is the standard audit design |
| Wilson & Caliskan 2024 (`wilson2024silicon`) | Embedding-based retrieval over >500 resumes: white-associated names preferred in 85.1% of comparisons | Embedding retrievers like ours must be audited, not assumed neutral |
| Armstrong et al. 2024 (`armstrong2024silicon`), An et al. 2024 (`an2024discriminate`, `an2025measuring`), Wang et al. 2024 (`wang2024jobfair`) | GPT/LLM scoring and hiring decisions vary with race- and gender-signalling names | LLM-only screening (the previous version of this project) inherits these risks |
| De-Arteaga et al. 2019 (`dearteaga2019biasinbios`), Gonen & Goldberg 2019 (`gonen2019lipstick`) | Scrubbing explicit gender indicators leaves proxy signal; debiasing can hide rather than remove bias | Redaction is necessary but not sufficient; we measure *residual* shift |
| Raghavan et al. 2020 (`raghavan2020mitigating`) | Review of vendor claims about bias mitigation in hiring | Claims need evidence; we publish the audit protocol and code |
| EU AI Act (`euaiact2024`) | Employment-screening AI is classed as high-risk | Transparency and human oversight are design requirements |

### 1.6 Retrieval and explanation building blocks

`reimers2019sbert`, `wang2020minilm`, `xiao2024cpack` (encoders);
`robertson2009bm25`, `thakur2021beir` (lexical baseline that remains strong
zero-shot); `khattab2020colbert` (late-interaction MaxSim idea that motivates
requirement-level coverage); `lundberg2017shap` (attribution);
`pedregosa2011sklearn`, `friedman2001gbm` (classifiers).

## 2. Gaps and how this project addresses each

| # | Gap in prior work | Design response | Where it is tested |
|---|---|---|---|
| G1 | Strong models need proprietary logs or very large labelled sets | Frozen general-purpose encoder + low-capacity interpretable head trained on a small public set | Learning-curve experiment (E5) |
| G2 | Single opaque similarity; no per-requirement evidence | Requirement-level semantic coverage: each JD requirement is linked to its best-matching resume sentence, with similarity | Deletion-fidelity test (E4) |
| G3 | LLM-only screening is costly, non-deterministic and name-sensitive | Deterministic encoder pipeline; LLM used only as an *optional* summariser constrained to the evidence list | LLM zero-shot baseline and bias audit (E2, E6) |
| G4 | Bias handled as future work, or assumed solved by scrubbing | Blind front end (PII, honorifics, pronouns, institutions) + counterfactual audit for explicit *and* proxy cues | Counterfactual audit (E6) |
| G5 | Evaluation on private data, single split, no uncertainty | Public dataset, JD-disjoint and doubly-disjoint splits, per-JD ranking metrics, bootstrap CIs, label-noise disclosure | E1-E3 |
| G6 | Regulatory expectations for transparency and oversight | Three-band decision with a human-review band, evidence trail, no prestige proxies (institution tier, CGPA) | Qualitative; system design section |

## 3. Honest limits of this review

* The review is selective (31 verified entries), not a systematic survey.
* Abstracts were read for all works; full texts were not re-derived for every
  claim. Table cells are phrased to stay within what the abstract supports.
* Proprietary-system claims (commercial ATS vendors) are out of scope because
  they cannot be verified.
