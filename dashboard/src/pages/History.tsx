import { useEffect, useState } from "react";
import * as api from "../services/api";

export default function History() {
  const [events, setEvents] = useState<any[]>([]);
  useEffect(() => { const load = () => api.endpoints.events().then(setEvents).catch(() => {}); load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, []);
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">History Timeline</h2>
      <div className="bg-slate-900 rounded p-4 border border-slate-800 max-h-[70vh] overflow-auto">
        <ul className="space-y-2">
          {events.map(e => (
            <li key={e.id} className="text-sm border-l-2 border-indigo-500 pl-3">
              <div className="text-xs text-slate-400">{e.timestamp} · {e.event_type}</div>
              <div>{e.description}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
