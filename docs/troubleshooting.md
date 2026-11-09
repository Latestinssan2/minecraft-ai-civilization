# Troubleshooting

- Ollama unavailable: backend reports error status; decisions queued. Start `ollama serve`, pull model.
- Model not installed: health check shows model_available=false. Run `ollama pull <model>`.
- Port in use: change port in config or env PORT.
- Dashboard can't reach backend: set VITE_API_BASE.
- Mod can't reach backend: check backendUrl in config/civilization-mod.properties.