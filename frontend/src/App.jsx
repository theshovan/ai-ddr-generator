import { useState, useRef, useCallback } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

function UploadZone({ label, sublabel, file, onChange }) {
  const ref = useRef();
  const [drag, setDrag] = useState(false);

  const onDrop = useCallback(e => {
    e.preventDefault(); setDrag(false);
    const f = e.dataTransfer.files[0];
    if (f?.type === "application/pdf") onChange(f);
  }, [onChange]);

  return (
    <div
      onClick={() => ref.current.click()}
      onDragOver={e => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      style={{
        border: `1.5px dashed ${drag ? "#6366f1" : file ? "#22c55e" : "#334155"}`,
        borderRadius: 12,
        padding: "28px 20px",
        cursor: "pointer",
        background: drag ? "#1e1b4b" : file ? "#052e16" : "#0f172a",
        transition: "all .2s",
        textAlign: "center",
        userSelect: "none",
      }}
    >
      <input ref={ref} type="file" accept=".pdf" style={{ display: "none" }}
        onChange={e => e.target.files[0] && onChange(e.target.files[0])} />

      <div style={{ fontSize: 26, marginBottom: 10 }}>
        {file ? "✓" : sublabel === "Thermal" ? "🌡️" : "📋"}
      </div>
      <div style={{ fontSize: 12, fontWeight: 700, color: file ? "#4ade80" : "#94a3b8", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 4 }}>
        {label}
      </div>
      {file
        ? <div style={{ fontSize: 11, color: "#4ade80", wordBreak: "break-all" }}>{file.name}</div>
        : <div style={{ fontSize: 11, color: "#475569" }}>Drop PDF or click to browse</div>
      }
      {file && (
        <button onClick={e => { e.stopPropagation(); onChange(null); }}
          style={{ marginTop: 8, fontSize: 10, color: "#f87171", background: "none", border: "none", cursor: "pointer", letterSpacing: 0.3 }}>
          REMOVE
        </button>
      )}
    </div>
  );
}

const STEPS = [
  { id: "extract", label: "Extracting content" },
  { id: "ai",      label: "AI analysis"        },
  { id: "build",   label: "Building PDF"        },
  { id: "done",    label: "Complete"            },
];

function ProgressBar({ active }) {
  const [step, setStep] = useState(0);
  const [pct, setPct]   = useState(0);

  // Drive progress automatically
  useState(() => {
    if (!active) return;
    setStep(0); setPct(0);
    const schedule = [
      [300,  () => { setStep(0); setPct(18); }],
      [1200, () => { setStep(1); setPct(42); }],
      [2800, () => { setStep(2); setPct(75); }],
      [4500, () => { setStep(3); setPct(92); }],
    ];
    const timers = schedule.map(([ms, fn]) => setTimeout(fn, ms));
    return () => timers.forEach(clearTimeout);
  }, [active]);

  if (!active) return null;

  return (
    <div style={{ marginTop: 28 }}>
      {/* Bar track */}
      <div style={{ height: 3, background: "#1e293b", borderRadius: 99, overflow: "hidden", marginBottom: 20 }}>
        <div style={{
          height: "100%",
          width: `${pct}%`,
          background: "linear-gradient(90deg, #6366f1, #a855f7)",
          borderRadius: 99,
          transition: "width 0.8s cubic-bezier(.4,0,.2,1)",
        }} />
      </div>

      {/* Step indicators */}
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        {STEPS.map((s, i) => {
          const done    = i < step;
          const current = i === step;
          return (
            <div key={s.id} style={{ textAlign: "center", flex: 1 }}>
              <div style={{
                width: 28, height: 28, borderRadius: "50%",
                margin: "0 auto 6px",
                background: done ? "#6366f1" : current ? "#1e1b4b" : "#0f172a",
                border: `1.5px solid ${done || current ? "#6366f1" : "#1e293b"}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 11, color: done ? "white" : current ? "#818cf8" : "#334155",
                fontWeight: 700,
                boxShadow: current ? "0 0 12px #6366f180" : "none",
                transition: "all .3s",
              }}>
                {done ? "✓" : i + 1}
              </div>
              <div style={{ fontSize: 10, color: done || current ? "#94a3b8" : "#334155", letterSpacing: 0.3 }}>
                {s.label}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function App() {
  const [insp,  setInsp]  = useState(null);
  const [therm, setTherm] = useState(null);
  const [state, setState] = useState("idle"); // idle | loading | done | error
  const [error, setError] = useState("");
  const [pdfUrl, setPdfUrl] = useState(null);

  const ready = insp && therm;

  const generate = async () => {
    if (!ready || state === "loading") return;
    setState("loading"); setError(""); setPdfUrl(null);

    const form = new FormData();
    form.append("inspection_report", insp);
    form.append("thermal_report", therm);

    try {
      const res = await fetch(`${API}/generate`, { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Server error");
      }
      const blob = await res.blob();
      setPdfUrl(URL.createObjectURL(blob));
      setState("done");
    } catch (e) {
      setError(e.message);
      setState("error");
    }
  };

  const reset = () => { setState("idle"); setInsp(null); setTherm(null); setPdfUrl(null); setError(""); };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#020817",
      fontFamily: "'Inter', -apple-system, sans-serif",
      color: "#e2e8f0",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 99px; }
      `}</style>

      {/* Nav */}
      <nav style={{
        borderBottom: "1px solid #1e293b",
        padding: "0 32px",
        height: 52,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        position: "sticky", top: 0, background: "#020817", zIndex: 10,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 26, height: 26, borderRadius: 6, background: "linear-gradient(135deg,#6366f1,#a855f7)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13 }}>⚡</div>
          <span style={{ fontWeight: 700, fontSize: 14, letterSpacing: -0.3 }}>AI DDR GENERATION</span>
        </div>
       
      </nav>

      <main style={{ maxWidth: 520, margin: "0 auto", padding: "56px 24px 80px" }}>

        {/* Hero */}
        <div style={{ marginBottom: 40 }}>
          <h1 style={{ fontSize: 30, fontWeight: 700, margin: "0 0 8px", letterSpacing: -0.8, lineHeight: 1.2 }}>
            Generate Diagnostic<br />
            <span style={{ background: "linear-gradient(90deg,#6366f1,#a855f7)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              Report
            </span>
          </h1>
          <p style={{ fontSize: 13, color: "#64748b", margin: 0 }}>
            Upload inspection + thermal PDFs. AI merges both into a structured DDR.
          </p>
        </div>

        {/* Upload zones */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
          <UploadZone label="Inspection Report" sublabel="Inspection" file={insp}  onChange={setInsp}  />
          <UploadZone label="Thermal Report"    sublabel="Thermal"    file={therm} onChange={setTherm} />
        </div>

        {/* File size info */}
        {(insp || therm) && (
          <div style={{ display: "flex", gap: 12, marginBottom: 20, fontSize: 11, color: "#475569" }}>
            {insp  && <span>📋 {(insp.size  / 1024).toFixed(1)} KB</span>}
            {therm && <span>🌡️ {(therm.size / 1024).toFixed(1)} KB</span>}
          </div>
        )}

        {/* Generate button */}
        <button onClick={generate} disabled={!ready || state === "loading"}
          style={{
            width: "100%", padding: "13px",
            background: ready && state !== "loading"
              ? "linear-gradient(135deg, #6366f1, #a855f7)"
              : "#0f172a",
            color: ready && state !== "loading" ? "white" : "#334155",
            border: `1px solid ${ready ? "transparent" : "#1e293b"}`,
            borderRadius: 10, fontSize: 14, fontWeight: 600,
            cursor: ready && state !== "loading" ? "pointer" : "not-allowed",
            transition: "all .2s",
            letterSpacing: 0.2,
            boxShadow: ready && state !== "loading" ? "0 4px 24px #6366f140" : "none",
          }}>
          {state === "loading" ? "Generating…" : "Generate Report →"}
        </button>

        {/* Progress */}
        <ProgressBar active={state === "loading"} />

        {/* Error */}
        {state === "error" && (
          <div style={{ marginTop: 20, padding: "14px 16px", background: "#1c0a0a", borderRadius: 10, fontSize: 13, color: "#f87171", border: "1px solid #7f1d1d" }}>
            <b>Error</b><br />{error}
          </div>
        )}

        {/* Result */}
        {state === "done" && pdfUrl && (
          <div style={{ marginTop: 28 }}>
            <div style={{
              padding: "14px 16px",
              background: "#052e16", border: "1px solid #166534",
              borderRadius: 10, display: "flex", alignItems: "center",
              justifyContent: "space-between", marginBottom: 14,
            }}>
              <span style={{ fontSize: 13, color: "#4ade80", fontWeight: 600 }}>✓ Report ready</span>
              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <a href={pdfUrl} download="DDR_Report.pdf"
                  style={{ fontSize: 12, color: "#818cf8", fontWeight: 600, textDecoration: "none", background: "#1e1b4b", padding: "5px 12px", borderRadius: 6 }}>
                  ↓ Download
                </a>
                <button onClick={reset}
                  style={{ fontSize: 12, color: "#64748b", background: "none", border: "none", cursor: "pointer" }}>
                  Reset
                </button>
              </div>
            </div>

            <iframe src={pdfUrl} title="DignoSite"
              style={{ width: "100%", height: 560, border: "1px solid #1e293b", borderRadius: 10, background: "#fff" }} />
          </div>
        )}
      </main>
    </div>
  );
}