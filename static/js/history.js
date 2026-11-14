// History page: loads the signed-in user's conversions and saved quotes.
document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([loadConversions(), loadQuotes()]);
});

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (response.status === 401) {
    window.location.href = "/login";
    return null;
  }
  return response.ok ? response.json() : null;
}

function fillBody(id, columns, rows, emptyText) {
  const tbody = document.getElementById(id);
  tbody.innerHTML = "";
  if (!rows || rows.length === 0) {
    const row = document.createElement("tr");
    row.className = "empty-row";
    const cell = document.createElement("td");
    cell.colSpan = columns;
    cell.textContent = emptyText;
    row.appendChild(cell);
    tbody.appendChild(row);
    return;
  }
  for (const values of rows) {
    const row = document.createElement("tr");
    for (const text of values) {
      const td = document.createElement("td");
      td.textContent = text;
      row.appendChild(td);
    }
    tbody.appendChild(row);
  }
}

async function loadConversions() {
  const rows = await fetchJson("/api/transactions");
  const body = (rows || []).map((t) => [
    t.created_at,
    t.from_currency,
    formatAmount(t.amount),
    t.to_currency,
    formatAmount(t.converted_amount),
    String(t.rate_used),
    formatMoney(t.fee_usd, "USD"),
  ]);
  fillBody("conversion-history", 7, body,
           "No conversions yet. A completed conversion is listed here.");
}

async function loadQuotes() {
  const rows = await fetchJson("/api/quotes");
  const body = (rows || []).map((q) => [
    q.created_at,
    q.plan_name,
    formatMoney(q.lump_sum, "GBP"),
    formatMoney(q.monthly_amount, "GBP"),
    q.recommended_name,
  ]);
  fillBody("quote-history", 5, body, "No saved quotes yet.");
}

function formatAmount(value) {
  return Number(value).toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
