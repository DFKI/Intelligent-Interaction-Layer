"""Intelligent Interaction Layer — FastAPI + WebSocket backend."""
from __future__ import annotations
import os, json, asyncio, secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml, ollama, httpx
import jwt as pyjwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Cookie, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from ce_services import ALL_TOOLS_SCHEMA as CE_TOOLS_SCHEMA, execute_tool as execute_ce_tool
from auth import get_role, get_role_questions, get_role_system_addendum, get_role_meta

BASE_DIR = Path(__file__).parent
SECRET_KEY = os.getenv("CE_SECRET_KEY", secrets.token_hex(32))
TOKEN_MINUTES = 60

ALLOWED_MODELS = ["gemma3:12b", "phi4:latest", "qwen2.5:7b", "mistral:latest"]
DEFAULT_MODEL = ALLOWED_MODELS[0]

CE_SERVICE_LABELS = {
    "get_available_services":          "Service Registry",
    "calculate_carbon_footprint":      "Product Carbon Footprint",
    "calculate_carbon_footprint_for_asset": "Product Carbon Footprint (Dataspace)",
    "extract_ce_data":                 "CE Data Extraction",
    "calculate_circularity_indicator": "Circularity Indicator",
    "calculate_circularity_indicator_for_asset": "Circularity Indicator (Dataspace)",
    "analyze_material_reuse":          "Material Reuse Potential",
    "analyze_material_reuse_for_asset": "Material Reuse Potential (Dataspace)",
}

SYSTEM_PROMPT = """You are the assistant of the Intelligent Interaction Layer, an expert in Circular Economy (CE) analysis.

CRITICAL RULE: Always call the appropriate tool before answering. Never answer CE questions from memory alone.

Tool routing:
- services/tools available → get_available_services
- product + materials + weight/region given inline → calculate_carbon_footprint
- product already in the dataspace (an asset/product id, no inline data) → calculate_carbon_footprint_for_asset
- unstructured text / datasheet → extract_ce_data
- circularity / recycled content / sustainability score given inline → calculate_circularity_indicator
- circularity of a product already in the dataspace (asset id) → calculate_circularity_indicator_for_asset
- reuse / upcycling / material recovery given inline → analyze_material_reuse
- reuse potential of a material stream already in the dataspace (asset id) → analyze_material_reuse_for_asset

After analysis, always suggest concrete next steps."""

