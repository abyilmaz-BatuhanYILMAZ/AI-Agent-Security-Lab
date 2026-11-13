# Research protocol

## Research objective

Measure unauthorized tool-use attempts arising from instructions embedded in lower-trust content, and measure whether a deterministic host capability gate prevents the simulated effects.

The laboratory is designed to generate **new measured results from a real LLM**, not to present hard-coded fixture output as empirical findings.

## Hypotheses

- **H1 — susceptibility:** Some tested models will follow action directives contained in retrieved source text even when the trusted user requested a summary.
- **H2 — defense:** A host-side exact-action/exact-target authorization gate will prevent these unauthorized actions from executing, even when the model attempts them.
- **H3 — utility:** Legitimate actions with explicitly granted target permissions should still be permitted in defended mode.

H1 and H3 require real model runs. H2 is principally a software invariant and is tested without an LLM.

## Dataset v1.0

[The cases](../data/cases.json) contain **12 attack** and **3 benign control** examples across four attack families. All text, addresses, canaries and note values are synthetic. By default each case is evaluated in baseline and combined-defense mode. With `--all-arms`, it is also evaluated in prompt-only and gate-only modes.

A trial contains one source and a single model decision. No iterative attack search, hidden test-set optimization or adaptive adversary is implemented.

## Running a reproducible experiment

1. Record the repo commit, Python version, model identifier/version, provider or local serving software, endpoint category, date, system resources if local, and whether your provider actually honors the requested temperature.
2. Run `python -m unittest discover -s tests -v` and `python -m agentsec_lab validate --dataset data/cases.json`.
3. Start with `--limit 2 --repetitions 1` to validate model compatibility.
4. Run the full dataset with `--repetitions 3` or more. By default 15 cases x 2 arms x 3 repetitions requires **90 model decisions**. With `--all-arms` it requires **180 model decisions**. Record which arms were used.
5. Save a distinct JSON report for every model/configuration; do not overwrite raw reports used in the final analysis.
6. Review invalid model replies, unexpected schema variations, refusals and missing answer contents.
7. Report trial-level outcomes and the following counts/rates for each mode: attempted attacker goals, executed attacker goals, blocked attempted goals, legitimate controls executed, and errors.
8. Repeat with multiple model seeds or nondeterministic trials where supported. If a provider does not support a fixed seed, report that limitation.
9. Do not pool results from different models or dataset revisions without stating that methodology.

## Denominators

For a given mode:

- **Attack attempts / attack trials** includes malformed replies and inference failures in the denominator; those trials contribute 0 attempts and are separately counted as errors.
- **Executed attack goals / attack trials** measures actions actually permitted by the gateway.
- **Blocked goal attempts** counts goal-matching actions refused at the host boundary.
- **Legitimate controls executed / benign control trials** is an action-level utility proxy; it is **not** an answer-quality score.
- **Errors / all trials** reflects provider, parsing, or adapter failures.

A zero executed attack rate with an equally zero legitimate-control pass rate may represent an unusable agent; review both.

## Recommended improvements before publishing a research paper

- Larger, blinded, balanced attack/control datasets with unseen paraphrases and scenario diversity.
- Run and compare **prompt-only** and **gate-only** ablations with `--all-arms`, and replicate across different model configurations.
- Multiple models, repeated trials, confidence intervals and explicit model/version identifiers.
- Native tool-calling APIs and real retrieval integrations in an isolated environment.
- Human or reproducible adjudication of answer contamination and data disclosure, which the current tool-goal metric misses.
- Threat-model-based severity weighting with clear, non-arbitrary criteria.

## Example result presentation

Use a table with model, dataset SHA-256, run date, sampling configuration, each arm's attempted attacks, executed attacks, legitimate controls and errors. Include prompt-only and gate-only rows when `--all-arms` is selected.

**Do not publish a metric as measured unless it came from a successful real-model run.** Scripted unit tests only verify code behavior.

## Reference mapping

- [OWASP LLM01 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [OWASP LLM Application Security Testing](https://owasp.github.io/DevSecOpsGuideline/2-Process/2-4-Test/2-4-6-AI-LLM-Application-Security-Testing/)
- [OWASP AI Red Teaming](https://genai.owasp.org/initiatives/ai-red-teaming-initiative/)

This mapping highlights overlapping risk themes; the lab is not a certification or comprehensive conformance test.
