# Securing the AI model lifecycle — an offensive-security threat model

**Prepared:** 14 November 2026  
**Classification:** Public architecture/research exercise, **not a penetration test or deployed system audit**.

## Objective and security claim boundary

This document maps a hypothetical organization that ingests a third-party open-weight model, optionally fine-tunes it, stores its artifacts, serves it through a Kubernetes platform and permits a limited AI agent to call organizational APIs.

The goal is to establish **where untrusted data and artifacts cross a trust boundary**, which actor could exploit weak authorization, how to detect the consequence, and which engineering control enforces the boundary. No real model weights, cluster, credentials, vendor infrastructure or customer systems are accessed by this document.

## Reference architecture

```text
  third-party model + dataset     source code + deployment definitions
               |                                 |
         artifact ingestion                CI build pipeline
               |                                 |
          provenance check ---------> signed image / attestation
               |                                 |
         model registry <---------- service identity + artifact policy
               |                                 |
          inference service (Kubernetes, restricted workload)
               |                     |
           retrieval store      monitoring and logs
               |
         agent decision boundary
               |
       independent tool authorization
               |
       approved downstream APIs only
```

## Trust boundaries

| Boundary | Threat actor and precondition | Representative failure | Preventive controls | Evidence to collect |
| --- | --- | --- | --- | --- |
| Model acquisition | An attacker can publish or substitute a model artifact | Unreviewed model is loaded as trusted | Provenance and digest pinning, source allowlist, sandbox inspection, safer serialization formats where possible | Model ID/revision, digest, signed provenance, acquisition logs |
| Training / RAG source | An attacker can modify lower-trust documents or data | Data poisoning, instruction laundering, response contamination | Dataset provenance, retrieval source boundaries, review and evaluation gates | Corpus revision, labeled examples, retrieved source IDs, model outputs |
| CI to registry | Compromised build credential or pipeline step | Malicious model-serving image with legitimate-looking tag | Minimal CI identity, immutable digests, signed build provenance, separation of release approval | Commit, builder identity, attestations, registry event logs |
| Registry to workload | Overly broad deployment/secret retrieval privilege | Unapproved artifacts run or tokens leak | Workload identities, artifact admission policy, secret scoping, egress limits | Admission decision, Pod spec, RBAC bindings, audit logs |
| API to model | Unauthenticated or overprivileged client | Unauthorized inference and data exposure | Strong authentication, rate limits, tenant isolation, logging | Principal, route, request policy verdict, logs with data minimization |
| Model to tools | Untrusted text drives a requested action | Agent invokes an unintended action against an external target | Exact-action and target authorization outside the model, limited grants and audit | Proposed tool call, policy result, simulated/real side effect |
| Operator control plane | Administrator account is compromised or mis-scoped | Broad privilege over model weights, secrets and serving stack | Identity hardening, least privilege, MFA, independent approval for sensitive changes | Effective identity/authorization audit, configuration snapshots |

## Priority validation scenarios (no exploit execution)

1. **Model provenance mismatch:** When the recorded model hash differs from the approved value, deployment should be rejected. Evidence: signed reference, actual digest, admission/build decision.
2. **Registry privilege separation:** An inference workload's identity should not be able to modify trusted model artifacts. Evidence: read-only permission checks for the workload identity.
3. **Tool action without explicit grant:** Even when injected content persuades a model to propose a tool action, the host should deny ungranted action/target combinations. Evidence: paired attempted/blocked outcome.
4. **Untrusted retrieval message:** A retrieved snippet that impersonates system or developer instruction must remain untrusted content. Evidence: model transcript, labeling of source, subsequent tool request.
5. **Audit trail completeness:** A blocked tool request should be observable without logging secret content. Evidence: decision identifiers, policy result, metadata retention and redaction review.
6. **Legitimate workflow continuity:** Explicitly authorized actions must remain usable under the defense. Evidence: approved control actions, validity errors, structured output compliance.

These scenarios require a real lab and measurements to move from threat-model hypotheses to validated findings.

## How existing projects relate (scope limits)

- [AI Agent Security Lab](../README.md): **actually implemented** simulated host-granted action checks, prompt conditions and synthetic paired-replay experiments. Its model evidence does **not** demonstrate real registry, cluster or build-pipeline enforcement.
- [KubeGuard](https://github.com/abyilmaz-BatuhanYILMAZ/KubeGuard): read-only Kubernetes configuration and RBAC relationship review. It does **not** validate artifact provenance or model weight integrity.
- [Publications](https://github.com/abyilmaz-BatuhanYILMAZ/Publications): separate peer-reviewed Android malware classification papers. They are **not** direct experimental evidence for this threat model.

## Defensive control priorities

**P0 — Hard security boundaries:** independent tool capability enforcement, identity/tenant scoping for model and registry access, and no production secret values in model prompts or public logs.

**P1 — Supply-chain integrity:** hash-pinned model artifacts and images, provenance with clear source/build metadata, strict CI identity, artifact promotion approval.

**P2 — Runtime isolation and visibility:** workload securityContext and RBAC review, namespace network policy with an enforcing CNI, request limits, relevant audit events and safe data retention.

**P3 — Research reliability:** broaden legitimate controls, separate provider formatting failures from injection outcomes, retain exact dataset and model revision metadata.

## Non-goals

No claim is made about a specific organization's posture, model theft event, training backdoor or live attack. This does **not** certify NIST, OWASP, SLSA or other standard compliance. An assessment must examine environment-specific permissions, data, running infrastructure and observability.

## Sources (for security practices, not proof of implementation)

- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) — prompt injection, supply-chain risk and excessive agency.
- [SLSA build provenance](https://slsa.dev/spec/v1.0/provenance) — provenance as build artifact context.
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) — AI risk management orientation.
- [Kubernetes RBAC good practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) — least-privilege workload authorization.
