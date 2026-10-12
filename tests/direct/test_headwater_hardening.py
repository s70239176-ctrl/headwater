"""Forged-leader tests: a well-formed but substantively false leader result must be rejected.

`direct_vm.run_validator` feeds the validator a leader result of our choosing while the validator
re-fetches the (mocked) pages and re-judges them itself.
"""
import copy

import pytest

from conftest import (
    A, B, C, DENIAL, OWN_B, OWN_C, Q_B, Q_C, Q_DENIAL, Q_WIRE, WIRE, WIRE_COPY, judged, row,
)


def honest(reach=(1, 1, 1), stance=("SUPPORTS",) * 3, quote=(Q_WIRE, Q_B, Q_C), cluster=(0, 1, 2),
           verdict="CORROBORATED", s=3, r=0, raw=3):
    return {"ok": True, "reach": list(reach), "stance": list(stance), "quote": list(quote),
            "cluster": list(cluster), "verdict": verdict, "s": s, "r": r, "raw": raw}


@pytest.fixture
def seeded(env):
    """A real corroborating assessment, so the contract's own validator is the one captured."""
    cid = env.open([A, B, C], min_independent=2)
    env.pages({A: WIRE, B: OWN_B, C: OWN_C})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_B), row(2, "SUPPORTS", Q_C)))
    env.assess(cid)
    return env


def ok(env, leader):
    return env.vm.run_validator(leader_result=leader)


def test_honest_result_accepted(seeded):
    assert ok(seeded, honest()) is True


def test_stored_leader_result_is_accepted(seeded):
    assert seeded.vm.run_validator() is True


def test_leader_error_rejected(seeded):
    assert seeded.vm.run_validator(leader_error=Exception("boom")) is False


# --- a wrong-but-well-formed leader is rejected on substance ------------------------------


def test_forged_corroboration_rejected_when_validator_sees_denial(seeded):
    seeded.pages({A: WIRE, B: OWN_B, C: DENIAL})
    seeded.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_B), row(2, "REFUTES", Q_DENIAL)))
    assert ok(seeded, honest()) is False


def test_forged_insufficient_rejected_when_validator_sees_corroboration(seeded):
    forged = honest(stance=("SILENT",) * 3, quote=("", "", ""), verdict="INSUFFICIENT", s=0, raw=0)
    assert ok(seeded, forged) is False


def test_forged_reachability_rejected(seeded):
    seeded.pages({A: WIRE, B: OWN_B, C: 503})
    seeded.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_B)))
    assert ok(seeded, honest()) is False  # claims C reachable and supporting
    honest_view = honest(reach=(1, 1, 0), stance=("SUPPORTS", "SUPPORTS", "SILENT"), quote=(Q_WIRE, Q_B, ""),
                         s=2, raw=2)
    assert ok(seeded, honest_view) is True


def test_invented_quote_rejected(seeded):
    forged = honest(quote=(Q_WIRE, Q_B, "the bridge was reopened by a team of helicopters on Monday"))
    assert ok(seeded, forged) is False


def test_quote_borrowed_from_another_source_rejected(seeded):
    forged = honest(quote=(Q_WIRE, Q_B, Q_B))  # source 2 does not contain Q_B
    assert ok(seeded, forged) is False


def test_splitting_syndicated_copies_into_separate_origins_rejected(env):
    """The deterministic floor: identical text cannot be reported as two independent origins."""
    cid = env.open([A, B, C], min_independent=2)
    env.pages({A: WIRE, B: WIRE_COPY, C: OWN_C})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_WIRE), row(2, "SUPPORTS", Q_C)))
    env.assess(cid)
    assert env.c.verdict(cid)["independent_support"] == 2
    forged = honest(quote=(Q_WIRE, Q_WIRE, Q_C), cluster=(0, 1, 2), s=3, raw=3)
    assert ok(env, forged) is False
    merged = honest(quote=(Q_WIRE, Q_WIRE, Q_C), cluster=(0, 0, 2), s=2, raw=3)
    assert ok(env, merged) is True


def test_same_domain_split_rejected(env):
    a2 = "https://alpha-news.com/other-desk"
    cid = env.open([A, a2, B], min_independent=2)
    env.pages({A: WIRE, a2: OWN_C, B: OWN_B})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_C), row(2, "SUPPORTS", Q_B)))
    env.assess(cid)
    forged = honest(quote=(Q_WIRE, Q_C, Q_B), cluster=(0, 1, 2), s=3, raw=3)
    assert ok(env, forged) is False


def test_forged_count_inconsistent_with_components_rejected(seeded):
    assert ok(seeded, honest(s=2)) is False
    assert ok(seeded, honest(raw=2)) is False
    assert ok(seeded, honest(r=1)) is False
    assert ok(seeded, honest(verdict="CONTESTED")) is False


# --- type and shape hardening --------------------------------------------------------------


def _mutated(**changes):
    base = honest()
    base.update(changes)
    return base


