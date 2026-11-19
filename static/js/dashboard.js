/* ============================================================
   InsightBoard — Dashboard JavaScript
   Fetches /api/dashboard and renders KPIs + 4 charts.
   ============================================================ */

"use strict";

// ── Chart instances (module-level so we can destroy/re-create) ─────────────
let monthlyChart   = null;
let regionalChart  = null;
let topProdChart   = null;
let categoryChart  = null;

// ── Chart.js global defaults ───────────────────────────────────────────────
Chart.defaults.color           = "#94a3b8";
Chart.defaults.borderColor     = "rgba(255,255,255,0.06)";
Chart.defaults.font.family     = "Inter, sans-serif";
Chart.defaults.font.size       = 12;
Chart.defaults.plugins.legend.display = false;

// Palette
const PALETTE = ["#7c3aed","#2563eb","#06b6d4","#10b981","#f59e0b","#f43f5e","#a78bfa","#60a5fa","#67e8f9","#6ee7b7"];

// ── Utilities ──────────────────────────────────────────────────────────────
function fmtCurrency(v) {
  if (v == null) return "—";
  return "₹" + Number(v).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtNum(v) {
  if (v == null) return "—";
  return Number(v).toLocaleString("en-IN");
}

function showError(msg) {
  const banner = document.getElementById("error-banner");
  if (!banner) return;
  banner.textContent = "⚠ " + msg;
  banner.style.display = "flex";
}

function hideError() {
  const banner = document.getElementById("error-banner");
  if (banner) banner.style.display = "none";
}

function getFilters() {
  return {
    start_date: document.getElementById("start-date")?.value || "",
    end_date:   document.getElementById("end-date")?.value   || "",
    region:     document.getElementById("region-filter")?.value || "",
  };
}

function buildParams(filters) {
  const p = new URLSearchParams();
  if (filters.start_date) p.set("start_date", filters.start_date);
  if (filters.end_date)   p.set("end_date",   filters.end_date);
  if (filters.region)     p.set("region",      filters.region);
  return p.toString();
}

function updateExportLink(filters) {
  const qs = buildParams(filters);
  // no export link on dashboard; skip gracefully
}

// ── Destroy + re-create chart ─────────────────────────────────────────────
function destroyChart(ref) {
  if (ref) { try { ref.destroy(); } catch (_) {} }
  return null;
}

// ── KPI rendering ─────────────────────────────────────────────────────────
function renderKPIs(kpis) {
  document.getElementById("kpi-revenue").textContent   = fmtCurrency(kpis.total_revenue);
  document.getElementById("kpi-orders").textContent    = fmtNum(kpis.total_orders);
  document.getElementById("kpi-customers").textContent = fmtNum(kpis.unique_customers);
  document.getElementById("kpi-units").textContent     = fmtNum(kpis.units_sold);
  document.getElementById("kpi-aov").textContent       = "Avg order: " + fmtCurrency(kpis.avg_order_value);
}

// ── Monthly revenue line chart ────────────────────────────────────────────
function renderMonthly(rows) {
  const ctx = document.getElementById("monthly-chart");
  if (!ctx) return;
  monthlyChart = destroyChart(monthlyChart);

  if (!rows || rows.length === 0) {
    ctx.parentElement.innerHTML = '<div class="empty-state"><div class="empty-icon">📉</div><div class="empty-title">No data</div></div>';
    return;
  }

  const labels  = rows.map(r => r.month);
  const values  = rows.map(r => r.revenue);
  const grad    = ctx.getContext("2d").createLinearGradient(0, 0, 0, 220);
  grad.addColorStop(0, "rgba(124,58,237,0.35)");
  grad.addColorStop(1, "rgba(124,58,237,0.01)");

  monthlyChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Revenue",
        data: values,
        borderColor: "#7c3aed",
        backgroundColor: grad,
        borderWidth: 2.5,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointBackgroundColor: "#7c3aed",
        tension: 0.35,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        tooltip: {
          callbacks: {
            label: ctx => "Revenue: " + fmtCurrency(ctx.parsed.y),
          },
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { maxTicksLimit: 12 } },
        y: {
          grid: { color: "rgba(255,255,255,0.05)" },
          ticks: { callback: v => "₹" + (v >= 1e6 ? (v/1e6).toFixed(1)+"M" : v >= 1e3 ? (v/1e3).toFixed(0)+"K" : v) },
        },
      },
    },
  });
}

// ── Regional bar chart ────────────────────────────────────────────────────
function renderRegional(rows) {
  const ctx = document.getElementById("regional-chart");
  if (!ctx) return;
  regionalChart = destroyChart(regionalChart);

  if (!rows || rows.length === 0) {
    ctx.parentElement.innerHTML = '<div class="empty-state"><div class="empty-icon">🗺</div><div class="empty-title">No data</div></div>';
    return;
  }

  const labels = rows.map(r => r.region);
  const values = rows.map(r => r.revenue);

  regionalChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Revenue",
        data: values,
        backgroundColor: PALETTE.slice(0, labels.length),
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: { callbacks: { label: c => "Revenue: " + fmtCurrency(c.parsed.y) } },
        legend: { display: false },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          grid: { color: "rgba(255,255,255,0.05)" },
          ticks: { callback: v => "₹" + (v >= 1e6 ? (v/1e6).toFixed(1)+"M" : v >= 1e3 ? (v/1e3).toFixed(0)+"K" : v) },
        },
      },
    },
  });
}

