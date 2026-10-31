# NetArchitect: Strategic Build Plan

**Course:** CIC-307 Computer Networks Mini-Project  
**Working title:** NetArchitect: Recommendation & Config Engine  
**Implementation choice:** Python 3.10+ command-line application using only the standard library

## Project goal

Build a small, inspectable planning utility that turns a network profile or custom JSON request into an address plan, explainable design recommendations, and Cisco IOS configuration drafts. Each recommendation must be traceable to a parameter or an explicit engineering rule. The tool is a planning aid; generated configurations require review against the actual inventory and operational policy before deployment.

## Why a CLI

The assignment permits a CLI, web dashboard, or API. A CLI keeps the algorithm visible, runs without a web server or third-party packages, and makes the same engine reusable by a future interface. The user can inspect each intermediate artifact instead of receiving an unexplained one-click design.

## Delivery strategy

### Step 1: Translate the specification into acceptance points

- Ship three built-in profiles: Campus LAN, Metro MAN, and Global WAN.
- Validate custom distance, endpoint density, resiliency, addressing, and subnet inputs with actionable errors.
- Select physical media by distance and reject copper when the requested copper run exceeds 100 m.
- Calculate fiber-loss estimates with stated assumptions and explain the transceiver/reach choice.
- Allocate host requests using descending, aligned IPv4 VLSM blocks; show network, gateway, usable range, broadcast, wildcard mask, and utilization.
- Detect invalid requests, address-space exhaustion, and overlap before producing configurations.
- Select OSPF Area 0 for a single routing domain with fewer than 50 subnets; select a multi-area OSPF/eBGP design for multi-site or cloud boundaries and explain the choice.
- Generate Cisco IOS drafts for a Layer 3 core switch and an edge router, including VLANs, SVIs, OSPF, and a sample isolation ACL.
- Include a standard-library unit-test suite and an AI audit log with two corrected failure cases and packet-flow reasoning.

### Step 2: Define one shared input and output model

Keep profile JSON, custom JSON, validation, recommendation logic, report text, and configuration generation on the same schema. This avoids the common failure where the report and device files describe different VLANs or addresses. Treat calculated data as immutable plan records after allocation.

### Step 3: Implement narrow algorithm modules

Separate concerns into `media.py`, `vlsm.py`, `routing.py`, `configgen.py`, `explain.py`, and `engine.py`. Put input models and domain-specific exceptions in `models.py` and `errors.py`. Keep orchestration and command parsing in `cli.py` and `__main__.py`.

### Step 4: Author representative inputs and defensive checks

Define the three profiles as versioned JSON under `profiles/`. Validate CIDRs and request fields before running algorithms. Make distance boundaries, VLSM alignment, host capacity, and wildcard masks explicit. Emit a concise explanation for both decisions and rejected requests.

### Step 5: Generate reviewable artifacts

For each profile, export a Markdown design report, CSV address plan, machine-readable JSON plan, and separate core-switch and edge-router IOS drafts. Keep the three sample exports in `examples/` so the deliverable can be reviewed without first running the tool.

### Step 6: Document operation and technical defense

Provide installation-free run instructions, custom-input schema, algorithm notes, assumptions, safe-use guidance, and the AI audit record. Explain where the design depends on real-world information that the program cannot infer, including optical-module datasheets, carrier SLAs, device syntax, security policy, and the production topology.

### Step 7: Verify the deliverable

Review file consistency and generated examples. The assignment requires a unit-test suite, so include tests for distance boundaries, copper violations, VLSM allocation and exhaustion, mask/wildcard math, and routing thresholds. Record test execution status separately from test coverage; do not claim a test run unless it was actually performed.

## Proposed repository layout

```text
README.md
pyproject.toml
netarchitect/
  __init__.py, __main__.py, cli.py, models.py, errors.py
  media.py, vlsm.py, routing.py, configgen.py, explain.py, engine.py
netarchitect/profiles/{campus,metro,global}.json
tests/
docs/{STRATEGIC_PLAN,ARCHITECTURE,ALGORITHMS,USER_GUIDE,ASSUMPTIONS,ai_audit_log}.md
examples/{campus,metro,global}/
```

## Completion criteria

The repository is complete when a clean Python 3.10+ environment can list profiles, generate all three preset exports, and accept a custom JSON profile; the generated report and configurations agree on addresses and routing choices; the unit-test suite covers the assessed edge cases; and the audit documentation distinguishes reproducible analysis from vendor lab or Packet Tracer evidence.

## Scope boundaries

The deliverable is an educational planner, not an autonomous deployment system. It will not connect to routers, discover live topology, guarantee a sub-5 ms carrier path, emulate vendor hardware, calculate a final optical link budget without module datasheets, or promise that generic IOS syntax is suitable for every platform. Those limits are visible in reports and documentation.
