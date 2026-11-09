import { useEffect, useState } from "react";
import * as api from "../services/api";

export default function World() {
  const [pos, setPos] = useState<any>({});
  const load = () => api.endpoints.worldPositions().then(setPos).catch(() => {});
  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, []);
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">World Map (coordinate-based)</h2>
      <div className="bg-slate-900 rounded p-4 border border-slate-800">
        <table className="text-sm w-full">
          <thead><tr><th className="text-left">Agent</th><th>Position</th><th>Biome</th></tr></thead>
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
