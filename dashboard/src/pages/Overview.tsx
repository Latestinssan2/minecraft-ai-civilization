import { useOutletContext } from "react-router-dom";
import { useEffect, useState } from "react";
import * as api from "../services/api";

export default function Overview() {
  const { snap } = useOutletContext<any>() || {};
  const [civ, setCiv] = useState<any>(null);
  const [ollama, setOllama] = useState<any>(null);
  useEffect(() => { api.endpoints.civilization().then(setCiv).catch(() => {}); api.endpoints.ollamaHealth().then(setOllama).catch(() => {}); }, []);
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Civilization Overview</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          ["Civilization", civ?.name ?? "—"],
          ["Agents", civ?.agent_count ?? 0],
          ["Projects", civ?.project_count ?? 0],
          ["Completed", civ?.completed_projects ?? 0],
        ].map(([k, v]) => (
          <div key={k} className="bg-slate-900 rounded p-4 border border-slate-800">
            <div className="text-xs text-slate-400">{k}</div>
            <div className="text-xl font-semibold">{v}</div>
          </div>
        ))}
      </div>
      <div className="bg-slate-900 rounded p-4 border border-slate-800">
        <h3 className="font-semibold mb-2">Ollama Status</h3>
        <pre className="text-xs text-slate-300 whitespace-pre-wrap">{JSON.stringify(ollama, null, 2)}</pre>
      </div>
      <div className="bg-slate-900 rounded p-4 border border-slate-800">
        <h3 className="font-semibold mb-2">Recent Events</h3>
        <ul className="text-sm space-y-1">
          {(snap?.events || []).map((e: any, i: number) => (
            <li key={i} className="text-slate-300">{e.timestamp} — {e.description}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
