import { useState } from "react";

const SEVERITY_ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

export default function RiskAnalysis({ apiBase }) {
  const [form, setForm] = useState({ supplier_name: "", country: "", category: "", include_alternatives: true });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await fetch(`${apiBase}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setResult(await r.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = (s) => s >= 80 ? "var(--critical)" : s >= 60 ? "var(--red)" : s >= 40 ? "var(--amber)" : "var(--green)";

  return (
    <div style={{ display: "grid", gap: 16, gridTemplateColumns: "300px 1fr" }}>

      {/* Query Form */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div className="card">
          <div className="card-title">ANALYSIS PARAMETERS</div>
          {[
            { key: "supplier_name", label: "SUPPLIER NAME", placeholder: "e.g. TSMC" },
            { key: "country", label: "COUNTRY / REGION", placeholder: "e.g. Taiwan" },
            { key: "category", label: "CATEGORY", placeholder: "e.g. semiconductors" },
          ].map(({ key, label, placeholder }) => (
            <div key={key} style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 9, color: "var(--text-secondary)", letterSpacing: 2, marginBottom: 6 }}>{label}</div>
              <input
                className="input"
                placeholder={placeholder}
                value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              />
            </div>
          ))}
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "var(--text-secondary)", cursor: "pointer", marginBottom: 16 }}>
            <input
              type="checkbox"
              checked={form.include_alternatives}
              onChange={(e) => setForm({ ...form, include_alternatives: e.target.checked })}
              style={{ accentColor: "var(--accent)" }}
            />
            INCLUDE ALTERNATIVE SUPPLIERS
          </label>
          <button className="btn btn-primary" onClick={analyze} disabled={loading} style={{ width: "100%" }}>
            {loading ? "ANALYZING..." : "▶ RUN ANALYSIS"}
          </button>
        </div>

        {/* Quick presets */}
        <div className="card">
          <div className="card-title">QUICK PRESETS</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {[
              { label: "TSMC / Taiwan / Semiconductors", supplier_name: "TSMC", country: "Taiwan", category: "semiconductors" },
              { label: "Foxconn / China / Assembly", supplier_name: "Foxconn", country: "China", category: "electronics assembly" },
              { label: "Global Semiconductor Risk", supplier_name: "", country: "", category: "semiconductors" },
              { label: "Middle East Logistics", supplier_name: "", country: "Middle East", category: "logistics" },
            ].map((p) => (
              <button key={p.label} className="btn" onClick={() => setForm({ ...form, ...p })}
                style={{ fontSize: 9, textAlign: "left", padding: "6px 10px" }}>
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      <div>
        {loading && (
          <div className="loading card">
            <div className="spinner" />
            COLLECTING INTELLIGENCE · ANALYZING RISKS · GENERATING REPORT...
          </div>
        )}

        {error && (
          <div className="card" style={{ borderColor: "var(--red)", color: "var(--red)", textAlign: "center", padding: 40 }}>
            ◎ Error: {error}
          </div>
        )}

        {result && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>

            {/* Risk Score Header */}
            <div className="card" style={{ display: "flex", alignItems: "center", gap: 24 }}>
              <div style={{ textAlign: "center", minWidth: 100 }}>
                <div style={{ fontSize: 56, fontWeight: 700, fontFamily: "var(--font-display)", color: scoreColor(result.overall_risk_score), filter: `drop-shadow(0 0 12px ${scoreColor(result.overall_risk_score)})` }}>
                  {result.overall_risk_score}
                </div>
                <div style={{ fontSize: 9, color: "var(--text-secondary)", letterSpacing: 2 }}>RISK SCORE</div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
                  <span className={`badge badge-${result.risk_level}`}>{result.risk_level}</span>
                  <span style={{ fontSize: 10, color: "var(--text-secondary)" }}>Confidence: {(result.confidence * 100).toFixed(0)}%</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 10 }}>
                  {[
                    { label: "30-DAY DISRUPTION PROB.", value: `${(result.disruption_probability_30d * 100).toFixed(0)}%` },
                    { label: "90-DAY DISRUPTION PROB.", value: `${(result.disruption_probability_90d * 100).toFixed(0)}%` },
                  ].map((s) => (
                    <div key={s.label} style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", padding: "6px 10px" }}>
                      <div style={{ fontSize: 8, color: "var(--text-secondary)", letterSpacing: 1 }}>{s.label}</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: "var(--accent)", fontFamily: "var(--font-display)" }}>{s.value}</div>
                    </div>
                  ))}
                </div>
                <div style={{ fontSize: 11, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                  {result.executive_summary?.slice(0, 200)}...
                </div>
              </div>
            </div>

            {/* Risk Factors */}
            <div className="card">
              <div className="card-title">RISK FACTORS</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {[...(result.risk_factors || [])].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]).map((f, i) => (
                  <div key={i} style={{ padding: "10px 12px", background: "var(--bg-panel)", border: "1px solid var(--border)", display: "grid", gridTemplateColumns: "1fr auto", gap: 8 }}>
                    <div>
                      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                        <span className={`badge badge-${f.severity}`}>{f.severity}</span>
                        <span style={{ fontSize: 9, color: "var(--text-dim)", letterSpacing: 1 }}>{f.category?.toUpperCase()}</span>
                      </div>
                      <div style={{ fontSize: 12, marginBottom: 3 }}>{f.title}</div>
                      <div style={{ fontSize: 10, color: "var(--text-secondary)" }}>{f.description?.slice(0, 100)}</div>
                    </div>
                    <div style={{ textAlign: "right", minWidth: 80 }}>
                      <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "var(--font-display)", color: "var(--amber)" }}>{(f.probability * 100).toFixed(0)}%</div>
                      <div style={{ fontSize: 8, color: "var(--text-dim)" }}>PROBABILITY</div>
                      <div style={{ fontSize: 10, color: "var(--text-secondary)", marginTop: 4 }}>{f.estimated_impact_days}d impact</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Alternative Suppliers */}
            {result.alternative_suppliers?.length > 0 && (
              <div className="card">
                <div className="card-title">ALTERNATIVE SUPPLIERS</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 10 }}>
                  {result.alternative_suppliers.map((s, i) => (
                    <div key={i} style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", padding: 12 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                        <span style={{ fontSize: 12, fontWeight: 600 }}>{s.name}</span>
                        <span style={{ fontSize: 16, fontWeight: 700, fontFamily: "var(--font-display)", color: scoreColor(s.risk_score) }}>{s.risk_score}</span>
                      </div>
                      <div style={{ fontSize: 10, color: "var(--text-secondary)", marginBottom: 6 }}>{s.country}</div>
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 6 }}>
                        <span className={`badge badge-${s.capacity_match === "FULL" ? "LOW" : s.capacity_match === "PARTIAL" ? "MEDIUM" : "HIGH"}`}>{s.capacity_match}</span>
                        <span style={{ fontSize: 9, color: "var(--text-secondary)" }}>{s.lead_time_days}d lead time</span>
                      </div>
                      <div style={{ fontSize: 9, color: "var(--text-dim)", lineHeight: 1.5 }}>{s.rationale?.slice(0, 80)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {result.recommendations?.length > 0 && (
              <div className="card">
                <div className="card-title">RECOMMENDATIONS</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {result.recommendations.map((r, i) => (
                    <div key={i} style={{ padding: "10px 14px", background: "var(--bg-panel)", border: "1px solid var(--border)", borderLeft: `3px solid ${r.priority === "IMMEDIATE" ? "var(--critical)" : r.priority === "SHORT_TERM" ? "var(--amber)" : "var(--accent)"}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <span className={`badge badge-${r.priority === "IMMEDIATE" ? "CRITICAL" : r.priority === "SHORT_TERM" ? "MEDIUM" : "LOW"}`}>{r.priority}</span>
                        {r.estimated_cost_usd && <span style={{ fontSize: 10, color: "var(--text-secondary)" }}>${r.estimated_cost_usd.toLocaleString()}</span>}
                      </div>
                      <div style={{ fontSize: 12, marginBottom: 3 }}>{r.action}</div>
                      <div style={{ fontSize: 10, color: "var(--text-secondary)" }}>{r.expected_outcome}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!result && !loading && !error && (
          <div className="card loading" style={{ color: "var(--text-dim)" }}>
            <div style={{ fontSize: 32 }}>◉</div>
            Configure parameters and run analysis
          </div>
        )}
      </div>
    </div>
  );
}