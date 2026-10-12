# Consensus design

## Nondeterministic calls (all inside one `gl.vm.run_nondet_unsafe` in `assess`)

| Call | Input | Output | Why code cannot replace it |
|---|---|---|---|
| `gl.nondet.web.request` per source | bounded HTTPS URL | status + body, cut to 5000 chars of text | Live web content is not on chain |
| `gl.nondet.exec_prompt(... json)` | claim + readable source texts as a JSON payload | per source: stance, verbatim quote, `copy_of` | "Does this page say the claim is true / is it a rewrite of that page" is a language judgment |

If fewer than two sources are readable, the model is **not called**; the result is a deterministic `INSUFFICIENT`.

## Leader

1. Fetch every source. 2. Compute deterministic links (same registrable domain; ≥50% containment of 5-word shingles, both sets ≥20). 3. Ask the model once. 4. Strict-parse: every readable index exactly once, stance in `SUPPORTS|REFUTES|SILENT`, `copy_of` an int in `[-1, n)` that is not self and not an unreadable source. Any violation → `{"ok": false}`. 5. Keep a stance only if its quote is 12–160 chars and appears verbatim (whitespace/case-normalised) in that source; otherwise it becomes `SILENT`. 6. Union deterministic links with model `copy_of` links into canonical clusters (label = smallest member index). 7. Derive counts and verdict with `_derive`.

## Validator (independent)

1. Reject non-`Return` leader results. 2. Fetch every source itself. 3. If the leader claims failure, accept only if the validator's own round also fails. 4. Otherwise `_well_formed` (exact types, bool is not int, canonical clusters, quote/stance consistency, counts and verdict recomputed from components). 5. Every non-`SILENT` quote must be grounded in **the validator's own** snapshot. 6. Every deterministic link must be one cluster in the leader's partition. 7. Re-run the whole observation and require equal **reach vector, verdict, independent support, independent refutation**.

## Equivalence

Must match: which sources were readable, the verdict, the number of independent supporting clusters, the number of independent refuting clusters.

May differ: quote choice, which of several valid quotes was used, `copy_of` links that do not change any count, raw support count (diagnostic), prose of any kind.

Not equivalent: a different verdict; a source readable for one party and not the other; a count that differs by one.

## Forged-leader defence (tested with `direct_vm.run_validator`)

Invented or borrowed quote; split syndicated copies; split same-domain sources; fabricated reachability; wrong counts for the components; verdict not derivable from components; `True`/`1.0`/`"3"` where an int is required; unknown or wrong-case enum; non-canonical clusters; missing/extra keys; non-dict envelopes; a false claim of failure. Mutation testing showed each comparison in the validator is individually load-bearing except the deterministic-link check, which is defence in depth (the count comparison already catches the cases the tests cover) and the post-consensus `_well_formed`, which cannot be reached by a forged leader in Direct Mode and is therefore untested there.

## Failure

| Event | Handling |
|---|---|
| Source unreachable / non-2xx / empty | reach 0; never read as a refutation |
| < 2 readable sources | deterministic `INSUFFICIENT`, no model call |
| Model error or malformed reply | `INCONCLUSIVE`, `recorded: false`, `failed_attempts += 1`, **prior verdict untouched** |
| Validators disagree | normal GenLayer rotation; nothing is written |
| Protocol `UNDETERMINED` | no state change; distinct from the contract verdict `INSUFFICIENT` |

## Why consensus is load-bearing

Remove it and the contract has no way to know what the sources say, whether they are readable, or which are copies. A single operator would supply those facts and could mint "independent" support at will.
