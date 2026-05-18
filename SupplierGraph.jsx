import { useState, useEffect } from "react";

// ── Supply Chain Graph Visualization ──────────────────────────────────────────

export default function SupplierGraph({ apiBase }) {
  const [graph, setGraph] = useState(null);
  const [suppliers, setSuppliers] = useState([]);
  const [form, setForm] = useState({ name: "", country: "", category: "", tier: 1 });
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);
  const [tab, setTab] = useState("graph");

  const loadGraph = async () => {
    setLoading(true);
    try {
      const [g, s] = await Promise.all([
        fetch(`${apiBase}/graph`).then((r) => r.json()),
        fetch(`${apiBase}/suppliers`).then((r) => r.json()),
      ]);
      setGraph(g);
      setSuppliers(Array.isArray(s) ? s : []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const addSupplier = async () => {
    if (!form.name || !form.country || !form.category) return;
    setAdding(true);
    try {
      await fetch(`${apiBase}/suppliers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      setForm({ name: "", country: "", category: "", tier: 1 });
      await loadGraph();
    } catch (e) {
      console.error(e);
    } finally {
      setAdding(false);
    }
  };

  useEffect(() => { loadGraph(); }, []);

  const TIER_COLOR = { 1: "var(--accent)", 2: "var(--amber)", 3: "var(--text-secondary)" };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", gap: 8 }}>
        {["graph", "suppliers", "add"].map((t) => (
          <button key={t} className={`btn ${tab === t ? "btn-primary" : ""}`} onClick={() => setTab(t)} style={{ fontSize: 10 }}>
            {t === "graph" ? "◈ GRAPH VIEW" : t === "suppliers" ? "☰ SUPPLIER LIST" : "+ ADD SUPPLIER"}
          </button>
        ))}
        <button className="btn" onClick={loadGraph} style={{ marginLeft: "auto", fontSize: 10 }}>↻ REFRESH</button>
      </div>

      {tab === "graph" && (
        <div className="card">
          <div className="card-title">SUPPLY CHAIN GRAPH</div>
          {loading ? (
            <div className="loading"><div className="spinner" />LOADING GRAPH...</div>
          ) : graph ? (
            <div>
              {/* Simple SVG graph */}
              <svg width="100%" height="400" style={{ background: "var(--bg-panel)", border: "1px solid var(--border)" }}>
                {graph.edges?.map((e, i) => {
                  const srcIdx = graph.nodes?.findIndex((n) => n.id === e.source) ?? -1;
                  const tgtIdx = graph.nodes?.findIndex((n) => n.id === e.target) ?? -1;
                  if (srcIdx < 0 || tgtIdx < 0) return null;
                  const cols = Math.ceil(Math.sqrt(graph.nodes?.length || 1));
                  const sx = ((srcIdx % cols) + 0.5) / cols * 100;
                  const sy = (Math.floor(srcIdx / cols) + 0.5) / Math.ceil((graph.nodes?.length || 1) / cols) * 100;
                  const tx = ((tgtIdx % cols) + 0.5) / cols * 100;
                  const ty = (Math.floor(tgtIdx / cols) + 0.5) / Math.ceil((graph.nodes?.length || 1) / cols) * 100;
                  return (
                    <line key={i}
                      x1={`${sx}%`} y1={`${sy}%`} x2={`${tx}%`} y2={`${ty}%`}
                      stroke={e.type === "ALTERNATIVE_FOR" ? "var(--green)" : "var(--border-bright)"}
                      strokeWidth={e.type === "ALTERNATIVE_FOR" ? 2 : 1}
                      strokeDasharray={e.type === "ALTERNATIVE_FOR" ? "4 4" : "none"}
                      opacity={0.6}
                    />
                  );
                })}
                {graph.nodes?.map((n, i) => {
                  const cols = Math.ceil(Math.sqrt(graph.nodes?.length || 1));
                  const x = ((i % cols) + 0.5) / cols * 100;
                  const y = (Math.floor(i / cols) + 0.5) / Math.ceil((graph.nodes?.length || 1) / cols) * 100;
                  const color = TIER_COLOR[n.tier] || "var(--text-secondary)";
                  return (
                    <g key={n.id}>
                      <circle cx={`${x}%`} cy={`${y}%`} r="18" fill="var(--bg-card)" stroke={color} strokeWidth="2" />
                      <text x={`${x}%`} y={`${y}%`} textAnchor="middle" dy="4" fill={color} fontSize="9" fontFamily="var(--font-mono)">
                        {(n.id || "").slice(0, 6)}
                      </text>
                      <text x={`${x}%`} y={`${y}%`} textAnchor="middle" dy="30" fill="var(--text-secondary)" fontSize="7" fontFamily="var(--font-mono)">
                        {n.country}
                      </text>
                    </g>
                  );
                })}
              </svg>
              <div style={{ display: "flex", gap: 16, marginTop: 12, fontSize: 10, color: "var(--text-secondary)" }}>
                <span><span style={{ color: "var(--accent)" }}>──</span> SUPPLIES</span>
                <span><span style={{ color: "var(--green)" }}>- -</span> ALTERNATIVE FOR</span>
                <span>Tier: <span style={{ color: "var(--accent)" }}>1</span> | <span style={{ color: "var(--amber)" }}>2</span> | <span style={{ color: "var(--text-secondary)" }}>3</span></span>
              </div>
            </div>
          ) : (
            <div style={{ color: "var(--text-dim)", textAlign: "center", padding: 40 }}>No graph data. Add suppliers to begin.</div>
          )}
        </div>
      )}

      {tab === "suppliers" && (
        <div className="card">
          <div className="card-title">SUPPLIER REGISTRY ({suppliers.length})</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 8 }}>
            {suppliers.map((s, i) => (
              <div key={i} style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", padding: 12 }}>
                <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{s.name}</div>
                <div style={{ fontSize: 10, color: "var(--text-secondary)", marginBottom: 6 }}>{s.country} · {s.category}</div>
                <span style={{ fontSize: 9, color: TIER_COLOR[s.tier], border: `1px solid ${TIER_COLOR[s.tier]}`, padding: "1px 6px" }}>
                  TIER {s.tier}
                </span>
              </div>
            ))}
            {suppliers.length === 0 && (
              <div style={{ color: "var(--text-dim)", fontSize: 12, padding: 20 }}>No suppliers registered yet.</div>
            )}
          </div>
        </div>
      )}

      {tab === "add" && (
        <div className="card" style={{ maxWidth: 400 }}>
          <div className="card-title">REGISTER SUPPLIER</div>
          {[
            { key: "name", label: "SUPPLIER NAME", placeholder: "e.g. TSMC" },
            { key: "country", label: "COUNTRY", placeholder: "e.g. Taiwan" },
            { key: "category", label: "CATEGORY", placeholder: "e.g. semiconductors" },
          ].map(({ key, label, placeholder }) => (
            <div key={key} style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 9, color: "var(--text-secondary)", letterSpacing: 2, marginBottom: 6 }}>{label}</div>
              <input className="input" placeholder={placeholder} value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
            </div>
          ))}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 9, color: "var(--text-secondary)", letterSpacing: 2, marginBottom: 6 }}>TIER</div>
            <select className="input" value={form.tier} onChange={(e) => setForm({ ...form, tier: Number(e.target.value) })}
              style={{ background: "var(--bg-panel)" }}>
              <option value={1}>Tier 1 — Direct Supplier</option>
              <option value={2}>Tier 2 — Sub-Supplier</option>
              <option value={3}>Tier 3 — Raw Materials</option>
            </select>
          </div>
          <button className="btn btn-primary" onClick={addSupplier} disabled={adding || !form.name} style={{ width: "100%" }}>
            {adding ? "ADDING..." : "+ ADD SUPPLIER"}
          </button>
        </div>
      )}
    </div>
  );
}