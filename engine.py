"""Offline ASPA-based BGP export checker.

Modelled on draft-ietf-sidrops-aspa-verification-05 sections 5.2-5.6 and
 draft-zhang-sidrops-aspa-egress-05 section 4.1/4.2. Paths are entered in
BGP display order: most recently added AS first, origin AS last.
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set, Tuple

VALID = "Valid"
INVALID = "Invalid"
UNKNOWN = "Unknown"

@dataclass
class CheckInput:
    local_as: int
    neighbor_as: int
    relationship: str  # provider, peer, customer
    as_path: List[int]
    as_sets: bool = False
    neighbor_augmented: bool = False
    route_server_client: bool = False

@dataclass
class CheckResult:
    status: str
    procedure: str
    compressed_path: List[int]
    max_up_ramp: int
    min_up_ramp: int
    max_down_ramp: int
    min_down_ramp: int
    reasons: List[str]
    audit: List[dict]

    def to_dict(self):
        return asdict(self)

class AspaDatabase:
    def __init__(self, records: Dict[str, List[int]], missing: Optional[Set[int]] = None):
        self.records = {int(k): set(v) for k, v in records.items()}
        self.missing = set(missing or set())

    def authorize(self, customer: int, provider: int) -> Tuple[str, str]:
        """Return Provider+, Not Provider+, or No Attestation plus an audit note."""
        if customer in self.missing or customer not in self.records:
            return "No Attestation", f"No valid ASPA attestation available for CAS {customer}."
        if provider in self.records[customer]:
            return "Provider+", f"ASPA({customer}) authorizes provider {provider}."
        return "Not Provider+", f"ASPA({customer}) does not authorize provider {provider}."


def _compress(path: List[int]) -> List[int]:
    out = []
    for asn in path:
        if not out or out[-1] != asn:
            out.append(asn)
    return out


def _ramp_bounds(path: List[int], db: AspaDatabase):
    """Calculate the four bounds exactly as the draft's indexed rules imply."""
    n = len(path)
    origin_first = list(reversed(path))
    up_audit = []
    max_up = min_up = n
    for i in range(n - 1):
        customer, provider = origin_first[i], origin_first[i + 1]
        outcome, note = db.authorize(customer, provider)
        up_audit.append({"direction": "up", "customer": customer, "provider": provider,
                         "authorization": outcome, "note": note})
        if outcome == "Not Provider+" and max_up == n:
            max_up = i + 1
        if outcome in ("No Attestation", "Not Provider+") and min_up == n:
            min_up = i + 1
    down_audit = []
    max_down = min_down = n
    for i in range(n - 1):
        customer, provider = path[i], path[i + 1]
        outcome, note = db.authorize(customer, provider)
        down_audit.append({"direction": "down", "customer": customer, "provider": provider,
                           "authorization": outcome, "note": note})
        if outcome == "Not Provider+" and max_down == n:
            max_down = i + 1
        if outcome in ("No Attestation", "Not Provider+") and min_down == n:
            min_down = i + 1
    return max_up, min_up, max_down, min_down, up_audit + down_audit


def check(inp: CheckInput, db: AspaDatabase) -> CheckResult:
    reasons: List[str] = []
    audit: List[dict] = []
    procedure = "Upstream" if inp.relationship in ("provider", "peer") else "Downstream"
    path = list(inp.as_path)
    if inp.neighbor_augmented and inp.relationship in ("provider", "customer"):
        path = [inp.neighbor_as] + path
        reasons.append(f"Neighbor-AS-augmented mode prepended neighbor AS {inp.neighbor_as} for verification only.")
    compressed = _compress(path)
    n = len(compressed)
    if n == 0:
        return CheckResult(INVALID, procedure, compressed, 0, 0, 0, 0,
                           reasons + ["The AS_PATH is empty; the draft requires Invalid."], audit)
    if not inp.route_server_client and compressed[0] != inp.neighbor_as:
        return CheckResult(INVALID, procedure, compressed, 0, 0, 0, 0,
                           reasons + [f"Most recently added AS {compressed[0]} does not match neighbor AS {inp.neighbor_as}."], audit)
    if inp.as_sets:
        return CheckResult(INVALID, procedure, compressed, 0, 0, 0, 0,
                           reasons + ["The AS_PATH contains an AS_SET; the verification procedure requires Invalid."], audit)
    max_up, min_up, max_down, min_down, audit = _ramp_bounds(compressed, db)
    if procedure == "Upstream":
        max_down = min_down = 0
        if max_up < n:
            status = INVALID
            reasons.append(f"A provable up-ramp break occurs: max_up_ramp={max_up} < N={n}.")
        elif min_up < n:
            status = UNKNOWN
            reasons.append(f"The path may be valid, but missing/uncertain authorization prevents proof: min_up_ramp={min_up} < N={n}.")
        else:
            status = VALID
            reasons.append(f"All {n} compressed ASes are covered by authorized up-ramp relationships.")
    else:
        if max_up + max_down < n:
            status = INVALID
            reasons.append(f"The combined maximum ramps cannot cover the path: {max_up}+{max_down} < N={n}.")
        elif min_up + min_down < n:
            status = UNKNOWN
            reasons.append(f"The combined minimum ramps do not prove the path: {min_up}+{min_down} < N={n}.")
        else:
            status = VALID
            reasons.append(f"The combined minimum ramps cover the path: {min_up}+{min_down} >= N={n}.")
    return CheckResult(status, procedure, compressed, max_up, min_up, max_down, min_down, reasons, audit)
