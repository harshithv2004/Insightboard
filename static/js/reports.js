/* ============================================================
   InsightBoard — Reports JavaScript
   Handles Sales, Products, and Customers pages.
   ============================================================ */

"use strict";

// ── Chart instances ────────────────────────────────────────────────────────
let _topProdChart  = null;
let _catChart      = null;

// ── Chart.js defaults (same as dashboard.js) ──────────────────────────────
Chart.defaults.color        = "#94a3b8";
Chart.defaults.borderColor  = "rgba(255,255,255,0.06)";
Chart.defaults.font.family  = "Inter, sans-serif";
Chart.defaults.font.size    = 12;

const PALETTE = ["#7c3aed","#2563eb","#06b6d4","#10b981","#f59e0b","#f43f5e","#a78bfa","#60a5fa","#67e8f9","#6ee7b7"];

// ── State (Sales page) ────────────────────────────────────────────────────
let _salesState = {
  page: 1,
  per_page: 25,
  sort_by: "order_date",
  sort_dir: "DESC",
  total: 0,
  pages: 0,
};

// ── Utilities ─────────────────────────────────────────────────────────────
function fmt(v) {
  if (v == null) return "—";
  return Number(v).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmtInt(v) {
  if (v == null) return "—";
  return Number(v).toLocaleString("en-IN");
}
function fmtCur(v) { return "₹" + fmt(v); }

function escHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function showError(msg) {
  const b = document.getElementById("error-banner");
  if (!b) return;
  b.textContent = "⚠ " + msg;
  b.style.display = "flex";
}
function hideError() {
  const b = document.getElementById("error-banner");
  if (b) b.style.display = "none";
}

function setLoading(show) {
  const ov = document.getElementById("loading-overlay");
  if (ov) ov.classList.toggle("show", show);
}

function destroyChart(ref) {
  if (ref) { try { ref.destroy(); } catch (_) {} }
  return null;
}

function getCommonFilters() {
  const get = id => document.getElementById(id)?.value?.trim() || "";
  return {
    start_date: get("start-date"),
    end_date:   get("end-date"),
    region:     get("region-filter"),
    category:   get("category-filter"),
    status:     get("status-filter"),
  };
}

function buildQS(obj) {
  const p = new URLSearchParams();
  for (const [k,v] of Object.entries(obj)) {
    if (v) p.set(k, v);
  }
  return p.toString();
}

function badgeHtml(status) {
  const map = { Completed: "badge-completed", Pending: "badge-pending", Cancelled: "badge-cancelled" };
  const cls = map[status] || "";
  return `<span class="badge ${cls}">${escHtml(status)}</span>`;
}

function rankBadge(i) {
  const cls = i === 0 ? "rank-1" : i === 1 ? "rank-2" : i === 2 ? "rank-3" : "rank-n";
  return `<span class="rank-badge ${cls}">${i+1}</span>`;
}

// ── Update CSV export link ────────────────────────────────────────────────
function updateExportLink(filters) {
  const link = document.getElementById("csv-export-btn") || document.getElementById("export-link");
  if (!link) return;
  const qs = buildQS(filters);
  link.href = `/reports/export.csv${qs ? "?" + qs : ""}`;
}

// ══════════════════════════════════════════════════════════════════════
// SALES REPORT
// ══════════════════════════════════════════════════════════════════════

async function fetchSalesData() {
  setLoading(true);
  hideError();

  const filters  = getCommonFilters();
  const params   = {
    ...filters,
    page:     _salesState.page,
    per_page: _salesState.per_page,
    sort_by:  _salesState.sort_by,
    sort_dir: _salesState.sort_dir,
  };

  updateExportLink(filters);

  try {
    const res  = await fetch(`/api/reports/sales?${buildQS(params)}`);
    const data = await res.json();

    if (!res.ok || data.error) { showError(data.error || "Failed to load sales data."); return; }

    _salesState.total = data.total;
    _salesState.pages = data.pages;

    renderSalesTable(data.data);
    renderPagination(data);
    document.getElementById("result-count").textContent =
      `${fmtInt(data.total)} records · Page ${data.page} of ${data.pages}`;
  } catch (err) {
    console.error(err);
    showError("Could not reach the server. Is Flask running?");
  } finally {
    setLoading(false);
  }
}

function renderSalesTable(rows) {
  const tbody = document.getElementById("sales-tbody");
  if (!tbody) return;

  if (!rows || rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10">
      <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <div class="empty-title">No records found</div>
        <div class="empty-sub">Try adjusting your filters</div>
      </div></td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(r => `
    <tr>
      <td class="color-muted">${escHtml(r.order_date)}</td>
      <td class="mono color-muted">#${r.order_id}</td>
      <td class="fw-600">${escHtml(r.customer_name)}</td>
      <td>${escHtml(r.region)}</td>
      <td>${badgeHtml(r.status)}</td>
      <td>${escHtml(r.product_name)}</td>
      <td class="color-muted">${escHtml(r.category)}</td>
      <td class="text-right mono">${fmtInt(r.quantity)}</td>
      <td class="text-right mono color-muted">${fmtCur(r.unit_price)}</td>
      <td class="text-right mono fw-600 color-purple">${fmtCur(r.line_total)}</td>
    </tr>`).join("");
}

function renderPagination(data) {
  const info = document.getElementById("pagination-info");
  const ctrl = document.getElementById("pagination-controls");
  if (!info || !ctrl) return;

  const start = (data.page - 1) * data.per_page + 1;
  const end   = Math.min(data.page * data.per_page, data.total);
  info.textContent = data.total > 0 ? `Showing ${fmtInt(start)}–${fmtInt(end)} of ${fmtInt(data.total)}` : "No records";

  ctrl.innerHTML = "";

  const addBtn = (label, page, disabled, active = false) => {
    const btn = document.createElement("button");
    btn.className = "pg-btn" + (active ? " active" : "");
    btn.textContent = label;
    btn.disabled    = disabled;
    btn.setAttribute("aria-label", "Page " + label);
    if (!disabled && !active) {
      btn.addEventListener("click", () => {
        _salesState.page = page;
        fetchSalesData();
      });
    }
    ctrl.appendChild(btn);
  };

  addBtn("«", 1, data.page <= 1);
  addBtn("‹", data.page - 1, data.page <= 1);

  const range = 2;
  for (let p = Math.max(1, data.page - range); p <= Math.min(data.pages, data.page + range); p++) {
    addBtn(p, p, false, p === data.page);
  }

  addBtn("›", data.page + 1, data.page >= data.pages);
  addBtn("»", data.pages, data.page >= data.pages);
}

function initSortHeaders() {
  document.querySelectorAll(".data-table th.sortable").forEach(th => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      if (_salesState.sort_by === col) {
        _salesState.sort_dir = _salesState.sort_dir === "ASC" ? "DESC" : "ASC";
      } else {
        _salesState.sort_by  = col;
        _salesState.sort_dir = "DESC";
      }
      // Update header classes
      document.querySelectorAll(".data-table th").forEach(h => h.classList.remove("sort-asc","sort-desc"));
      th.classList.add(_salesState.sort_dir === "ASC" ? "sort-asc" : "sort-desc");
      _salesState.page = 1;
      fetchSalesData();
    });
  });

  // Mark default sort header
  const defaultTh = document.getElementById("th-" + _salesState.sort_by);
  if (defaultTh) defaultTh.classList.add("sort-desc");
}

