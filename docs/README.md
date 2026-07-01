# Intelligent Interaction Layer — Documentation

The Intelligent Interaction Layer is a natural-language chatbot for Circular Economy services. Start it with **one command**,
then ask questions in **plain language** — the assistant picks the right service
and explains the result. No commands or code needed.

## Getting started

```
bash run.sh
```

This sets everything up and opens the chat in your browser. Log in (see the
[main README](../README.md)) and start asking. For a short tour, see
[quickstart.md](quickstart.md).

---

## Services

| # | Service | What it does |
|---|---------|--------------|
| 1 | [Service Registry](services/01_service_registry.md) | Lists what the assistant can do |
| 2 | [Product Carbon Footprint](services/02_carbon_footprint.md) | Estimates a product's CO₂e |
| 3 | [CE Data Extraction](services/03_ce_data_extraction.md) | Pulls CE facts from text |
| 4 | [Circularity Indicator](services/04_circularity_indicator.md) | Scores how circular a product is |
| 5 | [Material Reuse Potential](services/05_material_reuse.md) | Assesses reuse/recycling of a material |

You don't need to pick a service — just describe what you want and the assistant
routes it for you:

```
What CE services are available?
Calculate the carbon footprint of a 2 kg aluminum laptop made in China.
What's the circularity score for a product with 40% recycled content?
What's the reuse potential of post-consumer aluminum?
```

---

## Learn more

- **[Methodology & Limitations](methodology.md)** — how results are computed, which
  values come from published sources, and which are assumptions.
- **[Dataspace Integration](dataspace-integration.md)** *(developers)* — how the
  services can fetch data from the dataspace via the Intelligent Query agent, and
  are exposed as MCP tools for non-chat clients.
- **CE data points** — the production-level, AAS-mapped catalog of Circular Economy
  data points is maintained separately by DFKI:
  [Datapoints-for-Circular-Economy](https://github.com/DFKI/Datapoints-for-Circular-Economy).

## Standards

The services relate to ISO 14067 and ISO 14040/44 (carbon footprint & life-cycle
assessment), the EU EN 4555x material-efficiency standards (durability, repair,
recyclability, recycled content), and EU WEEE / REACH / RoHS. Per-service detail
is in [methodology.md](methodology.md).
