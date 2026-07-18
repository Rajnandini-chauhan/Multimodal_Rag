import { useRef, useState } from "react";
import { paperApi } from "../services/api";

export default function PaperUpload({ onUploaded }) {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  async function handleFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are accepted.");
      return;
    }

    setError("");
    setUploading(true);
    setProgress(0);

    try {
      const res = await paperApi.upload(file, (progressEvent) => {
        const percent = Math.round(
          (progressEvent.loaded / progressEvent.total) * 100
        );
        setProgress(percent);
      });
      onUploaded(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed. Try again.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFile(e.dataTransfer.files[0]);
      }}
      onClick={() => inputRef.current?.click()}
      className={`border-2 border-dashed rounded-sm p-8 text-center cursor-pointer transition-colors ${
        dragOver
          ? "border-indigo bg-indigo/5"
          : "border-pencil-light hover:border-pencil"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />

      {uploading ? (
        <div>
          <p className="font-mono text-sm text-pencil mb-2">
            uploading... {progress}%
          </p>
          <div className="h-1.5 bg-pencil-light rounded-full overflow-hidden max-w-xs mx-auto">
            <div
              className="h-full bg-indigo transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      ) : (
        <>
          <p className="font-display text-lg text-ink">
            Drop a paper here, or click to browse
          </p>
          <p className="mt-1 font-mono text-xs text-pencil">PDF only</p>
        </>
      )}

      {error && <p className="mt-3 text-sm text-danger">{error}</p>}
    </div>
  );
}