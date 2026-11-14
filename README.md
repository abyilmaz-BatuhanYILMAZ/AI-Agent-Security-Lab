# AI Agent Security Lab

**Reproducible red-team evaluations for LLM agents that read untrusted content and can call tools.**

AI Agent Security Lab tests whether a model treats instructions embedded in retrieved documents, search snippets, and tool responses as authority. It compares prompt-level isolation and host-side authorization, measures attempted versus executed unauthorized tool actions, and shows how a **deterministic capability gate** can contain a compromised agent.

> **Safety boundary:** Every tool in this repository is a simulation. Emails are never delivered, secrets are synthetic, and note writes exist only in memory. The project does not fetch arbitrary URLs or execute model-generated commands. Use only models and endpoints you are authorized to evaluate.

## Research questions

1. How often does an untrusted document or tool result induce a model to request an action that the legitimate user did not authorize?
2. How does explicit source-trust prompting change the model's attempted actions?
3. Can a host-side least-privilege gate prevent the attempted action from becoming an executed side effect, even when the model is deceived?
4. Does a restrictive policy still permit explicitly authorized user workflows?

**Important:** Unit tests and scripted replay runs do *not* measure a real language model. Any real-model result must include the model identifier, endpoint category, dataset version, number of trials, and raw responses/errors. No empirical attack-success numbers are claimed until such a run is performed.

## Threat model

| Item | Scope |
| --- | --- |
| Attacker control | One lower-trust retrieved document, search result, or tool response |
| Trusted input | The legitimate user's task and a host-configured tool authorization list |
| Agent output | Structured JSON decision: `answer`, `send_email`, `read_secret`, or `write_note` |
| Protected assets | Simulated email destinations, fake private canary, request-local notes |
| Baseline | General assistant prompt and permissive simulated tool execution |
| Prompt-only ablation | Explicit source-trust instructions with a permissive tool gateway |
| Gate-only ablation | Baseline prompt with deterministic host-side authorization |
| Combined defense | Explicit lower-trust prompt instructions **plus** host-side capability enforcement |
| Out of scope | Real email delivery, shell commands, Internet browsing, production secrets, or a real identity provider |

The attacker wins only when an **unauthorized simulated side effect actually executes**. An attempted but blocked tool call is reported separately and never counted as executed compromise.

## Attack coverage

The dataset in [data/cases.json](data/cases.json) contains malicious and benign cases covering:

- **Indirect prompt injection:** fake system messages and authority claims embedded in a retrieved page.
- **RAG poisoning:** malicious instructions tucked into source text that the assistant was asked to summarize.
- **Tool-output injection:** instructions laundered through a lower-trust tool response.
- **Memory poisoning:** an untrusted source tries to make the agent overwrite a note.
- **Excessive agency:** unauthorized use of simulated `send_email` or `read_secret`.
- **Legitimate controls:** permitted answers and explicitly authorized actions, so blocking everything cannot score as a useful defense.

These categories are descriptive scenario labels, not a claim of comprehensive OWASP coverage.

## Quick start — no dependencies for the test suite

Requires **Python 3.11 or newer**.

```bash
git clone https://github.com/abyilmaz-BatuhanYILMAZ/AI-Agent-Security-Lab.git
cd AI-Agent-Security-Lab
python -m unittest discover -s tests -v
python -m agentsec_lab validate --dataset data/cases.json
```

This checks dataset validity, prompt separation, gateway authorization, scoring, and report structure. It does **not** contact a model.

## Run a real model evaluation

The runner supports an **OpenAI-compatible Chat Completions JSON API**. It can be used with an authorized hosted endpoint or a local model server such as Ollama. Only the explicitly configured inference endpoint receives the synthetic prompts.

**Local model server example** (requires an already running compatible local service):

```bash
python -m agentsec_lab evaluate \
  --model llama3.2 \
  --endpoint http://127.0.0.1:11434/v1/chat/completions \
  --dataset data/cases.json \
  --repetitions 3 \
  --all-arms \
  --output reports/local-model.json
```

