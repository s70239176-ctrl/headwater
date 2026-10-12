"""Direct Mode tests: public surface, admission, and every verdict through the real contract code.

Only the web and the model are mocked; `assess` itself is never stubbed.
"""
import pytest

from conftest import (
    A, A2, B, C, CLAIM, D, DENIAL, OWN_B, OWN_C, OWN_D, Q_B, Q_C, Q_D, Q_DENIAL, Q_WIRE, REWRITE,
    WIRE, WIRE_COPY, judged, row,
)


def _open(env, urls, **kw):
    cid = env.open(urls, **kw)
    assert cid >= 1
    assert env.c.get_claim(cid)["urls"] == urls  # setup really created the record
    return cid


def _three_independent(env):
    env.pages({A: WIRE, B: OWN_B, C: OWN_C})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_B), row(2, "SUPPORTS", Q_C)))


# ------------------------------------------------------------------ admission


def test_open_claim_records_immutable_definition(env):
    cid = _open(env, [A, B, C], min_independent=2, max_age_s=7200)
    got = env.c.get_claim(cid)
    assert got["statement"] == CLAIM and got["min_independent"] == 2 and got["max_age_s"] == 7200
    assert got["assessments"] == 0 and len(got["definition_hash"]) == 64
    assert env.c.claim_total() == 1
    v = env.c.verdict(cid)
    assert v["verdict"] == "UNASSESSED" and v["status"] == "UNKNOWN"
    assert env.c.is_corroborated(cid) is False


def test_ids_are_sequential_and_independent(env):
    one = _open(env, [A, B])
    two = _open(env, [B, C], statement="Another claim about the bridge.")
    assert (one, two) == (1, 2)
    assert env.c.get_claim(one)["definition_hash"] != env.c.get_claim(two)["definition_hash"]


@pytest.mark.parametrize("urls", [
    ["http://alpha-news.com/x", B],            # not https
    ["https://user:pw@alpha-news.com/x", B],   # credentials
    ["https://alpha-news.com:8443/x", B],      # port
    ["https://localhost/x", B],
    ["https://printer.local/x", B],
    ["https://127.0.0.1/x", B],
    ["https://010.0.0.1/x", B],
    ["https://Alpha-News.com/x", B],           # uppercase host
    ["https://alpha-news.com/x#frag", B],      # fragment
    ["https://-bad.com/x", B],
    ["https://nodot/x", B],
    ["https://alpha-news.com/" + "a" * 250, B],  # too long
    [A, A],                                    # duplicate
    [A],                                       # too few
    [A, B, C, D, "https://eps-five.com/", "https://zeta-six.com/"],  # too many
])
def test_rejects_bad_sources(env, urls):
    with env.vm.expect_revert("EXPECTED"):
        env.open(urls)


@pytest.mark.parametrize("kw", [
    {"min_independent": 1}, {"min_independent": 4}, {"max_age_s": 10}, {"max_age_s": 10**9},
    {"statement": ""}, {"statement": "   "}, {"statement": "x" * 241},
])
def test_rejects_bad_parameters(env, kw):
    with env.vm.expect_revert("EXPECTED"):
        env.open([A, B, C], **kw)


def test_unknown_claim_reverts(env):
    with env.vm.expect_revert("EXPECTED: unknown claim"):
        env.c.verdict(99)
    with env.vm.expect_revert("EXPECTED: unknown claim"):
        env.assess(99)


# ------------------------------------------------------------------ verdicts


def test_three_independent_sources_corroborate(env):
    cid = _open(env, [A, B, C])
    _three_independent(env)
    out = env.assess(cid)
    assert out["recorded"] is True and out["verdict"] == "CORROBORATED"
    v = env.c.verdict(cid)
    assert (v["verdict"], v["status"]) == ("CORROBORATED", "RELIABLE")
    assert (v["independent_support"], v["raw_support"], v["independent_refute"]) == (3, 3, 0)
    assert env.c.is_corroborated(cid) is True and env.c.status(cid) == "RELIABLE"
    assert len(v["evidence_digest"]) == 32


def test_syndicated_copy_counts_once(env):
    """A and B carry the same wire text: three URLs, two independent origins."""
    cid = _open(env, [A, B, C], min_independent=2)
    env.pages({A: WIRE, B: WIRE_COPY, C: OWN_C})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_WIRE), row(2, "SUPPORTS", Q_C)))
    env.assess(cid)
    v = env.c.verdict(cid)
    assert (v["raw_support"], v["independent_support"]) == (3, 2)
    assert v["verdict"] == "CORROBORATED"


