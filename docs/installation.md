# Installation Guide

## 1. Ollama
Install from https://ollama.com. Then:
```
ollama serve
ollama pull qwen3:8b
```

## 2. Backend
```
cd ai-engine
PYTHONPATH=. python3 -m app.main --config ../config/civilization.yaml
```

## 3. Dashboard
```
cd dashboard
npm install
npm run dev
```

## 4. Minecraft
Install Fabric loader for 1.21.1, Fabric API, and the civilization mod jar. Start server.

## 5. Verify
- Backend health: curl http://localhost:8000/api/health
- Ollama: curl http://localhost:8000/api/ollama/health
- Dashboard: http://localhost:5173