import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { paperApi } from "../services/api";
import { useAuth } from "../context/AuthContext";
import PaperUpload from "../components/PaperUpload";
import IngestionProgress from "../components/IngestionProgress";

export default function Dashboard() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadPapers();
  }, []);

  async function loadPapers() {
    try {
      const res = await paperApi.list();
      setPapers(res.data);
    } finally {
      setLoading(false);
    }
  }

  async function handleUploaded(paper) {
    setPapers((prev) => [paper, ...prev]);
    // Kick off indexing right away, then send the user to the chat page
    // where they'll watch progress and can start asking questions.
    await paperApi.startIndexing(paper.id);
    navigate(`/papers/${paper.id}`);
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-pencil-light px-6 py-4 flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold">PaperQA</h1>
        <div className="flex items-center gap-4">
          <span className="font-mono text-xs text-pencil">{user?.email}</span>
          <button
            onClick={logout}
            className="text-xs text-pencil hover:text-ink underline"
          >
            log out
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-10">
        <PaperUpload onUploaded={handleUploaded} />

        <div className="mt-10">
          <h2 className="font-mono text-xs uppercase tracking-wide text-pencil mb-3">
            your papers
          </h2>

          {loading ? (
            <p className="text-sm text-pencil">loading...</p>
          ) : papers.length === 0 ? (
            <p className="text-sm text-pencil">
              Nothing uploaded yet. Drop a PDF above to get started.
            </p>
          ) : (
            <ul className="space-y-2">
              {papers.map((paper) => (
                <li key={paper.id}>
                  <button
                    onClick={() => navigate(`/papers/${paper.id}`)}
                    className="w-full text-left border border-pencil-light rounded-sm p-3 hover:border-indigo transition-colors bg-white/40"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="min-w-0">
                        <p className="font-display text-base truncate">
                          {paper.original_filename}
                        </p>
                        <p className="font-mono text-xs text-pencil">
                          {paper.page_count ? `${paper.page_count} pages` : ""}
                        </p>
                      </div>
                      <div className="w-32 shrink-0">
                        <IngestionProgress job={paper.ingestion_job} />
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  );
}