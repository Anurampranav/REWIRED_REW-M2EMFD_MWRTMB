const connection = document.querySelector("#connection");
const connectionLabel = document.querySelector("#connection-label");

async function checkConnection() {
  const base = window.CHITMIRROR_API_BASE || "";
  try {
    const response = await fetch(`${base}/health`, { headers: { Accept: "application/json" } });
    if (!response.ok || (await response.json()).status !== "ok") throw new Error("Backend health check failed");
    connection.classList.add("connected");
    connectionLabel.textContent = "Backend connected";
  } catch {
    connection.classList.add("failed");
    connectionLabel.textContent = "Backend unavailable · showing sample dashboard";
  }
}

checkConnection();

const LEDGER_POLL_MS = 1000;
const LEDGER_STATUS = {
  verified: {label: "Verified", symbol: "✓"},
  needs_review: {label: "Needs review", symbol: "!"},
  overdue: {label: "Overdue", symbol: "!"},
  rejected: {label: "Rejected", symbol: "×"},
  pending: {label: "Pending", symbol: "·"}
};
const ledgerGrid = document.querySelector("#ledger-grid");
const ledgerSync = document.querySelector("#ledger-sync");
const ledgerError = document.querySelector("#ledger-error");
let ledgerRequestPending = false;
let hasLedgerSnapshot = false;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[character]));
}

function moneyFromPaise(value) {
  const paise = Number(value);
  if (!Number.isFinite(paise)) return "Amount unavailable";
  return new Intl.NumberFormat("en-IN", {style:"currency", currency:"INR", minimumFractionDigits:2, maximumFractionDigits:2}).format(paise / 100);
}

function renderLedger(state) {
  if (!state || !Array.isArray(state.members) || !Array.isArray(state.months) || !Array.isArray(state.ledger)) {
    throw new Error("The shared state response does not match the ledger contract.");
  }
  const months = [...new Set(state.months.map(Number).filter(Number.isInteger))].sort((a, b) => a - b);
  const byMemberMonth = new Map(state.ledger.map(entry => [`${entry.member_id}:${entry.month}`, entry]));
  const monthHeaders = months.map(month => `<th scope="col">${month}</th>`).join("");
  const rows = state.members.map(member => {
    const cells = months.map(month => {
      const entry = byMemberMonth.get(`${member.id}:${month}`);
      const status = Object.hasOwn(LEDGER_STATUS, entry?.status) ? entry.status : "pending";
      const details = LEDGER_STATUS[status];
      const utr = entry?.utr || "—";
      const amount = entry ? moneyFromPaise(entry.amount_paise) : "No payment recorded";
      const tooltip = `${member.name} · Month ${month} · ${details.label} · UTR: ${utr} · ${amount}`;
      const testId = `ledger-cell-${member.id}-month-${month}`;
      return `<td><span class="ledger-cell ${status}" role="img" tabindex="0" data-status="${status}" data-testid="${escapeHtml(testId)}" aria-label="${escapeHtml(tooltip)}" title="${escapeHtml(tooltip)}">${details.symbol}</span></td>`;
    }).join("");
    return `<tr><th scope="row">${escapeHtml(member.name)}</th>${cells}</tr>`;
  }).join("");
  const memberLabel = state.members.length === 1 ? "member" : "members";
  const monthLabel = months.length === 1 ? "month" : "months";
  ledgerGrid.innerHTML = `<table class="ledger-table" aria-label="Payment status for ${state.members.length} ${memberLabel} across ${months.length} ${monthLabel}"><thead><tr><th scope="col">Member</th>${monthHeaders}</tr></thead><tbody>${rows}</tbody></table>`;
  ledgerGrid.setAttribute("aria-busy", "false");
  ledgerGrid.dataset.memberCount = String(state.members.length);
  ledgerGrid.dataset.monthCount = String(months.length);
  hasLedgerSnapshot = true;
}

async function refreshLedger() {
  if (ledgerRequestPending) return;
  ledgerRequestPending = true;
  const base = (window.CHITMIRROR_API_BASE || "").replace(/\/$/, "");
  try {
    const response = await fetch(`${base}/state?role=foreman`, {headers:{Accept:"application/json"}, cache:"no-store"});
    if (!response.ok) throw new Error(`GET /state returned ${response.status}`);
    const state = await response.json();
    renderLedger(state);
    ledgerError.hidden = true;
    ledgerError.textContent = "";
    ledgerSync.textContent = `Live · updated ${new Date().toLocaleTimeString([], {hour:"2-digit", minute:"2-digit", second:"2-digit"})}`;
  } catch (error) {
    ledgerSync.textContent = hasLedgerSnapshot ? "Stale · retrying" : "Waiting for shared state";
    ledgerError.textContent = hasLedgerSnapshot
      ? `Shared state could not refresh. Showing the last update. ${error.message}`
      : `Ledger state is unavailable. It will appear when GET /state is connected. ${error.message}`;
    ledgerError.hidden = false;
    if (!hasLedgerSnapshot) {
      ledgerGrid.innerHTML = '<p class="ledger-placeholder">Waiting for live ledger data…</p>';
      ledgerGrid.setAttribute("aria-busy", "false");
    }
  } finally {
    ledgerRequestPending = false;
  }
}

document.querySelector("#ledger-refresh").addEventListener("click", refreshLedger);
refreshLedger();
window.setInterval(refreshLedger, LEDGER_POLL_MS);