NEXT_STEPS = {
    "get_available_services":          ["Calculate carbon footprint of your product", "Extract CE data from a description or datasheet", "Calculate a circularity indicator"],
    "calculate_carbon_footprint":      ["Calculate circularity indicator for a full sustainability score", "Analyze material reuse potential", "Extract CE data from a product datasheet"],
    "calculate_carbon_footprint_for_asset": ["Calculate the circularity indicator for this asset", "Analyze material reuse potential for this product", "Compare against another product in the dataspace"],
    "extract_ce_data":                 ["Calculate circularity indicator from extracted values", "Calculate the product carbon footprint", "Analyze material reuse potential"],
    "calculate_circularity_indicator": ["Calculate product carbon footprint", "Analyze material reuse potential", "Extract CE data from a product description"],
    "calculate_circularity_indicator_for_asset": ["Calculate the carbon footprint for this asset", "Analyze material reuse potential", "Compare against another product in the dataspace"],
    "analyze_material_reuse":          ["Calculate carbon footprint impact of reuse", "Calculate a circularity indicator", "Extract CE data from a material datasheet"],
    "analyze_material_reuse_for_asset": ["Calculate the circularity indicator for this asset", "Calculate carbon footprint impact of reuse", "Assess another material stream in the dataspace"],
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_users() -> dict:
    with open(BASE_DIR / "config" / "users.yml") as f:
        return {u["username"]: u for u in yaml.safe_load(f)["users"]}

def create_token(username: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=TOKEN_MINUTES)
    return pyjwt.encode({"sub": username, "exp": exp}, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    try:
        return pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"]).get("sub")
    except Exception:
        return None

def get_models() -> list[str]:
    try:
        result = ollama.list()
        raw = result.get("models", []) if isinstance(result, dict) else getattr(result, "models", [])
        found = set()
        for m in raw:
            name = (m.get("name") or m.get("model","")) if isinstance(m,dict) else (getattr(m,"model","") or getattr(m,"name",""))
            if name in ALLOWED_MODELS:
                found.add(name)
        return [m for m in ALLOWED_MODELS if m in found] or ALLOWED_MODELS
    except Exception:
        return ALLOWED_MODELS

def _content(msg) -> str:
    return (msg.get("content","") if isinstance(msg,dict) else getattr(msg,"content","")) or ""

def _tool_calls(msg):
    return msg.get("tool_calls") if isinstance(msg,dict) else getattr(msg,"tool_calls",None)

def _parse_call(tc) -> tuple[str, dict, str]:
    if isinstance(tc, dict):
        f = tc.get("function", {})
        name, raw, cid = f.get("name",""), f.get("arguments",{}), tc.get("id","")
    else:
        name, raw, cid = tc.function.name, tc.function.arguments, getattr(tc,"id","")
    if isinstance(raw, str):
        try: args = json.loads(raw)
        except: args = {}
    else:
        args = raw or {}
    return name, args, cid

def next_steps_for(tools: list[str]) -> list[str]:
    seen, out = set(), []
    for t in tools:
        for s in NEXT_STEPS.get(t, []):
            if s not in seen:
                seen.add(s); out.append(s)
            if len(out) >= 3: return out
    return out


# Pre-routing: skip the first LLM call for queries that unambiguously map
# to a single tool with no free parameters.  Returns (tool_name, args) or None.
_PREROUTE: list[tuple[list[str], str, dict]] = [
    # Patterns → tool, fixed args
    (["available service", "list service", "what service", "which service",
      "what can you do", "capabilities", "list tools", "what tools",
      "show services", "all service"],
     "get_available_services", {}),
]

def pre_route(text: str) -> Optional[tuple[str, dict]]:
    t = text.lower().strip()
    for patterns, tool, args in _PREROUTE:
        if any(p in t for p in patterns):
            return tool, args
    return None


# Format tool result as readable markdown (skips 2nd LLM call for pre-routed queries)
def format_result(tool_name: str, result: dict) -> str:
    if tool_name == "get_available_services":
        lines = [f"**{result['service_count']} CE Services available:**\n"]
        for s in result["services"]:
            stds = ", ".join(s["standards"]) if s["standards"] else "—"
            lines.append(f"**{s['name']}** (`{s['id']}`)\n{s['description']}\n*Standards: {stds}*\n")
        return "\n".join(lines)
    return json.dumps(result, indent=2)


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Intelligent Interaction Layer", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


# Disable browser caching of frontend assets so edits always show on refresh.
@app.middleware("http")
async def no_cache_frontend(request, call_next):
    resp = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/static"):
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    return resp


@app.get("/")
async def root():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse(BASE_DIR / "static" / "images" / "ce_logo.svg")


@app.post("/api/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = load_users().get(username)
    if not user or user.get("password") != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    resp = JSONResponse({"ok": True})
    resp.set_cookie("ce_token", create_token(username), httponly=True, samesite="lax", max_age=TOKEN_MINUTES * 60)
    return resp


@app.post("/api/logout")
async def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("ce_token")
    return resp


@app.get("/api/status")
async def status():
    tools_ok = True
    # Count distinct services, not raw tool schemas: carbon, circularity and
    # material reuse each expose a second "(Dataspace)" variant, but those are the
    # same service reached by asset id — so the user-facing number stays at 5.
    tool_count = sum(1 for lbl in CE_SERVICE_LABELS.values()
                     if not lbl.endswith("(Dataspace)"))
    try:
        from ce_services import ALL_TOOLS_SCHEMA  # noqa: F401 — verify tools import
    except Exception:
        tools_ok = False

    ollama_ok = True
    try:
        ollama.list()
    except Exception:
        ollama_ok = False

    mcp_server_ok = False
    try:
        # SSE endpoint streams indefinitely — use stream() and read only headers
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET", "http://localhost:8002/sse",
                timeout=httpx.Timeout(connect=2.0, read=1.0, write=1.0, pool=1.0),
            ) as r:
                mcp_server_ok = r.status_code == 200
    except Exception:
        pass

    return {
        "mcp_tools": tool_count,
        "mcp_ok": tools_ok,
        "mcp_server_ok": mcp_server_ok,
        "ollama_ok": ollama_ok,
        "default_model": DEFAULT_MODEL,
    }


@app.get("/api/me")
async def me(ce_token: Optional[str] = Cookie(None)):
    if not ce_token or not (username := verify_token(ce_token)):
        raise HTTPException(status_code=401)
    user = load_users().get(username, {})
    role = user.get("role", "researcher")
    meta = get_role_meta(role)
    return {
        "username": username,
        "display_name": user.get("display_name", username),
        "role": role,
        "role_label": meta["label"],
        "organization": user.get("organization", ""),
        "questions": get_role_questions(role),
        "models": get_models(),
        "default_model": DEFAULT_MODEL,
        "services": CE_SERVICE_LABELS,
    }


@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    # Read cookie directly from the WS upgrade request (more reliable than Cookie dependency)
    ce_token = websocket.cookies.get("ce_token")
    username = verify_token(ce_token) if ce_token else None
    if not username:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    user = load_users().get(username, {})
    role = user.get("role", "researcher")
    addendum = get_role_system_addendum(role)
    prompt = SYSTEM_PROMPT + (f"\n\n{addendum}" if addendum else "")
    messages: list[dict] = [{"role": "system", "content": prompt}]
    model = DEFAULT_MODEL

    async def tx(data: dict):
        await websocket.send_text(json.dumps(data))

    try:
        while True:
            raw = await websocket.receive_text()
            pkt = json.loads(raw)

            if pkt.get("type") == "clear":
                messages[:] = [{"role": "system", "content": prompt}]
                await tx({"type": "cleared"})
                continue

            if pkt.get("type") == "model_change":
                model = pkt.get("model", DEFAULT_MODEL)
                continue

            user_input = pkt.get("content", "").strip()
            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
            await tx({"type": "services_reset"})

            # ── Pre-route: bypass LLM for deterministic single-tool queries ─
            pre = pre_route(user_input)
            if pre:
                tool_name, tool_args = pre
                label = CE_SERVICE_LABELS.get(tool_name, tool_name)
                await tx({"type": "tool_start", "tool": tool_name, "label": label})
                try:
                    result = await asyncio.to_thread(execute_ce_tool, tool_name, tool_args)
                    await tx({"type": "tool_done", "tool": tool_name})
                    formatted = format_result(tool_name, result)
                    await tx({"type": "stream_start"})
                    # Stream the formatted result token-by-token (no LLM needed)
                    for char in formatted:
                        await tx({"type": "token", "content": char})
                    await tx({"type": "done", "next_steps": next_steps_for([tool_name])})
                    messages.append({"role": "assistant", "content": formatted})
                except Exception as ex:
                    await tx({"type": "tool_error", "tool": tool_name, "error": str(ex)})
                    await tx({"type": "error", "content": str(ex)})
                continue

            await tx({"type": "thinking"})   # feedback while LLM processes

            # ── Call 1: tool detection (non-streaming, required) ──────────
            tools_ok = True
            try:
                resp1 = await asyncio.to_thread(
                    ollama.chat, model=model, messages=messages,
                    tools=CE_TOOLS_SCHEMA, stream=False,
                )
            except Exception as e:
                err = str(e)
                if "does not support tools" in err or "400" in err:
                    tools_ok = False
                    await tx({"type": "warning", "content": f"`{model}` has no tool support — switch to gemma3 or qwen2.5 for CE services."})
                    try:
                        resp1 = await asyncio.to_thread(
                            ollama.chat, model=model, messages=messages, stream=False
                        )
                    except Exception as e2:
                        await tx({"type": "error", "content": str(e2)}); continue
                else:
                    await tx({"type": "error", "content": err}); continue

            amsg = resp1.get("message") if isinstance(resp1, dict) else resp1.message
            tcs = _tool_calls(amsg)
            used: list[str] = []

            # ── Tool execution ────────────────────────────────────────────
            if tcs and tools_ok:
                messages.append(
                    amsg if isinstance(amsg, dict)
                    else {"role": "assistant", "content": _content(amsg), "tool_calls": tcs}
                )
                for tc in tcs:
                    name, args, cid = _parse_call(tc)
                    label = CE_SERVICE_LABELS.get(name, name)
                    await tx({"type": "tool_start", "tool": name, "label": label})
                    try:
                        result = await asyncio.to_thread(execute_ce_tool, name, args)
                        rtxt = json.dumps(result, indent=2) if not isinstance(result, str) else result
                        await tx({"type": "tool_done", "tool": name})
                        used.append(name)
                        messages.append({"role": "tool", "tool_call_id": cid, "name": name, "content": rtxt})
                    except Exception as ex:
                        await tx({"type": "tool_error", "tool": name, "error": str(ex)})
                        messages.append({"role": "tool", "tool_call_id": cid, "name": name, "content": f"Error: {ex}"})

            # ── Call 2: streaming synthesis ───────────────────────────────
            await tx({"type": "stream_start"})
            client = ollama.AsyncClient()
            full = ""
            try:
                async for chunk in await client.chat(model=model, messages=messages, stream=True):
                    token = chunk.message.content or ""
                    if token:
                        full += token
                        await tx({"type": "token", "content": token})
            except Exception as ex:
                await tx({"type": "error", "content": str(ex)}); continue

            await tx({"type": "done", "next_steps": next_steps_for(used)})
            messages.append({"role": "assistant", "content": full})

    except WebSocketDisconnect:
        pass
