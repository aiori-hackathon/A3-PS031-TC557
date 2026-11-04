# AIORI-3-HACKATHON-PROJECTS
This repository will contain the code and resources for the AIORI-3 hackathon that will be developed during the AIORI-3

## Team Introduction Video
YouTube:https://www.youtube.com/watch?v=w7CLg5a7KVw

# Project Demonstration Video AIORI3 Hackathon 2026
Team Name: TrustZero
Team Code: A3-PS031-TC557
Problem Statement ID: PS-031
Problem Statement: Offline ASPA-Based BGP Export Policy Checker
# Working Demo
This demonstration video presents our proposed solution, Python application execution, sample test cases, and validation results, including Valid, Invalid, and Unknown classifications.
# Project Demonstration Video
YouTube:https://youtu.be/y6EqeSNyJB8?si=rJturnLT1VjXmNlb


# AIORI-3 PS-031 Offline ASPA-Based BGP Export Policy Checker

This is a runnable, dependency-free Python prototype for the PS-031 challenge. It evaluates a proposed eBGP export against a synthetic ASPA database, an AS_PATH, and an explicit neighbor relationship. It reports **Valid**, **Invalid**, or **Unknown**, and shows the authorization lookups and reasons behind the result.

## Run it

Python 3.9+ is sufficient; there are no third-party dependencies.

```bash
cd aiori3_ps031_checker
python3 app.py
```

A graphical Tkinter window opens. Enter the AS_PATH in BGP display order: most recently added AS first and origin AS last. Select `provider`, `peer`, or `customer`, then click **Check export**. The dataset and UI are local/offline after the project is copied to a machine with Python and Tkinter.

Run the structured fixture suite with:

```bash
python3 test_fixtures.py
```

The repository contains 24 fixtures spanning valid paths, provable invalid paths, unknown paths caused by missing attestation, neighbor mismatches, AS_SET handling, route-server-client exception handling, relationship/policy context, and neighbor-AS augmentation.

## Algorithm basis

The implementation follows the procedure described by the pinned mentor draft revision at implementation time:

- `draft-ietf-sidrops-aspa-verification-05`, sections 5.2–5.6: consecutive duplicate compression; `authorized(CAS, provider)` with `Provider+`, `Not Provider+`, and `No Attestation`; up/down ramp bounds; upstream and downstream result rules.
- `draft-zhang-sidrops-aspa-egress-05`, section 4.1: egress verification uses the AS_PATH after BGP update/prepending; a Provider or Peer neighbor selects upstream verification, while a Customer neighbor selects downstream verification.
- The optional checkbox implements the egress draft's section 4.2 neighbor-AS-augmented verification mode for offline/monitoring use. It changes the verification input only; it does not mutate the displayed route.

The key result ordering is intentionally not “missing data equals invalid”: a provable maximum-ramp failure is **Invalid**; if the maximum bounds do not disprove the path but minimum bounds cannot prove it because of `No Attestation`, the result is **Unknown**; otherwise it is **Valid**. Empty paths, AS_SETs, and (unless the route-server-client exception is selected) a most-recent AS that differs from the configured neighbor are **Invalid** before ramp evaluation.

## Important caveats for mentor review

These are synthetic ASPA records, not RPKI objects. The prototype does not parse ROAs, validate ASPA signatures, reconstruct AS4_PATH, implement RFC 4271 treat-as-withdraw processing, model confederations, OTC, BGP Roles negotiation, or perform live route blocking. The UI treats an AS_SET as a separate boolean because a full BGP attribute parser is out of scope.

The draft is an Internet-Draft and can change. The fixture expected outcomes are proposed test vectors for mentor review, not normative truth. Before demonstration or submission, pin the exact mentor-approved draft revision and reconcile every fixture with that revision and the mentor-supplied algorithm. In particular, confirm path ordering, neighbor-AS augmentation policy, route-server handling, and any policy-specific treatment of Unknown. This checker displays the verification result; it does not decide a router's mitigation policy.

## Files

- `app.py` — local Tkinter user interface.
- `engine.py` — standalone verification engine.
- `dataset.json` — synthetic ASPA records and explicitly missing CAS entries.
- `fixtures.json` — 24 structured expected-result cases.
- `test_fixtures.py` — deterministic fixture runner.



[3]: https://github.com/aiori-hackathon "AIORI Hackathon GitHub account referenced by the PS-031 brief"
