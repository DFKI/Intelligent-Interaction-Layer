"""
mcp/materials.py — analyze_material_reuse CE tool.
"""

from .constants import MATERIAL_EMISSION_FACTORS
from .dataspace import resolve_inputs, QueryAgentClient

# CE data points this service consumes from the dataspace (a material-stream asset).
REQUIRED_DATA_POINTS = ["material_type", "condition"]
OPTIONAL_DATA_POINTS = ["contamination_level", "quantity_kg"]


_MATERIAL_REUSE_DB = {
    "hdpe": {
        "score": 82, "value": 0.35, "co2_save_pct": 72,
        "pathways": [
            {"pathway": "Mechanical recycling → pellets",     "viability": "High",   "value_recovery_pct": 85},
            {"pathway": "Chemical recycling → monomers",      "viability": "Medium", "value_recovery_pct": 70},
            {"pathway": "Downcycling → construction boards",  "viability": "High",   "value_recovery_pct": 55},
        ],
        "processing": ["Size reduction (shredding)", "Washing & contaminant removal", "Pelletizing"],
    },
    "pet": {
        "score": 88, "value": 0.55, "co2_save_pct": 79,
        "pathways": [
            {"pathway": "Bottle-to-bottle rPET recycling",          "viability": "High",   "value_recovery_pct": 95},
            {"pathway": "Fibre-grade PET for textiles",              "viability": "High",   "value_recovery_pct": 80},
            {"pathway": "Chemical depolymerisation (glycolysis)",    "viability": "Medium", "value_recovery_pct": 75},
        ],
        "processing": ["Colour sorting", "Washing", "Flaking & extrusion"],
    },
    "aluminum": {
        "score": 95, "value": 1.45, "co2_save_pct": 95,
        "pathways": [
            {"pathway": "Secondary aluminium smelting",          "viability": "High",   "value_recovery_pct": 98},
            {"pathway": "Direct remelting for alloy production", "viability": "High",   "value_recovery_pct": 95},
            {"pathway": "Dross processing for alumina recovery", "viability": "Medium", "value_recovery_pct": 60},
        ],
        "processing": ["Sorting by alloy grade", "Delacquering", "Smelting"],
    },
    "aluminium": {
        "score": 95, "value": 1.45, "co2_save_pct": 95,
        "pathways": [
            {"pathway": "Secondary aluminium smelting",          "viability": "High",   "value_recovery_pct": 98},
            {"pathway": "Direct remelting for alloy production", "viability": "High",   "value_recovery_pct": 95},
            {"pathway": "Dross processing for alumina recovery", "viability": "Medium", "value_recovery_pct": 60},
        ],
        "processing": ["Sorting by alloy grade", "Delacquering", "Smelting"],
    },
    "steel": {
        "score": 90, "value": 0.28, "co2_save_pct": 74,
        "pathways": [
            {"pathway": "Electric arc furnace (EAF) steelmaking", "viability": "High",   "value_recovery_pct": 97},
            {"pathway": "Structural reuse (beams, plates)",        "viability": "Medium", "value_recovery_pct": 100},
            {"pathway": "Scrap export to secondary mills",         "viability": "High",   "value_recovery_pct": 90},
        ],
        "processing": ["Magnetic separation", "Shredding (if mixed)", "Baling"],
    },
    "copper": {
        "score": 93, "value": 5.80, "co2_save_pct": 85,
        "pathways": [
            {"pathway": "Hydrometallurgical refining → cathode copper", "viability": "High",   "value_recovery_pct": 99},
            {"pathway": "Alloying into brass/bronze",                    "viability": "High",   "value_recovery_pct": 95},
            {"pathway": "Wire drawing from scrap copper",                "viability": "Medium", "value_recovery_pct": 88},
        ],
        "processing": ["De-insulation / cable stripping", "Smelting", "Electrolytic refining"],
    },
    "glass": {
        "score": 75, "value": 0.08, "co2_save_pct": 30,
        "pathways": [
            {"pathway": "Cullet-to-container glass",        "viability": "High",   "value_recovery_pct": 90},
            {"pathway": "Foam glass insulation boards",      "viability": "Medium", "value_recovery_pct": 65},
            {"pathway": "Glass aggregate for road sub-base", "viability": "High",   "value_recovery_pct": 40},
        ],
        "processing": ["Colour sorting", "Contaminant removal", "Crushing (cullet)"],
    },
    "paper": {
        "score": 70, "value": 0.12, "co2_save_pct": 45,
        "pathways": [
            {"pathway": "Paper mill repulping",               "viability": "High",   "value_recovery_pct": 85},
            {"pathway": "Cellulose insulation production",     "viability": "Medium", "value_recovery_pct": 70},
            {"pathway": "Cardboard / boxboard production",     "viability": "High",   "value_recovery_pct": 80},
        ],
        "processing": ["De-inking", "Pulping", "Screening & cleaning"],
    },
    "e-waste": {
        "score": 65, "value": 8.50, "co2_save_pct": 88,
        "pathways": [
            {"pathway": "Urban mining — precious metal recovery",    "viability": "High",   "value_recovery_pct": 92},
            {"pathway": "Component harvesting (capacitors, ICs)",    "viability": "Medium", "value_recovery_pct": 75},
            {"pathway": "Certified WEEE recycler processing",        "viability": "High",   "value_recovery_pct": 80},
        ],
        "processing": [
            "Depollution (batteries, Hg lamps)",
            "Manual disassembly",
            "Shredding & eddy-current separation",
        ],
    },
}