function initSalesReport() {
  const form     = document.getElementById("filter-form");
  const resetBtn = document.getElementById("reset-btn");
  const perPage  = document.getElementById("per-page-select");

  if (form) form.addEventListener("submit", e => { e.preventDefault(); _salesState.page = 1; fetchSalesData(); });
  if (resetBtn) resetBtn.addEventListener("click", () => { form?.reset(); _salesState.page = 1; fetchSalesData(); });
  if (perPage) perPage.addEventListener("change", () => {
    _salesState.per_page = parseInt(perPage.value, 10);
    _salesState.page = 1;
    fetchSalesData();
  });

  initSortHeaders();
  fetchSalesData();
}

// ══════════════════════════════════════════════════════════════════════
// PRODUCTS REPORT
// ══════════════════════════════════════════════════════════════════════

async function fetchProductsData() {
  setLoading(true);
  hideError();
  const filters = getCommonFilters();

  try {
    const res  = await fetch(`/api/reports/products?${buildQS(filters)}`);
    const data = await res.json();
    if (!res.ok || data.error) { showError(data.error || "Failed to load products data."); return; }

    renderTopProductsBar(data.top_products);
    renderCategoryDonut(data.category_revenue);
    renderProductsTable(data.top_products);
    renderCategoryTable(data.category_revenue);
  } catch (err) {
    console.error(err);
    showError("Could not reach the server.");
  } finally {
    setLoading(false);
  }
}

