"""
mcp/registry.py — get_available_services CE tool (NEW).

Returns a structured directory of all available CE services and tools.
"""


def get_available_services() -> dict:
    """Return a structured dict of all available CE services."""
    return {
        "service_count": 5,
        "services": [
            {
                "id": "get_available_services",
                "name": "Service Registry",
                "description": (
                    "Returns the list of all available CE (Circular Economy) services and "
                    "tools with their descriptions, inputs, outputs, and applicable standards."
                ),
                "category": "Data Management",
                "inputs": [],
                "output_type": "service_directory",
                "standards": [],
                "status": "available",
            },
            {
                "id": "calculate_carbon_footprint",
                "name": "Product Carbon Footprint",
                "description": (
                    "Calculate the carbon footprint (kgCO2e) of a product based on its "
                    "material composition, weight, and manufacturing region. Returns a full "
                    "breakdown by materials, manufacturing, and transport, plus an A–E rating."
                ),
                "category": "Environmental Impact",
                "inputs": ["product_name", "material_composition", "weight_kg", "manufacturing_region"],
                "output_type": "carbon_assessment",
                "standards": ["ISO 14067", "IDTA 02023"],
                "status": "available",
            },
            {
                "id": "extract_ce_data",
                "name": "CE Data Extraction",
                "description": (
                    "Parse unstructured text (product descriptions, datasheets, sustainability "
                    "reports) and extract circular economy relevant data: materials, recycled "
                    "content, recyclability, certifications, hazardous substances, and "
                    "end-of-life options."
                ),
                "category": "Data Management",
                "inputs": ["text"],
                "output_type": "extracted_ce_data",
                "standards": ["ISO 14040", "REACH", "RoHS"],
                "status": "available",
            },
            {
                "id": "calculate_circularity_indicator",
                "name": "Circularity Indicator",
                "description": (
                    "Compute a composite circularity index (0–1) and A–E grade as a weighted "
                    "sum of four EN 4555x dimensions: 30% recycled content (EN 45557) + 35% "
                    "recyclability (EN 45555) + 20% durability (EN 45552) + 15% repairability "
                    "(EN 45554). Weights are an author-defined, configurable choice; compared "
                    "to an illustrative reference index (not an official EU figure)."
                ),
                "category": "Circularity",
                "inputs": ["product_id", "recycled_content_pct", "recyclability_pct", "durability_score", "repairability_score"],
                "output_type": "circularity_score",
                "standards": ["EN 45552", "EN 45554", "EN 45555", "EN 45557"],
                "status": "available",
            },
            {
                "id": "analyze_material_reuse",
                "name": "Material Reuse Potential",
                "description": (
                    "Assess the reuse and recycling potential of a specific material stream. "
                    "Returns reuse score, recommended pathways with viability and "
                    "value-recovery percentages, required processing steps, market value "
                    "per kg, and CO2 savings vs. virgin material production."
                ),
                "category": "Material Analysis",
                "inputs": ["material_type", "condition", "contamination_level", "quantity_kg"],
                "output_type": "reuse_assessment",
                "standards": ["EU WEEE Directive", "ISO 14040"],
                "status": "available",
            },
        ],
        "categories": [
            "Environmental Impact",
            "Data Management",
            "Circularity",
            "Material Analysis",
        ],
        "mcp_version": "1.0",
        "agent_name": "Intelligent Interaction Layer",
    }


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_available_services",
        "description": (
            "Returns the list of all available CE (Circular Economy) services and tools "
            "with their descriptions, inputs, outputs, and applicable standards."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}