_CONDITION_PENALTY    = {"excellent": 0, "good": 5, "fair": 15, "poor": 30, "damaged": 50}
_CONTAMINATION_PENALTY = {"none": 0, "low": 3, "medium": 10, "high": 25, "severe": 45}


def analyze_material_reuse(
    material_type: str,
    condition: str,
    contamination_level: str = "low",
    quantity_kg: float = 1.0,
) -> dict:
    """Assess reuse/recycling potential for a given material stream."""
    mat_key = material_type.lower().replace("-", "_").replace(" ", "_")
    db = _MATERIAL_REUSE_DB.get(mat_key, {
        "score": 50, "value": 0.20, "co2_save_pct": 40,
        "pathways": [
            {"pathway": "General material recycling",     "viability": "Medium", "value_recovery_pct": 60},
            {"pathway": "Energy recovery (waste-to-energy)", "viability": "Low", "value_recovery_pct": 20},
        ],
        "processing": ["Sorting", "Size reduction"],
    })

    cond_key = condition.lower()
    cont_key = contamination_level.lower()

    penalty = (
        _CONDITION_PENALTY.get(cond_key, 15)
        + _CONTAMINATION_PENALTY.get(cont_key, 10)
    )
    reuse_score = max(0.0, min(100.0, db["score"] - penalty))

    if reuse_score >= 75:
        reuse_potential = "High"
    elif reuse_score >= 45:
        reuse_potential = "Medium"
    else:
        reuse_potential = "Low"

    value_factor = max(0.3, 1.0 - penalty / 100.0)
    value_per_kg = round(db["value"] * value_factor, 3)

    virgin_co2 = MATERIAL_EMISSION_FACTORS.get(mat_key, 3.5)
    co2_saving = virgin_co2 * (db["co2_save_pct"] / 100.0) * quantity_kg

    return {
        "material_type":        material_type,
        "reuse_potential":      reuse_potential,
        "reuse_score":          round(reuse_score, 1),
        "recommended_pathways": db["pathways"],
        "processing_required":  db["processing"],
        "estimated_value_per_kg": value_per_kg,
        "co2_savings_vs_virgin":  round(co2_saving, 3),
    }


def analyze_material_reuse_for_asset(
    asset_id: str,
    requester: str = None,
    client: QueryAgentClient = None,
) -> dict:
    """
    Dataspace-backed material-reuse analysis: fetch the material-stream data points
    for `asset_id` from the CE Data Space via the Intelligent Query agent, then run
    the same assessment. Only the source of the inputs differs.
    """
    data, error = resolve_inputs(
        asset_id, REQUIRED_DATA_POINTS, OPTIONAL_DATA_POINTS,
        requester=requester, client=client,
    )
    if error:
        return error

    result = analyze_material_reuse(
        material_type=data["material_type"],
        condition=data["condition"],
        contamination_level=data.get("contamination_level", "low"),
        quantity_kg=data.get("quantity_kg", 1.0),
    )
    result["asset_id"] = asset_id
    result["data_source"] = "ce_dataspace"
    return result


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "analyze_material_reuse",
        "description": (
            "Assess the reuse and recycling potential of a specific material stream. "
            "Returns reuse score, recommended pathways with viability and value-recovery "
            "percentages, required processing steps, market value per kg, and CO2 "
            "savings vs. virgin material production."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "material_type": {
                    "type": "string",
                    "description": (
                        "Material to assess. Supported: HDPE, PET, aluminum, steel, "
                        "copper, glass, paper, e-waste."
                    ),
                },
                "condition": {
                    "type": "string",
                    "description": (
                        "Physical condition of the material. "
                        "One of: excellent, good, fair, poor, damaged."
                    ),
                    "enum": ["excellent", "good", "fair", "poor", "damaged"],
                },
                "contamination_level": {
                    "type": "string",
                    "description": (
                        "Level of contamination. "
                        "One of: none, low, medium, high, severe. Default: low."
                    ),
                    "enum": ["none", "low", "medium", "high", "severe"],
                },
                "quantity_kg": {
                    "type": "number",
                    "description": "Mass of material in kilograms (default 1.0).",
                },
            },
            "required": ["material_type", "condition"],
        },
    },
}


# Dataspace-backed variant: the agent supplies only an asset id; the service
# fetches the material-stream data points from its AAS submodels.
ASSET_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "analyze_material_reuse_for_asset",
        "description": (
            "Assess the reuse potential of a recovered material stream stored in the "
            "CE dataspace. Provide only the stream's asset id; the service retrieves "
            "material type, condition, contamination level, and quantity from its AAS "
            "submodels via the Intelligent Query agent, then runs the assessment. Use "
            "this when the material stream already exists in the dataspace."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "string",
                    "description": "Global asset identifier of the material stream in the dataspace (e.g. an AAS globalAssetId URN).",
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
