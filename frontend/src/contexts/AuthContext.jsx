import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { authApi, userApi } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const { data } = await userApi.getProfile();
      setUser(data);
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (email, password) => {
    const { data } = await authApi.login(email, password);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    await loadUser();
  };

  const register = async (username, email, password, fullName) => {
    const { data } = await authApi.register(username, email, password, fullName);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    await loadUser();
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Logout is best-effort; clear local state regardless.
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  const updateProfile = async (fields) => {
    const { data } = await userApi.updateProfile(fields);
    setUser(data);
  };

  return (
    <AuthContext.Provider
      value={{ user, isLoading, login, register, logout, updateProfile, loadUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
