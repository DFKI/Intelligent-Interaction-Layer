"""
mcp/circularity.py — calculate_circularity_indicator CE tool.

------------------------------------------------------------------------------
Methodology & references
------------------------------------------------------------------------------
This service reports a single composite "circularity index" (0–1) computed as a
weighted sum of four product-level dimensions. The CHOICE OF DIMENSIONS and the
way each is assessed map directly to the CEN-CENELEC material-efficiency
standards developed for the EU Ecodesign framework (CEN-CLC/JTC 10):

  - durability        → EN 45552:2020  "General method for the assessment of
                        the durability of energy-related products"
  - repairability     → EN 45554:2020  "General methods for the assessment of
                        the ability to repair, reuse and upgrade ..."
  - recyclability     → EN 45555:2019  "General methods for assessing the
                        recyclability and recoverability ..."
  - recycled content  → EN 45557:2020  "General method for assessing the
                        proportion of recycled material content ..."
  (terminology: CLC/TR 45550:2020 "Definitions for material efficiency".)

IMPORTANT — what is NOT from a standard:
  * The aggregation WEIGHTS (CI_WEIGHTS below: 0.30/0.35/0.20/0.15) are an
    author-defined choice. No EN 4555x standard prescribes how to combine the
    dimensions into one index, nor any weighting. They are exposed as a
    configurable constant and should be treated as a transparent assumption.
  * The GRADE_THRESHOLDS (A–E bands) are illustrative.
  * REFERENCE_INDEX (0.42) is an ILLUSTRATIVE reference value, NOT a measured
    figure. There is no official 0–1 product-level "EU average circularity
    index." The closest official EU metric is the Circular Material Use Rate
    (Eurostat, cei_srm030) = 11.5% in 2022 — but that is an economy-wide
    material-flow share, not comparable to this product composite, so it is
    used only as context, not as the benchmark value.

This composite is DISTINCT from the Ellen MacArthur Foundation's Material
Circularity Indicator (MCI), which is defined as a Linear Flow Index modified by
a utility factor — a different formula, not a weighted sum of these dimensions.
"""

from .dataspace import resolve_inputs, QueryAgentClient

# CE data points this service consumes from the dataspace (AAS submodels).
REQUIRED_DATA_POINTS = ["recycled_content_pct", "recyclability_pct", "durability_score"]
OPTIONAL_DATA_POINTS = ["repairability_score"]

# Weighted-sum coefficients for the composite index (author-defined; must sum to 1.0).
CI_WEIGHTS = {
    "recycled_content": 0.30,   # assessed per EN 45557
    "recyclability":    0.35,   # assessed per EN 45555
    "durability":       0.20,   # assessed per EN 45552
    "repairability":    0.15,   # assessed per EN 45554
}

# A–E grade boundaries on the 0–1 index (illustrative).
GRADE_THRESHOLDS = [(0.80, "A"), (0.65, "B"), (0.50, "C"), (0.35, "D")]

# Illustrative reference index for the comparison string (NOT an official figure;
# see module docstring). Closest official EU metric: Circular Material Use Rate
# = 11.5% (2022), an economy-wide share, not directly comparable.
REFERENCE_INDEX = 0.42


