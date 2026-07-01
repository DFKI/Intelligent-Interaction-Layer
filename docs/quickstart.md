# Quickstart Guide

The Intelligent Interaction Layer is used in **plain natural language**. Log in, type your question in
the chat, and the assistant picks the right Circular Economy service, runs it, and
explains the result — no commands or code required.

> Tip: you don't need exact keywords. Just describe your product or material and
> what you want to know. The assistant will ask for anything it's missing.

---

## Example 1 — Carbon footprint of a product

**You ask:**

> Calculate the carbon footprint of a 0.3 kg water bottle made in Europe.
> It's 70% aluminum, 20% stainless steel, and 10% rubber.

**You get back:** the total kg CO₂e, a breakdown by materials / manufacturing /
transport, an A–E carbon rating, and how it compares to a typical product.

---

## Example 2 — Sustainability score from a product description

You can paste a product description or datasheet and ask follow-up questions in
the same conversation — the assistant carries the data forward.

**You paste / ask:**

> Here's our product: "The ProPack container is made from 45% recycled PET and
> polypropylene. It is 82% recyclable, certified to ISO 14040." Extract the CE
> data, then give me its circularity score and the reuse potential of the PET.

**You get back:** the extracted CE data (recycled content, recyclability,
certifications…), a circularity index with an A–E grade, and a reuse assessment
for the PET — all in one reply.

---

## Example 3 — End-of-life planning for collected materials

**You ask:**

> I have a batch of mixed electronics: about 300 kg of copper in good condition,
> 600 kg of aluminum (fair, some contamination), and 800 kg of e-waste. Which
> streams should I prioritise for recovery?

**You get back:** for each material, its reuse potential, estimated value per kg,
and CO₂ savings vs. virgin material — with a suggestion of which to recover first.

---

## Using products already in the system

If a product or material already exists in the connected data space, you don't
need to repeat its details — just refer to it by its name or id:

> What's the carbon footprint and circularity score for product LAPTOP-X1?

The assistant retrieves the stored data for that product and runs the services on
it. Access is governed by your role, so you only see what you're allowed to.

---

## What you can ask

| You want to… | Just say something like… |
|--------------|--------------------------|
| Carbon footprint | "Carbon footprint of a 2 kg steel chair made in Europe" |
| Circularity score | "Circularity score for 60% recycled content, 80% recyclable, durability 8" |
| Extract CE data | "Pull the CE data from this datasheet: …" |
| Material reuse | "Reuse potential of post-consumer HDPE in good condition" |
| See all services | "What CE services are available?" |

Not sure where to start? Each role's home screen suggests a few starter questions —
click one, or type your own.

---

*Developers:* the same services are also callable programmatically and over MCP —
see [`docs/README.md`](README.md) and [`docs/dataspace-integration.md`](dataspace-integration.md).
