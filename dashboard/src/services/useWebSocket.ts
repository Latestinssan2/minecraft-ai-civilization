import { useEffect, useRef, useState } from "react";

const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8001";

export function useWebSocket(onMessage: (data: any) => void) {
  const [connected, setConnected] = useState(false);
  const onRef = useRef(onMessage);
  onRef.current = onMessage;
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: number;
    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);
        ws.onopen = () => setConnected(true);
        ws.onclose = () => { setConnected(false); reconnectTimer = window.setTimeout(connect, 3000); };
        ws.onerror = () => { try { ws?.close(); } catch {} };
        ws.onmessage = (ev) => {
          try { onRef.current(JSON.parse(ev.data)); } catch { onRef.current(ev.data); }
        };
      } catch { reconnectTimer = window.setTimeout(connect, 3000); }
    };
    connect();
    return () => { if (reconnectTimer) clearTimeout(reconnectTimer); ws?.close(); };
  }, []);
  return connected;
}