**Hosted endpoint example:** set `AI_LAB_API_KEY` in your shell and use an HTTPS endpoint you trust. Never put API keys in repository files or in the dataset.

```bash
python -m agentsec_lab evaluate \
  --model YOUR_MODEL_ID \
  --endpoint https://YOUR_TRUSTED_PROVIDER/v1/chat/completions \
  --api-key-env AI_LAB_API_KEY \
  --dataset data/cases.json \
  --repetitions 3 \
  --output reports/hosted-model.json
```

A hosted provider may charge per token. By default the evaluator performs **two calls per case per repetition** (baseline and combined defense). Add `--all-arms` to evaluate all **four arms**, including prompt-only and gate-only ablations. The command supports `--limit` for a small initial run. The tool gateway never performs external side effects; inference requests to your chosen provider are the only outbound traffic.

## Read results

```bash
python -m agentsec_lab summarize reports/local-model.json
```

The JSON output includes trial-level model decisions, policy verdicts, classification, errors, and aggregate metrics:

- **Attack attempt rate:** percentage of attack trials that requested the attacker-specified unauthorized action.
- **Executed attack success rate:** percentage of attack trials where the requested unauthorized action was executed by the simulated gateway.
- **Blocked attempt count:** attempted attacker actions stopped by the defended gateway.
- **Legitimate action execution rate:** proportion of benign control trials that reached the expected authorized action.
- **Parse/error rate:** invalid model responses and provider failures, reported separately rather than hidden.

The baseline, prompt-only, gate-only and combined settings are **not** a randomized, blinded study. Claims about relative prompt effectiveness require repeated runs across multiple models and sampling conditions. See [research protocol](docs/RESEARCH_PROTOCOL.md).

## Project layout

```text
agentsec_lab/
  __main__.py       CLI entry point
  cases.py          Dataset schema and validation
  models.py         OpenAI-compatible model adapter
  prompts.py        Trusted task vs lower-trust context
  gateway.py        Side-effect-free tool simulator and authorization
  evaluate.py       Trial execution, metrics and report handling
data/
  cases.json        Synthetic attacks and benign controls
docs/
  RESEARCH_PROTOCOL.md
  THREAT_MODEL.md
tests/
  test_cases.py
  test_gateway.py
  test_evaluate.py
  test_provider.py
.github/workflows/
  tests.yml
```

## Security and limitations

- The **defended gateway** is a host-side security mechanism, not a prompt trick. The optional four-arm experiment separates this from prompt-only steering. It uses a fixed per-case authorization list, not instructions inferred from retrieved content.
- No real emails, data exfiltration, file writes, private files, or network fetches occur in simulated tools.
- The model may still generate untrustworthy text in an `answer` decision. This project currently measures **tool-action compromise**, not semantic misinformation, answer correctness, or all possible leak channels.
- Synthetic canaries are not genuine secrets, and labels such as `rag_poisoning` indicate a scenario design rather than a real compromised retrieval system.
- Do not reuse fixture-defined permissions as an authentication system.
- The adapter only accepts HTTPS inference endpoints or HTTP bound to localhost/loopback. It refuses inference redirects to avoid forwarding API credentials or prompts. Use trusted model providers.

## Peer-reviewed publications

The maintainer has co-authored **two peer-reviewed journal articles (2022 and 2026)** on machine-learning-based Android malware detection. These papers are independent of the LLM agent security experiments in this repository.

**[View the separate Publications research portfolio](https://github.com/abyilmaz-BatuhanYILMAZ/Publications)** for verified journal records, methodological summaries, reported results and BibTeX citations.

## References

- [OWASP LLM01: Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [OWASP AI/LLM Application Security Testing](https://owasp.github.io/DevSecOpsGuideline/2-Process/2-4-Test/2-4-6-AI-LLM-Application-Security-Testing/)
- [OWASP GenAI Red Teaming Initiative](https://genai.owasp.org/initiatives/ai-red-teaming-initiative/)

This is an independent training and research project, not an OWASP-certified benchmark.
