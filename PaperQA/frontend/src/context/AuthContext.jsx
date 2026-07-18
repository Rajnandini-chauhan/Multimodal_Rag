import { createContext, useContext, useEffect, useState } from "react";
import { authApi } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On first load, if a token is already stored, try to resolve who it
  // belongs to -- this is what keeps a user logged in across page refreshes.
  useEffect(() => {
    const token = localStorage.getItem("paperqa_token");
    if (!token) {
      setLoading(false);
      return;
    }

    authApi
      .me()
      .then((res) => setUser(res.data))
      .catch(() => localStorage.removeItem("paperqa_token"))
      .finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    const res = await authApi.login(email, password);
    localStorage.setItem("paperqa_token", res.data.access_token);
    const me = await authApi.me();
    setUser(me.data);
  }

  async function register(email, password) {
    const res = await authApi.register(email, password);
    localStorage.setItem("paperqa_token", res.data.access_token);
    const me = await authApi.me();
    setUser(me.data);
  }

  function logout() {
    localStorage.removeItem("paperqa_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
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