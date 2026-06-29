import { useState, useRef, useCallback } from "react";
import { Upload, FileText, Loader2, Download, AlertTriangle, CheckCircle } from "lucide-react";
import { convertPdf, downloadFile } from "../services/api";

/**
 * Attempts to save a Blob via the File System Access API (Chrome).
 * Falls back to an <a>-tag download when the API is unavailable or the user cancels.
 *
 * @param {Blob} blob        - File contents
 * @param {string} fileName  - Suggested file name
 * @returns {Promise<boolean>} True if the file was saved successfully
 */
async function saveBlobAs(blob, fileName) {
  // "Save As" via the File System Access API (Chromium only)
  if ("showSaveFilePicker" in window) {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: fileName,
        types: [
          {
            description: "Excel File",
            accept: { "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"] },
          },
        ],
      });
      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
      return true;
    } catch {
      // User cancelled or the API threw — fall through to the <a>-tag fallback
    }
  }

  // Fallback: trigger download via a hidden <a> element.
  const url = URL.createObjectURL(blob);
  try {
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } finally {
    URL.revokeObjectURL(url);
  }
  return true;
}

/**
 * PDF-to-Excel converter component.
 *
 * Provides a drag-and-drop zone and a file picker for PDF upload,
 * triggers conversion on the backend, and offers a download flow
 * (native "Save As" dialog with fallback to a regular download).
 *
 * @returns {JSX.Element} The converter box UI
 */
export default function PDFConverterBox() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [resultWarning, setResultWarning] = useState(null);
  const [blob, setBlob] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  /**
   * Validates and stores the selected PDF file.
   * Resets previous results on new file selection.
   *
   * @param {File} selectedFile - The file picked by the user
   */
  const handleFile = useCallback((selectedFile) => {
    if (!selectedFile || !selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a valid PDF file.");
      setFile(null);
      return;
    }
    setFile(selectedFile);
    setError(null);
    setResult(null);
    setResultWarning(null);
    setBlob(null);
    setSaved(false);
  }, []);

  /**
   * Handles the drop event from drag-and-drop.
   *
   * @param {React.DragEvent} e - The drag event
   */
  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer?.files?.[0];
    if (f) handleFile(f);
  }, [handleFile]);

  /**
   * Highlights the drop zone while dragging over it.
   *
   * @param {React.DragEvent} e - The drag event
   */
  const onDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };
  /**
   * Removes the highlight when the drag leaves the drop zone.
   */
  const onDragLeave = () => setDragging(false);

  /**
   * Uploads the selected PDF to the backend and stores the result.
   * The user can then download the file manually via the download button.
   */
  const onUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setResultWarning(null);
    setBlob(null);
    setSaved(false);

    try {
      const data = await convertPdf(file);
      setResult(data);

      if (data.warning) {
        setResultWarning(data.warning_message || "Warning: the balance does not match.");
      }

      // Only try to download the blob if the file actually exists on the server
      if (data.file_name) {
        const fileBlob = await downloadFile(data.file_name);
        setBlob(fileBlob);
      }
    } catch (err) {
      setError(err.message || "Error during conversion");
    } finally {
      setLoading(false);
    }
  };

  /**
   * Opens the "Save As" dialog and lets the user pick where to save.
   */
  const handleDownload = async () => {
    if (!blob || !result) return;
    setDownloading(true);
    try {
      await saveBlobAs(blob, result.file_name);
      setSaved(true);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all
          ${dragging
            ? "border-blue-500 bg-blue-500/10"
            : "border-zinc-700 hover:border-zinc-500 bg-white/[0.01]"
          }`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        <Upload className="mx-auto mb-2 text-zinc-400" size={32} />
        <p className="text-zinc-400 text-sm">
          {dragging
            ? "Drop the file here"
            : "Drag a PDF here or click to upload"}
        </p>
      </div>

      {/* File selected */}
      {file && (
        <div className="flex items-center gap-3 glass rounded-xl px-4 py-3">
          <FileText className="text-blue-400 shrink-0" size={20} />
          <span className="text-sm text-zinc-300 truncate flex-1">
            {file.name}
          </span>
          <span className="text-xs text-zinc-500">
            {(file.size / 1024).toFixed(0)} KB
          </span>
        </div>
      )}

      {/* Convert button */}
      {file && !result && (
        <button
          onClick={onUpload}
          disabled={loading}
          className="w-full py-3 rounded-xl font-medium text-sm transition-all
            bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500
            hover:opacity-90 disabled:opacity-50 text-white flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              Converting...
            </>
          ) : (
            <>
              <Download size={18} />
              Convert to Excel
            </>
          )}
        </button>
      )}

      {/* Error — only when we truly have no result */}
      {error && !result && (
        <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
          {error}
        </div>
      )}

      {/* Success (no warning) */}
      {result && !resultWarning && !result.success && (
        <div className="text-amber-400 text-sm bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3">
          Conversion had errors — the file may be incomplete.
          {result.warning_message && <div className="mt-1">{result.warning_message}</div>}
        </div>
      )}

      {/* Success (no warning) */}
      {result && !resultWarning && result.success && (
        <div className="text-green-400 text-sm bg-green-500/10 border border-green-500/20 rounded-xl px-4 py-3 flex items-start gap-2">
          <FileText size={18} className="shrink-0 mt-0.5" />
          <span className="flex-1">PDF exported successfully.</span>
        </div>
      )}

      {/* Success with validation warning */}
      {result && resultWarning && (
        <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 flex items-start gap-2">
          <AlertTriangle size={18} className="shrink-0 mt-0.5" />
          <span className="flex-1">{resultWarning}</span>
        </div>
      )}

      {/* Download button — shown after conversion, whether success or warning */}
      {result && blob && !saved && (
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="w-full py-3 rounded-xl font-medium text-sm transition-all
            bg-gradient-to-r from-emerald-500 to-teal-600
            hover:opacity-90 disabled:opacity-50 text-white flex items-center justify-center gap-2"
        >
          {downloading ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              Preparing download...
            </>
          ) : (
            <>
              <Download size={18} />
              Download Excel — Choose where to save
            </>
          )}
        </button>
      )}

      {/* Saved confirmation */}
      {saved && (
        <div className="text-emerald-400 text-sm bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3 flex items-start gap-2">
          <CheckCircle size={18} className="shrink-0 mt-0.5" />
          <div className="flex-1">
            <span>File saved successfully.</span>
            {result?.file_path && (
              <div className="text-zinc-500 text-xs mt-1">
                Server copy: {result.file_path}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
