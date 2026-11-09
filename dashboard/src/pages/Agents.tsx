import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "../services/api";

export default function Agents() {
  const [agents, setAgents] = useState<any[]>([]);
  const load = () => api.endpoints.agents().then(setAgents).catch(() => {});
  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, []);
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Agents</h2>
        <button onClick={() => api.endpoints.decideAll().then(load)} className="bg-indigo-600 px-3 py-1 rounded text-sm">Decide All</button>
      </div>
      <AddAgentForm onAdded={load} />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {agents.map(a => (
          <div key={a.agent_id} className="bg-slate-900 rounded p-4 border border-slate-800">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-indigo-300">{a.name}</h3>
              <span className="text-xs text-slate-400">{a.status}</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">{a.personality}</p>
            <div className="text-sm mt-3 space-y-1">
              <div><span className="text-slate-400">Goal:</span> {a.current_goal || "—"}</div>
              <div><span className="text-slate-400">Intention:</span> {a.intention || "—"}</div>
              <div><span className="text-slate-400">Thoughts:</span> {a.thoughts || "—"}</div>
              <div><span className="text-slate-400">Activity:</span> {a.current_activity}</div>
              <div><span className="text-slate-400">Health:</span> {a.health} <span className="text-slate-400">Hunger:</span> {a.hunger}</div>
              <div><span className="text-slate-400">Pos:</span> {JSON.stringify(a.position)}</div>
              {a.alert && <div className="text-red-400 text-xs">⚠ {a.alert}</div>}
            </div>
            <div className="mt-3 flex gap-2">
              <Link to={`/agents/${a.agent_id}`} className="text-xs bg-slate-800 px-2 py-1 rounded">Profile</Link>
              <button onClick={() => api.endpoints.decideAgent(a.agent_id).then(load)} className="text-xs bg-indigo-700 px-2 py-1 rounded">Decide</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AddAgentForm({ onAdded }: { onAdded: () => void }) {
  const [aid, setAid] = useState("");
  const [name, setName] = useState("");
  const [personality, setPersonality] = useState("");
  const [skin, setSkin] = useState("");
  const submit = async () => {
    if (!aid.trim() || !name.trim()) return;
    await api.post("/api/agents/add", { agent_id: aid, name, personality, interests: [], skin });
    setAid(""); setName(""); setPersonality(""); setSkin("");
    onAdded();
  };
  return (
    <div className="bg-slate-900 rounded p-4 border border-slate-800">
      <h3 className="font-semibold mb-2">Add Agent</h3>
      <div className="flex flex-wrap gap-2">
        <input value={aid} onChange={e => setAid(e.target.value)} placeholder="agent_id" className="bg-slate-800 p-2 rounded" />
        <input value={name} onChange={e => setName(e.target.value)} placeholder="gamertag" className="bg-slate-800 p-2 rounded" />
        <input value={personality} onChange={e => setPersonality(e.target.value)} placeholder="personality" className="bg-slate-800 p-2 rounded flex-1" />
        <input value={skin} onChange={e => setSkin(e.target.value)} placeholder="skin URL" className="bg-slate-800 p-2 rounded flex-1" />
        <button onClick={submit} className="bg-emerald-600 px-4 rounded">Add</button>
      </div>
    </div>
  );
}
