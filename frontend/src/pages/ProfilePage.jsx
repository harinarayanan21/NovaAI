import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";

function ProfilePage() {
  const { user, updateProfile } = useAuth();
  const [form, setForm] = useState({
    full_name: user?.full_name || "",
    username: user?.username || "",
    profile_picture: user?.profile_picture || "",
  });
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const updateField = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setIsLoading(true);
    try {
      await updateProfile(form);
      setSuccess("Profile updated successfully.");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold text-white mb-6">Profile</h1>

      <div className="bg-neutral-900 border border-neutral-700/50 rounded-xl p-6">
        {/* Avatar */}
        <div className="flex items-center gap-4 mb-6 pb-6 border-b border-neutral-700/50">
          <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center text-accent text-xl font-bold">
            {user?.username?.charAt(0).toUpperCase() || "?"}
          </div>
          <div>
            <p className="text-white font-medium">{user?.username}</p>
            <p className="text-sm text-neutral-400">{user?.email}</p>
            <p className="text-xs text-neutral-500 mt-0.5">
              Member since {new Date(user?.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {success && (
            <div className="bg-green-500/10 border border-green-500/30 text-green-400 text-sm px-4 py-2.5 rounded-lg">
              {success}
            </div>
          )}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-4 py-2.5 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Full Name</label>
            <input
              type="text"
              value={form.full_name}
              onChange={updateField("full_name")}
              className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-800 border border-neutral-600 text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-accent transition-colors"
              placeholder="John Doe"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Username</label>
            <input
              type="text"
              value={form.username}
              onChange={updateField("username")}
              required
              minLength={3}
              className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-800 border border-neutral-600 text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-accent transition-colors"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Profile Picture URL</label>
            <input
              type="url"
              value={form.profile_picture}
              onChange={updateField("profile_picture")}
              className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-800 border border-neutral-600 text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-accent transition-colors"
              placeholder="https://example.com/avatar.jpg"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="px-5 py-2.5 rounded-lg bg-accent hover:bg-accent-hover text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? "Saving..." : "Save Changes"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default ProfilePage;
