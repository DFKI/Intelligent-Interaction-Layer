"""
mcp/extraction.py — extract_ce_data CE tool.
"""

import re


_MATERIAL_KEYWORDS = [
    "aluminum", "aluminium", "steel", "plastic", "glass", "copper", "paper",
    "cardboard", "rubber", "wood", "textile", "ceramic", "lithium", "cobalt",
    "nickel", "titanium", "silver", "gold", "hdpe", "pet", "pp", "pvc",
    "abs", "pc", "nylon", "epoxy", "polypropylene", "polyethylene",
    "polycarbonate", "polyurethane", "silicon", "silicone",
]

_CERT_KEYWORDS = {
    "ISO 14001": r"iso\s*14001",
    "ISO 14040": r"iso\s*14040",
    "ISO 14044": r"iso\s*14044",
    "ISO 9001":  r"iso\s*9001",
    "REACH":     r"\breach\b",
    "RoHS":      r"\brohs\b",
    "CE Mark":   r"\bce\s*mark\b|\bce\s*marking\b",
    "FSC":       r"\bfsc\b",
    "Cradle to Cradle": r"cradle\s*to\s*cradle|c2c",
    "EU Ecolabel": r"eu\s*ecolabel|ecolabel",
    "EPEAT":     r"\bepeat\b",
    "Energy Star": r"energy\s*star",
    "Blauer Engel": r"blauer\s*engel|blue\s*angel",
}

_HAZARDOUS = [
    "lead", "mercury", "cadmium", "chromium vi", "chromium-vi", "hexavalent chromium",
    "pbb", "pbde", "bpa", "asbestos", "arsenic", "beryllium", "antimony",
    "formaldehyde", "pcb",
]

_EOL_KEYWORDS = [
    "recyclable", "recycling", "compostable", "biodegradable", "reusable",
    "refurbishable", "remanufacturing", "take-back", "takeback", "return program",
    "deposit", "landfill", "incineration", "energy recovery", "upcycle",
]


def extract_ce_data(text: str) -> dict:
    """Parse free text and extract circular economy relevant data."""
    lower = text.lower()

    # Materials
    found_materials = [m for m in _MATERIAL_KEYWORDS if m in lower]

    # Recycled content — look for % near "recycl"
    recycled_content = None
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*%\s*(?:post[- ]?consumer|recycled|recycle)", lower
    ):
        recycled_content = float(m.group(1))
        break
    if recycled_content is None:
        for m in re.finditer(
            r"recycled?\s+(?:content\s+)?(?:of\s+)?(\d+(?:\.\d+)?)\s*%", lower
        ):
            recycled_content = float(m.group(1))
            break

    # Recyclability %
    recyclability = None
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*%\s*(?:recyclable|recyclability)", lower
    ):
        recyclability = float(m.group(1))
        break
    if recyclability is None:
        for m in re.finditer(
            r"recyclable?\s+(?:up\s+to\s+)?(\d+(?:\.\d+)?)\s*%", lower
        ):
            recyclability = float(m.group(1))
            break

    # Certifications
    certs = [
        name for name, pattern in _CERT_KEYWORDS.items()
        if re.search(pattern, lower)
    ]

    # Hazardous substances
    hazardous = [h for h in _HAZARDOUS if h in lower]

    # End-of-life options
    eol = [kw for kw in _EOL_KEYWORDS if kw in lower]

    # Confidence: rough heuristic
    found_count = (
        len(found_materials)
        + (1 if recycled_content is not None else 0)
        + (1 if recyclability is not None else 0)
        + len(certs)
        + len(eol)
    )
    confidence = min(1.0, round(found_count / 10.0, 2)) if found_count else 0.1

    # Missing data
    missing = []
    if not found_materials:
        missing.append("material composition")
    if recycled_content is None:
        missing.append("recycled content percentage")
    if recyclability is None:
        missing.append("recyclability percentage")
    if not certs:
        missing.append("certifications")
    if not eol:
        missing.append("end-of-life options")

    # Recommendations
    recs = []
    if recycled_content is None or (recycled_content is not None and recycled_content < 30):
        recs.append(
            "Increase recycled content to at least 30% to meet EU Green Deal targets."
        )
    if recyclability is None or (recyclability is not None and recyclability < 70):
        recs.append("Design for disassembly to improve recyclability above 70%.")
    if not certs:
        recs.append(
            "Pursue ISO 14040 LCA certification to validate environmental claims."
        )
    if hazardous:
        recs.append(
            f"Address restricted substances ({', '.join(hazardous)}) for REACH/RoHS compliance."
        )
    if not eol:
        recs.append(
            "Define and communicate end-of-life pathways (take-back, recycling drop-off)."
        )

    return {
        "extracted_data": {
            "materials":            found_materials,
            "recycled_content_pct": recycled_content,
            "recyclability_pct":    recyclability,
            "certifications":       certs,
            "hazardous_substances": hazardous,
            "end_of_life_options":  eol,
        },
        "confidence":      confidence,
        "missing_data":    missing,
        "recommendations": recs,
    }


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "extract_ce_data",
        "description": (
            "Parse unstructured text (product descriptions, datasheets, sustainability reports) "
            "and extract circular economy relevant data: materials, recycled content, "
            "recyclability, certifications, hazardous substances, and end-of-life options."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Free-form text to analyse for CE data.",
                },
            },
            "required": ["text"],
        },
    },
}