def calculate_circularity_indicator(
    recycled_content_pct: float,
    recyclability_pct: float,
    durability_score: float,
    repairability_score: float = 5.0,
    product_id: str = "unknown",
) -> dict:
    """
    Compute a composite circularity index (0–1) as a weighted sum of four
    EN 4555x dimensions (see module docstring for sources and caveats).

    recycled_content_pct : 0–100
    recyclability_pct    : 0–100
    durability_score     : 0–10
    repairability_score  : 0–10
    """
    # Accept both conventions for the percentage inputs: 0–100 (as documented) or
    # 0–1 fractions. LLM callers sometimes pass a fraction ({"recyclability_pct":
    # 0.8}) despite the schema asking for 0–100, which would otherwise be read as
    # 0.8% and deflate the index ~100×. A value in (0, 1] is treated as a fraction.
    def _as_pct(v):
        return v * 100.0 if isinstance(v, (int, float)) and 0.0 < v <= 1.0 else v

    recycled_content_pct = _as_pct(recycled_content_pct)
    recyclability_pct    = _as_pct(recyclability_pct)

    # Same idea for the 0–10 scores: a value > 10 was almost certainly given on a
    # 0–100 scale ({"durability_score": 80} meaning 8/10), so rescale it. Values
    # in 0–10 (including sub-1 like 0.8) are left as-is — those are valid scores.
    def _as_score(v):
        return v / 10.0 if isinstance(v, (int, float)) and v > 10.0 else v

    durability_score    = _as_score(durability_score)
    repairability_score = _as_score(repairability_score)

    rc  = max(0.0, min(recycled_content_pct, 100.0)) / 100.0
    ra  = max(0.0, min(recyclability_pct,    100.0)) / 100.0
    dur = max(0.0, min(durability_score,      10.0)) / 10.0
    rep = max(0.0, min(repairability_score,   10.0)) / 10.0

    # Weighted composite index
    ci = (
        CI_WEIGHTS["recycled_content"] * rc
        + CI_WEIGHTS["recyclability"]  * ra
        + CI_WEIGHTS["durability"]     * dur
        + CI_WEIGHTS["repairability"]  * rep
    )

    # Grade
    grade = "E"
    for threshold, letter in GRADE_THRESHOLDS:
        if ci >= threshold:
            grade = letter
            break

    # Comparison against the illustrative reference index (see caveat in docstring)
    diff_pct = ((ci - REFERENCE_INDEX) / REFERENCE_INDEX) * 100
    if diff_pct >= 10:
        bench_str = f"{diff_pct:.0f}% above the illustrative reference index ({REFERENCE_INDEX})"
    elif diff_pct <= -10:
        bench_str = f"{abs(diff_pct):.0f}% below the illustrative reference index ({REFERENCE_INDEX})"
    else:
        bench_str = f"at the illustrative reference index ({REFERENCE_INDEX})"

    improvement_potential = round(1.0 - ci, 3)

    recs = []
    if rc < 0.30:
        recs.append(
            f"Increase recycled content from {recycled_content_pct:.0f}% to at least 30%."
        )
    if ra < 0.70:
        recs.append("Design for disassembly to push recyclability above 70%.")
    if dur < 0.60:
        recs.append(
            "Extend product lifetime through more durable components or modular design."
        )
    if rep < 0.60:
        recs.append(
            "Improve repairability: publish repair manuals and ensure spare-part availability."
        )
    if not recs:
        recs.append(
            "Maintain current circularity standards and pursue A-grade certification."
        )

    return {
        "product_id":        product_id,
        "circularity_index": round(ci, 4),
        "grade":             grade,
        "component_scores":  {
            "material_circularity": round(rc,  4),
            "recyclability":        round(ra,  4),
            "durability":           round(dur, 4),
            "repairability":        round(rep, 4),
        },
        "benchmark_comparison":  bench_str,
        "improvement_potential": improvement_potential,
        "recommendations":       recs,
    }


def calculate_circularity_indicator_for_asset(
    asset_id: str,
    requester: str = None,
    client: QueryAgentClient = None,
) -> dict:
    """
    Dataspace-backed circularity indicator: fetch the EN 4555x data points for
    `asset_id` from the CE Data Space via the Intelligent Query agent, then run
    the same composite calculation. Only the source of the inputs differs.
    """
    data, error = resolve_inputs(
        asset_id, REQUIRED_DATA_POINTS, OPTIONAL_DATA_POINTS,
        requester=requester, client=client,
    )
    if error:
        return error

    result = calculate_circularity_indicator(
        recycled_content_pct=data["recycled_content_pct"],
        recyclability_pct=data["recyclability_pct"],
        durability_score=data["durability_score"],
        repairability_score=data.get("repairability_score", 5.0),
        product_id=asset_id,
    )
    result["asset_id"] = asset_id
    result["data_source"] = "ce_dataspace"
    return result


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate_circularity_indicator",
        "description": (
            "Compute a composite circularity index (0–1) and A–E grade for a product "
            "as a weighted sum of four EN 4555x dimensions: 30% recycled content "
            "(EN 45557) + 35% recyclability (EN 45555) + 20% durability (EN 45552) "
            "+ 15% repairability (EN 45554). The weights are an author-defined, "
            "configurable choice; the result is compared to an illustrative reference "
            "index (not an official EU figure)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Optional product identifier (SKU, EAN, or internal ID). Defaults to 'unknown'.",
                },
                "recycled_content_pct": {
                    "type": "number",
                    "description": "Percentage of recycled input materials (0–100).",
                },
                "recyclability_pct": {
                    "type": "number",
                    "description": "Percentage of product that can be recycled at end of life (0–100).",
                },
                "durability_score": {
                    "type": "number",
                    "description": "Durability score on a 0–10 scale.",
                },
                "repairability_score": {
                    "type": "number",
                    "description": "Repairability score on a 0–10 scale (default 5.0).",
                },
            },
            "required": [
                "recycled_content_pct",
                "recyclability_pct",
                "durability_score",
            ],
        },
    },
}


# Dataspace-backed variant: the agent supplies only an asset id; the service
# fetches the EN 4555x data points from the product's AAS submodels.
ASSET_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate_circularity_indicator_for_asset",
        "description": (
            "Compute the circularity indicator of a product whose data is stored in the "
            "CE dataspace. Provide only the product's asset id; the service retrieves "
            "recycled content, recyclability, durability, and repairability from the "
            "product's AAS submodels via the Intelligent Query agent, then computes the "
            "composite index. Use this when the product already exists in the dataspace."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "string",
                    "description": "Global asset/product identifier in the dataspace (e.g. an AAS globalAssetId URN).",
                },
                "requester": {
                    "type": "string",
                    "description": "Optional identity (e.g. WebID) of the caller, used by the trust layer for access control.",
                },
            },
            "required": ["asset_id"],
        },
    },
}
