"""
mcp/carbon.py — calculate_carbon_footprint CE tool.

Two entry points:
  * calculate_carbon_footprint(...)            — pure computation from explicit
                                                 inputs (used directly or as a
                                                 building block).
  * calculate_carbon_footprint_for_asset(...)  — dataspace-backed: fetches the
                                                 inputs for an asset from the CE
                                                 Data Space via the Intelligent
                                                 Query agent, then computes.
"""

from .constants import MATERIAL_EMISSION_FACTORS, REGION_TRANSPORT_FACTORS, INDUSTRY_AVERAGE_CO2_PER_KG
from .dataspace import resolve_inputs, QueryAgentClient

# CE data points this service consumes from the dataspace (AAS submodels).
# A production query-agent adapter maps these to AAS SemanticIDs / eCl@ss IRIs.
REQUIRED_DATA_POINTS = ["material_composition", "weight_kg", "manufacturing_region"]
OPTIONAL_DATA_POINTS = ["product_name"]


def calculate_carbon_footprint(
    product_name: str,
    material_composition: dict,
    weight_kg: float,
    manufacturing_region: str,
) -> dict:
    """
    Calculate product carbon footprint from materials, weight, and region.

    material_composition: e.g. {"aluminum": 0.40, "plastic": 0.35, "steel": 0.25}
                          values are fractions (0–1) summing to ~1.0.
    """
    region_key = manufacturing_region.lower().replace(" ", "_").replace("-", "_")
    transport_factor = REGION_TRANSPORT_FACTORS.get(region_key, 1.4)

    # Accept both conventions: fractions (0–1) or percentages (0–100). LLM callers
    # frequently pass percentages ({"aluminum": 100}) despite the schema asking for
    # fractions. If the values clearly sum to a percentage scale, normalize to
    # fractions so the result doesn't silently inflate ~100×.
    comp_total = sum(v for v in material_composition.values() if isinstance(v, (int, float)))
    if comp_total > 1.5:
        material_composition = {
            mat: (v / 100.0 if isinstance(v, (int, float)) else v)
            for mat, v in material_composition.items()
        }

    materials_co2 = 0.0
    for mat, fraction in material_composition.items():
        factor = MATERIAL_EMISSION_FACTORS.get(mat.lower(), 3.0)
        materials_co2 += factor * fraction * weight_kg

    # Manufacturing energy overhead: ~18% of material CO2 on average
    manufacturing_co2 = materials_co2 * 0.18

    # Transport: base 0.25 kgCO2/kg × weight × regional factor
    transport_co2 = 0.25 * weight_kg * transport_factor

    total_co2 = materials_co2 + manufacturing_co2 + transport_co2

    industry_avg = INDUSTRY_AVERAGE_CO2_PER_KG * weight_kg
    delta_pct = ((total_co2 - industry_avg) / industry_avg) * 100

    if delta_pct <= -10:
        comparison = f"{abs(delta_pct):.0f}% below industry average"
    elif delta_pct <= 10:
        comparison = "approximately at industry average"
    elif delta_pct <= 30:
        comparison = f"{delta_pct:.0f}% above industry average"
    else:
        comparison = f"{delta_pct:.0f}% above industry average"

    # Rating A–E based on CO2 per kg of product
    co2_per_kg = total_co2 / weight_kg if weight_kg else 0
    if co2_per_kg < 2.0:
        rating = "A"
    elif co2_per_kg < 3.5:
        rating = "B"
    elif co2_per_kg < 5.5:
        rating = "C"
    elif co2_per_kg < 8.0:
        rating = "D"
    else:
        rating = "E"

    # Reduction potential: switching high-emission materials to recycled alternatives
    # saves ~40% of material CO2
    reduction_potential = materials_co2 * 0.40

    return {
        "product_name": product_name,
        "total_co2_kg": round(total_co2, 3),
        "breakdown": {
            "materials":     round(materials_co2, 3),
            "manufacturing": round(manufacturing_co2, 3),
            "transport":     round(transport_co2, 3),
        },
        "comparison_to_avg":    comparison,
        "carbon_rating":        rating,
        "reduction_potential_kg": round(reduction_potential, 3),
    }


def calculate_carbon_footprint_for_asset(
    asset_id: str,
    requester: str = None,
    client: QueryAgentClient = None,
) -> dict:
    """
    Dataspace-backed carbon footprint.

    Instead of receiving product data inline, this resolves the required CE data
    points for `asset_id` from the CE Data Space via the Intelligent Query agent,
    then runs the same calculation. This is the version compatible with the
    service-oriented dataspace scenario (Fig. 2): the only difference from the
    pure function is *where the inputs come from*.
    """
    data, error = resolve_inputs(
        asset_id, REQUIRED_DATA_POINTS, OPTIONAL_DATA_POINTS,
        requester=requester, client=client,
    )
    if error:
        return error

    result = calculate_carbon_footprint(
        product_name=data.get("product_name", asset_id),
        material_composition=data["material_composition"],
        weight_kg=data["weight_kg"],
        manufacturing_region=data["manufacturing_region"],
    )
    result["asset_id"] = asset_id
    result["data_source"] = "ce_dataspace"
    return result


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate_carbon_footprint",
        "description": (
            "Calculate the carbon footprint (kgCO2e) of a product based on its material "
            "composition, weight, and manufacturing region. Returns a full breakdown by "
            "materials, manufacturing, and transport, plus an A–E carbon rating."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Commercial name or SKU of the product.",
                },
                "material_composition": {
                    "type": "object",
                    "description": (
                        "Dictionary mapping material name to its fraction of total weight (0–1). "
                        "Must sum to approximately 1.0. "
                        'E.g. {"aluminum": 0.4, "plastic": 0.35, "steel": 0.25}.'
                    ),
                    "additionalProperties": {"type": "number"},
                },
                "weight_kg": {
                    "type": "number",
                    "description": "Total product weight in kilograms.",
                },
                "manufacturing_region": {
                    "type": "string",
                    "description": (
                        "Region where product is manufactured. "
                        "Options: China, Europe, USA, India, Japan, Brazil, Southeast_Asia, etc."
                    ),
                },
            },
            "required": [
                "product_name",
                "material_composition",
                "weight_kg",
                "manufacturing_region",
            ],
        },
    },
}


# Dataspace-backed variant: the agent supplies only an asset id; the service
# fetches the required CE data points from the CE Data Space via the query agent.
ASSET_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate_carbon_footprint_for_asset",
        "description": (
            "Calculate the carbon footprint of a product whose data is stored in the "
            "CE dataspace. Provide only the product's asset id; the service retrieves "
            "material composition, weight, and manufacturing region from the product's "
            "AAS submodels via the Intelligent Query agent, then computes the footprint. "
            "Use this when the product already exists in the dataspace."
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
