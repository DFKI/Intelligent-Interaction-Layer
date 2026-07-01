# Intelligent-Interaction-Layer

The **Intelligent Interaction Layer** is a natural-language chatbot — the agentic front end of a service-oriented **Circular Economy (CE)** dataspace. Ask questions in **plain language** and an LLM agent picks and runs the right **CE service** for you, exposed as tools over the Model Context Protocol (MCP). Built for DFKI, it combines a FastAPI + WebSocket chat interface, Ollama LLMs, and 5 example CE services — from carbon footprint calculation to material reuse analysis.

---

## Features

- **Natural-language interface** — ask in plain English; the agent interprets your intent, calls the right CE service, and explains the result (no commands or code)
- **5 CE analysis services** exposed as MCP tools (carbon footprint, circularity indicator, material reuse, CE data extraction, service registry)
- **FastMCP SSE server** on port 8002 — tools callable from any MCP client
- **Streaming LLM responses** via Ollama (gemma3, phi4, qwen2.5, mistral)
- **Role-based access control** — 10 users across 10 CE roles (manufacturer, designer, recycler, policy maker, auditor, etc.)
- **Light / dark mode** with theme persistence
- **Pre-routing** — deterministic queries bypass the LLM entirely for instant answers
- **5-minute inactivity auto-logout** with countdown warning
- **JWT cookie auth** — session invalidated on every server restart
- **Auto-opens browser** on startup

---

## CE Services

| # | Service | Tool ID | Standards |
|---|---------|---------|-----------|
| 1 | Service Registry | `get_available_services` | — |
| 2 | Product Carbon Footprint | `calculate_carbon_footprint` | ISO 14067, IDTA 02023 |
| 3 | CE Data Extraction | `extract_ce_data` | ISO 14040, REACH, RoHS |
| 4 | Circularity Indicator | `calculate_circularity_indicator` | EN 45552/45554/45555/45557 |
| 5 | Material Reuse Potential | `analyze_material_reuse` | WEEE, ISO 14040 |

Full documentation: [`docs/`](docs/README.md) · Quick examples: [`docs/quickstart.md`](docs/quickstart.md) · Methodology & limitations: [`docs/methodology.md`](docs/methodology.md)

---

## Prerequisites

- **Python 3.10+**
- **[Ollama](https://ollama.com/)** running locally. You must install **at least one**
  of the supported models — `gemma3`, `phi4`, `qwen2.5`, or `mistral`:

```bash
ollama pull gemma3:12b    # default model
ollama pull phi4
ollama pull qwen2.5:7b
ollama pull mistral
```

The default model is set to **`gemma3:12b`**, so installing it is recommended.
Smaller variants (e.g. `gemma3:4b`) respond much faster on CPU-only machines.
To change the default, reorder `ALLOWED_MODELS` in `fastapi_app.py` (the first
entry is used as `DEFAULT_MODEL`).

---

## Quick Start

```bash
git clone https://github.com/DFKI/Intelligent-Interaction-Layer.git
cd Intelligent-Interaction-Layer
chmod +x run.sh
./run.sh
```

`run.sh` will:
1. Create a Python virtual environment and install dependencies
2. Print a FastMCP-style banner with server info
3. Start the **FastMCP MCP server** on port `8002`
4. Start the **FastAPI web server** on port `8000`
5. Auto-open `http://localhost:8000` in your browser

---

## Login Credentials

| Username | Password | Role |
|----------|----------|------|
| user1 | user1 | Manufacturer |
| user2 | user2 | Designer |
| user3 | user3 | Recycler |
| user4 | user4 | Policy Maker |
| admin | admin | Orchestrator |

Each role gets tailored suggested questions and a role-specific LLM context.

These are sample accounts shipped for demonstration. New users can be defined
by adding entries to `config/users.yml` — see [Configuration](#configuration).

---

## Usage

Just type what you want in the chat, in plain language — the agent figures out
which service to run. For example:

```
Calculate the carbon footprint of a 2 kg aluminum laptop made in China.
What's the circularity score for 60% recycled content, 80% recyclable, durability 8?
Pull the CE data from this datasheet: …
What's the reuse potential of post-consumer HDPE in good condition?
```

You can also refer to a product already in the connected data space by its id
(e.g. *"carbon footprint and circularity score for LAPTOP-X1"*) and the agent
retrieves its stored data. See [`docs/quickstart.md`](docs/quickstart.md) for a
short walkthrough.

---

## Configuration

No configuration is required. `run.sh` generates a fresh `CE_SECRET_KEY` (the key
used to sign login-session JWTs) on every start, which invalidates previous
sessions. Two **optional** overrides are picked up from your environment — or from
a local, git-ignored `.env` if you choose to create one:

- `CE_SECRET_KEY` — set a fixed value if you want login sessions to survive restarts.
- `OLLAMA_HOST` — point at a non-default Ollama (default `http://localhost:11434`).

### Adding users

Users are defined in `config/users.yml`. To add a new user, append an entry with
the following fields:

```yaml
  - username: user5
    password: user5
    role: researcher
    display_name: Researcher User
    organization: Example Organization
```

The `role` field determines the user's behavior in the system — its available
tools, role-specific LLM context, suggested questions, and UI badge. Any of the
built-in roles can be assigned **without code changes**:

`manufacturer`, `designer`, `recycler`, `policy_maker`, `researcher`, `auditor`,
`logistics_manager`, `sustainability_officer`, `data_scientist`, `orchestrator`.

Role definitions live in `auth.py` (`ROLE_META`, `ROLE_SYSTEM_ADDENDA`,
`ROLE_QUESTIONS`); add a new role there if you need one beyond the list above.

To change allowed LLM models, edit `ALLOWED_MODELS` in `fastapi_app.py`.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + Uvicorn |
| Real-time chat | WebSockets |
| LLM inference | Ollama (local) |
| MCP protocol | FastMCP 3.x (SSE transport) |
| Auth | JWT cookies (PyJWT) |
| Frontend | Vanilla JS + CSS (no framework) |
| CE tools | Pure Python (no external deps) |

---

## License

Licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** — see [LICENSE](LICENSE).

---

**Powered by [DFKI](https://www.dfki.de) — German Research Center for Artificial Intelligence**
