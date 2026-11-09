import { useEffect, useState } from "react";
import * as api from "../services/api";

export default function Memories() {
  const [agentId, setAgentId] = useState("agent_01");
  const [mems, setMems] = useState<any[]>([]);
  const load = () => api.endpoints.agentMemories(agentId).then(setMems).catch(() => {});
  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, [agentId]);
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Memories</h2>
      <select value={agentId} onChange={e => setAgentId(e.target.value)} className="bg-slate-800 p-2 rounded">
        {["agent_01","agent_02","agent_03"].map(a => <option key={a} value={a}>{a}</option>)}
      </select>
      <div className="bg-slate-900 rounded p-4 border border-slate-800 max-h-[70vh] overflow-auto">
        <ul className="text-sm space-y-2">
          {mems.map(m => (
            <li key={m.memory_id} className="border-b border-slate-800 pb-2">
              <div className="text-xs text-slate-400">{m.timestamp} · {m.memory_type} · importance {m.importance}</div>
              <div>{m.content}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
