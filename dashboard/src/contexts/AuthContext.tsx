import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { User } from '../types/users';
import { generateToken } from '../api/queryvault';

interface AuthState {
  user: User;
  jwt: string;
}

interface AuthContextValue {
  auth: AuthState | null;
  login: (user: User) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [loading, setLoading] = useState(false);

  const login = useCallback(async (user: User) => {
    setLoading(true);
    try {
      const result = await generateToken(user.oid);
      if (result.data) {
        setAuth({ user, jwt: result.data.jwt_token });
      } else {
        throw new Error(result.error ?? 'Failed to generate token');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => setAuth(null), []);

  return (
    <AuthContext.Provider value={{ auth, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
