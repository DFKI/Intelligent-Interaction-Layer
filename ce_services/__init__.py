"""
mcp/__init__.py — CE services modular tool package.

Re-exports ALL_TOOLS_SCHEMA, execute_tool, and all 5 tool functions.
"""

from .carbon import (
    calculate_carbon_footprint,
    calculate_carbon_footprint_for_asset,
    TOOL_SCHEMA as _carbon_schema,
    ASSET_TOOL_SCHEMA as _carbon_asset_schema,
)
from .extraction import extract_ce_data, TOOL_SCHEMA as _extract_schema
from .circularity import (
    calculate_circularity_indicator,
    calculate_circularity_indicator_for_asset,
    TOOL_SCHEMA as _circ_schema,
    ASSET_TOOL_SCHEMA as _circ_asset_schema,
)
from .materials import (
    analyze_material_reuse,
    analyze_material_reuse_for_asset,
    TOOL_SCHEMA as _materials_schema,
    ASSET_TOOL_SCHEMA as _materials_asset_schema,
)
from .registry import get_available_services, TOOL_SCHEMA as _registry_schema

ALL_TOOLS_SCHEMA = [
    _registry_schema,
    _carbon_schema,
    _carbon_asset_schema,
    _extract_schema,
    _circ_schema,
    _circ_asset_schema,
    _materials_schema,
    _materials_asset_schema,
]

_TOOL_MAP = {
    "get_available_services":                   get_available_services,
    "calculate_carbon_footprint":               calculate_carbon_footprint,
    "calculate_carbon_footprint_for_asset":     calculate_carbon_footprint_for_asset,
    "extract_ce_data":                          extract_ce_data,
    "calculate_circularity_indicator":          calculate_circularity_indicator,
    "calculate_circularity_indicator_for_asset": calculate_circularity_indicator_for_asset,
    "analyze_material_reuse":                   analyze_material_reuse,
    "analyze_material_reuse_for_asset":         analyze_material_reuse_for_asset,
}


def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Dispatch a tool call by name with the provided arguments."""
    func = _TOOL_MAP.get(tool_name)
    if not func:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return func(**arguments)
    except Exception as e:
        return {"error": str(e), "tool": tool_name}


__all__ = [
    "ALL_TOOLS_SCHEMA", "execute_tool",
    "get_available_services",
    "calculate_carbon_footprint", "calculate_carbon_footprint_for_asset",
    "extract_ce_data",
    "calculate_circularity_indicator", "calculate_circularity_indicator_for_asset",
    "analyze_material_reuse", "analyze_material_reuse_for_asset",
]
