export default function SourceViewer({ sources = [], figures = [], tables = [] }) {
  const hasAny = sources.length > 0 || figures.length > 0 || tables.length > 0;
  if (!hasAny) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {sources.map((page) => (
        <span key={`p-${page}`} className="citation-tab">
          page {page}
        </span>
      ))}
      {figures.map((n) => (
        <span key={`f-${n}`} className="citation-tab citation-tab-figure">
          Figure {n}
        </span>
      ))}
      {tables.map((n) => (
        <span key={`t-${n}`} className="citation-tab citation-tab-table">
          Table {n}
        </span>
      ))}
    </div>
  );
}
