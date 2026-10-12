# Submission: Headwater

**Category:** standalone Intelligent Contract. **One line:** counts independent origins behind a claim, not URLs.

- Repository: local only, not pushed (no remote configured).
- Contract: `0x05d2eaE4BBB5C3fB4339Fde37eCf3A8A5D4bcC50` on Studionet. Explorer: https://explorer-studio.genlayer.com/address/0x05d2eaE4BBB5C3fB4339Fde37eCf3A8A5D4bcC50
- Deploy tx: `0xb843849af925ca083f6adde4342b19e4746d5546b6b4dd3ec96a125334751f39` (ACCEPTED, MAJORITY_AGREE; finalization not checked). Source commit `190781e`, blob `242b7f9c…`.
- **Why GenLayer:** validators fetch and judge the sources themselves; a single operator would decide what counts as independent.
- **Consensus:** custom `run_nondet_unsafe`. Validators re-fetch, re-judge and compare reach vector, verdict, independent support and refutation; quotes must be grounded in the validator's own snapshot.
- **Deterministic:** admission, same-domain and text-overlap merging, quorum counts, verdict, freshness, cooldown.
- **Failure policy:** unreadable source never refutes; malformed model reply changes no state; one independent refutation blocks corroboration.
- **Reuse:** `is_corroborated(id)`, `status(id)`, `verdict(id)` (see docs/INTEGRATION.md; consumer snippet not executed on-chain).
- **Tests:** 109 Direct Mode, GenVM lint/check pass, 5 Studionet integration tests. Live evidence in docs/DEPLOYMENT.md.
- **Limitations:** agreement among listed sources, not truth; paraphrasing sock-puppet domains can pass; pages cut at 5000 chars; dev network.

## Portal text (under 1000 characters)

Headwater is a standalone GenLayer Intelligent Contract that checks whether the sources behind a claim are independent, not just numerous. Validators fetch each source, a model labels stance and copying, and deterministic code counts origin clusters (same-domain and heavily overlapping text merge without the model). Other contracts read is_corroborated or status. Verified with 109 Direct Mode tests, GenVM lint/SDK validation, 5 live Studionet integration tests, and a Studionet deployment whose live run showed 3 supporting URLs counted as 2 independent origins (receipts ACCEPTED; finalization not checked).
