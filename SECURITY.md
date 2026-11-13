# Security policy

This repository is a deliberately vulnerable **synthetic training and evaluation lab**. Attack cases in `data/cases.json` are expected behavior, not vulnerabilities in the host operating system.

## Reporting an issue

If you discover a way for the provided code to perform an unintended real-world side effect, leak real credentials, contact an unconfigured endpoint, or bypass the explicit restrictions on network or tool actions, report it privately through GitHub's security advisory mechanism where available.

Do not include actual keys or personal data in an issue or pull request. Do not probe third-party AI providers without authorization.

## Intended boundaries

- Only the user-configured inference endpoint may receive outbound evaluation requests.
- All agent tool calls remain simulated.
- Only reserved `.invalid` addresses and fake canaries are used.
- Authentication and production authorization integrations are out of scope.

## Scope

We welcome reports about parser, configuration, and tool gateway vulnerabilities. A language model following a malicious instruction inside a designed attack case is an evaluation finding, not by itself a vulnerability in this repository.
