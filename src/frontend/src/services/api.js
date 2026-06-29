const API_BASE = "/api";

/**
 * Checks whether the backend server is reachable.
 *
 * @returns {Promise<Object>} The health-check response JSON
 */
export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

/**
 * Sends a PDF file to the backend for conversion to Excel.
 *
 * @param {File} file - The PDF file to convert
 * @returns {Promise<Object>} The conversion result with file_name and optional warning
 */
export async function convertPdf(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/convert`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Error during conversion");
  }

  return res.json();
}

/**
 * Downloads a converted Excel file by its filename.
 *
 * @param {string} filename - The name of the file to download
 * @returns {Promise<Blob>} The file contents as a Blob
 */
export async function downloadFile(filename) {
  const res = await fetch(`${API_BASE}/download/${filename}`);
  if (!res.ok) throw new Error("Download failed");
  return res.blob();
}

/**
 * Sends a liveness ping to the backend. Called periodically while the
 * app is open so the server's watchdog knows a client is still
 * connected; if these stop arriving the server shuts itself down.
 *
 * @returns {void}
 */
export function sendHeartbeat() {
  // Fire-and-forget: a missed heartbeat just means the watchdog
  // triggers a little sooner, which is the desired fallback behavior.
  navigator.sendBeacon(`${API_BASE}/heartbeat`);
}

/**
 * Requests a graceful server shutdown.
 *
 * Uses navigator.sendBeacon instead of fetch: sendBeacon is guaranteed
 * by the browser to be delivered even if the page is unloaded/closed
 * immediately after the call, which a regular fetch() is not.
 *
 * @returns {void}
 */
export function requestShutdown() {
  navigator.sendBeacon(`${API_BASE}/shutdown`);
}
