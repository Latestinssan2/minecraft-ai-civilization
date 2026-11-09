import { useEffect, useState } from "react";
import * as api from "../services/api";

export default function Chat() {
  const [msgs, setMsgs] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [sender, setSender] = useState("agent_01");
  const [receiver, setReceiver] = useState("broadcast");
  const [content, setContent] = useState("");
  const load = () => {
    api.endpoints.messages({ limit: 200 }).then(setMsgs).catch(() => {});
  };
  useEffect(() => { load(); api.endpoints.agents().then(setAgents); const t = setInterval(load, 4000); return () => clearInterval(t); }, []);
  const send = async () => {
    if (!content.trim()) return;
    await api.endpoints.sendMessage({ sender, receiver, content });
    setContent("");
    load();
  };
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Live Chat</h2>
      <div className="flex gap-2">
        <select value={sender} onChange={e => setSender(e.target.value)} className="bg-slate-800 p-2 rounded">
          {agents.map(a => <option key={a.agent_id} value={a.agent_id}>{a.name}</option>)}
        </select>
        <select value={receiver} onChange={e => setReceiver(e.target.value)} className="bg-slate-800 p-2 rounded">
          <option value="broadcast">broadcast</option>
          {agents.map(a => <option key={a.agent_id} value={a.agent_id}>{a.name}</option>)}
        </select>
        <input value={content} onChange={e => setContent(e.target.value)} className="flex-1 bg-slate-800 p-2 rounded" placeholder="Message..." onKeyDown={e => e.key === "Enter" && send()} />
        <button onClick={send} className="bg-indigo-600 px-4 rounded">Send</button>
      </div>
      <div className="bg-slate-900 rounded p-4 border border-slate-800 max-h-[60vh] overflow-auto space-y-2">
        {msgs.map(m => (
          <div key={m.message_id} className="text-sm">
            <span className="text-indigo-300 font-semibold">{m.sender}</span>
            <span className="text-slate-500"> → {m.receiver}</span>
            <span className="text-slate-400 text-xs ml-2">{m.timestamp}</span>
            <div className="text-slate-200">{m.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
