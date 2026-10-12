"""Real-consensus Studionet tests. Each test deploys its own disposable contract.

Run:  gltest tests/integration/ -v -s --network studionet

Sources are stable public pages. docs.python.org serves the same release notes under two URLs
(one registrable domain, near-identical text); endoflife.date is an unrelated origin. So there are
three URLs but at most TWO independent origins, whatever the model says. Assertions are limited to
settlement-critical fields (verdict, status, counts), never model prose.
"""
from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_succeeded

DOCS_A = "https://docs.python.org/3.12/whatsnew/3.12.html"
DOCS_B = "https://docs.python.org/release/3.12.0/whatsnew/3.12.html"
EOL = "https://endoflife.date/api/python/3.12.json"
MISSING = "https://endoflife.date/api/python/9.99.json"

TRUE_CLAIM = "Python 3.12 was released on 2 October 2023."
FALSE_CLAIM = "Python 3.12 was released in October 2019."


def _deploy():
    factory = get_contract_factory(contract_file_path="headwater.py")
    return factory.deploy(account=get_default_account(), consensus_max_rotations=3)


def _open(c, statement, urls, min_independent=2, max_age_s=86400):
    r = c.open_claim(args=[statement, urls, min_independent, max_age_s]).transact(consensus_max_rotations=3)
    assert tx_execution_succeeded(r)
    assert c.claim_total(args=[]).call() == 1  # setup really created state
    assert c.get_claim(args=[1]).call()["urls"] == urls
    return 1


def _assess(c, claim_id):
    r = c.assess(args=[claim_id]).transact(consensus_max_rotations=3)
    assert tx_execution_succeeded(r)
    return c.verdict(args=[claim_id]).call()


def test_deploy_and_public_surface():
    c = _deploy()
    cid = _open(c, TRUE_CLAIM, [DOCS_A, DOCS_B, EOL])
    v = c.verdict(args=[cid]).call()
    assert v["verdict"] == "UNASSESSED" and v["status"] == "UNKNOWN"
    assert c.is_corroborated(args=[cid]).call() is False
    assert len(c.get_claim(args=[cid]).call()["definition_hash"]) == 64


def test_live_true_claim_counts_origins_not_urls():
    c = _deploy()
    cid = _open(c, TRUE_CLAIM, [DOCS_A, DOCS_B, EOL], min_independent=2)
    v = _assess(c, cid)
    assert v["independent_support"] <= 2  # the two docs.python.org URLs can never count twice
    assert v["independent_support"] <= v["raw_support"]
    assert v["verdict"] == "CORROBORATED" and v["status"] == "RELIABLE"
    assert c.is_corroborated(args=[cid]).call() is True


def test_live_three_independent_origins_cannot_be_reached_from_two():
    c = _deploy()
    cid = _open(c, TRUE_CLAIM, [DOCS_A, DOCS_B, EOL], min_independent=3)
    v = _assess(c, cid)
    assert v["verdict"] != "CORROBORATED" and v["status"] != "RELIABLE"
    assert v["independent_support"] <= 2
    assert c.is_corroborated(args=[cid]).call() is False


def test_live_false_claim_is_never_corroborated():
    c = _deploy()
    cid = _open(c, FALSE_CLAIM, [DOCS_A, DOCS_B, EOL], min_independent=2)
    v = _assess(c, cid)
    assert v["verdict"] != "CORROBORATED"
    assert c.is_corroborated(args=[cid]).call() is False


def test_live_unreachable_source_and_cooldown():
    c = _deploy()
    cid = _open(c, TRUE_CLAIM, [EOL, MISSING], min_independent=2)
    v = _assess(c, cid)  # 404 -> one readable source -> deterministic INSUFFICIENT, no model call
    assert v["verdict"] == "INSUFFICIENT" and v["independent_support"] == 0
    again = c.assess(args=[cid]).transact(consensus_max_rotations=3)
    assert not tx_execution_succeeded(again)  # reassess cooldown (120s of chain time) not elapsed
    assert c.get_claim(args=[cid]).call()["assessments"] == 1
