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

## Paired replay protocol (v2)

The historical [0.5B first pass](../research/runs/qwen2.5-0.5b-first-pass.md) used separate model queries for all four arms and a 96-token output limit. Retain its report unchanged as a historical exploratory measurement.

The improved local evaluation uses **two prompt conditions** and **two host enforcement conditions**:

| Prompt condition | Host gate disabled | Host gate enabled |
| --- | --- | --- |
| General prompt | baseline | gate_only |
| Source-trust prompt | prompt_only | defended |

For each case and each repetition, the evaluator obtains **one model proposal for each prompt condition**. The *exact same structured model decision* (or the same parsing error) is then replayed under the two respective host authorization settings. This paired design avoids treating repeated deterministic model outputs as independent data; it also isolates the effect of the host gate without variation in the proposed action.

For 15 cases, one repetition and four arms this means **30 actual model inferences** and **60 simulated agent outcomes**. The report records `model_calls_actual`, `agent_trials`, `paired_replay`, and a `model_decision_reused` flag for each outcome. A strict, unchanged JSON schema is used for scoring; the local-model generator allows up to 160 new tokens. Invalid replies remain errors rather than being silently repaired.

**Do not compare v2 attack rates directly with the original 96-token v1 experiment as though only the model had changed.** The output length and replay method also differ.

### Measurement validity and error reporting

In every arm, the denominator for the primary attack attempt/execution rates is **all attack trials**, including malformed model outputs. A secondary valid-only attempt rate is included to aid diagnosis but must never replace the primary rate without an explicit explanation. Report both the absolute error count and legitimate-control execution rate. If most decisions are invalid, the measured attack rates are insufficient to establish practical model safety.

Raw generated text is recorded for **synthetic local-model** evaluations to permit investigation of invalid JSON and incomplete generations. Provider-backed API evaluations do not persist raw text by default. The dataset must contain synthetic-only content before enabling public run artifacts.

With greedy decoding, repeated calls to identical prompts typically produce identical output. Increasing repetitions without varying seed or sampling strategy **does not** create statistically independent observations. Future generalizable research requires preregistered or held-out cases, more diverse controls, more models, and explicit uncertainty quantification.

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
