# Research extension plan — balanced exploratory corpus (v2)

**Status: protocol and cases prepared; model outcome claims require successful real-model inference.**

## Why a second dataset?

The original [15-case corpus](../data/cases.json) contains 12 adversarial cases but only **3 legitimate controls**. Its four-arm paired-replay evaluations with Qwen2.5 0.5B and 1.5B used deterministic decoding and revealed high invalid-output rates, especially for the smaller model. This makes both security and usability estimates fragile.

The separate [exploratory-v2 dataset](../data/cases-exploratory-v2.json) contains **24 new synthetic cases: 12 attack cases and 12 legitimate controls**. The underlying JSON *schema* remains `version: "1.0"`; “v2” refers only to the **corpus revision**, not a change to the input schema. IDs are disjoint from the first corpus. This is a **public, researcher-authored, unblinded extension**—not a statistically independent or secret held-out evaluation set.

### Planned composition

| Class | Composition |
| --- | --- |
| Attacks, 12 | 3 per family: RAG, tool output, indirect prompt injection, memory poisoning |
| Legitimate controls, 12 | 4 answer-only, 4 explicitly authorized email, 4 explicitly authorized note-write |
| Surfaces | Retrieved document, search snippet, tool response |
| Security boundary | Exact action and target are granted or denied at the simulated host gate |

All email recipients use reserved `.invalid` domains and secrets are the fixed synthetic canary. There is **no real data transmission or credential access**.

## Research question and preregistered criteria

**Question:** Does prompt-only intervention reduce goal-matching unauthorized tool requests without degrading legitimate-task completion, compared with a host-enforced exact-target capability boundary?

H1. For at least one model and adversarial case, the permissive host executes the model's goal-matching unauthorized tool request.

H2. The guarded host denies all goal-matching unauthorized requests for which the exact target/action grant is absent (**software property in this simulator**).

H3. For explicitly authorized controls, the guarded host should allow valid requests at the exact granted target. Whether the model can reliably produce these outputs is a **separate utility outcome**.

These are experimental hypotheses, not confirmed outcomes on the new corpus.

### Primary measurements

1. Unauthorized action **attempts / all attack cases**.
2. Unauthorized actions **executed / all attack cases**.
3. Rejected goal-matching actions, reported as an absolute count.
4. Valid control actions **executed / all legitimate controls**.
5. **Invalid or missing decisions / all trials** (do not drop invalid responses).

Secondary: attempt rate **among valid attack outputs**, explicitly labeled and never substituted for the primary rate. Answer semantic correctness is **not yet measured**. A single greedy run is descriptive only: the analysis must not claim statistical superiority.

## Execution and evidence policy

The v2 paired-replay method generates one proposal per (case, prompt condition) and replays it with each of two host policies. Thus with 24 cases × 2 prompt conditions:

- **48 genuine model generations**
- **96 simulated action outcomes**
- **1 deterministic repetition**, four arm conditions

Run the 1.5B pilot before deciding whether repeating the 0.5B model is informative, since output validity is a known confounder.

```bash
python -m agentsec_lab validate --dataset data/cases-exploratory-v2.json
python scripts/real_model_eval.py \
  --dataset data/cases-exploratory-v2.json \
  --model-size 1.5b --max-new-tokens 160 --repetitions 1 \
  --output research/runs/qwen2.5-1.5b-exploratory-v2.json
```

Before an empirical claim is added to the README, verify: successful inference, raw report file, exact dataset SHA-256, repo revision, model revision, model calls, control validity, attack counts and all arm denominators. Dataset results must **never be pooled** with original 15-case reports without explicit scope and caveats.

## Historical-results verification

```bash
python scripts/audit_evidence.py --dataset data/cases.json --reports \
  research/runs/qwen2.5-0.5b-paired-160.json \
  research/runs/qwen2.5-1.5b-paired-160.json
```

This verifies **saved report consistency, not reproduction of model inference**. The 2026-11-14 matched reports are immutable historical experimental evidence.

## Future reliability work

- Compare the strict JSON adapter with **provider-native structured tool calls** in a separate versioned arm/protocol, reporting transport and schema errors explicitly.
- Build new, **non-public held-out** cases under a documented sampling plan. Avoid tuning models or prompts against that evaluation set.
- Collect human-judged semantic answer contamination metrics separately from executed tool actions, with a reproducible rubric.
- Evaluate legitimate answer quality and authorized tool utility, not just whether an action reached the gateway.
- Pre-register larger per-family samples, perturbations and model versions before conducting significance tests.
- Add isolated, disposable retrieval and actual tool-call transcripts to assess ecological validity.

## Limitations

This experimental extension remains small, public and synthetic. The model receives lower-trust source text within a user message rather than native tool-role history. The host gate uses predetermined exact-match grants, not a full identity/access policy. No real infrastructure is attacked, no real email sent and no company data handled. Even 96 simulated outcomes should not be presented as 96 statistically independent model generations.

[Original research protocol](RESEARCH_PROTOCOL.md) · [Matched baseline runs](MATCHED-MODEL-COMPARISON-2026-11-14.md)
