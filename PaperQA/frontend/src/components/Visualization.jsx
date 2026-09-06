import { useEffect, useRef } from "react";

export default function Visualization({ spec }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!spec || !containerRef.current) return;

    let isMounted = true;

    function renderPlot() {
      if (window.Plotly && containerRef.current && isMounted) {
        window.Plotly.newPlot(
          containerRef.current,
          spec.data || [],
          spec.layout || { title: "Chart Visualization" },
          { responsive: true }
        );
      }
    }

    if (window.Plotly) {
      renderPlot();
    } else {
      const script = document.createElement("script");
      script.src = "https://cdn.plot.ly/plotly-2.27.0.min.js";
      script.async = true;
      script.onload = () => {
        if (isMounted) renderPlot();
      };
      document.body.appendChild(script);
    }

    return () => {
      isMounted = false;
    };
  }, [spec]);

  if (!spec) return null;

  return (
    <div className="mt-3 p-3 bg-paper-light border border-pencil-light rounded-sm">
      <div ref={containerRef} className="w-full min-h-[300px]" />
    </div>
  );
}
