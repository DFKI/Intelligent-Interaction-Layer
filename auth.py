"""Role-based configuration for the Intelligent Interaction Layer."""
from typing import Optional
import yaml
import os

# ── User loading ──────────────────────────────────────────────────────────────

def _load_users() -> dict[str, dict]:
    config_path = os.path.join(os.path.dirname(__file__), "config", "users.yml")
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return {u["username"]: u for u in data["users"]}

USERS = _load_users()

# ── Role metadata ─────────────────────────────────────────────────────────────

ROLE_META = {
    "manufacturer": {
        "icon": "M",
        "color": "#3B82F6",
        "label": "Manufacturer",
        "focus": "Product carbon footprint, material composition, circularity scoring",
    },
    "designer": {
        "icon": "D",
        "color": "#8B5CF6",
        "label": "Product Designer",
        "focus": "Circularity-by-design, material selection, repairability scoring",
    },
    "recycler": {
        "icon": "R",
        "color": "#22C55E",
        "label": "Recycler",
        "focus": "Material reuse pathways, value recovery, end-of-life analysis",
    },
    "policy_maker": {
        "icon": "P",
        "color": "#F59E0B",
        "label": "Policy Maker",
        "focus": "Circularity benchmarking, standards alignment, policy impact assessment",
    },
    "researcher": {
        "icon": "Re",
        "color": "#06B6D4",
        "label": "Researcher",
        "focus": "Full tool access, LCA methodology, CE data analysis",
    },
    "auditor": {
        "icon": "Au",
        "color": "#EF4444",
        "label": "Auditor",
        "focus": "CE data extraction, circularity assessment, ISO methodology review",
    },
    "logistics_manager": {
        "icon": "L",
        "color": "#F97316",
        "label": "Logistics Manager",
        "focus": "Supply chain emissions, transport optimization, packaging reuse",
    },
    "sustainability_officer": {
        "icon": "S",
        "color": "#10B981",
        "label": "Sustainability Officer",
        "focus": "Sustainability metrics, carbon reporting, circularity & ESG",
    },
    "data_scientist": {
        "icon": "DS",
        "color": "#6366F1",
        "label": "Data Scientist",
        "focus": "CE data extraction, parameter analysis, model validation",
    },
    "orchestrator": {
        "icon": "★",
        "color": "#F8FAFC",
        "label": "Orchestrator",
        "focus": "Full platform access, all CE tools, system oversight",
    },
}

# ── Role-specific system prompt addenda ───────────────────────────────────────

ROLE_SYSTEM_ADDENDA = {
    "manufacturer": (
        "The user is a manufacturer. Prioritize: product carbon footprint calculation, "
        "material composition analysis, circularity indicator scoring, and extracting CE "
        "data from product documentation."
    ),
    "designer": (
        "The user is a product designer. Prioritize: circularity-by-design principles, "
        "material selection for CE compliance, design for disassembly (EN 45552), "
        "repairability scoring, and recyclability optimization."
    ),
    "recycler": (
        "The user is a recycler/waste processor. Prioritize: material reuse potential analysis, "
        "end-of-life pathways, value recovery estimation, and circularity scoring of recovered "
        "material streams."
    ),
    "policy_maker": (
        "The user is a policy maker or regulator. Prioritize: circularity indicator benchmarking "
        "against industry averages, carbon footprint analysis, CE data extraction from reports, "
        "and policy impact assessment. Reference relevant standards (ISO 14040, EN 45552) and use "
        "precise regulatory language."
    ),
    "researcher": (
        "The user is a researcher. Provide full methodological detail, cite standards and literature, "
        "explain calculation methods, and support LCA analysis. All CE tools are available."
    ),
    "auditor": (
        "The user is a CE auditor. Prioritize: CE data extraction from documentation, circularity "
        "indicator assessment, carbon footprint validation, and reviewing data against ISO "
        "methodology (ISO 14040, ISO 14044, EN 45552)."
    ),
    "logistics_manager": (
        "The user manages supply chain and logistics. Prioritize: transport emission calculation, "
        "supply chain CE data extraction, packaging reuse potential, and green logistics optimization."
    ),
    "sustainability_officer": (
        "The user is a sustainability/ESG officer. Provide comprehensive sustainability metrics, "
        "carbon reporting support, circularity scoring, material reuse analysis, and ESG compliance "
        "guidance."
    ),
    "data_scientist": (
        "The user is a data scientist. Prioritize: CE data extraction and structuring, "
        "parameter validation, data quality assessment, and YAML/JSON output formats for "
        "integration with analysis pipelines."
    ),
    "orchestrator": (
        "The user has full platform access (orchestrator/admin). All CE tools and services are "
        "available. Provide comprehensive analysis, system-level insights, and cross-role guidance."
    ),
}

