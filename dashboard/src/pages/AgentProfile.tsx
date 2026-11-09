import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import * as api from "../services/api";

export default function AgentProfile() {
  const { id } = useParams();
  const [agent, setAgent] = useState<any>(null);
  const [mems, setMems] = useState<any[]>([]);
  const [decs, setDecs] = useState<any[]>([]);
  const [acts, setActs] = useState<any[]>([]);
  const load = () => {
    if (!id) return;
    api.endpoints.agent(id).then(setAgent).catch(() => {});
    api.endpoints.agentMemories(id).then(setMems).catch(() => {});
    api.endpoints.agentDecisions(id).then(setDecs).catch(() => {});
    api.endpoints.agentActions(id).then(setActs).catch(() => {});
  };
  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, [id]);
  if (!agent) return <div>Loading...</div>;
  return (
    <div className="space-y-4">
      <Link to="/agents" className="text-sm text-indigo-400">← Back</Link>
      <h2 className="text-2xl font-bold">{agent.name}</h2>
      <div className="bg-slate-900 rounded p-4 border border-slate-800">
        <div className="grid grid-cols-2 gap-2 text-sm mb-3">
          <div><span className="text-slate-400">Goal:</span> {agent.current_goal}</div>
          <div><span className="text-slate-400">Intention:</span> {agent.intention}</div>
          <div><span className="text-slate-400">Activity:</span> {agent.current_activity}</div>
          <div><span className="text-slate-400">Health/Hunger:</span> {agent.health}/{agent.hunger}</div>
          <div><span className="text-slate-400">Pos:</span> {JSON.stringify(agent.position)}</div>
          <div><span className="text-slate-400">Alert:</span> {agent.alert || "none"}</div>
        </div>
        <div className="text-sm mb-2"><span className="text-slate-400">Thoughts:</span> {agent.thoughts}</div>
        <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(agent, null, 2)}</pre>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 rounded p-4 border border-slate-800">
          <h3 className="font-semibold mb-2">Memories</h3>
          <ul className="text-xs space-y-1 max-h-64 overflow-auto">
            {mems.map(m => <li key={m.memory_id}>{m.timestamp} [{m.memory_type}] {m.content}</li>)}
          </ul>
        </div>
        <div className="bg-slate-900 rounded p-4 border border-slate-800">
          <h3 className="font-semibold mb-2">Decisions</h3>
          <ul className="text-xs space-y-1 max-h-64 overflow-auto">
            {decs.map(d => <li key={d.decision_id}>{d.timestamp} — {d.current_goal}: {d.reasoning_summary}</li>)}
          </ul>
        </div>
        <div className="bg-slate-900 rounded p-4 border border-slate-800">
          <h3 className="font-semibold mb-2">Actions</h3>
          <ul className="text-xs space-y-1 max-h-64 overflow-auto">
            {acts.map(a => <li key={a.action_id}>{a.created_at} {a.action} [{a.status}]</li>)}
          </ul>
        </div>
      </div>
    </div>
  );
}
