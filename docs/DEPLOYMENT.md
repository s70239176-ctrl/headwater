# Deployment and live evidence

Date of runs: 2026-10-12. Network: Studionet (`https://studio.genlayer.com/api`, chain 61999). Python 3.12.10, genlayer-test 0.29.2, genlayer-py 0.16.3, genvm-lint 0.11.0. Accounts: genlayer-test's generated Studionet development accounts (no key stored here).

## Integration results (real validators and consensus, not leader-only)

| Test | Result |
|---|---|
| deploy_and_public_surface | passed (run alone, then in the full run) |
| live_true_claim_counts_origins_not_urls | passed in full run |
| live_false_claim_is_never_corroborated | passed in full run |
| live_unreachable_source_and_cooldown | passed in full run |
| live_three_independent_origins_cannot_be_reached_from_two | failed once in the full run with a connect timeout at deploy (no transaction was submitted); passed when re-run alone |

Each test deploys its own disposable contract.

## NOT recorded

No canonical deployment address, transaction hashes, or Explorer URL are recorded: the tests do not print them and I did not run a separate canonical deployment. Finality status of those transactions was not inspected. Do not cite this repo as having a canonical Studionet address until one is deployed and documented here.

## Source parity

Not applicable until a canonical deployment exists. Contract blob SHA at the current commit: see `git rev-parse HEAD:contracts/headwater.py`.
