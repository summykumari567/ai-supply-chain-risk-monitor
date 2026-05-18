import { useState, useEffect } from "react";

const RISK_COLOR = {
  LOW: "var(--green)",
  MEDIUM: "var(--amber)",
  HIGH: "var(--red)",
  CRITICAL: "var(--critical)",
};

function ScoreGauge({ score }) {
  const color = score >= 80 ? "var(--critical)" : score >= 60 ? "var(--red)" : score >= 40 ? "var(--amber)" : "var(--green)";
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: 52, fontWeight: 700, color, fontFamily: "var(--font-display)", lineHeight: 1, filter: `drop-shadow(0 0 12px ${color})` }}>
        {score}
      </div>
      <div style={{ fontSize: 10, color: "var(--text-secondary)", letterSpacing: 2, marginTop: 4 }}>GLOBAL RISK INDEX</div>
      <div className="score-bar-track" style={{ marginTop: 8, width: 120, margin: "8px auto 0" }}>
        <div className="score-bar-fill" style={{ width: `${score}%`, background: color }} />
      </div>
    </div>
  );
}

export default function Dashboard({ apiBase, alerts }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${apiBase}/dashboard`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setData(await r.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return (
    <div className="loading">
      <div className="spinner" />
      AGGREGATING INTELLIGENCE...
    </div>
  );

  if (error) return (
    <div style={{ padding: 40, textAlign: "center", color: "var(--red)" }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>◎</div>
      <div style={{ fontSize: 12, marginBottom: 16 }}>API unavailable: {error}</div>
      <button className="btn" onClick={load}>RETRY</button>
    </div>
  );

  const d = data || {};

  return (
    <div style={{ display: "grid", gap: 16, gridTemplateColumns: "240px 1fr 1fr", gridTemplateRows: "auto auto" }}>

      {/* Global Risk Score */}
      <div className="card" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16 }}>
        <ScoreGauge score={d.global_risk_index || 0} />
        <div style={{ textAlign: "center" }}>
          <div className={`badge badge-${d.risk_trend === "DETERIORATING" ? "HIGH" : d.risk_trend === "IMPROVING" ? "LOW" : "MEDIUM"}`}>
            {d.risk_trend || "STABLE"} TREND
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, width: "100%" }}>
          {[
            { label: "DISRUPTIONS", value: d.active_disruptions || 0, color: "var(--red)" },
            { label: "SUPPLIERS AT RISK", value: d.suppliers_at_risk || 0, color: "var(--amber)" },
          ].map((s) => (
            <div key={s.label} style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", padding: "8px", textAlign: "center" }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: s.color, fontFamily: "var(--font-display)" }}>{s.value}</div>
              <div style={{ fontSize: 8, color: "var(--text-secondary)", letterSpacing: 1 }}>{s.label}</div>
            </div>
          ))}
        </div>
        <button className="btn" onClick={load} style={{ width: "100%", fontSize: 10 }}>↻ REFRESH</button>
      </div>

      {/* Top Threats */}
      <div className="card">
        <div className="card-title">TOP THREATS</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {(d.top_threats || []).map((t, i) => (
            <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12, padding: "10px", background: "var(--bg-panel)", border: "1px solid var(--border)" }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text-dim)", fontFamily: "var(--font-display)", minWidth: 24 }}>
                {String(t.rank).padStart(2, "0")}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, color: "var(--text-primary)", marginBottom: 4 }}>{t.threat}</div>
                <div style={{ fontSize: 10, color: "var(--text-secondary)" }}>{t.region} — {t.impact}</div>
              </div>
              <span className={`badge badge-${t.severity}`}>{t.severity}</span>
            </div>
          ))}
          {(!d.top_threats || d.top_threats.length === 0) && (
            <div style={{ color: "var(--text-dim)", fontSize: 12, padding: 20, textAlign: "center" }}>No threat data available</div>
          )}
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="card">
        <div className="card-title">RECENT ALERTS</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {alerts.slice(0, 5).map((a) => (
            <div key={a.id} style={{ padding: "8px 12px", background: "var(--bg-panel)", border: `1px solid ${RISK_COLOR[a.severity] || "var(--border)"}22`, borderLeft: `3px solid ${RISK_COLOR[a.severity] || "var(--accent)"}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                <span style={{ fontSize: 10, color: "var(--text-secondary)" }}>{a.event_type?.toUpperCase()}</span>
                <span className={`badge badge-${a.severity || "MEDIUM"}`}>{a.severity}</span>
              </div>
              <div style={{ fontSize: 11, color: "var(--text-primary)" }}>{a.description?.slice(0, 80)}</div>
            </div>
          ))}
          {alerts.length === 0 && (
            <div style={{ color: "var(--text-dim)", fontSize: 12, padding: 20, textAlign: "center" }}>
              ◎ Monitoring for alerts...
            </div>
          )}
          {(d.recent_alerts || []).slice(0, 4).map((a, i) => (
            <div key={`api-${i}`} style={{ padding: "8px 12px", background: "var(--bg-panel)", border: "1px solid var(--border)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                <span style={{ fontSize: 10, color: "var(--text-secondary)" }}>{a.time}</span>
                <span className={`badge badge-${a.severity}`}>{a.severity}</span>
              </div>
              <div style={{ fontSize: 11 }}>{a.title}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Risk by Region */}
      <div className="card" style={{ gridColumn: "1 / -1" }}>
        <div className="card-title">RISK BY REGION</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 10 }}>
          {(d.risk_by_region || []).map((r) => {
            const color = r.risk_score >= 80 ? "var(--critical)" : r.risk_score >= 60 ? "var(--red)" : r.risk_score >= 40 ? "var(--amber)" : "var(--green)";
            return (
              <div key={r.region} style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", padding: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span style={{ fontSize: 11, color: "var(--text-primary)" }}>{r.region}</span>
                  <span style={{ fontSize: 16, fontWeight: 700, color, fontFamily: "var(--font-display)" }}>{r.risk_score}</span>
                </div>
                <div className="score-bar-track">
                  <div className="score-bar-fill" style={{ width: `${r.risk_score}%`, background: color }} />
                </div>
                <div style={{ fontSize: 9, color: "var(--text-secondary)", marginTop: 6 }}>{r.primary_risk}</div>
              </div>
            );
          })}
        </div>
        <div style={{ marginTop: 12, fontSize: 9, color: "var(--text-dim)" }}>
          Generated at: {d.generated_at || "—"} · {d.summary?.slice(0, 120)}
        </div>
      </div>
    </div>
  );
}