# Methodology & Limitations

This document describes how the CE services compute their results, which
values are drawn from published sources, and — just as importantly — which are
**illustrative assumptions**. It is intended to make the system reproducible and
to support an honest description in any paper or report that uses it.

> **One-line summary:** the quantitative services use *published, cited emission
> factors and standards-based dimensions*, combined with *deliberately simple,
> configurable model coefficients*. The system is a transparent demonstrator, **not
> a certified ISO 14067 / ISO 14040 LCA tool**.

---

## 1. Product Carbon Footprint (`calculate_carbon_footprint`)

### Structure

The footprint follows the standard cradle-to-gate product-carbon-footprint stage
decomposition (cf. ISO 14067, ISO 14040/44, GHG Protocol Product Standard):

```
materials_CO2 = Σ (emission_factor[material] × mass_fraction × weight_kg)
manufacturing = materials_CO2 × 0.18
transport     = 0.25 × weight_kg × region_factor
total         = materials_CO2 + manufacturing + transport
```

`mass_fraction` is expected on a 0–1 scale, but the composition may be supplied
as percentages instead (values summing to ~100); the service detects this and
normalizes to fractions, so a caller can use either convention. The circularity
service applies the same tolerance to its percentage and 0–10 score inputs.

### Emission factors — published & cited

Per-material cradle-to-gate GWP-100a factors (kg CO₂e/kg) are defined, with a
source tag on every entry, in [`ce_services/constants.py`](../ce_services/constants.py):

| Group | Source |
|-------|--------|
| Metals (Al, Fe→steel, Cu, Ni, Co, Li, Ti, Ag, Au) | Nuss & Eckelman (2014), *PLOS ONE* — Table S38, GWP-100a, supply-mix-weighted primary production, GLO |
| Plastics & common materials (glass, paper, board, rubber, timber, textile, ceramic, HDPE/PP/PVC/ABS/PC/nylon/epoxy) | ICE database v2.0 (Hammond & Jones, Univ. of Bath) |
| Steel | worldsteel LCI — global average crude steel ≈ 1.9 kg CO₂e/kg |
| PET | NAPCOR / U.S. LCI (2020) ≈ 2.23 kg CO₂e/kg |

Two deliberate source choices are documented in the code: **titanium** uses the
titanium-*metal* figure (45.1) rather than the pigment-weighted supply-mix total
(8.1), because the tool models metal parts; and **PET** uses NAPCOR/PlasticsEurope
rather than ICE's anomalous carpet-fibre entry (5.56).

### Illustrative coefficients — *not* from a source

The following are reasonable order-of-magnitude assumptions for demonstration and
are exposed for tuning. They should **not** be cited as measured values:

| Coefficient | Value | Status |
|-------------|-------|--------|
| Manufacturing energy overhead | 18% of material CO₂ | assumption |
| Base transport intensity | 0.25 kg CO₂/kg | assumption |
| Regional transport multipliers | 1.0–1.8 | relative, illustrative |
| Industry-average benchmark | 4.5 kg CO₂e/kg | assumption |
| A–E rating thresholds | 2.0 / 3.5 / 5.5 / 8.0 kg CO₂e/kg | illustrative bands |
| Recycled-material saving | 40% of material CO₂ | assumption |

Factors are **primary-production averages** and do **not** adjust for a product's
actual recycled content (recycled metals/plastics are typically far lower).

---

## 2. Circularity Indicator (`calculate_circularity_indicator`)

### Structure

A composite index on 0–1, a weighted sum of four normalised dimensions:

```
CI = 0.30·recycled_content + 0.35·recyclability + 0.20·durability + 0.15·repairability
```

### Dimensions — grounded in standards

The choice and assessment of each dimension map to the CEN-CENELEC
material-efficiency standards (CEN-CLC/JTC 10) for the EU Ecodesign framework:

| Dimension | Standard |
|-----------|----------|
| Recycled content | EN 45557:2020 |
| Recyclability / recoverability | EN 45555:2019 |
| Durability | EN 45552:2020 |
| Repairability (repair/reuse/upgrade) | EN 45554:2020 |
| Terminology | CLC/TR 45550:2020 |

