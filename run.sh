#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"
APP="fastapi_app:app"
MCP_PORT=8002
WEB_PORT=8000

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ── FastMCP-style banner ───────────────────────────────────────────────────────
clear
python3 - << 'PYEOF'
import re
G  = "\033[0;32m"
C  = "\033[0;36m"
D  = "\033[2m"
B  = "\033[1m"
N  = "\033[0m"
W  = 80

_ANSI = re.compile(r'\x1b\[[0-9;]*m')
_WIDE = set("🔌🌐⚡🤖")          # emojis render as 2 terminal columns

def vlen(s):                        # visible width: ignore ANSI, count emoji as 2
    s = _ANSI.sub('', s)
    return sum(2 if ch in _WIDE else 1 for ch in s)

def box_top(w, col=G): print(f"{col}╭{'─'*(w-2)}╮{N}")
def box_bot(w, col=G): print(f"{col}╰{'─'*(w-2)}╯{N}")
def box_row(s="", w=W, col=G):
    pad = max(0, w-2-vlen(s))
    print(f"{col}│{N}{s}{' '*pad}{col}│{N}")
def center(s, w=W):
    return ' '*max(0, (w-2-vlen(s))//2) + s

box_top(W)
box_row()
box_row(center(f"{B}Intelligent Interaction Layer{N}  v1.0.0"))
box_row(center(f"{D}Natural-language chatbot for Circular Economy services · DFKI{N}"))
box_row()
box_bot(W)
print()

W2 = 64
def box2_row(label="", val=""):
    content = f"  {label}"
    # pad the label column to a fixed visible width, then add the value
    gap = max(1, 26 - vlen(content))
    line = f"{content}{' '*gap}{val}"
    pad = max(0, W2-2-vlen(line))
    print(f"{C}│{N}{line}{' '*pad}{C}│{N}")

box_top(W2, C)
box2_row("🔌  MCP Server:", "http://0.0.0.0:8002/sse")
box2_row("🌐  Web UI:",     "http://localhost:8000")
box2_row("⚡  CE Tools:",   "5 services")
box2_row("🤖  LLM:",        "Ollama (qwen2.5 · phi4 · mistral)")
box_bot(W2, C)
print()
PYEOF

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Install Python 3.10+."
    exit 1
fi

# Create or reuse venv
if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}Found existing virtual environment${NC}"
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}Virtual environment created${NC}"
fi

source "$VENV_DIR/bin/activate"

# Install requirements if needed
INSTALLED_PACKAGES=$("$VENV_DIR/bin/pip" list --format=freeze 2>/dev/null)
NEEDS_INSTALL=false

while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    PKG_NAME=$(echo "$line" | sed 's/[>=<].*//' | tr '[:upper:]' '[:lower:]')
    if ! echo "$INSTALLED_PACKAGES" | grep -qi "^$PKG_NAME"; then
        NEEDS_INSTALL=true
        break
    fi
done < "$REQUIREMENTS"

if [ "$NEEDS_INSTALL" = true ]; then
    echo -e "${YELLOW}Installing requirements...${NC}"
    pip install --quiet --upgrade pip
    pip install --quiet -r "$REQUIREMENTS"
    echo -e "${GREEN}Requirements installed${NC}"
else
    echo -e "${GREEN}All requirements already installed${NC}"
fi

# Optional local overrides — no file is required. If you created a .env (git-ignored)
# to set a stable CE_SECRET_KEY or a custom OLLAMA_HOST, load it.
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

# Auth secret for signing login JWT cookies. If not provided, generate a fresh one
# each run — this rotates the secret and invalidates previous browser sessions.
if [ -z "${CE_SECRET_KEY:-}" ]; then
    export CE_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
    echo -e "${GREEN}Generated a fresh auth secret — previous sessions invalidated${NC}"
else
    echo -e "${GREEN}Using CE_SECRET_KEY from your environment / .env${NC}"
fi

# ── Check Ollama and ensure the default model is available ─────────────────────
# Derive the default model from the app so this stays in sync with ALLOWED_MODELS.
DEFAULT_MODEL="$(grep -oP 'ALLOWED_MODELS\s*=\s*\["\K[^"]+' "$PROJECT_DIR/fastapi_app.py" 2>/dev/null)"
DEFAULT_MODEL="${DEFAULT_MODEL:-qwen2.5:7b}"

if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "\"$DEFAULT_MODEL\""; then
    echo -e "${GREEN}Default model '$DEFAULT_MODEL' is installed.${NC}"
elif curl -s http://localhost:11434/api/tags &>/dev/null; then
    # Ollama is running, but the default model isn't pulled yet.
    echo -e "${YELLOW}Default model '$DEFAULT_MODEL' is not installed in Ollama.${NC}"
    if [ -t 0 ]; then
        read -r -p "  Pull it now (ollama pull $DEFAULT_MODEL)? [y/N] " REPLY
        case "$REPLY" in
            [yY]|[yY][eE][sS])
                if ollama pull "$DEFAULT_MODEL"; then
                    echo -e "${GREEN}Pulled '$DEFAULT_MODEL'.${NC}"
                else
                    echo -e "${YELLOW}Pull failed — pull a model manually, then pick it in the UI:${NC}"
                    echo "  ollama pull $DEFAULT_MODEL"
                fi
                ;;
            *)
                echo -e "${DIM}Skipped. Pull manually before chatting: ollama pull $DEFAULT_MODEL${NC}"
                ;;
        esac
    else
        echo -e "${DIM}Non-interactive shell — skipping auto-pull. Pull manually: ollama pull $DEFAULT_MODEL${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}Warning: Ollama not detected at localhost:11434${NC}"
    echo "  Start Ollama: ollama serve"
    echo ""
fi

# Kill any existing process on port 8000
if lsof -ti:$WEB_PORT &>/dev/null; then
    echo -e "${YELLOW}Port $WEB_PORT in use — stopping existing process...${NC}"
    kill -9 $(lsof -ti:$WEB_PORT) 2>/dev/null || true
    sleep 1
fi

# Kill any existing process on port 8002
if lsof -ti:$MCP_PORT &>/dev/null; then
    echo -e "${YELLOW}Port $MCP_PORT in use — stopping existing MCP server...${NC}"
    kill -9 $(lsof -ti:$MCP_PORT) 2>/dev/null || true
    sleep 1
fi

# Start FastMCP server in background (prints its own banner)
echo -e "${CYAN}Starting FastMCP server on port $MCP_PORT...${NC}"
python3 -m ce_services.fastmcp_server $MCP_PORT &
MCP_PID=$!

# Wait for MCP to bind (FastMCP takes ~3s to start uvicorn internally)
sleep 3

# Auto-open browser (Linux/macOS)
(sleep 2 && xdg-open "http://localhost:$WEB_PORT" 2>/dev/null || open "http://localhost:$WEB_PORT" 2>/dev/null) &

# Cleanup on exit: also kill MCP server
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    kill "$MCP_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo -e "${GREEN}Starting Intelligent Interaction Layer web server on port $WEB_PORT...${NC}"
echo ""

uvicorn "$APP" --host 0.0.0.0 --port $WEB_PORT --reload "$@"
