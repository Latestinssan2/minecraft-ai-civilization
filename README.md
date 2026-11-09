# 🏰 Minecraft AI Civilization Simulator

A fully autonomous **three-agent AI civilization** living inside a single Minecraft Java Edition world, powered by **local Ollama** models. No vision API, no paid cloud AI, no screenshots. Agents observe the world through server-side structured JSON, think, plan, talk, mine, build, fight, and remember — all visible on a live "crazy UI" dashboard.

> Founding members: **CHAIWALA**, **Arin**, **Mira**. Each has a distinct personality, memory, goals, relationships, and independent decision schedule.

---

## ✨ Feature List (everything the system can do)

### 🧠 AI Agents (3 independent brains)
- Separate identity, personality, interests, memory, goals, conversation history, decision history, relationships.
- Personalities: CHAIWALA (leadership/exploration/planning), Arin (construction/engineering/mining), Mira (exploration/farming/trading).
- Decision cycle: observe → retrieve memory → evaluate goals → plan → select actions → execute → evaluate → update memory.
- Structured JSON decisions with `current_goal`, `intention`, `thoughts`, `plan`, `priority`, `actions`, `messages`. No exposed private chain-of-thought — only concise summaries.
- Event-driven decisions: AI is only called when needed (alerts, manual trigger, periodic fallback) to optimize Ollama usage.
- Per-agent model selection from installed Ollama models (not hardcoded).

### 👁️ Observation (no vision API)
Server-side structured JSON scanning:
- `scan_area`, `inspect_block`, `inspect_entity`, `inspect_inventory`, `inspect_location`, `inspect_biome`, `inspect_structure`, `inspect_resources`, `inspect_health`, `inspect_environment`.
- Payload includes: position, biome, health, hunger, hotbar slot, inventory, nearby blocks, nearby entities, nearby agents, nearby mobs (with coords/distance), dropped items, nearby signs (text), structures, timestamps, world id.
- Configurable radius, caching, chunk-safe, bounded payload size.

### ⚔️ Actions (validated, logged)
`move_to`, `look_at`, `follow_agent`, `stop_moving`, `mine_block`, `collect_item`, `place_block`, `interact_with_block`, `craft_item`, `equip_item`, `drop_item`, `store_item`, `eat_food`, `sleep`, `send_message`, `start_project`, `join_project`, `scan_area`, `locate_structure`, `auto_walk`, `place_sign`, `read_sign`, `pvp_attack`, `switch_hotbar`, `automine`, `alert_response`.
- Each action: agent id, action id, params, validation, status, result, error, timestamps.
- Duplicate execution prevention, timeouts, retries, actual Minecraft confirmation before success.

### 🏰 Civilization / structures
- Locate villages, bastions, and other structures via JSON command; agents auto-walk to coordinates.
- In-path: kill mobs, auto-eat when hungry/low health.
- Alerts when mobs or dropped items nearby.
- Place sign boards and read them (text in observations).
- PVP against nearby entities with one command.
- Hotbar auto-switching.
- Auto-mining with ore selection.
- Settlements, housing, farms, shared storage, projects, job assignment, trading/economy ledger, leadership, relationships, milestones, historical events.

### 💬 Communication
- Private messages, group conversations, nearby chat, project discussions, public announcements.
- Minecraft in-game chat integration (`[AgentName] message`).
- Every message recorded: sender, receiver, timestamp, content, conversation id, context, project.

### 🧠 Memory & Persistence
- SQLite with tables: agents, agent_personalities, agent_goals, agent_memories, messages, conversations, actions, action_results, decisions, relationships, civilizations, projects, project_members, world_observations, historical_events, resource_ledger, llm_requests.
- Memory types: short-term, long-term, episodic, social, shared.
- Importance scoring, duplicate detection, summarization (archives, never deletes originals), relevant retrieval.

### 🤖 AI Provider (Ollama only)
- Local Ollama HTTP API; no API keys, no paid cloud.
- Configurable URL and model; change model without code changes.
- Health check, available models list, retries with exponential backoff, timeouts, concurrency limit (default 1).
- Per-agent model selection from installed models via dashboard.
- Pending decisions preserved if Ollama unavailable; resume later.

### 📊 Dashboard (crazy UI)
Modern dark interface at `http://localhost:5173`:
1. **Overview** — civilization name, status, agents, resources, projects, recent events, Ollama status.
2. **Agents** — all 3 agents: name, personality, position, health, hunger, activity, goal, intention, thoughts, inventory, alert, relationships, last decision/message.
3. **Agent Profile** — full state, memories, decisions, actions.
4. **Live Chat** — all conversations with filters.
5. **World** — coordinate-based map, agent positions, biomes.
6. **Projects** — name, assigned agents, requirements, progress, status.
7. **Memories** — per-agent memory browser.
8. **History** — chronological event timeline.
9. **Live Monitor** — real-time coords, intentions, thoughts, action log, memory, all agent positions.
10. **Settings** — Ollama connection, model list, per-agent model selection, LLM usage stats.