### Assumptions — *not* standardised

No EN 4555x standard prescribes how to aggregate the dimensions into one index.
The following are author-defined and configurable (see `CI_WEIGHTS`,
`GRADE_THRESHOLDS`, `REFERENCE_INDEX` in
[`ce_services/circularity.py`](../ce_services/circularity.py)):

- the **weights** (0.30 / 0.35 / 0.20 / 0.15);
- the **A–E grade thresholds**;
- the **reference index (0.42)** used for the comparison string. This is an
  *illustrative* value, **not** an official figure. There is no published 0–1
  product-level "EU average circularity index." The closest official EU metric is
  the **Circular Material Use Rate** (Eurostat `cei_srm030`, 11.5% in 2022), which
  is an economy-wide material-flow share and is **not comparable** to this product
  composite.

This composite is **distinct from the Ellen MacArthur Foundation Material
Circularity Indicator (MCI)**, which is defined as a Linear Flow Index modified by
a utility factor — a different formula, not a weighted sum.

---

> **CE data points.** The product/material inputs these services consume are a small,
> demonstrator-level subset. The production-level, AAS-mapped catalog of Circular Economy
> data points is maintained separately by DFKI:
> [Datapoints-for-Circular-Economy](https://github.com/DFKI/Datapoints-for-Circular-Economy).

## 3. Other services

- **CE Data Extraction (`extract_ce_data`)** — a rule-/keyword-based parser that
  pulls CE-relevant fields (materials, recycled content, recyclability,
  certifications, hazardous substances, end-of-life) from unstructured text. It is
  a heuristic information-extraction demonstrator, not a validated NLP model.
- **Material Reuse Potential (`analyze_material_reuse`)** — returns reuse scores,
  pathways, value-recovery percentages and CO₂ savings from a curated per-material
  lookup table. The tabulated values are illustrative reference figures.
- **Service Registry (`get_available_services`)** — metadata only; no calculation.

---

## 4. Limitations (summary)

1. Calculations are simplified models intended to demonstrate the agent/MCP
   architecture, not to deliver certified LCA results.
2. Emission factors are cited cradle-to-gate primary-production averages; they
   ignore product-specific recycled content, use phase, and end-of-life.
3. Several model coefficients (Section 1) and the circularity aggregation
   (Section 2) are transparent assumptions, not standardised or empirically fitted.
4. The circularity reference value and any "benchmark" comparisons are illustrative.
5. The extraction and reuse services are heuristic/lookup-based.

All assumptions are isolated in named constants so they can be replaced with
project-specific or empirically calibrated values.

---

## References

- Nuss, P. & Eckelman, M. J. (2014). *Life Cycle Assessment of Metals: A Scientific
  Synthesis.* PLOS ONE 9(7): e101298. https://doi.org/10.1371/journal.pone.0101298
- Hammond, G. & Jones, C. (2011). *Inventory of Carbon & Energy (ICE) Database,
  v2.0.* University of Bath / Circular Ecology.
  https://circularecology.com/embodied-carbon-footprint-database.html
- World Steel Association — *Life Cycle Inventory (LCI) data and eco-profiles.*
  https://worldsteel.org/
- NAPCOR — *Virgin PET life-cycle inventory* (U.S. LCI, 2020 revision).
- CEN-CENELEC EN 45552:2020, EN 45554:2020, EN 45555:2019, EN 45557:2020;
  CLC/TR 45550:2020. (CEN-CLC/JTC 10, material efficiency for ecodesign.)
- Eurostat — *Circular material use rate* (`cei_srm030`).
- Ellen MacArthur Foundation & Granta Design — *Circularity Indicators:
  Methodology* (Material Circularity Indicator).
- ISO 14067:2018; ISO 14040:2006 / ISO 14044:2006; GHG Protocol Product Standard.
- DFKI — *Datapoints for Circular Economy* (production-level, AAS-mapped CE data points).
  https://github.com/DFKI/Datapoints-for-Circular-Economy
