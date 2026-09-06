import { createContext, useContext, useEffect, useState } from "react";
import * as api from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("careerai_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .getCurrentUser()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("careerai_token");
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    await api.login({ email, password });
    const me = await api.getCurrentUser();
    setUser(me);
    return me;
  }

  async function signup(name, email, password) {
    await api.signup({ name, email, password });
    return login(email, password);
  }

  function logout() {
    api.logout();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