WebSocket live updates + polling.

### 💰 Cost Optimization
- Staggered/event-driven decision scheduling.
- Sequential Ollama requests (configurable concurrency).
- Local deterministic logic for navigation/inventory/crafting.
- Observation caching, memory retrieval instead of full history.
- Conversation summarization, LLM request logging, token usage tracking, configurable budgets.

### 🔒 Reliability
- Health checks (backend, Ollama, DB).
- Connection recovery, graceful shutdown, restart recovery.
- Request timeouts, failed action recovery, DB transactions.
- Agent isolation: one agent failure doesn't stop others.
- Ollama failure doesn't crash Minecraft server.

### 🧪 Testing
- Backend unittest: **33 tests** (database, agent, integration, API, memory/economy).
- Dashboard production build verified.
- Mod compilation unverified (environment lacks Fabric/Minecraft/Java 21/network).

---

## 🏗️ Architecture

```
minecraft-ai-civilization/
├── minecraft-mod/          # Fabric mod (Java 21) for MC 1.21.1
├── ai-engine/              # Python backend + agent brains
├── dashboard/              # React + TS + Tailwind
├── shared/                 # JSON schemas
├── config/                 # YAML configs
├── scripts/                # start/stop/init
├── docs/                   # installation, architecture, troubleshooting
├── tests/
├── .env.example
├── docker-compose.yml
└── README.md
```

**Data flow:** Mod pushes observations → backend stores → agents decide (Ollama) → actions queued → mod pulls & executes → results reported → memories updated → dashboard shows live.

---

## 📋 Requirements
- Java 21 (mod; build unverified in this env)
- Python 3.11+
- Node.js 18+
- Ollama with a model, e.g. `ollama pull qwen3:8b`
- Minecraft Java 1.21.1 server + Fabric + Fabric API

---

## 🚀 Installation

### 1. Ollama
```bash
brew install ollama   # or download from ollama.com
ollama serve
ollama pull qwen3:8b
```

### 2. Backend
```bash
cd ai-engine
PYTHONPATH=. python3 -m app.main --config ../config/civilization.yaml
```
Health: `http://localhost:8000/api/health` · Ollama: `http://localhost:8000/api/ollama/health`

### 3. Dashboard
```bash
cd dashboard
npm install
npm run dev
```
Open `http://localhost:5173`

### 4. Minecraft mod
```bash
cd minecraft-mod
./gradlew build
```
Copy jar from `build/libs/` into server `mods/` with Fabric API.

### 5. Verify
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/ollama/health
curl http://localhost:8000/api/agents
```

### Minecraft bots (real players via Mineflayer)
The agents now run as **real Minecraft players** using Mineflayer (Node.js), which gives them
tab-list presence, natural walking, knockback, skins, and pathfinding.

```bash
cd mineflayer-bots
npm install
node main.js
```
Bots connect to `localhost:25565` (offline mode) as CHAIWALA, Arin, Mira and talk to the
Python backend at `http://localhost:8000`.

### Quick start (all services)
```bash
./scripts/start-all.sh
# In another terminal:
cd mineflayer-bots && node main.js
```

---

## ⚙️ Configuration
- `config/civilization.yaml` — agents, AI provider, simulation settings.
- Change model without code: edit `ai.providers.ollama.model` or use dashboard Settings.
- Agent count default 3 (CHAIWALA, Arin, Mira).
- `use_mock_world: true` for offline demo; `false` for real Minecraft.

---

## 🧪 Testing
Backend:
```bash
cd ai-engine
PYTHONPATH=. python3 -m unittest discover -s tests
```
Dashboard:
```bash
cd dashboard && npm run build
```

---

## ⚠️ Known Limitations
- Mod compilation **verified** (Fabric Loom 1.19.4, Java 21). Runtime on a real Minecraft server still requires manual verification (server + Fabric API + Ollama).
- Ollama not bundled; install separately. If unavailable, decisions queued & retried.
- Java 21 toolchain not available in build environment; mod targets Java 21.

---

## 📁 Key Files
- `ai-engine/app/main.py` — backend entrypoint.
- `ai-engine/app/agents/` — agent brains.
- `ai-engine/app/providers/ollama_provider.py` — Ollama integration.
- `ai-engine/app/database/db.py` — SQLite persistence.
- `dashboard/src/pages/` — UI pages.
- `minecraft-mod/src/main/java/com/civilization/` — mod source.
- `IMPLEMENTATION_STATUS.md` — detailed status & known bugs.

## License
MIT