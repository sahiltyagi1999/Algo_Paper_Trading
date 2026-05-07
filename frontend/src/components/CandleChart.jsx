import { useEffect, useRef } from "react";

export default function CandleChart({ data, instrument }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!data?.length) return;
    const canvas = ref.current;
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.offsetWidth || canvas.parentElement?.offsetWidth || 900;
    const H = 340;
    canvas.width = W * dpr; canvas.height = H * dpr;
    canvas.style.width = W + "px"; canvas.style.height = H + "px";
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, W, H);

    const ML=72, MR=16, MT=16, MB=28, CW=W-ML-MR, CH=H-MT-MB;
    const allH = data.map(d => d.h), allL = data.map(d => d.l);
    const allE = data.flatMap(d => [d.ema8, d.ema30]);
    const minP = Math.min(...allL, ...allE) - 15;
    const maxP = Math.max(...allH, ...allE) + 15;
    const priceH = maxP - minP;
    const px = p => MT + CH * (1 - (p - minP) / priceH);
    const cx = i => ML + (i + 0.5) * (CW / data.length);

    ctx.strokeStyle = "#21262d"; ctx.lineWidth = 1;
    for (let i = 0; i <= 6; i++) {
      const p = minP + (priceH / 6) * i, y = px(p);
      ctx.beginPath(); ctx.moveTo(ML, y); ctx.lineTo(ML + CW, y); ctx.stroke();
      ctx.fillStyle = "#8b949e"; ctx.font = "10px sans-serif"; ctx.textAlign = "right";
      ctx.fillText("₹" + Math.round(p).toLocaleString("en-IN"), ML - 4, y + 3);
    }

    const evN = Math.ceil(data.length / 10);
    ctx.fillStyle = "#8b949e"; ctx.font = "10px sans-serif"; ctx.textAlign = "center";
    data.forEach((d, i) => {
      if (i % evN === 0 || i === data.length - 1) {
        ctx.fillText(d.t, cx(i), H - MB + 14);
        ctx.beginPath(); ctx.strokeStyle = "#30363d"; ctx.lineWidth = 0.5;
        ctx.moveTo(cx(i), MT); ctx.lineTo(cx(i), MT + CH); ctx.stroke();
      }
    });

    const barW = Math.max(Math.floor(CW / data.length * 0.6), 2);
    data.forEach((d, i) => {
      const x = cx(i), bull = d.c >= d.o, color = bull ? "#3fb950" : "#f85149";
      ctx.strokeStyle = color; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, px(d.h)); ctx.lineTo(x, px(d.l)); ctx.stroke();
      const bTop = Math.min(px(d.o), px(d.c));
      const bH = Math.max(Math.abs(px(d.c) - px(d.o)), 1.5);
      ctx.fillStyle = color;
      ctx.fillRect(x - barW / 2, bTop, barW, bH);
    });

    ctx.beginPath(); ctx.strokeStyle = "#f0883e"; ctx.lineWidth = 1.5;
    data.forEach((d, i) => i === 0 ? ctx.moveTo(cx(i), px(d.ema8)) : ctx.lineTo(cx(i), px(d.ema8)));
    ctx.stroke();

    ctx.beginPath(); ctx.strokeStyle = "#58a6ff"; ctx.lineWidth = 1.5;
    data.forEach((d, i) => i === 0 ? ctx.moveTo(cx(i), px(d.ema30)) : ctx.lineTo(cx(i), px(d.ema30)));
    ctx.stroke();
  }, [data]);

  const last = data?.[data.length - 1];

  return (
    <div className="chart-card" style={{ marginBottom: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div className="chart-title">{instrument || "NIFTY"} Live — 5 Min Candles (EMA 8 &amp; EMA 30)</div>
        <div style={{ display: "flex", gap: 16, fontSize: 11, color: "#8b949e" }}>
          <span style={{ color: "#f0883e" }}>▬ EMA 8</span>
          <span style={{ color: "#58a6ff" }}>▬ EMA 30</span>
          <span style={{ color: "#3fb950" }}>▮ Bullish</span>
          <span style={{ color: "#f85149" }}>▮ Bearish</span>
        </div>
      </div>
      <div style={{ position: "relative", height: 340, width: "100%" }}>
        <canvas ref={ref} style={{ display: "block", width: "100%", height: 340 }} />
      </div>
      {last && (
        <div style={{ fontSize: 11, color: "#8b949e", marginTop: 8, textAlign: "right" }}>
          Last: <b>{last.t}</b> &nbsp;|&nbsp;
          O:<b>{last.o}</b> H:<b style={{ color: "#3fb950" }}>{last.h}</b> L:<b style={{ color: "#f85149" }}>{last.l}</b> C:<b style={{ color: "#58a6ff" }}>{last.c}</b> &nbsp;|&nbsp;
          EMA8:<b style={{ color: "#f0883e" }}>{last.ema8}</b> EMA30:<b style={{ color: "#58a6ff" }}>{last.ema30}</b>
        </div>
      )}
    </div>
  );
}
