async function checkConnection() {
  const status = document.querySelector("#connection");
  try {
    const response = await fetch(`${window.CHITMIRROR_API_BASE}/health`);
    if (!response.ok || (await response.json()).status !== "ok") {
      throw new Error("Health check failed");
    }
    status.textContent = "Backend connected";
  } catch {
    status.textContent = "Backend unavailable — check the server and API URL.";
  }
}

checkConnection();
