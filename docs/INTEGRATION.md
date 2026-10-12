# Using Headwater from another Intelligent Contract

The consumer needs no web access, prompts, or equivalence logic.

```python
from genlayer import *


@gl.contract_interface
class IHeadwater:
    class View:
        def is_corroborated(self, claim_id: int) -> bool: ...
        def verdict(self, claim_id: int) -> dict: ...


class Market(gl.Contract):
    headwater: Address

    def __init__(self, headwater: str):
        self.headwater = Address(headwater)

    @gl.public.write
    def settle_yes(self, claim_id: int) -> None:
        if not IHeadwater(self.headwater).view().is_corroborated(claim_id):
            raise gl.vm.UserError("EXPECTED: claim is not currently corroborated")
        ...  # settle
```

## Reading the result

`verdict(claim_id)` returns `status` (`RELIABLE` | `STALE` | `BLOCKED` | `UNKNOWN`), `verdict` (`CORROBORATED` | `CONTESTED` | `REFUTED` | `INSUFFICIENT` | `UNASSESSED`), `independent_support`, `raw_support` (naive URL count, to show inflation), `independent_refute`, `age_s`, `definition_hash`, and `evidence_digest`.

Pin `definition_hash` (from `get_claim`) if you must be sure the claim and sources are the ones you reviewed; they are immutable.

## Creating and refreshing

`open_claim(statement, urls, min_independent, max_age_s)` returns the new claim id for direct callers. Cross-contract writes are asynchronous, so a calling contract should read `claim_total()` afterwards rather than rely on a synchronous return. Anyone may call `assess(claim_id)`; call it again before `max_age_s` elapses to keep `RELIABLE`.

Note: the consumer interface above has not been executed on a network in this repository; only the contract's own views are covered by tests.
