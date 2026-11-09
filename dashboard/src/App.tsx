import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import Agents from "./pages/Agents";
import AgentProfile from "./pages/AgentProfile";
import Chat from "./pages/Chat";
import World from "./pages/World";
import Projects from "./pages/Projects";
import Memories from "./pages/Memories";
import History from "./pages/History";
import Settings from "./pages/Settings";
import LiveMonitor from "./pages/LiveMonitor";
import Templates from "./pages/Templates";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="agents" element={<Agents />} />
          <Route path="agents/:id" element={<AgentProfile />} />
          <Route path="chat" element={<Chat />} />
          <Route path="world" element={<World />} />
          <Route path="projects" element={<Projects />} />
          <Route path="memories" element={<Memories />} />
          <Route path="history" element={<History />} />
          <Route path="settings" element={<Settings />} />
          <Route path="live" element={<LiveMonitor />} />
          <Route path="templates" element={<Templates />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
