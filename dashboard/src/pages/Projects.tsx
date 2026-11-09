import { useEffect, useState } from "react";
import * as api from "../services/api";

export default function Projects() {
  const [projects, setProjects] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [by, setBy] = useState("agent_01");
  const load = () => api.endpoints.projects().then(setProjects).catch(() => {});
  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, []);
  const create = async () => {
    if (!name.trim()) return;
    await api.endpoints.createProject({ name, proposed_by: by, requirements: {}, assigned_agents: [by] });
    setName("");
    load();
  };
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Projects</h2>
      <div className="flex gap-2">
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Project name" className="bg-slate-800 p-2 rounded flex-1" />
        <select value={by} onChange={e => setBy(e.target.value)} className="bg-slate-800 p-2 rounded">
          {["agent_01","agent_02","agent_03"].map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <button onClick={create} className="bg-indigo-600 px-4 rounded">Create</button>
      </div>
      <div className="space-y-2">
        {projects.map(p => (
          <div key={p.project_id} className="bg-slate-900 rounded p-4 border border-slate-800">
            <div className="flex justify-between">
              <h3 className="font-semibold">{p.name}</h3>
              <span className="text-xs text-slate-400">{p.status}</span>
            </div>
            <div className="text-xs text-slate-400">By {p.proposed_by} · Agents: {p.assigned_agents?.join(", ")}</div>
            <div className="text-xs mt-1">Requirements: {JSON.stringify(p.requirements)} · Progress: {JSON.stringify(p.progress)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
