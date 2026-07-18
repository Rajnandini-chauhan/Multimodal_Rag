import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register(email, password);
      navigate("/");
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Something went wrong. Try again."
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
            set up your desk
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
              password (min 8 characters)
            </label>
            <input
              type="password"
              required
              minLength={8}
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
            {submitting ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-pencil">
          Already have an account?{" "}
          <Link to="/login" className="text-indigo hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}