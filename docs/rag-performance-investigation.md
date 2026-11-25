# RAG latency investigation — 2026-11-14

Same machine, Python environment and corpus (1847 slides, 894 questions).
Baseline sources extracted with git archive 63c8086; working tree was not stashed.
Each implementation used temporary approvals and 20 samples per lesson, including
outline, slide and question retrieval in each sample. No warm-up discarded.

For M12-C1-B1 baseline min/median/max were 24.250/25.290/27.222 ms;
working code 26.755/28.046/29.436 ms. The median increase is real in this run;
one run cannot attribute all variance to individual changes. Profiling identifies
recursive hash canonicalization as additional work; deepcopy and registry loading
remain major costs. Sorting was not a leading cumulative cost.

Keep 30 ms; measure median of 20 samples using perf_counter_ns rather than a
single wall-clock sample. This does not establish a p95 or worst-case guarantee.
The corpus-backed test requires local data and is not part of the synthetic CI gate.
Reproduce with scripts/quality/measure_rag_latency.py.

Known ranking limitation: equal-quality distractor tests do not certify rejection
of higher-quality distractors. Quality bonuses can contribute 0.5 versus at most
0.4 for BM25; a high-overlap distractor can still win. No weight changes made.
