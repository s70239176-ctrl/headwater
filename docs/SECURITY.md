# Threat model

**Protected:** the integrity of `CORROBORATED` as a gate for other contracts. No funds are held.

**Actors:** requester (chooses claim and sources); anyone calling `assess`; source owners (control page content); a malicious leader; a malicious validator minority; downstream consumers.

**Trust assumptions:** an honest majority of validators fetches and judges independently; the chosen sources are not all controlled by one adversary *and also* disguised as unrelated domains with rewritten text (see Limitations).

## Inputs and attacks

| Attack | Defence |
|---|---|
| Prompt injection in a page | Pages enter the prompt only as JSON data under an instruction to treat them as untrusted; the model returns labels, never actions; a stance counts only with a verbatim quote found in that page; deterministic code does all gating |
| Echoed / syndicated sources | Same registrable domain and ≥50% shingle containment are merged without the model; the validator rejects a leader that splits them |
| Sock-puppet domains with paraphrased text | Not solved deterministically; relies on the model's `copy_of` and on the requester choosing sources (limitation) |
| Invented quote | Grounded against each validator's own snapshot |
| Forged leader result | Strict types, recomputation of counts and verdict, independent re-observation |
| Malformed URL, credentials, port, IP literal, `.local`/`localhost`, fragment, uppercase host | Rejected at `open_claim` (defence in depth only; validator egress policy still matters) |
| Oversized inputs | Statement ≤240, URL ≤200, 2–5 sources, 5000 chars per source, quote ≤160 |
| Stale corroboration | `status` is `STALE` past `max_age_s`; `is_corroborated` is false |
| Spam reassessment | 120 s cooldown from the last attempt, successful or not |
| Replay / double write | `assess` only overwrites the latest assessment; no value transfer |

## Fail-closed defaults

Unreadable source → not support. Unparseable model reply → no state change. Unknown enum anywhere → whole round fails. One independent refutation or a mixed origin cluster → `CONTESTED`, never `CORROBORATED`. An unknown claim id reverts.

## Limitations

Not a proof of truth: it measures agreement among *listed* sources. Independence is judged from text and domain, not from real-world ownership. A page can change between a validator's fetch and yours. Text is truncated at 5000 chars, so a decisive fact further down is invisible (choose focused pages). Stance and `copy_of` labels can vary between honest validators; only count-level dimensions are compared. Studionet is a development network, not a production audit.
