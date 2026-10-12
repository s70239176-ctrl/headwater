# Deployment and live evidence

Run date: 2026-10-12. Network: Studionet (`https://studio.genlayer.com/api`, chain 61999). Python 3.12.10, genlayer-test 0.29.2, genlayer-py 0.16.3, genvm-lint 0.11.0. Deployer: a genlayer-test generated Studionet development account (public address below; no key stored). Method: `gltest scripts/canonical_deploy_test.py -s --network studionet` (resumed once with `RESUME=1` after a transport timeout; the same deployment was kept).

| | |
|---|---|
| Contract address | `0x05d2eaE4BBB5C3fB4339Fde37eCf3A8A5D4bcC50` |
| Explorer | https://explorer-studio.genlayer.com/address/0x05d2eaE4BBB5C3fB4339Fde37eCf3A8A5D4bcC50 |
| Deployer | `0x103D0c8436aA1013B6269230323746B0918B0621` |
| Deploy tx | `0xb843849af925ca083f6adde4342b19e4746d5546b6b4dd3ec96a125334751f39` |
| Receipt | status `ACCEPTED`, result `MAJORITY_AGREE` (finalization was **not** checked; do not read this as FINALIZED) |
| Deployment source commit | `190781e` |
| Contract blob SHA | `242b7f9c812ad68e1a1e37f5deec2bd18210af1e`, identical in `HEAD` and the working file at deployment time |

Raw output: [canonical-evidence.json](canonical-evidence.json).

## Live scenarios on the canonical deployment

All receipts below are `ACCEPTED` / `MAJORITY_AGREE`. Sources: two docs.python.org URLs (one domain, same text) and an endoflife.date JSON endpoint.

| Scenario | Claim id | Assess tx | Stored result |
|---|---|---|---|
| success: true claim, min 2 | 1 | `0x0569facb8377bbcd9fce80f409195087f1853ce0c5b024617bca40020ed5d7de` | `CORROBORATED`, status `RELIABLE`, independent_support 2, **raw_support 3** |
| negative: false claim (2019), min 2 | 3 | `0x9a5921369950e599b298982bee379cd3fc62215942c6100a1256df0a6d60c994` | `REFUTED`, status `BLOCKED`, independent_refute 2, `is_corroborated` false |
| recovery: one source 404 | 4 | `0xfec23e11a4ad6e429699f63d69ec4aed0b1152b435b30a002a9cdb4f3d2a9974` | `INSUFFICIENT`, status `UNKNOWN` (deterministic path, no model call) |

Claim 2 is an orphan: an earlier interrupted run opened it and never assessed it. The first scenario (raw 3 vs independent 2) is the point of the primitive: three supporting URLs, two origins.

## Test results

- Direct Mode: 109 passed. `genvm-lint` lint and check: pass.
- Integration (`tests/integration`, disposable deployments): 5 of 5 passed; one needed a re-run alone after a connect timeout at deploy.
- Two earlier canonical-script attempts failed on transport timeouts. One of them retried a write whose first attempt had already landed, which produced a cooldown-reverted duplicate; retries on writes were then removed.

Disposable test deployments are not the canonical deployment.
