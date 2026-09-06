import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [darkMode, setDarkMode] = useState(() => {
    return (
      localStorage.getItem("theme") === "dark" ||
      (!("theme" in localStorage) &&
        window.matchMedia("(prefers-color-scheme: dark)").matches)
    );
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  return (
    <button
      onClick={() => setDarkMode(!darkMode)}
      className="p-1.5 rounded-md border border-pencil-light text-pencil hover:text-ink hover:border-indigo transition-all duration-200 text-xs flex items-center gap-1.5"
      title="Toggle Dark/Light Mode"
    >
      {darkMode ? (
        <>
          <span>🌙</span>
          <span className="font-mono hidden sm:inline">Dark</span>
        </>
      ) : (
        <>
          <span>☀️</span>
          <span className="font-mono hidden sm:inline">Light</span>
        </>
      )}
    </button>
  );
}
