import { useEffect, useState } from "react";
import * as api from "../services/api";

export default function LiveMonitor() {
  const [agents, setAgents] = useState<any[]>([]);
  const [selected, setSelected] = useState("agent_01");
  const [mems, setMems] = useState<any[]>([]);
  const [acts, setActs] = useState<any[]>([]);
  const [decs, setDecs] = useState<any[]>([]);
  const [pos, setPos] = useState<any>({});
  const load = async () => {
    const a = await api.endpoints.agents();
    setAgents(a);
    setPos(await api.endpoints.worldPositions());
    setMems(await api.endpoints.agentMemories(selected));
    setActs(await api.endpoints.agentActions(selected));
    setDecs(await api.endpoints.agentDecisions(selected));
  };
  useEffect(() => { load(); const t = setInterval(load, 3000); return () => clearInterval(t); }, [selected]);
  const cur = agents.find(a => a.agent_id === selected);
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Live Monitor</h2>
      <div className="flex gap-2 flex-wrap">
        {agents.map(a => (
          <button key={a.agent_id} onClick={() => setSelected(a.agent_id)}
            className={`px-3 py-1 rounded text-sm ${selected === a.agent_id ? "bg-indigo-600" : "bg-slate-800"}`}>
            {a.name}
          </button>
        ))}
      </div>
      {cur && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900 rounded p-4 border border-slate-800 col-span-1">
            <h3 className="font-semibold mb-2">Live State</h3>
            <div className="text-sm space-y-1">
              <div className="text-indigo-300 text-lg">{cur.name}</div>
              <div>Coords: {JSON.stringify(cur.position)}</div>
              <div>Health: {cur.health} Hunger: {cur.hunger}</div>
              <div>Inventory: {Object.keys(cur.inventory || {}).length ? Object.entries(cur.inventory).map(([k,v]) => `${k}×${v}`).join(", ") : "empty"}</div>
              <div>Hotbar slot: {cur.hotbar_slot}</div>
              <div>Activity: {cur.current_activity}</div>
              <div>Goal: {cur.current_goal}</div>
              <div className="text-amber-300">Intention: {cur.intention}</div>
              <div className="text-slate-300">Thoughts: {cur.thoughts}</div>
              {cur.alert && <div className="text-red-400">⚠ {cur.alert}</div>}
            </div>
          </div>
          <div className="bg-slate-900 rounded p-4 border border-slate-800">
            <h3 className="font-semibold mb-2">Recent Decisions</h3>
            <ul className="text-xs space-y-1 max-h-64 overflow-auto">
              {decs.map(d => <li key={d.decision_id}>{d.timestamp} — {d.current_goal}: {d.thoughts || d.reasoning_summary}</li>)}
            </ul>
          </div>
          <div className="bg-slate-900 rounded p-4 border border-slate-800">
            <h3 className="font-semibold mb-2">Action Log</h3>
            <ul className="text-xs space-y-1 max-h-64 overflow-auto">
              {acts.map(a => <li key={a.action_id}>{a.created_at} {a.action} [{a.status}] {JSON.stringify(a.result)}</li>)}
            </ul>
          </div>
        </div>
      )}
      <div className="bg-slate-900 rounded p-4 border border-slate-800">
        <h3 className="font-semibold mb-2">Memory</h3>
        <ul className="text-xs space-y-1 max-h-48 overflow-auto">
          {mems.map(m => <li key={m.memory_id}>{m.timestamp} [{m.memory_type}] {m.content}</li>)}
        </ul>
      </div>
      <div className="bg-slate-900 rounded p-4 border border-slate-800">
        <h3 className="font-semibold mb-2">All Agent Coords</h3>
        <table className="text-sm w-full">
          <tbody>
            {Object.entries(pos).map(([aid, o]: any) => (
              <tr key={aid} className="border-t border-slate-800">
                <td className="py-1">{aid}</td>
                <td>{JSON.stringify(o?.position)}</td>
                <td>{o?.biome}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
