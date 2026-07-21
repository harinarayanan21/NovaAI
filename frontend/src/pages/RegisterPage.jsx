import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    fullName: "",
  });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const updateField = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      await register(form.username, form.email, form.password, form.fullName || null);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#212121] px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-accent" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white">Create account</h1>
          <p className="text-neutral-400 text-sm mt-1">Get started with AI Assistant</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-neutral-900 border border-neutral-700/50 rounded-xl p-6 space-y-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-4 py-2.5 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Username</label>
            <input
              type="text"
              value={form.username}
              onChange={updateField("username")}
              required
              minLength={3}
              className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-800 border border-neutral-600 text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-accent transition-colors"
              placeholder="Choose a username"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={updateField("email")}
              required
              className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-800 border border-neutral-600 text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-accent transition-colors"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Full Name (optional)</label>
            <input
              type="text"
              value={form.fullName}
              onChange={updateField("fullName")}
              className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-800 border border-neutral-600 text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-accent transition-colors"
              placeholder="John Doe"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Password</label>
            <input
              type="password"
              value={form.password}
              onChange={updateField("password")}
              required
              minLength={8}
              className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-800 border border-neutral-600 text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-accent transition-colors"
              placeholder="Min 8 chars, uppercase, lowercase, digit"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Confirm Password</label>
            <input
              type="password"
              value={form.confirmPassword}
              onChange={updateField("confirmPassword")}
              required
              className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-800 border border-neutral-600 text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-accent transition-colors"
              placeholder="Re-enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 rounded-lg bg-accent hover:bg-accent-hover text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="text-center text-sm text-neutral-400 mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

export default RegisterPage;
