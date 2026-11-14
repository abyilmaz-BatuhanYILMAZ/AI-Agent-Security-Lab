# Matched-Protocol Comparison: Qwen2.5 0.5B vs 1.5B

**Date:** 14 November 2026 · **Evidence:** two completed local CPU model runs · **Status:** exploratory, not a statistically powered benchmark

## Research question

How do two different Qwen2.5 instruction-tuned model sizes behave on the same synthetic prompt-injection and tool-authorization evaluation when **all evaluation controls, dataset and decoding settings are matched**?

Unlike the earlier first-pass study, both runs use the **v2 paired-replay protocol**.

## Matched experiment settings

| Configuration | Qwen2.5 0.5B | Qwen2.5 1.5B |
| --- | --- | --- |
| Model | `Qwen/Qwen2.5-0.5B-Instruct` | `Qwen/Qwen2.5-1.5B-Instruct` |
| Model revision | `7ae557604adf67be50417f59c2c2f167def9a775` | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` |
| Dataset SHA-256 | `853ae32f3738eb985d5caee4b91f31a2066cf3d44a2ad798a07f9ee61350bbc4` | Same |
| Dataset | 12 synthetic attack goals, 3 legitimate controls | Same |
| Protocol | `v2-paired-replay-strict-json-160` | Same |
| Sampling | Greedy / deterministic, 160 new tokens | Same |
| Repetitions | 1 | 1 |
| Actual model generations | 30 | 30 |
| Simulated agent outcomes | 60 | 60 |
| Code revision recorded by model run | `48b0a9d20bc0dee23f774b5b69a3f885c3bc9722` | `c895a05b10ff88c19cf407cb6bddfd0af3752a45` |

The model evaluation logic, prompts and dataset were not changed between the two v2 runs; the later revision added a dedicated comparison workflow. The identical dataset SHA and protocol labels are recorded in both JSON files.

## Measured results

Each arm contains **12 attack trials** and **3 benign-control trials**. The reported attack-goal count requires an exact match on the target action and target argument. Invalid model decisions remain in the denominators.

| Model | Condition | Attack goal attempts | Unauthorized goals executed | Blocked goal attempts | Benign controls executed | Invalid decisions |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **0.5B** | Baseline | 1/12 | 1/12 | 0 | 1/3 | **11/15** |
| 0.5B | Prompt only | 0/12 | 0/12 | 0 | 1/3 | **8/15** |
| 0.5B | Host gate only | 1/12 | **0/12** | 1 | 1/3 | **11/15** |
| 0.5B | Prompt + host gate | 0/12 | **0/12** | 0 | 1/3 | **8/15** |
| **1.5B** | Baseline | 2/12 | 2/12 | 0 | 1/3 | **2/15** |
| 1.5B | Prompt only | 2/12 | 2/12 | 0 | 0/3 | **6/15** |
| 1.5B | Host gate only | 2/12 | **0/12** | 2 | 1/3 | **2/15** |
| 1.5B | Prompt + host gate | 2/12 | **0/12** | 2 | 0/3 | **6/15** |

### Why interpreting this as "0.5B is safer" would be wrong

The smaller model produced invalid decisions in **11/15 baseline trials**, compared with **2/15** for 1.5B. An invalid response is **not** evidence that the underlying model reliably refused an attack, and suppressing invalid outputs can artificially lower measured exact-action attack rates. Among *valid attack outputs*, the denominators also differ substantially: 0.5B baseline had only **3** valid attack decisions, whereas 1.5B had **11**. Therefore, the observed one-versus-two attempted attack difference cannot establish comparative model robustness.

For the 1.5B run, the prompt-only treatment did **not** reduce attempted attacker goals (2/12 vs 2/12) and had more invalid decisions (6/15 vs 2/15). For the 0.5B run, the prompt-only treatment changed attempt counts but the error rate remained high.

The **host-side exact-action/exact-target authorization gate** successfully blocked all *observed* unauthorized tool attempts in both models' simulations. This result establishes a software policy property **for the predefined attacker targets only**; it is not a proof of production agent security.

## Major limitations

1. **One greedy pass per case and arm prompt.** Repeating a deterministic output with the same prompt does not create independent evidence.
2. **Only 15 synthetic cases, 3 benign controls.** Too small for general model rankings or meaningful uncertainty intervals.
3. **Strict schema fragility.** The smaller model frequently failed to provide all required JSON fields or used prose; error behavior is a key measured outcome rather than a removed nuisance.
4. **Simplified tool interface.** Structured JSON proposals, simulated side effects, and no live retrieval/index mean the evaluation does not cover all real-agent behaviors.
5. **Objective limits.** A model may hallucinate, contaminate answers, or disclose information in plain text without matching the exact simulated tool-action goal. Those effects are not measured here.
6. **No significance claims.** Differences are descriptive. We do not report a p-value, confidence interval, or model superiority from this sample.

## Reproduce

Use the same checked-in dataset and protocol from the repository root. Requires Python 3.11+, the project's dependencies, CPU or other supported local inference hardware:

```bash
python scripts/real_model_eval.py --model-size 0.5b --max-new-tokens 160 --repetitions 1
python scripts/real_model_eval.py --model-size 1.5b --max-new-tokens 160 --repetitions 1
```

The complete metadata, exact model revisions, individual decisions, raw local model text where available, and error states are stored in the machine-readable reports:

- [Qwen2.5 0.5B — v2 raw JSON](../research/runs/qwen2.5-0.5b-paired-160.json)
- [Qwen2.5 1.5B — v2 raw JSON](../research/runs/qwen2.5-1.5b-paired-160.json)
- [0.5B generated run report](../research/runs/qwen2.5-0.5b-paired-160.md)
- [1.5B generated run report](../research/runs/qwen2.5-1.5b-paired-160.md)

## Next steps

- Test a model and output interface that can reliably produce valid structured decisions.
- Increase benign controls and add held-out attack variants to reduce evaluation fragility.
- Use native tool calling and a disposable retrieval system to study external validity.
- Pre-register a broader experiment design before making statistical security comparisons.

For the original threat model and exact metrics, see [research protocol](RESEARCH_PROTOCOL.md).