// ── Top products horizontal bar chart ─────────────────────────────────────
function renderTopProductsChart(rows) {
  const ctx = document.getElementById("top-products-chart");
  if (!ctx) return;
  topProdChart = destroyChart(topProdChart);

  const top5 = (rows || []).slice(0, 5);
  if (top5.length === 0) {
    ctx.parentElement.innerHTML = '<div class="empty-state"><div class="empty-icon">📦</div><div class="empty-title">No data</div></div>';
    return;
  }

  topProdChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: top5.map(r => r.product_name.length > 20 ? r.product_name.slice(0,18)+"…" : r.product_name),
      datasets: [{
        label: "Revenue",
        data: top5.map(r => r.revenue),
        backgroundColor: ["#7c3aed","#2563eb","#06b6d4","#10b981","#f59e0b"],
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: c => "Revenue: " + fmtCurrency(c.parsed.x) } },
      },
      scales: {
        x: {
          grid: { color: "rgba(255,255,255,0.05)" },
          ticks: { callback: v => "₹" + (v >= 1e6 ? (v/1e6).toFixed(1)+"M" : v >= 1e3 ? (v/1e3).toFixed(0)+"K" : v) },
        },
        y: { grid: { display: false } },
      },
    },
  });
}

// ── Category donut chart ──────────────────────────────────────────────────
function renderCategory(rows) {
  const ctx = document.getElementById("category-chart");
  if (!ctx) return;
  categoryChart = destroyChart(categoryChart);

  if (!rows || rows.length === 0) {
    ctx.parentElement.innerHTML = '<div class="empty-state"><div class="empty-icon">🗂</div><div class="empty-title">No data</div></div>';
    return;
  }

  categoryChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: rows.map(r => r.category),
      datasets: [{
        data: rows.map(r => r.revenue),
        backgroundColor: PALETTE.slice(0, rows.length),
        borderColor: "#070b14",
        borderWidth: 2,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: {
          display: true,
          position: "right",
          labels: { boxWidth: 10, padding: 12, font: { size: 11 } },
        },
        tooltip: {
          callbacks: {
            label: c => `${c.label}: ${fmtCurrency(c.parsed)} (${((c.parsed / c.dataset.data.reduce((a,b)=>a+b,0))*100).toFixed(1)}%)`,
          },
        },
      },
    },
  });
}

// ── Top products table ────────────────────────────────────────────────────
function renderTopProductsTable(rows) {
  const wrap = document.getElementById("top-products-table-wrap");
  if (!wrap) return;

  if (!rows || rows.length === 0) {
    wrap.innerHTML = `<div class="empty-state">
      <div class="empty-icon">📦</div>
      <div class="empty-title">No products found</div>
      <div class="empty-sub">Adjust your filters</div>
    </div>`;
    return;
  }

  const rank_class = i => i === 0 ? "rank-1" : i === 1 ? "rank-2" : i === 2 ? "rank-3" : "rank-n";

  const rows_html = rows.map((r, i) => `
    <tr>
      <td class="text-center"><span class="rank-badge ${rank_class(i)}">${i+1}</span></td>
      <td class="fw-600">${escHtml(r.product_name)}</td>
      <td>${escHtml(r.category)}</td>
      <td class="text-right mono">${fmtNum(r.units_sold)}</td>
      <td class="text-right mono fw-600 color-purple">${fmtCurrency(r.revenue)}</td>
    </tr>`).join("");

  wrap.innerHTML = `
    <div class="data-table-wrap">
      <table class="data-table">
        <thead><tr>
          <th class="text-center">Rank</th>
          <th>Product</th>
          <th>Category</th>
          <th class="text-right">Units Sold</th>
          <th class="text-right">Revenue</th>
        </tr></thead>
        <tbody>${rows_html}</tbody>
      </table>
    </div>`;
}

// ── XSS helper ─────────────────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Main load function ────────────────────────────────────────────────────
async function loadDashboard() {
  hideError();
  const filters = getFilters();
  const qs      = buildParams(filters);

  try {
    const res  = await fetch(`/api/dashboard?${qs}`);
    const data = await res.json();

    if (!res.ok || data.error) {
      showError(data.error || "Failed to load dashboard data.");
      return;
    }

    renderKPIs(data.kpis);
    renderMonthly(data.monthly_revenue);
    renderRegional(data.regional_performance);
    renderTopProductsChart(data.top_products);
    renderCategory(data.category_revenue);
    renderTopProductsTable(data.top_products);

    const el = document.getElementById("last-updated");
    if (el) el.textContent = "Updated " + new Date().toLocaleTimeString();

  } catch (err) {
    console.error("Dashboard fetch error:", err);
    showError("Could not reach the server. Is Flask running?");
  }
}

// ── Init ──────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // Filter form
  const form = document.getElementById("filter-form");
  if (form) {
    form.addEventListener("submit", e => { e.preventDefault(); loadDashboard(); });
  }

  // Reset button
  const resetBtn = document.getElementById("reset-btn");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      form?.reset();
      loadDashboard();
    });
  }

  // Initial load
  loadDashboard();
});
