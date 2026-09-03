import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { paperApi } from "../services/api";
import IngestionProgress from "../components/IngestionProgress";
import ChatWindow from "../components/ChatWindow";

const POLL_INTERVAL_MS = 2000;

export default function PaperChat() {
  const { paperId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reindexError, setReindexError] = useState("");
  const intervalRef = useRef(null);

  useEffect(() => {
    fetchStatus();
    intervalRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS);
    return () => clearInterval(intervalRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paperId]);

  async function fetchStatus() {
    try {
      const res = await paperApi.getStatus(paperId);
      setJob(res.data);
      if (res.data.status === "completed" || res.data.status === "failed") {
        clearInterval(intervalRef.current);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleReindex() {
    setReindexError("");
    try {
      await paperApi.startIndexing(paperId);
      // Restart polling so the user sees progress.
      intervalRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS);
      await fetchStatus();
    } catch (err) {
      setReindexError(
        err.response?.data?.detail || "Could not restart indexing."
      );
    }
  }

  const isReady = job?.status === "completed";
  const isFailed = job?.status === "failed";

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-pencil-light px-6 py-4 flex items-center justify-between">
        <Link
          to="/"
          className="font-display text-xl font-semibold hover:text-indigo transition-colors"
        >
          ← PaperQA
        </Link>
      </header>

      <main className="flex-1 max-w-3xl w-full mx-auto px-6 py-8 flex flex-col">
        {loading ? (
          <p className="text-sm text-pencil font-mono">loading...</p>
        ) : (
          <>
            {!isReady && (
              <div className="mb-6">
                <p className="font-mono text-xs text-pencil mb-2">
                  indexing this paper
                </p>
                <IngestionProgress job={job} />
                {isFailed && (
                  <div className="mt-3">
                    <button
                      onClick={handleReindex}
                      className="text-xs font-mono text-indigo hover:underline"
                    >
                      try re-indexing this paper
                    </button>
                    {reindexError && (
                      <p className="mt-1 text-xs text-danger">{reindexError}</p>
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="flex-1 border border-pencil-light rounded-sm bg-white/40 min-h-[60vh]">
              <ChatWindow paperId={paperId} disabled={!isReady} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}
