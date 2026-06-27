import { useState, useRef, useCallback } from "react";
import { Upload, FileText, Loader2, Download } from "lucide-react";
import { convertPdf, downloadFile } from "../services/api";

export default function PDFConverterBox() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = useCallback((selectedFile) => {
    if (!selectedFile || !selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setError("Seleziona un file PDF valido.");
      setFile(null);
      return;
    }
    setFile(selectedFile);
    setError(null);
    setResult(null);
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer?.files?.[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const onDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };
  const onDragLeave = () => setDragging(false);

  const onUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await convertPdf(file);
      setResult(data);

      const blob = await downloadFile(data.file_name);

      // Prova File System Access API (finestra "Salva con nome")
      if ("showSaveFilePicker" in window) {
        try {
          const handle = await window.showSaveFilePicker({
            suggestedName: data.file_name,
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
          return;
        } catch {
          return;
        }
      }

      // Fallback: download diretto
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = data.file_name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message || "Errore durante la conversione");
    } finally {
      setLoading(false);
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
            ? "Rilascia il file qui"
            : "Trascina il PDF qui o clicca per caricarlo"}
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
              Conversione in corso...
            </>
          ) : (
            <>
              <Download size={18} />
              Converti in Excel
            </>
          )}
        </button>
      )}

      {/* Error */}
      {error && (
        <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
          {error}
        </div>
      )}

      {/* Success */}
      {result && (
        <div className="text-green-400 text-sm bg-green-500/10 border border-green-500/20 rounded-xl px-4 py-3">
          Conversione completata con successo! Il file Excel è stato salvato.
        </div>
      )}
    </div>
  );
}
