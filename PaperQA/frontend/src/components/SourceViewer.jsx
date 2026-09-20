export default function SourceViewer({ sources, figures, tables }) {
  const safeSources = Array.isArray(sources) ? sources : [];
  const safeFigures = Array.isArray(figures) ? figures : [];
  const safeTables = Array.isArray(tables) ? tables : [];

  const hasAny = safeSources.length > 0 || safeFigures.length > 0 || safeTables.length > 0;
  if (!hasAny) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {safeSources.map((page) => (
        <span key={`p-${page}`} className="citation-tab">
          page {page}
        </span>
      ))}
      {safeFigures.map((n) => (
        <span key={`f-${n}`} className="citation-tab citation-tab-figure">
          Figure {n}
        </span>
      ))}
      {safeTables.map((n) => (
        <span key={`t-${n}`} className="citation-tab citation-tab-table">
          Table {n}
        </span>
      ))}
    </div>
  );
}
