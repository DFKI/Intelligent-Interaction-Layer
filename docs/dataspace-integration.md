# Connecting CE Services to the Dataspace (Intelligent Query Agent)

This explains how a CE service obtains its inputs from the **CE Data Space**
instead of receiving them inline — i.e., how the services in this repo plug into
the architecture of Fig. 2 (Intelligent Interaction Layer → Intelligent Query
agent → CE Data Space / AAS submodels).

> **These CE services are illustrative examples.** The five services here (carbon
> footprint, circularity, data extraction, material reuse, registry) are *example*
> tools that demonstrate the pattern — things you can use as-is, adapt, or build on.
> The architecture is service-oriented and pluggable, so any number of additional CE
> services can be exposed the same way and orchestrated by the agent. The point of
> the system is the **agentic orchestration of tools over MCP**, not this particular
> set of services.

## The two access modes

Each quantitative service has a pure computation core and (optionally) a
dataspace-backed wrapper:

| Mode | Function | Where inputs come from |
|------|----------|------------------------|
| Inline | `calculate_carbon_footprint(material_composition, weight_kg, region, ...)` | Caller passes all data |
| Dataspace | `calculate_carbon_footprint_for_asset(asset_id, requester=None)` | Fetched from the asset's AAS submodels via the query agent |

The computation is identical; only the **source of the inputs** changes. This is
the "only needed change": connect the service to the query agent.

## The integration seam

A service depends only on the `QueryAgentClient` interface
([`ce_services/dataspace.py`](../ce_services/dataspace.py)):

```python
class QueryAgentClient(Protocol):
    def fetch_data_points(self, asset_id: str, data_points: list[str],
                          requester: str | None = None) -> dict: ...
```

The real **Intelligent Query agent** (Semantic Expander + Query Planner +
SPARQL/Cypher/REST adapters over the Solid/IDS trust layer) is implemented
elsewhere; it implements this interface. The agent resolves *where* each data
point lives, enforces access control, and returns the values. The service neither
knows nor cares about storage location or access policy.

Each service declares the data points it needs, e.g. for carbon:

```python
REQUIRED_DATA_POINTS = ["material_composition", "weight_kg", "manufacturing_region"]
```

### Data-point names are logical, not canonical

The names above (`material_composition`, `recycled_content_pct`, …) are
**demonstrator-level logical names**, chosen to match each service's inputs. They
are deliberately *not* canonical identifiers — **the query agent is the mapping
layer** that resolves each logical name to the authoritative Circular Economy data
point and its AAS submodel / SemanticID (eCl@ss).

The production-level, AAS-mapped catalog of CE data points is maintained by DFKI in
[Datapoints-for-Circular-Economy](https://github.com/DFKI/Datapoints-for-Circular-Economy).
A real deployment maps the logical names used here to entries in that catalog, so
adopting the official identifiers is a **query-agent / adapter concern and requires
no change to the services themselves**.

## Wiring the real agent

At startup, inject the deployed agent once:

```python
from ce_services.dataspace import set_query_client
set_query_client(MyIntelligentQueryAgentClient(...))   # implements fetch_data_points
```

If nothing is injected, services fall back to `StubQueryAgentClient`, an
in-memory store of sample assets (e.g. `urn:product:LAPTOP-X1`) so the repo runs
end-to-end without the deployed dataspace. The stub is **not** a real dataspace
client — it only mimics the contract for local runs and tests.

## End-to-end call

The chatbot/LLM invokes the dataspace-backed tool with only an asset id:

```python
execute_tool("calculate_carbon_footprint_for_asset", {"asset_id": "urn:product:LAPTOP-X1"})
# -> {... "total_co2_kg": 12.496, "carbon_rating": "D", "asset_id": ...,
#     "data_source": "ce_dataspace"}
```

## Services with a dataspace-backed variant

The same refactor is applied to all three quantitative services. Each keeps its
pure compute function and adds a `<service>_for_asset(asset_id, requester=None)`
tool that fetches its `REQUIRED_DATA_POINTS` via the query agent (using the shared
`resolve_inputs()` helper) and forwards them to the pure function:

| Service | Dataspace tool | Data points fetched | Example asset |
|---------|----------------|---------------------|---------------|
| Carbon footprint | `calculate_carbon_footprint_for_asset` | material_composition, weight_kg, manufacturing_region | `urn:product:LAPTOP-X1` |
| Circularity indicator | `calculate_circularity_indicator_for_asset` | recycled_content_pct, recyclability_pct, durability_score, repairability_score | `urn:product:ECOCHAIR-001` |
| Material reuse | `analyze_material_reuse_for_asset` | material_type, condition, contamination_level, quantity_kg | `urn:material:ALU-SCRAP-LOT-7` |

So the MCP server advertises **8 tools** for **5 services**: the three above each
expose an inline tool *and* a dataspace tool; extraction and the registry are
unchanged. A single dataspace asset (e.g. `urn:product:ECOCHAIR-001`) can feed
several services, letting the agent compose a multi-service answer from one id.

### To add the variant to a new service

1. keep the pure compute function;
2. declare `REQUIRED_DATA_POINTS` (and any `OPTIONAL_DATA_POINTS`);
3. add `<service>_for_asset(...)` using `resolve_inputs(asset_id, REQUIRED, OPTIONAL, ...)`;
4. register the new tool in `__init__.py` and `fastmcp_server.py`.
