"""Canonical Studionet deployment + live evidence. Run:
  gltest scripts/canonical_deploy_test.py -s --network studionet
Writes docs/canonical-evidence.json (public addresses and tx hashes only)."""
import json
import os
import pathlib
import time

from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_succeeded
from gltest.utils import extract_contract_address

DOCS_A = "https://docs.python.org/3.12/whatsnew/3.12.html"
DOCS_B = "https://docs.python.org/release/3.12.0/whatsnew/3.12.html"
EOL = "https://endoflife.date/api/python/3.12.json"
MISSING = "https://endoflife.date/api/python/9.99.json"


def retry(fn, tries=6):
    """Transport-level retry only (connect timeouts before a request lands)."""
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa
            if "timed out" not in str(e) and "Max retries" not in str(e) or i == tries - 1:
                raise
            time.sleep(20)


def save(ev):
    pathlib.Path("docs/canonical-evidence.json").write_text(json.dumps(ev, indent=2, default=str))


def _h(r):
    return {k: r.get(k) for k in ("hash", "status_name", "result_name") if isinstance(r, dict) and k in r} or str(r)[:300]


def test_canonical():
    ev = {}
    f = get_contract_factory(contract_file_path="headwater.py")
    acct = get_default_account()
    prev = pathlib.Path("docs/canonical-evidence.json")
    if os.environ.get("RESUME") and prev.exists():  # continue on the same deployment after a transport failure
        ev = json.loads(prev.read_text())
        addr = ev["address"]
    else:
        r = retry(lambda: f.deploy_contract_tx(account=acct, consensus_max_rotations=3))
        assert tx_execution_succeeded(r)
        addr = extract_contract_address(r)
        ev["address"], ev["deployer"], ev["deploy"] = addr, acct.address, _h(r)
        save(ev)
    print("ADDRESS", addr)
    c = f.build_contract(contract_address=addr, account=acct)

    def run(name, stmt, urls, mn):
        if name in ev:
            return
        o = c.open_claim(args=[stmt, urls, mn, 86400]).transact(consensus_max_rotations=3)
        assert tx_execution_succeeded(o)
        cid = retry(lambda: c.claim_total(args=[]).call())
        a = c.assess(args=[cid]).transact(consensus_max_rotations=3)  # never retried: writes are not idempotent
        ev.setdefault('tx_ok', {})[name] = bool(tx_execution_succeeded(a))
        ev[name] = {"claim_id": cid, "open": _h(o), "assess": _h(a), "verdict": retry(lambda: c.verdict(args=[cid]).call()),
                    "is_corroborated": retry(lambda: c.is_corroborated(args=[cid]).call())}
        save(ev)
        print(name, json.dumps(ev[name], default=str))

    run("success", "Python 3.12 was released on 2 October 2023.", [DOCS_A, DOCS_B, EOL], 2)
    run("negative", "Python 3.12 was released in October 2019.", [DOCS_A, DOCS_B, EOL], 2)
    run("unreachable", "Python 3.12 was released on 2 October 2023.", [EOL, MISSING], 2)
    save(ev)
    assert all(ev["tx_ok"].values()), ev["tx_ok"]
    assert ev["success"]["verdict"]["verdict"] == "CORROBORATED"
    assert ev["negative"]["is_corroborated"] is False
    assert ev["unreachable"]["verdict"]["verdict"] == "INSUFFICIENT"
