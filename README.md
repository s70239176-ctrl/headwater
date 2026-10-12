# Headwater

**Do these sources corroborate a claim independently, or is it one story echoed N times?**

Headwater is a standalone GenLayer Intelligent Contract. A requester commits a claim, 2–5 public HTTPS sources, and how many *independent origins* must support it. Validators fetch the sources themselves, a model judges stance and copying, and deterministic code counts origin clusters, not URLs. Other contracts read `is_corroborated(claim_id)`.

It holds no funds, has no admin key, and ships no frontend.

- **Who calls it:** resolvers, DAOs, registries that need a factual premise nobody authored alone.
- **What it decides (consensus):** which sources are readable, what each says about the claim, and which are copies of each other.
- **What it never delegates to a model:** thresholds, origin merging floors, quorum counts, freshness, state transitions.

## Status (what has actually been verified)

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for exact transaction evidence. This repository is local only; it has not been pushed anywhere.

| Gate | Result |
|---|---|
| Direct Mode (`tests/direct`) | 109 passed, 0 failed (needs the Windows shim on Windows, see below) |
| Pickling check (`direct_vm.check_pickling = True`) | enabled for every Direct test |
| Mutation check of the validator | 8 mutants: 7 killed, 1 survives by design (see docs/CONSENSUS.md) |
| `genvm-lint lint` / `check` (0.11.0) | pass / pass |
| Studionet integration | see docs/DEPLOYMENT.md |

## Why GenLayer

| Alternative | What goes wrong |
|---|---|
| Backend operator | Chooses which copies count as independent and authors the verdict |
| Single LLM | A trusted reporter that can be prompt-injected by a page |
| Deterministic parser | Cannot read "did this page say the claim is true" or "is this a rewrite of that" |
| Ordinary oracle | Delivers a number, not a judgment over several documents |

**Delete GenLayer, and what breaks?** Nobody but the operator knows what the pages say or which are copies, so "independent corroboration" becomes whatever the operator reports.

## Why this is not a rejected pattern

Not a thin LLM wrapper (the model only labels; counts and verdict are deterministic and recomputed by every validator). Not format-only validation (a forged leader with perfect JSON is rejected on substance). Not caller-authored evidence (validators fetch the sources). Not a full application.

## Contract surface

| Method | Kind | Purpose |
|---|---|---|
| `open_claim(statement, urls, min_independent, max_age_s)` | write | Immutable claim definition, returns id |
| `assess(claim_id)` | write | Consensus round; 120 s cooldown |
| `verdict(claim_id)` | view | status, verdict, `independent_support`, `raw_support`, `independent_refute`, age, hashes |
| `status(claim_id)` / `is_corroborated(claim_id)` | view | `RELIABLE` / `STALE` / `BLOCKED` / `UNKNOWN`; true only when `RELIABLE` |
| `get_claim(claim_id)`, `claim_total()` | view | Definition and counters |

Verdicts: `CORROBORATED` (enough independent supporting origins and no independent refutation), `CONTESTED`, `REFUTED`, `INSUFFICIENT`. A failed or malformed model round is `INCONCLUSIVE` and changes nothing.

## Docs

[DECISION.md](DECISION.md) · [docs/CONSENSUS.md](docs/CONSENSUS.md) · [docs/SECURITY.md](docs/SECURITY.md) · [docs/INTEGRATION.md](docs/INTEGRATION.md) · [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Limitations

Measures agreement among listed sources, not absolute truth. Independence is inferred from domain and text, so paraphrasing sock-puppets can pass. Pages are cut at 5000 characters. Studionet is a development network.

## Reviewer fast path

```bash
python -m venv .venv-test && .venv-test/Scripts/python -m pip install -r requirements-test.txt
PYTHONPATH=. .venv-test/Scripts/python -m pytest tests/direct -q -p tests.support.win_direct_shim   # drop -p ... off Windows
genvm-lint check contracts/headwater.py
.venv-test/Scripts/gltest tests/integration/ -v -s --network studionet
```

On Windows, genlayer-test 0.29.2's Direct loader unlinks a temp file it still holds open (`WinError 32`) before any contract code runs. `tests/support/win_direct_shim.py` replaces only that one loader function and is a no-op elsewhere. The contract is unaffected.
