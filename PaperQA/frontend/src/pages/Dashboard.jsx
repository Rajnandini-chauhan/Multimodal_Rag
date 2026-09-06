import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { paperApi } from "../services/api";
import { useAuth } from "../context/AuthContext";
import PaperUpload from "../components/PaperUpload";
import IngestionProgress from "../components/IngestionProgress";
import ThemeToggle from "../components/ThemeToggle";

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
    await paperApi.startIndexing(paper.id);
    navigate(`/papers/${paper.id}`);
  }

  return (
    <div className="min-h-screen transition-colors duration-200">
      <header className="border-b border-pencil-light px-6 py-4 flex items-center justify-between backdrop-blur-md bg-paper/80 sticky top-0 z-10">
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">PaperQA</h1>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <span className="font-mono text-xs text-pencil">{user?.email}</span>
          <button
            onClick={logout}
            className="text-xs font-mono text-pencil hover:text-ink transition-colors"
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
            <p className="text-sm text-pencil font-mono">loading...</p>
          ) : papers.length === 0 ? (
            <p className="text-sm text-pencil">
              Nothing uploaded yet. Drop a PDF above to get started.
            </p>
          ) : (
            <ul className="space-y-3">
              {papers.map((paper) => (
                <li key={paper.id}>
                  <button
                    onClick={() => navigate(`/papers/${paper.id}`)}
                    className="w-full text-left border border-pencil-light rounded-md p-4 hover:border-indigo transition-all duration-200 bg-paper-dim/40 hover:bg-paper-dim/80 shadow-sm"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="min-w-0">
                        <p className="font-display text-base truncate font-medium text-ink">
                          {paper.original_filename}
                        </p>
                        <p className="font-mono text-xs text-pencil mt-1">
                          {paper.page_count ? `${paper.page_count} pages` : ""}
                        </p>
                      </div>
                      <div className="w-36 shrink-0">
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