# Architecture

## Components
1. Minecraft Fabric mod (Java) — observes world, executes actions, communicates with backend over HTTP/JSON.
2. Python AI engine — agent brains, memory, SQLite, Ollama provider, REST API, WebSocket.
3. React dashboard — monitoring UI.

## Data flow
Mod pushes observations -> backend stores -> agents decide (Ollama) -> actions queued -> mod pulls & executes -> results reported -> memories updated.

## Cost optimization
Staggered scheduling, event-triggered decisions, local deterministic actions, memory retrieval, sequential Ollama requests (concurrency 1 default).