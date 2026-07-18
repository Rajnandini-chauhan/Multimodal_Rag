const STATUS_LABEL = {
  pending: "queued",
  processing: "indexing",
  completed: "ready",
  failed: "failed",
};

export default function IngestionProgress({ job }) {
  if (!job) return null;

  const isFailed = job.status === "failed";
  const isDone = job.status === "completed";

  return (
    <div className="border border-pencil-light rounded-sm p-3 bg-white/50">
      <div className="flex items-center justify-between mb-1.5">
        <span className="font-mono text-xs text-pencil">
          {STATUS_LABEL[job.status] || job.status}
        </span>
        <span className="font-mono text-xs text-pencil">
          {job.progress_percent}%
        </span>
      </div>
      <div className="h-1.5 bg-pencil-light rounded-full overflow-hidden">
        <div
          className={`h-full transition-all ${
            isFailed ? "bg-danger" : isDone ? "bg-indigo" : "bg-highlight"
          }`}
          style={{ width: `${job.progress_percent}%` }}
        />
      </div>
      {isFailed && job.error_message && (
        <p className="mt-2 text-xs text-danger">{job.error_message}</p>
      )}
    </div>
  );
}