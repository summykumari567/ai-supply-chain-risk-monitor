import { useState, useEffect, useRef } from "react";
import Dashboard from "./components/Dashboard";
import SupplierGraph from "./components/SupplierGraph";
import RiskAnalysis from "./components/RiskAnalysis";
import AlertFeed from "./components/AlertFeed";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const WS_BASE = import.meta.env.VITE_WS_BASE || "ws://localhost:8000";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [alerts, setAlerts] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  // WebSocket connection for real-time alerts
  useEffect(() => {
    const connect = () => {
      wsRef.current = new WebSocket(`${WS_BASE}/ws/alerts`);

      wsRef.current.onopen = () => {
        setWsConnected(true);
        console.log("[WS] Connected to risk alert stream");
      };

      wsRef.current.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type !== "ping") {
            setAlerts((prev) => [
              { ...data, id: Date.now(), receivedAt: new Date().toISOString() },
              ...prev.slice(0, 49),
            ]);
          }
        } catch {}
      };

      wsRef.current.onclose = () => {
        setWsConnected(false);
        setTimeout(connect, 3000);
      };

      wsRef.current.onerror = () => {
        setWsConnected(false);
      };
    };

    connect();
    return () => wsRef.current?.close();
  }, []);

  const tabs = [
    { id: "dashboard", label: "Dashboard", icon: "⬡" },
    { id: "graph", label: "Supply Graph", icon: "◈" },
    { id: "analyze", label: "Risk Analysis", icon: "◉" },
    { id: "alerts", label: `Alerts ${alerts.length > 0 ? `(${alerts.length})` : ""}`, icon: "◎" },
  ];

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">⬡</span>
            <div className="logo-text">
              <span className="logo-title">SUPPLY CHAIN</span>
              <span className="logo-sub">RISK MONITOR</span>
            </div>
          </div>
        </div>
        <nav className="nav">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`nav-btn ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="nav-icon">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
        <div className="header-right">
          <div className={`ws-status ${wsConnected ? "connected" : "disconnected"}`}>
            <span className="ws-dot" />
            {wsConnected ? "LIVE" : "OFFLINE"}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        {activeTab === "dashboard" && <Dashboard apiBase={API_BASE} alerts={alerts} />}
        {activeTab === "graph" && <SupplierGraph apiBase={API_BASE} />}
        {activeTab === "analyze" && <RiskAnalysis apiBase={API_BASE} />}
        {activeTab === "alerts" && <AlertFeed alerts={alerts} />}
      </main>
    </div>
  );
}