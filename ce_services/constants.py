"""
mcp/constants.py — Shared constants for the CE services.

Emission factors, transport multipliers, and industry benchmarks used by the
carbon-footprint service.

------------------------------------------------------------------------------
Data sources for the material emission factors (cradle-to-gate GWP-100a)
------------------------------------------------------------------------------
[1] Metals — Nuss, P. & Eckelman, M. J. (2014). "Life Cycle Assessment of
    Metals: A Scientific Synthesis." PLOS ONE, 9(7): e101298.
    https://doi.org/10.1371/journal.pone.0101298
    Values are the supply-mix-weighted primary-production "TOTAL" figures from
    Supporting Information S1, Table S38, column "GWP 100a [kg CO2-eq/kg]"
    (region GLO, 2008 global supply mix). Exceptions noted inline.

[2] Plastics & common materials — Hammond, G. & Jones, C. (2011). "Inventory
    of Carbon & Energy (ICE) Database, v2.0." University of Bath / Circular
    Ecology. https://circularecology.com/embodied-carbon-footprint-database.html
    Cradle-to-gate embodied carbon (kg CO2e/kg). A few entries report only
    kg CO2/kg in ICE v2.0; these are flagged inline.

[3] Steel — World Steel Association (worldsteel), Life Cycle Inventory (LCI).
    https://worldsteel.org/.../life-cycle-inventory-data-and-eco-profiles/
    ~1.9 kg CO2e/kg = global average crude-steel cradle-to-gate (BF-BOF + EAF
    mix). (worldsteel's 2024 expanded-scope intensity incl. CH4/N2O + upstream
    mining is ~2.18; we use the classic scope-comparable LCI figure here.)

[4] PET — NAPCOR / U.S. LCI (2020 revision): virgin bottle-grade PET ≈ 2.23
    kg CO2e/kg. Used instead of ICE's PET entry (5.56), which is an anomalous
    carpet-fibre sub-figure. Consistent with PlasticsEurope eco-profiles
    (~2.2-3.2 kg CO2e/kg).

NOTE: All factors are PRIMARY-production, cradle-to-gate averages. They do NOT
account for a product's actual recycled content (recycled metals/plastics are
typically far lower). They are representative reference values, not a certified
ISO 14067 dataset.
"""

# ---------------------------------------------------------------------------
# Material emission factors (kg CO2e per kg of material, cradle-to-gate GWP-100a)
# Source key in brackets — see module docstring.
# ---------------------------------------------------------------------------
MATERIAL_EMISSION_FACTORS = {
    # --- Metals: Nuss & Eckelman 2014, Table S38 "TOTAL" rows [1] ---
    "aluminum":  8.2,      # [1] Al TOTAL (incl. ~36% scrap in 2008 supply mix)
    "aluminium": 8.2,      # [1] (alt. spelling)
    "steel":     1.9,      # [3] worldsteel global average crude steel
    "copper":    2.8,      # [1] Cu TOTAL
    "nickel":    6.5,      # [1] Ni TOTAL
    "cobalt":    8.3,      # [1] Co TOTAL
    "lithium":   7.1,      # [1] Li TOTAL (Li2CO3-weighted; Li metal alone = 21.1)
    "titanium": 45.1,      # [1] Ti metal (NOT the pigment-weighted TOTAL of 8.1)
    "silver":   196.0,     # [1] Ag TOTAL
    "gold":   12500.0,     # [1] Au TOTAL

    # --- Plastics: ICE v2.0 [2] (PET from [4]) ---
    "plastic":   3.31,     # [2] general plastics average
    "hdpe":      1.93,     # [2] HDPE resin
    "pet":       2.23,     # [4] virgin bottle-grade PET
    "pp":        3.43,     # [2] polypropylene
    "pvc":       3.10,     # [2] PVC general
    "abs":       3.76,     # [2] ABS
    "pc":        7.62,     # [2] polycarbonate
    "nylon":     7.92,     # [2] Nylon 6,6
    "epoxy":     5.70,     # [2] epoxide resin (kg CO2/kg in ICE v2.0)

    # --- Other common materials: ICE v2.0 [2] ---
    "glass":     0.91,     # [2] primary glass
    "paper":     1.49,     # [2] fine paper (kg CO2/kg; excl. biogenic)
    "cardboard": 1.29,     # [2] paperboard (proxy; kg CO2/kg)
    "rubber":    2.85,     # [2] rubber, general
    "wood":      0.31,     # [2] timber, general (fossil; biogenic excluded)
    "textile":   6.78,     # [2] cotton fabric (proxy; kg CO2/kg)
    "ceramic":   0.70,     # [2] ceramic, general
}

# ---------------------------------------------------------------------------
# Transport multiplier by manufacturing region.
# ILLUSTRATIVE relative adjustments (no single LCI source) reflecting typical
# shipping distance/mode to the European market — NOT measured freight factors.
# ---------------------------------------------------------------------------
REGION_TRANSPORT_FACTORS = {
    "china":          1.8,
    "southeast_asia": 1.7,
    "india":          1.65,
    "usa":            1.4,
    "canada":         1.35,
    "mexico":         1.3,
    "europe":         1.2,
    "germany":        1.15,
    "france":         1.15,
    "uk":             1.2,
    "brazil":         1.5,
    "australia":      1.6,
    "japan":          1.45,
    "south_korea":    1.5,
    "local":          1.0,
}

# Industry-average product carbon intensity used as a comparison benchmark.
# ILLUSTRATIVE assumption (order-of-magnitude), not a sourced sector figure.
INDUSTRY_AVERAGE_CO2_PER_KG = 4.5
