# Contributing

Contributions should make the lab easier to reproduce, audit, and extend.

## Requirements

1. Keep all tool effects simulated. Do not add real email delivery, arbitrary HTTP fetching, shell execution, filesystem access, or non-synthetic secrets.
2. Add each new case to the versioned JSON dataset with a stable ID, a legitimate task, a lower-trust source, an attacker goal or benign-control expectation, and host grants.
3. Ensure the goal of every attack case is **not** in its host grants.
4. Add unit tests for new actions, new scoring logic, new input validation and failure modes.
5. Document any changes to evaluation semantics or denominators.
6. Clearly distinguish scripted fixtures from real-model measurements.

Run:

```sh
python -m agentsec_lab validate --dataset data/cases.json
python -m unittest discover -s tests -v
```

Never submit private provider keys, model transcripts containing sensitive user data, or unreviewed external attack datasets.