# ── Role-specific suggested questions ─────────────────────────────────────────

ROLE_QUESTIONS = {
    "manufacturer": [
        "Calculate the carbon footprint of a 500g aluminum laptop shell made in China",
        "Calculate the circularity indicator for our EcoPack v3 product line",
        "What recycled content percentage improves a product's circularity grade?",
        "Extract CE data from our product specification document",
        "Analyze material reuse potential for our packaging offcuts",
    ],
    "designer": [
        "What is the circularity indicator for a product with 60% recycled content and 80% recyclability?",
        "How can I improve the repairability score of my electronics design?",
        "Analyze reuse potential for the bio-based PLA plastic in our packaging",
        "Compare the carbon footprint of an aluminum vs. steel housing",
        "Calculate circularity indicator for: recycled_content=50%, recyclability=75%, durability=8",
    ],
    "recycler": [
        "Analyze material reuse potential for post-consumer HDPE plastic in good condition",
        "What is the value recovery potential for mixed e-waste components?",
        "Analyze reuse potential for automotive plastics (PP, ABS) with low contamination",
        "Analyze reuse potential for lithium battery modules with low contamination",
        "Calculate the circularity indicator for a recovered material stream",
    ],
    "policy_maker": [
        "Compute a circularity indicator and explain how each EN 4555x dimension contributes",
        "Calculate a circularity indicator: recycled_content=0.45, recyclability=0.70",
        "What recycled-content levels move a product into a higher circularity grade?",
        "Extract CE data from a sustainability report for policy analysis",
        "Calculate the carbon footprint of a representative product category",
    ],
    "researcher": [
        "Extract CE data from: 'This product contains 40% recycled PET, RoHS compliant, Cradle-to-Cradle certified'",
        "Calculate the carbon footprint of a 2kg steel frame using the cradle-to-gate method",
        "What are all available CE services and their applicable standards?",
        "Analyze material reuse potential for carbon fiber composites in aerospace",
        "Calculate a circularity indicator from recycled content, recyclability, durability, and repairability",
    ],
    "auditor": [
        "Calculate a circularity indicator: recycled_content=0.55, recyclability=0.80, durability=7",
        "Extract CE data from a product datasheet for a compliance review",
        "What standards underpin the circularity indicator calculation?",
        "Calculate the carbon footprint of a product to validate a reported figure",
        "Analyze material reuse potential to support an end-of-life assessment",
    ],
    "logistics_manager": [
        "Calculate transport emissions for a 10kg product shipped from China",
        "What is the carbon footprint difference between road and rail freight?",
        "Analyze reuse potential for wooden pallets and cardboard packaging",
        "Calculate supply chain CO2 for a product with components from 3 regions",
        "Calculate the circularity indicator for reusable transport packaging",
    ],
    "sustainability_officer": [
        "What is the full sustainability profile for our aluminum product line?",
        "Calculate carbon footprint and circularity indicator for our flagship product",
        "Analyze material reuse potential across our packaging portfolio",
        "Extract CE data from our supplier sustainability statements",
        "What CE services are available for ESG reporting support?",
    ],
    "data_scientist": [
        "Extract CE data from: 'Material: 45% recycled aluminum, 30% virgin steel, REACH compliant, ISO 14040 certified'",
        "What CE parameters are tracked by the platform? List all available services.",
        "Extract and structure CE data from a complex material description",
        "Calculate a circularity indicator from a set of extracted parameters",
        "Calculate the carbon footprint for a batch of products from their compositions",
    ],
    "orchestrator": [
        "What are all available CE services and their capabilities?",
        "Calculate carbon footprint and circularity indicator for EcoDevice Pro by TechCorp",
        "Extract CE data from a datasheet, then calculate its circularity indicator",
        "Analyze material reuse potential for a complex multi-material product",
        "Run a full CE analysis: extract data, calculate circularity, and assess reuse",
    ],
}

# Default fallback questions
DEFAULT_QUESTIONS = [
    "What CE services are available on this platform?",
    "Calculate the carbon footprint of a 500g aluminum product made in China",
    "Calculate the circularity indicator for a product with 60% recycled content",
]

def get_role(role_str: str) -> str:
    return role_str if role_str in ROLE_META else "researcher"


def get_role_questions(role: str) -> list[str]:
    return ROLE_QUESTIONS.get(role, DEFAULT_QUESTIONS)


def get_role_system_addendum(role: str) -> str:
    return ROLE_SYSTEM_ADDENDA.get(role, "")


def get_role_meta(role: str) -> dict:
    return ROLE_META.get(role, ROLE_META["researcher"])