function renderTopProductsBar(rows) {
  const ctx = document.getElementById("top-products-chart");
  if (!ctx) return;
  _topProdChart = destroyChart(_topProdChart);
  if (!rows?.length) return;
  const top10 = rows.slice(0, 10);
  _topProdChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: top10.map(r => r.product_name.length > 22 ? r.product_name.slice(0,20)+"…" : r.product_name),
      datasets: [{ label: "Revenue", data: top10.map(r => r.revenue),
        backgroundColor: PALETTE.slice(0, top10.length), borderRadius: 6, borderSkipped: false }],
    },
    options: {
      indexAxis: "y",
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => "₹" + fmt(c.parsed.x) } } },
      scales: {
        x: { grid: { color:"rgba(255,255,255,0.05)" }, ticks: { callback: v => "₹"+(v>=1e6?(v/1e6).toFixed(1)+"M":v>=1e3?(v/1e3).toFixed(0)+"K":v) } },
        y: { grid: { display:false } },
      },
    },
  });
}

function renderCategoryDonut(rows) {
  const ctx = document.getElementById("category-chart");
  if (!ctx) return;
  _catChart = destroyChart(_catChart);
  if (!rows?.length) return;
  _catChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: rows.map(r => r.category),
      datasets: [{ data: rows.map(r => r.revenue), backgroundColor: PALETTE.slice(0,rows.length), borderColor:"#070b14", borderWidth:2, hoverOffset:8 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: "68%",
      plugins: {
        legend: { display:true, position:"right", labels: { boxWidth:10, padding:10, font:{size:11} } },
        tooltip: { callbacks: { label: c => `${c.label}: ₹${fmt(c.parsed)} (${((c.parsed/c.dataset.data.reduce((a,b)=>a+b,0))*100).toFixed(1)}%)` } },
      },
    },
  });
}

