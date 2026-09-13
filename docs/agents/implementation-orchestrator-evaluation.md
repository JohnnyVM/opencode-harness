# Implementation Orchestrator evaluation

The Guadalbot #46 case is stored in
`evaluations/implementation-orchestrator/guadalbot-46/`. Its versioned
manifest is intentionally strict and lists every evaluator asset. The package
contains the complete requirements and verification matrix, while the oracle
checks observable behavior rather than a particular implementation.

## Usage

```bash
python3 scripts/evaluate_orchestrator.py doctor guadalbot-46 --source-repo .
python3 scripts/evaluate_orchestrator.py run guadalbot-46 --source-repo . --output-root /tmp/guadalbot-46
python3 evaluations/implementation-orchestrator/guadalbot-46/calibration.py
```

The calibration and contract probes are offline and fake-only. Live doctor/run
coverage is opt-in and must be precondition-gated by the surrounding runner;
tests must not invoke a live service or fetch external data. Treat generated
reports and raw traces as sensitive evaluation output.
