import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(
        err.response?.data?.detail || "Something went wrong. Try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="font-display text-3xl font-semibold text-ink">
            PaperQA
          </h1>
          <p className="mt-1 font-mono text-xs text-pencil">
            log in to your desk
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="border border-pencil-light bg-white/60 rounded-sm p-6 space-y-4"
        >
          {error && (
            <p className="text-sm text-danger border-l-2 border-danger pl-2">
              {error}
            </p>
          )}

          <div>
            <label className="block text-xs font-mono text-pencil mb-1">
              email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-pencil-light rounded-sm px-3 py-2 text-sm bg-paper focus:outline-none focus:ring-2 focus:ring-indigo"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-pencil mb-1">
              password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-pencil-light rounded-sm px-3 py-2 text-sm bg-paper focus:outline-none focus:ring-2 focus:ring-indigo"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-indigo hover:bg-indigo-dim text-white text-sm font-medium py-2 rounded-sm transition-colors disabled:opacity-50"
          >
            {submitting ? "Logging in..." : "Log in"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-pencil">
          No account yet?{" "}
          <Link to="/register" className="text-indigo hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}