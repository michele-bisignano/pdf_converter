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
