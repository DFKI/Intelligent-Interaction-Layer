"""
ce_services/dataspace.py — connection point between CE services and the
Intelligent Query agent of the service-oriented CE dataspace.

In the architecture (see the paper / docs/methodology.md and Fig. 2), product
data is NOT passed inline to a service. It lives as AAS submodels in the CE Data
Space, and a service obtains the data points it needs by asking the **Intelligent
Query agent**, which:
  - resolves which data asset / AAS submodel holds each requested data point
    (via the semantic data catalog + Semantic Expander + Query Planner),
  - enforces access control through the trust layer (Solid WAC / IDS policies),
  - retrieves the values over the dataspace and returns them.

The real query agent is implemented elsewhere. A CE service therefore depends
ONLY on the `QueryAgentClient` interface below — wire it to the real agent in
production, or to `StubQueryAgentClient` for standalone runs and tests. This is
the single integration seam: "connect the service to the query agent."

Data-point names: the names each service requests (e.g. "material_composition",
"recycled_content_pct") are DEMONSTRATOR-LEVEL LOGICAL NAMES, not canonical ids.
The query agent maps them to the authoritative CE data points and their AAS
submodel / SemanticID (eCl@ss). The production-level, AAS-mapped catalog is DFKI's
"Datapoints for Circular Economy"
(https://github.com/DFKI/Datapoints-for-Circular-Economy); adopting the official
identifiers is a query-agent/adapter concern and needs no change to the services.

NOTE: the CE services in this repo are illustrative examples of tools that can be
exposed and orchestrated this way — not an exhaustive or fixed set.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class QueryAgentError(Exception):
    """Raised when the query agent cannot resolve or return requested data points
    (unknown asset, access denied, transport failure, etc.)."""


@runtime_checkable
class QueryAgentClient(Protocol):
    """Interface a CE service uses to pull CE data points from the dataspace.

    Implemented by the Intelligent Query agent (Semantic Expander + Query Planner
    + SPARQL/Cypher/REST adapters over the Solid/IDS trust layer). A service does
    not know where data lives or how access is enforced — it only names the data
    points it needs for an asset.
    """

    def fetch_data_points(
        self,
        asset_id: str,
        data_points: list[str],
        requester: str | None = None,
    ) -> dict[str, Any]:
        """Resolve and retrieve the named CE data points for `asset_id`.

        Parameters
        ----------
        asset_id : str
            Global asset / product identifier (e.g., an AAS globalAssetId URN).
        data_points : list[str]
            Logical CE data-point identifiers (e.g., "material_composition").
            A production adapter maps these to AAS SemanticIDs / eCl@ss IRIs.
        requester : str | None
            Identity of the caller (e.g., WebID) used by the trust layer for
            access control. None for anonymous / public-only access.

        Returns
        -------
        dict
            {data_point_id: value} for the points that exist AND are accessible.
            Points that are missing or access-denied are simply omitted; the
            calling service decides whether the result is sufficient.
        """
        ...


# ---------------------------------------------------------------------------
# Local stub — stands in for the real Intelligent Query agent for standalone
# runs and tests. Holds a tiny in-memory "AAS store" keyed by asset id.
# A production deployment replaces this via set_query_client(...).
# ---------------------------------------------------------------------------

_SAMPLE_AAS_STORE: dict[str, dict[str, Any]] = {
    "urn:product:LAPTOP-X1": {
        "product_name": "Laptop X1",
        "material_composition": {"aluminum": 0.40, "plastic": 0.35, "steel": 0.25},
        "weight_kg": 2.0,
        "manufacturing_region": "China",
        # circularity-related data points also live in the AAS:
        "recycled_content_pct": 25.0,
        "recyclability_pct": 70.0,
        "durability_score": 7.0,
        "repairability_score": 6.0,
    },
    "urn:product:ECOCHAIR-001": {
        "product_name": "EcoChair Pro",
        "material_composition": {"steel": 0.60, "wood": 0.30, "rubber": 0.10},
        "weight_kg": 8.0,
        "manufacturing_region": "Europe",
        "recycled_content_pct": 35.0,
        "recyclability_pct": 80.0,
        "durability_score": 8.5,
        "repairability_score": 7.0,
    },
    # Recovered material-stream assets (for material-reuse analysis).
    "urn:material:ALU-SCRAP-LOT-7": {
        "material_type": "aluminum",
        "condition": "good",
        "contamination_level": "low",
        "quantity_kg": 1200.0,
    },
    "urn:material:HDPE-BALE-22": {
        "material_type": "hdpe",
        "condition": "fair",
        "contamination_level": "medium",
        "quantity_kg": 800.0,
    },
}


class StubQueryAgentClient:
    """In-memory stand-in for the Intelligent Query agent.

    NOT a real dataspace client — it simply reads from a local dict so the repo
    runs end-to-end without the deployed query agent. It mimics the contract:
    unknown asset -> QueryAgentError; missing data points -> omitted from result.
    """

    def __init__(self, store: dict[str, dict[str, Any]] | None = None) -> None:
        self._store = store if store is not None else _SAMPLE_AAS_STORE

    def fetch_data_points(
        self,
        asset_id: str,
        data_points: list[str],
        requester: str | None = None,
    ) -> dict[str, Any]:
        asset = self._store.get(asset_id)
        if asset is None:
            raise QueryAgentError(f"Unknown asset in dataspace: {asset_id!r}")
        return {dp: asset[dp] for dp in data_points if dp in asset}


# ---------------------------------------------------------------------------
# Client wiring. Production injects the real agent via set_query_client();
# otherwise services fall back to the stub so the repo works standalone.
# ---------------------------------------------------------------------------

_client: QueryAgentClient | None = None


def set_query_client(client: QueryAgentClient) -> None:
    """Inject the query-agent client all CE services should use (call this once
    at startup with the real Intelligent Query agent)."""
    global _client
    _client = client


def get_query_client() -> QueryAgentClient:
    """Return the configured query-agent client, defaulting to the local stub."""
    global _client
    if _client is None:
        _client = StubQueryAgentClient()
    return _client


def resolve_inputs(
    asset_id: str,
    required: list[str],
    optional: list[str] = (),
    requester: str | None = None,
    client: QueryAgentClient | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Fetch `required`+`optional` data points for `asset_id` via the query agent.

    Shared helper for every dataspace-backed service. Returns `(data, error)`:
      - on success: (data_dict, None)
      - on failure: (None, error_dict) — a ready-to-return error if the asset is
        unknown or any required data point is missing/inaccessible.
    """
    client = client or get_query_client()
    try:
        data = client.fetch_data_points(
            asset_id, list(required) + list(optional), requester=requester
        )
    except QueryAgentError as e:
        return None, {"error": str(e), "asset_id": asset_id}

    missing = [dp for dp in required if dp not in data]
    if missing:
        return None, {
            "error": f"Required CE data points not available in the dataspace: {missing}",
            "asset_id": asset_id,
            "available": list(data.keys()),
        }
    return data, None
