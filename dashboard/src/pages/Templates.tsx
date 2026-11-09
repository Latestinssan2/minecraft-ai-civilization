import { useEffect, useState } from "react";
import * as api from "../services/api";

export default function Templates() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [by, setBy] = useState("agent_01");
  const [autobuild, setAutobuild] = useState(true);
  useEffect(() => { api.get("/api/templates").then(setTemplates).catch(() => {}); }, []);
  const build = async (tid: string) => {
    await api.post("/api/templates/project", { template_id: tid, proposed_by: by, autobuild });
    alert("Project created");
  };
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Build Templates</h2>
      <div className="flex gap-2">
        <select value={by} onChange={e => setBy(e.target.value)} className="bg-slate-800 p-2 rounded">
          {["agent_01","agent_02","agent_03"].map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={autobuild} onChange={e => setAutobuild(e.target.checked)} /> Auto-build
        </label>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {templates.map(t => (
          <div key={t.template_id} className="bg-slate-900 rounded p-4 border border-slate-800">
            <h3 className="font-semibold">{t.name}</h3>
            <p className="text-xs text-slate-400">{t.description}</p>
            <div className="text-xs mt-2">Requirements: {JSON.stringify(t.requirements)}</div>
            <button onClick={() => build(t.template_id)} className="mt-3 bg-indigo-600 px-3 py-1 rounded text-sm">Build</button>
          </div>
        ))}
      </div>
    </div>
  );
}
