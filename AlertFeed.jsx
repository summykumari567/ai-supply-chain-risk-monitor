const SEVERITY_COLOR = {
    LOW: "var(--green)",
    MEDIUM: "var(--amber)",
    HIGH: "var(--red)",
    CRITICAL: "var(--critical)",
  };
  
  const TYPE_ICON = {
    sanctions: "◈",
    weather: "◎",
    geopolitical: "◉",
    news: "◆",
    risk_update: "⬡",
  };
  
  export default function AlertFeed({ alerts }) {
    if (alerts.length === 0) {
      return (
        <div className="card loading" style={{ minHeight: 300, color: "var(--text-dim)" }}>
          <div style={{ fontSize: 40 }}>◎</div>
          <div>Monitoring for real-time alerts...</div>
          <div style={{ fontSize: 10, color: "var(--text-dim)", marginTop: 4 }}>
            Alerts will appear here as events are detected via WebSocket
          </div>
        </div>
      );
    }
  
    return (
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <div style={{ fontSize: 10, color: "var(--text-secondary)", letterSpacing: 2 }}>
            {alerts.length} ALERT{alerts.length !== 1 ? "S" : ""} RECEIVED
          </div>
          <div style={{ display: "flex", gap: 12, fontSize: 9, color: "var(--text-dim)" }}>
            {Object.entries(SEVERITY_COLOR).map(([k, v]) => (
              <span key={k} style={{ color: v }}>■ {k}</span>
            ))}
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {alerts.map((a) => {
            const color = SEVERITY_COLOR[a.severity] || "var(--accent)";
            const icon = TYPE_ICON[a.type] || TYPE_ICON[a.event_type] || "◆";
            return (
              <div key={a.id} className="card"
                style={{ borderLeft: `4px solid ${color}`, padding: "12px 16px", display: "grid", gridTemplateColumns: "36px 1fr auto", gap: 12, alignItems: "start" }}>
                <div style={{ fontSize: 22, color, filter: `drop-shadow(0 0 6px ${color})` }}>{icon}</div>
                <div>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                    <span className={`badge badge-${a.severity || "MEDIUM"}`}>{a.severity}</span>
                    <span style={{ fontSize: 9, color: "var(--text-dim)", letterSpacing: 1 }}>
                      {(a.event_type || a.type || "").toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: 13, marginBottom: 6, lineHeight: 1.4 }}>
                    {a.description || a.data?.executive_summary?.slice(0, 120) || "Risk event detected"}
                  </div>
                  {a.affected_regions?.length > 0 && (
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {a.affected_regions.map((r) => (
                        <span key={r} style={{ fontSize: 9, color: "var(--text-secondary)", border: "1px solid var(--border)", padding: "1px 6px" }}>
                          {r}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div style={{ fontSize: 9, color: "var(--text-dim)", textAlign: "right", whiteSpace: "nowrap" }}>
                  {a.receivedAt ? new Date(a.receivedAt).toLocaleTimeString() : ""}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }