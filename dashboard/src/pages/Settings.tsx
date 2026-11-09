import { useEffect, useState } from "react";
import * as api from "../services/api";

export default function Settings() {
  const [ollama, setOllama] = useState<any>(null);
  const [models, setModels] = useState<string[]>([]);
  const [llm, setLlm] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  useEffect(() => {
    api.endpoints.ollamaHealth().then(setOllama).catch(() => {});
    api.endpoints.ollamaModels().then(d => setModels(d.models || [])).catch(() => {});
    api.endpoints.llmStats().then(setLlm).catch(() => {});
    api.endpoints.agents().then(setAgents).catch(() => {});
  }, []);
  const setModel = async (aid: string, model: string) => {
    await api.post(`/api/agents/${aid}/model`, { model });
    setAgents(await api.endpoints.agents());
  };
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Settings</h2>
      <div className="bg-slate-900 rounded p-4 border border-slate-800">
        <h3 className="font-semibold mb-2">Ollama</h3>
        <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(ollama, null, 2)}</pre>
        <div className="mt-2 text-sm">Available models: {models.join(", ") || "—"}</div>
      </div>
      <div className="bg-slate-900 rounded p-4 border border-slate-800">
        <h3 className="font-semibold mb-2">Agent Model Selection</h3>
        <div className="space-y-2">
          {agents.map(a => (
            <div key={a.agent_id} className="flex items-center gap-2">
              <span className="w-24 text-sm">{a.name}</span>
              <select onChange={e => setModel(a.agent_id, e.target.value)} className="bg-slate-800 p-1 rounded text-sm flex-1">
                <option value="">default</option>
                {models.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-slate-900 rounded p-4 border border-slate-800">
        <h3 className="font-semibold mb-2">LLM Usage</h3>
        <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(llm, null, 2)}</pre>
      </div>
    </div>
  );
}