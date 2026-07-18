export default function SourceViewer({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {sources.map((page) => (
        <span key={page} className="citation-tab">
          page {page}
        </span>
      ))}
    </div>
  );
}