function renderProductsTable(rows) {
  const tbody = document.getElementById("products-tbody");
  if (!tbody) return;
  if (!rows?.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📦</div><div class="empty-title">No products found</div></div></td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((r,i) => `
    <tr>
      <td class="text-center">${rankBadge(i)}</td>
      <td class="fw-600">${escHtml(r.product_name)}</td>
      <td><span class="badge badge-pending">${escHtml(r.category)}</span></td>
      <td class="text-right mono">${fmtInt(r.units_sold)}</td>
      <td class="text-right mono fw-600 color-purple">${fmtCur(r.revenue)}</td>
      <td class="text-right mono color-muted">${fmtCur(r.units_sold > 0 ? r.revenue / r.units_sold : 0)}</td>
    </tr>`).join("");
}

function renderCategoryTable(rows) {
  const tbody = document.getElementById("category-tbody");
  if (!tbody) return;
  if (!rows?.length) {
    tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state"><div class="empty-icon">🗂</div><div class="empty-title">No categories found</div></div></td></tr>`;
    return;
  }
  const totalRev = rows.reduce((s,r) => s + r.revenue, 0);
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td class="fw-600">${escHtml(r.category)}</td>
      <td class="text-right mono fw-600 color-purple">${fmtCur(r.revenue)}</td>
      <td class="text-right mono">${fmtInt(r.units_sold)}</td>
      <td class="text-right mono">${fmtInt(r.order_count)}</td>
      <td class="text-right mono color-amber">${totalRev > 0 ? ((r.revenue/totalRev)*100).toFixed(1)+"%" : "—"}</td>
    </tr>`).join("");
}

function initProductsReport() {
  const form = document.getElementById("filter-form");
  const reset = document.getElementById("reset-btn");
  if (form) form.addEventListener("submit", e => { e.preventDefault(); fetchProductsData(); });
  if (reset) reset.addEventListener("click", () => { form?.reset(); fetchProductsData(); });
  fetchProductsData();
}

// ══════════════════════════════════════════════════════════════════════
// CUSTOMERS REPORT
// ══════════════════════════════════════════════════════════════════════

async function fetchCustomersData() {
  setLoading(true);
  hideError();
  const filters = getCommonFilters();

  try {
    const res  = await fetch(`/api/reports/customers?${buildQS(filters)}`);
    const data = await res.json();
    if (!res.ok || data.error) { showError(data.error || "Failed to load customer data."); return; }

    renderHVTable(data.high_value_customers);
    renderRepeatTable(data.repeat_customers);
    renderMoMTable(data.mom_growth);
    renderCustomerKPIs(data.repeat_customers, data.high_value_customers);
  } catch (err) {
    console.error(err);
    showError("Could not reach the server.");
  } finally {
    setLoading(false);
  }
}

function renderCustomerKPIs(repeat, hv) {
  const repEl       = document.getElementById("stat-repeat");
  const topSpendEl  = document.getElementById("stat-top-spend");
  const topNameEl   = document.getElementById("stat-top-name");
  const avgOrdersEl = document.getElementById("stat-avg-orders");

  if (repEl) repEl.textContent = fmtInt(repeat?.length ?? 0);

  if (hv?.length > 0) {
    const top = hv[0];
    if (topSpendEl)  topSpendEl.textContent = fmtCur(top.total_spend);
    if (topNameEl)   topNameEl.textContent  = top.customer_name;
  }

  if (repeat?.length > 0 && avgOrdersEl) {
    const avg = repeat.reduce((s,r) => s + r.order_count, 0) / repeat.length;
    avgOrdersEl.textContent = avg.toFixed(1);
  }
}

function renderHVTable(rows) {
  const tbody = document.getElementById("hv-tbody");
  if (!tbody) return;
  if (!rows?.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">💎</div><div class="empty-title">No data</div></div></td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((r,i) => `
    <tr>
      <td class="text-center">${rankBadge(i)}</td>
      <td class="fw-600">${escHtml(r.customer_name)}</td>
      <td>${escHtml(r.region)}</td>
      <td class="text-right mono">${fmtInt(r.order_count)}</td>
      <td class="text-right mono fw-600 color-purple">${fmtCur(r.total_spend)}</td>
      <td class="color-muted">${escHtml(r.last_order)}</td>
    </tr>`).join("");
}

function renderRepeatTable(rows) {
  const tbody = document.getElementById("repeat-tbody");
  if (!tbody) return;
  if (!rows?.length) {
    tbody.innerHTML = `<tr><td colspan="4"><div class="empty-state"><div class="empty-icon">🔁</div><div class="empty-title">No repeat customers</div></div></td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td class="fw-600">${escHtml(r.customer_name)}</td>
      <td>${escHtml(r.region)}</td>
      <td class="text-right mono">${fmtInt(r.order_count)}</td>
      <td class="text-right mono fw-600 color-purple">${fmtCur(r.total_spend)}</td>
    </tr>`).join("");
}

function renderMoMTable(rows) {
  const tbody = document.getElementById("mom-tbody");
  if (!tbody) return;
  if (!rows?.length) {
    tbody.innerHTML = `<tr><td colspan="4"><div class="empty-state"><div class="empty-icon">📈</div><div class="empty-title">No data</div></div></td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(r => {
    const g   = r.growth_percentage;
    const gTxt = g == null ? '<span class="growth-nil">—</span>'
               : g > 0 ? `<span class="growth-up">▲ ${g.toFixed(2)}%</span>`
               : g < 0 ? `<span class="growth-down">▼ ${Math.abs(g).toFixed(2)}%</span>`
               : '<span class="growth-nil">0.00%</span>';
    return `
    <tr>
      <td class="fw-600 mono">${escHtml(r.month)}</td>
      <td class="text-right mono fw-600 color-purple">${fmtCur(r.revenue)}</td>
      <td class="text-right mono color-muted">${r.previous_revenue != null ? fmtCur(r.previous_revenue) : "—"}</td>
      <td class="text-right">${gTxt}</td>
    </tr>`;
  }).join("");
}

function initCustomersReport() {
  const form = document.getElementById("filter-form");
  const reset = document.getElementById("reset-btn");
  if (form) form.addEventListener("submit", e => { e.preventDefault(); fetchCustomersData(); });
  if (reset) reset.addEventListener("click", () => { form?.reset(); fetchCustomersData(); });
  fetchCustomersData();
}