def test_echo_chamber_is_insufficient_even_with_many_urls(env):
    cid = _open(env, [A, B, C], min_independent=3)
    env.pages({A: WIRE, B: WIRE_COPY, C: OWN_C})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_WIRE), row(2, "SUPPORTS", Q_C)))
    env.assess(cid)
    v = env.c.verdict(cid)
    assert (v["raw_support"], v["independent_support"]) == (3, 2)
    assert v["verdict"] == "INSUFFICIENT" and v["status"] == "UNKNOWN"
    assert env.c.is_corroborated(cid) is False


def test_same_registrable_domain_is_one_origin(env):
    cid = _open(env, [A, A2, B], min_independent=2)
    env.pages({A: WIRE, A2: OWN_D, B: OWN_B})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_D), row(2, "SUPPORTS", Q_B)))
    env.assess(cid)
    v = env.c.verdict(cid)
    assert (v["raw_support"], v["independent_support"]) == (3, 2)


def test_model_reported_copy_merges_paraphrase(env):
    cid = _open(env, [A, B, C], min_independent=3)
    env.pages({A: WIRE, B: REWRITE, C: OWN_C})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", "the Monday reopening followed the completed works", copy_of=0),
                   row(2, "SUPPORTS", Q_C)))
    env.assess(cid)
    v = env.c.verdict(cid)
    assert (v["raw_support"], v["independent_support"], v["verdict"]) == (3, 2, "INSUFFICIENT")


def test_one_independent_refutation_contests(env):
    cid = _open(env, [A, B, C], min_independent=2)
    env.pages({A: WIRE, B: OWN_B, C: DENIAL})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_B), row(2, "REFUTES", Q_DENIAL)))
    env.assess(cid)
    v = env.c.verdict(cid)
    assert (v["verdict"], v["status"]) == ("CONTESTED", "BLOCKED")
    assert (v["independent_support"], v["independent_refute"]) == (2, 1)
    assert env.c.is_corroborated(cid) is False


def test_independent_refutation_quorum_refutes(env):
    DENIAL2 = "Officials confirmed in writing that the Harbor Bridge remains closed to commuters while inspectors wait for parts."
    cid = _open(env, [A, B, C], min_independent=2)
    env.pages({A: DENIAL, B: DENIAL2, C: OWN_C})
    env.llm(judged(row(0, "REFUTES", Q_DENIAL), row(1, "REFUTES", "the Harbor Bridge remains closed to commuters"), row(2)))
    env.assess(cid)
    v = env.c.verdict(cid)
    assert (v["verdict"], v["status"], v["independent_refute"]) == ("REFUTED", "BLOCKED", 2)


def test_single_refuter_alone_is_insufficient_not_refuted(env):
    cid = _open(env, [A, B], min_independent=2)
    env.pages({A: DENIAL, B: OWN_B})
    env.llm(judged(row(0, "REFUTES", Q_DENIAL), row(1)))
    env.assess(cid)
    assert env.c.verdict(cid)["verdict"] == "INSUFFICIENT"


def test_cluster_that_both_supports_and_refutes_blocks(env):
    cid = _open(env, [A, A2, B], min_independent=2)
    env.pages({A: WIRE, A2: DENIAL, B: OWN_B})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "REFUTES", Q_DENIAL), row(2, "SUPPORTS", Q_B)))
    env.assess(cid)
    v = env.c.verdict(cid)
    assert v["verdict"] == "CONTESTED" and v["independent_support"] == 1


def test_all_silent_is_insufficient(env):
    cid = _open(env, [A, B])
    env.pages({A: WIRE, B: OWN_B})
    env.llm(judged(row(0), row(1)))
    env.assess(cid)
    v = env.c.verdict(cid)
    assert (v["verdict"], v["independent_support"]) == ("INSUFFICIENT", 0)


def test_ungrounded_quote_downgrades_to_silent(env):
    cid = _open(env, [A, B])
    env.pages({A: WIRE, B: OWN_B})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", "a sentence the page never contained at all")))
    env.assess(cid)
    v = env.c.verdict(cid)
    assert (v["raw_support"], v["verdict"]) == (1, "INSUFFICIENT")


def test_too_short_quote_downgrades_to_silent(env):
    cid = _open(env, [A, B])
    env.pages({A: WIRE, B: OWN_B})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", "Monday")))
    env.assess(cid)
    assert env.c.verdict(cid)["raw_support"] == 1


# ------------------------------------------------------------------ reachability and failure


def test_unreachable_sources_never_call_the_model(env):
    cid = _open(env, [A, B, C], min_independent=2)
    env.pages({A: WIRE, B: 503, C: None})  # no LLM mock registered: a model call would raise
    out = env.assess(cid)
    assert out["recorded"] is True and out["verdict"] == "INSUFFICIENT"


