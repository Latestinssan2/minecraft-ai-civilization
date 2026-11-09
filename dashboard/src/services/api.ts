import axios from "axios";

const base = import.meta.env.VITE_API_BASE || "http://localhost:8000";
export const api = axios.create({ baseURL: base });

export const get = (path: string, params?: any) => api.get(path, { params }).then(r => r.data);
export const post = (path: string, body?: any) => api.post(path, body).then(r => r.data);

export const endpoints = {
  health: () => get("/api/health"),
  ollamaHealth: () => get("/api/ollama/health"),
  ollamaModels: () => get("/api/ollama/models"),
  agents: () => get("/api/agents"),
  agent: (id: string) => get(`/api/agents/${id}`),
  agentMemories: (id: string) => get(`/api/agents/${id}/memories`),
  agentDecisions: (id: string) => get(`/api/agents/${id}/decisions`),
  agentActions: (id: string) => get(`/api/agents/${id}/actions`),
  messages: (params?: any) => get("/api/messages", params),
  conversations: () => get("/api/conversations"),
  projects: () => get("/api/projects"),
  events: () => get("/api/events"),
  civilization: () => get("/api/civilization"),
  relationships: (id?: string) => get("/api/relationships", id ? { agent_id: id } : {}),
  llmStats: () => get("/api/llm/stats"),
  worldPositions: () => get("/api/world/positions"),
  sendMessage: (body: any) => post("/api/messages", body),
  createProject: (body: any) => post("/api/projects", body),
  decideAgent: (id: string) => post(`/api/agents/${id}/decide`),
  decideAll: () => post("/api/agents/decide-all"),
};
