import { NavLink, Outlet } from "react-router-dom";
import { useWebSocket } from "../services/useWebSocket";
import { useState } from "react";

const nav = [
  { to: "/", label: "Overview" },
  { to: "/agents", label: "Agents" },
  { to: "/chat", label: "Live Chat" },
  { to: "/world", label: "World" },
  { to: "/projects", label: "Projects" },
  { to: "/memories", label: "Memories" },
  { to: "/history", label: "History" },
  { to: "/live", label: "Live Monitor" },
  { to: "/settings", label: "Settings" },
];

export default function Layout() {
  const [snap, setSnap] = useState<any>(null);
  const connected = useWebSocket((d) => { if (d?.type === "snapshot") setSnap(d); });

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <aside className="w-56 border-r border-slate-800 p-4 flex flex-col gap-1">
        <h1 className="text-lg font-bold mb-3 text-indigo-400">Minecraft Civ</h1>
        <div className="text-xs mb-3 flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400" : "bg-red-400"}`} />
          {connected ? "WS connected" : "WS disconnected"}
        </div>
        {nav.map(n => (
          <NavLink key={n.to} to={n.to} end={n.to === "/"}
            className={({ isActive }) => `px-3 py-2 rounded text-sm ${isActive ? "bg-indigo-600" : "hover:bg-slate-800"}`}>
            {n.label}
          </NavLink>
        ))}
        {snap && (
          <div className="mt-auto text-xs text-slate-400">
            Agents: {snap.agents?.length ?? 0}<br/>
            Projects: {snap.projects?.length ?? 0}
          </div>
        )}
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        <Outlet context={{ snap }} />
      </main>
    </div>
  );
}
