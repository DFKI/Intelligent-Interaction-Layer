"""CE services FastMCP Server — 5 CE services over SSE on port 8002.
Carbon, circularity and material-reuse each offer an inline tool plus a
dataspace-backed (_for_asset) tool, so 8 tools total."""
from __future__ import annotations
import sys
from typing import Optional
from fastmcp import FastMCP
from . import execute_tool

mcp = FastMCP("CE Services", version="1.0.0")


@mcp.tool()
def get_available_services() -> dict:
    """Return all available CE services with descriptions, standards, and capabilities."""
    return execute_tool("get_available_services", {})


@mcp.tool()
def calculate_carbon_footprint(
    product_name: str,
    material_composition: dict,
    weight_kg: float,
    manufacturing_region: str,
) -> dict:
    """Calculate carbon footprint (kgCO2e) from material composition, weight, and manufacturing region."""
    return execute_tool("calculate_carbon_footprint", {
        "product_name": product_name,
        "material_composition": material_composition,
        "weight_kg": weight_kg,
        "manufacturing_region": manufacturing_region,
    })


@mcp.tool()
def calculate_carbon_footprint_for_asset(asset_id: str, requester: str = None) -> dict:
    """Carbon footprint for a product stored in the CE dataspace: fetches its data
    points from the product's AAS submodels via the Intelligent Query agent, then computes."""
    return execute_tool("calculate_carbon_footprint_for_asset", {
        "asset_id": asset_id,
        "requester": requester,
    })


@mcp.tool()
def extract_ce_data(text: str) -> dict:
    """Extract circular economy data from unstructured text, product descriptions, or datasheets."""
    return execute_tool("extract_ce_data", {"text": text})


@mcp.tool()
def calculate_circularity_indicator(
    recycled_content_pct: float,
    recyclability_pct: float,
    durability_score: float,
    repairability_score: float = 5.0,
    product_id: str = "unknown",
) -> dict:
    """Compute circularity index (0–1) and A–E grade using weighted formula."""
    return execute_tool("calculate_circularity_indicator", {
        "recycled_content_pct": recycled_content_pct,
        "recyclability_pct": recyclability_pct,
        "durability_score": durability_score,
        "repairability_score": repairability_score,
        "product_id": product_id,
    })


@mcp.tool()
def calculate_circularity_indicator_for_asset(asset_id: str, requester: str = None) -> dict:
    """Circularity indicator for a product stored in the CE dataspace: fetches its EN 4555x
    data points from the product's AAS submodels via the Intelligent Query agent, then computes."""
    return execute_tool("calculate_circularity_indicator_for_asset", {
        "asset_id": asset_id,
        "requester": requester,
    })


@mcp.tool()
def analyze_material_reuse(
    material_type: str,
    condition: str,
    contamination_level: str,
    quantity_kg: float,
) -> dict:
    """Assess reuse and recycling potential of a specific material stream."""
    return execute_tool("analyze_material_reuse", {
        "material_type": material_type,
        "condition": condition,
        "contamination_level": contamination_level,
        "quantity_kg": quantity_kg,
    })


@mcp.tool()
def analyze_material_reuse_for_asset(asset_id: str, requester: str = None) -> dict:
    """Material-reuse analysis for a recovered material stream stored in the CE dataspace:
    fetches its data points from the stream's AAS submodels via the Intelligent Query agent."""
    return execute_tool("analyze_material_reuse_for_asset", {
        "asset_id": asset_id,
        "requester": requester,
    })


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8002
    mcp.run(transport="sse", host="0.0.0.0", port=port)
