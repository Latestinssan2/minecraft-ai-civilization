import { useEffect, useState } from "react";
import * as api from "../services/api";

export default function Settings() {
  const [ollama, setOllama] = useState<any>(null);
  const [models, setModels] = useState<string[]>([]);
  const [llm, setLlm] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [profiles, setProfiles] = useState<any[]>([]);
  const [selectedAgent, setSelectedAgent] = useState("agent_01");
  const [skinUrl, setSkinUrl] = useState("");
  const [profileName, setProfileName] = useState("");
  const load = async () => {
    setOllama(await api.endpoints.ollamaHealth().catch(() => null));
    const m = await api.endpoints.ollamaModels().catch(() => ({ models: [] }));
    setModels(m.models || []);
    setLlm(await api.endpoints.llmStats().catch(() => []));
    setAgents(await api.endpoints.agents().catch(() => []));
    setProfiles(await api.get("/api/profiles").catch(() => []));
  };
  useEffect(() => { load(); }, []);
  const setModel = async (aid: string, model: string) => {
    await api.post(`/api/agents/${aid}/model`, { model });
    await load();
  };
  const setSkin = async () => {
    await api.post(`/api/agents/${selectedAgent}/skin`, { skin: skinUrl });
    setSkinUrl("");
    await load();
  };
  const saveProfile = async () => {
    const a = agents.find(x => x.agent_id === selectedAgent);
    if (!a) return;
    await api.post("/api/profiles", {
      agent_id: selectedAgent,
      name: profileName || `${a.name}-profile`,
      personality: a.personality,
      interests: a.interests,
      skin: a.skin,
      is_default: false,
    });
    setProfileName("");
    await load();
  };
  const restoreProfile = async (pid: string) => {
    await api.post(`/api/profiles/${pid}/restore`, {});
    await load();
  };
  const restoreDefault = async (aid: string) => {
    await api.post(`/api/agents/${aid}/restore-default`, {});
    await load();
  };
  void restoreDefault;
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
        <h3 className="font-semibold mb-2">Skins</h3>
        <div className="flex gap-2">
          <select value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)} className="bg-slate-800 p-2 rounded">
            {agents.map(a => <option key={a.agent_id} value={a.agent_id}>{a.name}</option>)}
          </select>
          <input value={skinUrl} onChange={e => setSkinUrl(e.target.value)} placeholder="skin image URL (download from web)" className="bg-slate-800 p-2 rounded flex-1" />
          <button onClick={setSkin} className="bg-indigo-600 px-3 rounded">Apply Skin</button>
        </div>
        <div className="text-xs text-slate-400 mt-2">Download a skin PNG from the web and paste its URL. Default skins can be replaced.</div>
      </div>
      <div className="bg-slate-900 rounded p-4 border border-slate-800">
        <h3 className="font-semibold mb-2">Profiles (save/restore)</h3>
        <div className="flex gap-2 mb-3">
          <select value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)} className="bg-slate-800 p-2 rounded">
            {agents.map(a => <option key={a.agent_id} value={a.agent_id}>{a.name}</option>)}
          </select>
          <input value={profileName} onChange={e => setProfileName(e.target.value)} placeholder="profile name" className="bg-slate-800 p-2 rounded flex-1" />
          <button onClick={saveProfile} className="bg-emerald-600 px-3 rounded">Save Profile</button>
        </div>
        <ul className="text-sm space-y-1">
          {profiles.map(p => (
            <li key={p.profile_id} className="flex items-center justify-between border-b border-slate-800 py-1">
              <span>{p.name} ({p.agent_id}) {p.is_default ? "[default]" : ""}</span>
              <span className="flex gap-2">
                <button onClick={() => restoreProfile(p.profile_id)} className="text-xs bg-indigo-700 px-2 py-1 rounded">Restore</button>
                <button onClick={() => api.post(`/api/agents/${p.agent_id}/restore-default`, {}).then(load)} className="text-xs bg-slate-700 px-2 py-1 rounded">Reset Default</button>
              </span>
            </li>
          ))}
        </ul>
      </div>
      <div className="bg-slate-900 rounded p-4 border border-slate-800">
        <h3 className="font-semibold mb-2">LLM Usage</h3>
        <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(llm, null, 2)}</pre>
      </div>
    </div>
  );
}
