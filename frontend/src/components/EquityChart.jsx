import { useEffect, useRef } from "react";
import { Chart, registerables } from "chart.js";
Chart.register(...registerables);

export default function EquityChart({ data, title }) {
  const ref = useRef(null);
  const chart = useRef(null);

  useEffect(() => {
    if (!data?.length) return;
    if (chart.current) chart.current.destroy();
    const labels = data.map(p => p.x);
    const values = data.map(p => p.y);
    const color = values[values.length - 1] >= values[0] ? "#3fb950" : "#f85149";
    chart.current = new Chart(ref.current, {
      type: "line",
      data: {
        labels,
        datasets: [{ data: values, borderColor: color, backgroundColor: color + "22", borderWidth: 2, pointRadius: 3, fill: true, tension: 0.3 }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => "₹" + ctx.parsed.y.toLocaleString("en-IN") } } },
        scales: {
          x: { ticks: { color: "#8b949e", font: { size: 10 }, maxTicksLimit: 8 }, grid: { color: "#21262d" } },
          y: { ticks: { color: "#8b949e", font: { size: 10 }, callback: v => "₹" + v.toLocaleString("en-IN") }, grid: { color: "#21262d" } },
        },
      },
    });
    return () => chart.current?.destroy();
  }, [data]);

  return (
    <div className="chart-card">
      <div className="chart-title">{title}</div>
      <div className="chart-container"><canvas ref={ref} /></div>
    </div>
  );
}