@pytest.mark.parametrize("leader", [
    None, [], "CORROBORATED", 3, True,
    {"ok": True},
    {"ok": 1},
    {"ok": "true"},
    {"ok": False, "extra": 1},
])
def test_non_dict_or_wrong_envelope_rejected(seeded, leader):
    assert ok(seeded, leader) is False


@pytest.mark.parametrize("field,value", [
    ("reach", [True, True, True]),               # bool is not an int
    ("reach", [1.0, 1, 1]),
    ("reach", [1, 1, 2]),
    ("reach", [1, 1]),                            # wrong length
    ("reach", "111"),
    ("stance", ["SUPPORTS", "SUPPORTS", "supports"]),
    ("stance", ["SUPPORTS", "SUPPORTS", "MAYBE"]),
    ("stance", ["SUPPORTS", "SUPPORTS", True]),
    ("quote", [Q_WIRE, Q_B, 3]),
    ("cluster", [0, 1, 1.0]),
    ("cluster", [0, 1, True]),
    ("cluster", [0, 1, 3]),                       # out of range
    ("cluster", [0, 1, -1]),
    ("cluster", [0, 0, 1]),                       # root is not canonical (1 is not its own root)
    ("verdict", "corroborated"),
    ("verdict", "MAYBE"),
    ("verdict", None),
    ("s", True),
    ("s", 3.0),
    ("s", "3"),
    ("s", -1),
    ("raw", 99),
])
def test_malformed_field_rejected(seeded, field, value):
    assert ok(seeded, _mutated(**{field: value})) is False


def test_missing_and_extra_keys_rejected(seeded):
    short = honest()
    del short["raw"]
    assert ok(seeded, short) is False
    extra = honest()
    extra["admin"] = True
    assert ok(seeded, extra) is False


def test_positive_stance_without_quote_rejected(seeded):
    assert ok(seeded, honest(quote=(Q_WIRE, Q_B, ""))) is False


def test_silent_with_quote_rejected(seeded):
    forged = honest(stance=("SUPPORTS", "SUPPORTS", "SILENT"), quote=(Q_WIRE, Q_B, Q_C), s=2, raw=2)
    assert ok(seeded, forged) is False


def test_unreachable_source_cannot_carry_a_stance(seeded):
    forged = honest(reach=(1, 1, 0))
    assert ok(seeded, forged) is False


# --- failure claims -------------------------------------------------------------------------


def test_leader_cannot_claim_failure_when_validator_can_judge(seeded):
    assert ok(seeded, {"ok": False}) is False


def test_honest_failure_accepted_when_validator_also_cannot_judge(seeded):
    seeded.llm("garbage")
    assert ok(seeded, {"ok": False}) is True
    assert ok(seeded, honest()) is False  # and a positive claim cannot be confirmed either


def test_honest_result_accepted_does_not_mutate_input(seeded):
    leader = honest()
    snapshot = copy.deepcopy(leader)
    ok(seeded, leader)
    assert leader == snapshot


# --- dimensions that only a specific comparison catches (found by mutation testing) ---------


def test_reach_mismatch_with_equal_counts_rejected(seeded):
    """Leader claims C readable-but-silent; validator gets a 503. Counts are identical, reach is not."""
    seeded.pages({A: WIRE, B: OWN_B, C: 503})
    seeded.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_B)))
    forged = honest(stance=("SUPPORTS", "SUPPORTS", "SILENT"), quote=(Q_WIRE, Q_B, ""), s=2, raw=2)
    assert ok(seeded, forged) is False


def test_verdict_mismatch_with_equal_counts_rejected(env):
    """Same s and r, but the validator sees a mixed (supports+refutes) origin that blocks REFUTED."""
    a2 = "https://alpha-news.com/other-desk"
    d2 = "Officials confirmed in writing that the Harbor Bridge remains closed to commuters while inspectors wait for parts."
    d3 = "A union spokesperson said the Harbor Bridge stays shut because the replacement bearings have not yet arrived."
    cid = env.open([A, a2, B, C], min_independent=2)
    env.pages({A: DENIAL, a2: WIRE, B: d2, C: d3})
    env.llm(judged(row(0, "REFUTES", Q_DENIAL), row(1, "SUPPORTS", Q_WIRE),
                   row(2, "REFUTES", "the Harbor Bridge remains closed to commuters"),
                   row(3, "REFUTES", "the Harbor Bridge stays shut")))
    env.assess(cid)
    v = env.c.verdict(cid)
    assert (v["verdict"], v["independent_refute"], v["independent_support"]) == ("INSUFFICIENT", 2, 0)
    forged = {"ok": True, "reach": [1, 1, 1, 1], "stance": ["SILENT", "SILENT", "REFUTES", "REFUTES"],
              "quote": ["", "", "the Harbor Bridge remains closed to commuters", "the Harbor Bridge stays shut"],
              "cluster": [0, 0, 2, 3], "verdict": "REFUTED", "s": 0, "r": 2, "raw": 0}
    assert ok(env, forged) is False
