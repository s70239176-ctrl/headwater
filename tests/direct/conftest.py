import datetime
import json
import sys

import pytest

BASE = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)

A = "https://alpha-news.com/story"
A2 = "https://alpha-news.com/other-desk"  # same registrable domain as A
B = "https://beta-daily.org/report"
C = "https://gamma-wire.net/item"
D = "https://delta-post.io/piece"

CLAIM = "The Harbor Bridge reopened to traffic on Monday after repairs."

WIRE = (
    "The Harbor Bridge reopened to all traffic on Monday morning after nine weeks of structural repairs, "
    "city engineers said, and the first vehicles crossed at dawn while crews removed the final barriers "
    "from the eastern approach and inspectors signed the completion certificate for the crossing."
)
WIRE_COPY = "Republished with permission. " + WIRE + " Copyright holders reserve all rights."
OWN_B = (
    "Our reporter stood at the toll plaza and watched the Harbor Bridge open to cars on Monday; the transport "
    "authority confirmed in a statement that repairs were complete and the lanes were cleared for commuters."
)
OWN_C = (
    "Commuters on the north shore welcomed the end of the detour as the Harbor Bridge carried traffic again "
    "on Monday, with the harbour master noting that shipping inspections beneath the span had also finished."
)
OWN_D = (
    "Independent surveyors who examined the Harbor Bridge decking last week reported that the repaired spans "
    "meet load standards, and a spokesperson said traffic returned to the crossing on Monday as scheduled."
)
REWRITE = (
    "Motorists are using the rebuilt Harbor Bridge once more after the long closure ended, according to "
    "the news agency report published earlier, which said the Monday reopening followed the completed works."
)
DENIAL = (
    "Contrary to rumours the Harbor Bridge remains closed to all traffic this week, and officials say "
    "the repairs have slipped so no reopening date has been set for the crossing."
)

Q_WIRE = "The Harbor Bridge reopened to all traffic on Monday morning"
Q_B = "watched the Harbor Bridge open to cars on Monday"
Q_C = "the Harbor Bridge carried traffic again on Monday"
Q_D = "traffic returned to the crossing on Monday as scheduled"
Q_DENIAL = "the Harbor Bridge remains closed to all traffic this week"


def iso(offset_s: int) -> str:
    return (BASE + datetime.timedelta(seconds=offset_s)).isoformat().replace("+00:00", "Z")


def row(i, stance="SILENT", quote="", copy_of=-1):
    return {"i": i, "stance": stance, "quote": quote, "copy_of": copy_of}


def judged(*rows):
    return json.dumps({"sources": list(rows)})


class Env:
    def __init__(self, vm, contract, alice, bob):
        self.vm, self.c = vm, contract
        self.alice, self.bob = alice, bob
        self.t = 0
        self._pages = {}

    def warp(self, offset_s):
        # genlayer-test 0.29.2: vm.warp() does not refresh the already-loaded
        # gl.message_raw['datetime'] that the contract reads, so sync it here.
        self.t = offset_s
        self.vm.warp(iso(offset_s))
        sys.modules["genlayer.gl"].message_raw["datetime"] = iso(offset_s)

    def as_(self, who):
        self.vm.sender = who

    def reset(self):
        self.vm.clear_mocks()

    def pages(self, mapping):
        """mapping: url -> text (200) | int (HTTP status) | None (unreachable)."""
        self._pages = dict(mapping)
        self.reset()
        for url, body in mapping.items():
            if body is None:
                continue
            if isinstance(body, int):
                self.vm.mock_web("^" + url.replace(".", r"\.") + "$", {"method": "GET", "status": body, "body": "x"})
            else:
                self.vm.mock_web("^" + url.replace(".", r"\.") + "$", {"method": "GET", "status": 200, "body": body})

    def llm(self, response):
        """Replace the model mock (mocks are first-match, so old ones must go), keeping the page mocks."""
        self.pages(self._pages)
        self.vm.mock_llm(r"HEADWATER_JUDGE", response)

    def open(self, urls, min_independent=2, max_age_s=86400, statement=CLAIM, who=None):
        self.as_(who or self.alice)
        return self.c.open_claim(statement, urls, min_independent, max_age_s)

    def assess(self, claim_id, dt=200, who=None):
        self.warp(self.t + dt)
        self.as_(who or self.bob)
        return self.c.assess(claim_id)


@pytest.fixture
def env(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.check_pickling = True
    direct_vm.warp(iso(0))
    contract = direct_deploy("contracts/headwater.py")
    from genlayer.py.types import Address  # importable once the loader has staged the SDK
    a, b = (Address(x) if isinstance(x, bytes) else x for x in (direct_alice, direct_bob))
    e = Env(direct_vm, contract, a, b)
    e.warp(0)
    return e
