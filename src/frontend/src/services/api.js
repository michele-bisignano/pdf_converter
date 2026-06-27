const API_BASE = "/api";

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

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

export async function downloadFile(filename) {
  const res = await fetch(`${API_BASE}/download/${filename}`);
  if (!res.ok) throw new Error("Download failed");
  return res.blob();
}
