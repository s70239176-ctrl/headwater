# DECISION: why Headwater

## Selected primitive

**Headwater** answers one reusable question: *do these sources corroborate a claim independently, or is it one story echoed N times?* A requester commits a claim plus 2–5 public sources and a required number of **independent origins**. Validators fetch the sources themselves, a model judges stance and copying, and deterministic code counts origin clusters, not URLs.

## Owner portfolio reviewed (local checkouts under `Documents/Projects`, plus `Documents/New folder`)

I read each README and, where noted, the contract's public surface. I did not have a `gh repo list`; this covers only what is on this machine.

| Project | Core trust question | Same lane as Headwater? |
|---|---|---|
| Credo | Standing of a public identity → collateral quote | No (identity, not corroboration) |
| Chargeback | Challengeable veto on agent spend | No (bonded challenge game) |
| CharterKeeper | Does a change or spend conform to an immutable charter | No |
| Driftline | Has a public commitment drifted since it was relied on | No (one page over time; Headwater is many pages at one time) |
| OpenNotum | Attest what live pages say; has a CONFLICT mode over 2–3 URLs | **Nearest.** It picks between conflicting pages; it never asks whether agreeing pages are independent, and has no origin clustering or quorum floor |
| RfpFit | Does a bid answer a brief | No |
| sla-claim (Tally) | Uptime of an endpoint | No |
| Stagehold | Photo-gated staged payments | No |
| Meridian | Cross-chain escrow dispute judge | No |

## Candidates considered (scored 0–10 on GenLayer necessity / novelty vs portfolio / reuse / testability; my judgment, not measured)

| # | Candidate | Score | Verdict |
|---|---|---|---|
| 1 | **Source-independence corroboration (Headwater)** | 9 / 8 / 9 / 8 | **Selected** |
| 2 | Prompt-injection safety gate for a URL | 8 / 7 / 8 / 7 | Strong; next in line |
| 3 | Behavioral conformance of an agent to a published spec | 8 / 6 / 7 / 6 | Overlaps Tally's neighbourhood, evidence is hard to make public |
| 4 | Causal responsibility from incident evidence | 7 / 8 / 5 / 4 | Too open-ended to bound |
| 5 | License-permits-use policy judgment | 7 / 6 / 7 / 7 | Close to Driftline/CharterKeeper policy lane |
| 6 | Package/dependency deprecation signal | 6 / 5 / 8 / 6 | Mostly deterministic from registry data |
| 7 | Citation-entails-claim checker (single source) | 7 / 4 / 7 / 8 | Collides with OpenNotum snapshot mode |
| 8 | Duplicate/originality judgment | 6 / 6 / 6 / 5 | Heuristic-heavy, weak ground truth |
| 9 | Appeal re-examination wrapper | 6 / 5 / 5 / 4 | Needs a host primitive; not standalone |
| 10 | Staleness oracle for accepted facts | 6 / 4 / 7 / 6 | Subsumed by Driftline |

## Delete-GenLayer test

Without GenLayer, whoever runs the backend chooses which copies count as "independent" and authors the verdict. With it, each validator re-fetches every source and independently recomputes the origin partition; a leader that splits syndicated copies, invents a quote, or inflates the count is rejected on substance.

## Three downstream consumers (no change to the contract)

1. A prediction-market resolver that settles only when `is_corroborated(claim)` holds.
2. A DAO proposal contract that requires a corroborated factual premise before a vote opens.
3. A content/oracle registry that lists a fact only while its status is `RELIABLE`, and delists on `STALE` or `BLOCKED`.

## Hardest technical risk

Making the model's *fuzzy* copy judgment safe. Mitigation: deterministic floors the model cannot undo (same registrable domain, ≥50% shingle containment), a model that can only *add* merges, strict parse where any malformed row fails the whole round, and a validator that compares settlement-critical dimensions (reach vector, verdict, independent support, independent refutation) rather than prose.

## Why a standalone Intelligent Contract

One deployable contract, no funds, no admin key, no frontend. The result is an enum plus counts that other contracts read directly.
