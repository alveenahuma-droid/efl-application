// Savings quote page: sends the form to /api/quote, shows every plan's result
// (including why a plan is not available), and lets a signed-in user save it.
let lastRequest = null;

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("quote-form");
  if (!form) return;

  const saved = restoreForm("quote");
  if (saved) {
    if (saved.lump_sum) document.getElementById("lump-sum").value = saved.lump_sum;
    if (saved.monthly_amount) document.getElementById("monthly").value = saved.monthly_amount;
    if (saved.plan) {
      const radio = form.querySelector(`input[name="plan"][value="${saved.plan}"]`);
      if (radio) radio.checked = true;
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage("quote-error", "");
    setSaveState(false, "");

    const lump = document.getElementById("lump-sum").value.trim() || "0";
    const monthly = document.getElementById("monthly").value.trim() || "0";
    const planInput = form.querySelector('input[name="plan"]:checked');
    const plan = planInput ? planInput.value : null;

    cacheForm("quote", { lump_sum: lump, monthly_amount: monthly, plan: plan });

    try {
      const { ok, data } = await postJson("/api/quote", {
        lump_sum: lump, monthly_amount: monthly, plan: plan,
      });
      if (!ok) {
        const message = (data && data.error) || "Quote failed. Please try again.";
        showMessage("quote-error", message);
        renderMessageRow(message);
        return;
      }
      lastRequest = { lump_sum: lump, monthly_amount: monthly, plan: plan };
      renderQuote(data);
      const anyEligible = (data.results || []).some((r) => r.eligible);
      setSaveState(anyEligible, "");
    } catch (problem) {
      showMessage("quote-error", "Could not reach the server. Please try again.");
      renderMessageRow("Could not reach the server. Please try again.");
    }
  });

  document.getElementById("save-quote").addEventListener("click", async () => {
    if (!lastRequest) return;
    setSaveState(true, "Saving…");
    try {
      const { ok, data } = await postJson("/api/quotes/save", lastRequest);
      if (ok) {
        setSaveState(false, "Saved. You can see it on the History page.");
      } else {
        setSaveState(true, (data && data.error) || "The quote could not be saved.");
      }
    } catch (problem) {
      setSaveState(true, "Could not reach the server. Please try again.");
    }
  });
});

function setSaveState(showButton, text) {
  const button = document.getElementById("save-quote");
  button.hidden = !showButton;
  document.getElementById("save-message").textContent = text;
}

function renderMessageRow(text) {
  const tbody = document.querySelector("#quote-results tbody");
  tbody.innerHTML = "";
  const row = document.createElement("tr");
  row.className = "empty-row";
  const cell = document.createElement("td");
  cell.colSpan = 6;
  cell.textContent = text;
  row.appendChild(cell);
  tbody.appendChild(row);
}

function renderQuote(data) {
  const tbody = document.querySelector("#quote-results tbody");
  const placeholder = document.getElementById("quote-placeholder");
  tbody.innerHTML = "";
  const results = data.results || [];

  for (const plan of results.filter((r) => !r.eligible)) {
    const row = document.createElement("tr");
    row.className = "empty-row";
    const cell = document.createElement("td");
    cell.colSpan = 6;
    cell.textContent = plan.plan_name + ": not available. " + plan.reason + ".";
    row.appendChild(cell);
    tbody.appendChild(row);
  }

  const eligible = results.filter((r) => r.eligible);
  if (!eligible.length) {
    if (placeholder) placeholder.textContent = "No plan is available for these amounts.";
    return;
  }

  if (placeholder) {
    placeholder.textContent = data.recommended_name
      ? "Recommended plan: " + data.recommended_name
      : "Results for each eligible plan.";
  }

  for (const plan of eligible) {
    for (const p of plan.projections || []) {
      for (const s of [
        { label: "Min", final: p.min_final, profit: p.min_profit, fees: p.min_fees, tax: p.min_tax },
        { label: "Max", final: p.max_final, profit: p.max_profit, fees: p.max_fees, tax: p.max_tax },
      ]) {
        const row = document.createElement("tr");
        const cells = [
          `${p.years} year(s) – ${plan.plan_name}`,
          s.label,
          formatMoney(s.final, "GBP"),
          formatMoney(s.profit, "GBP"),
          formatMoney(s.fees, "GBP"),
          formatMoney(s.tax, "GBP"),
        ];
        for (const text of cells) {
          const td = document.createElement("td");
          td.textContent = text;
          row.appendChild(td);
        }
        tbody.appendChild(row);
      }
    }
  }
}