def test_empty_body_counts_as_unreachable(env):
    cid = _open(env, [A, B])
    env.pages({A: WIRE, B: ""})
    assert env.assess(cid)["verdict"] == "INSUFFICIENT"


@pytest.mark.parametrize("reply", [
    "not json at all",
    "[]",
    '{"sources": "nope"}',
    judged(row(0, "SUPPORTS", Q_WIRE)),                                   # missing index 1
    judged(row(0, "SUPPORTS", Q_WIRE), row(0, "SUPPORTS", Q_WIRE), row(1)),  # duplicate index
    judged(row(0, "MAYBE", Q_WIRE), row(1)),                              # unknown stance
    judged(row(0, "supports", Q_WIRE), row(1)),                           # wrong case is not repaired
    judged(row(0, "SUPPORTS", Q_WIRE, copy_of=0), row(1)),                # copy of itself
    judged(row(0, "SUPPORTS", Q_WIRE, copy_of=9), row(1)),                # out of range
    judged(row(0, "SUPPORTS", Q_WIRE), row(5)),                           # invented index
    judged(row(0, "SUPPORTS", Q_WIRE), {"i": 1, "stance": "SILENT", "quote": "", "copy_of": True}),
    judged(row(0, "SUPPORTS", 7), row(1)),                                # non-string quote
])
def test_malformed_model_reply_is_inconclusive_and_changes_no_verdict(env, reply):
    cid = _open(env, [A, B])
    env.pages({A: WIRE, B: OWN_B})
    env.llm(reply)
    out = env.assess(cid)
    assert out == {"claim_id": cid, "verdict": "INCONCLUSIVE", "recorded": False}
    assert env.c.verdict(cid)["verdict"] == "UNASSESSED"
    assert env.c.get_claim(cid)["failed_attempts"] == 1


def test_fenced_json_is_recovered(env):
    cid = _open(env, [A, B])
    env.pages({A: WIRE, B: OWN_B})
    env.llm("```json\n" + judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_B)) + "\n```")
    assert env.assess(cid)["verdict"] == "CORROBORATED"


def test_failed_reassessment_keeps_prior_corroboration(env):
    cid = _open(env, [A, B, C])
    _three_independent(env)
    env.assess(cid)
    env.llm("garbage")
    assert env.assess(cid)["recorded"] is False
    v = env.c.verdict(cid)
    assert v["verdict"] == "CORROBORATED" and env.c.get_claim(cid)["assessments"] == 1


def test_reassessment_can_withdraw_corroboration(env):
    cid = _open(env, [A, B, C])
    _three_independent(env)
    env.assess(cid)
    env.pages({A: WIRE, B: OWN_B, C: DENIAL})
    env.llm(judged(row(0, "SUPPORTS", Q_WIRE), row(1, "SUPPORTS", Q_B), row(2, "REFUTES", Q_DENIAL)))
    env.assess(cid)
    assert env.c.status(cid) == "BLOCKED" and env.c.get_claim(cid)["assessments"] == 2


# ------------------------------------------------------------------ cooldown and freshness


def test_cooldown_enforced_then_released(env):
    cid = _open(env, [A, B])
    env.pages({A: WIRE, B: OWN_B})
    env.llm(judged(row(0), row(1)))
    env.assess(cid)
    with env.vm.expect_revert("cooldown"):
        env.assess(cid, dt=119)
    env.assess(cid, dt=1)  # exactly 120s after the previous attempt


def test_failed_attempt_also_starts_cooldown(env):
    cid = _open(env, [A, B])
    env.pages({A: WIRE, B: OWN_B})
    env.llm("garbage")
    env.assess(cid)
    with env.vm.expect_revert("cooldown"):
        env.assess(cid, dt=10)


def test_corroboration_goes_stale_after_max_age(env):
    cid = _open(env, [A, B, C], max_age_s=3600)
    _three_independent(env)
    env.assess(cid)
    env.warp(env.t + 3600)
    assert env.c.status(cid) == "RELIABLE"  # exactly at the boundary is still fresh
    env.warp(env.t + 1)
    v = env.c.verdict(cid)
    assert v["status"] == "STALE" and v["verdict"] == "CORROBORATED" and v["age_s"] == 3601
    assert env.c.is_corroborated(cid) is False


def test_anyone_can_assess_and_claims_are_isolated(env):
    one = _open(env, [A, B, C])
    two = _open(env, [A, B, C], statement="The Harbor Bridge is closed.")
    _three_independent(env)
    env.assess(one, who=env.alice)
    assert env.c.status(one) == "RELIABLE" and env.c.status(two) == "UNKNOWN"
